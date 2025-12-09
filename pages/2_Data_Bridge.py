import streamlit as st
import os
import pandas as pd
from src.wrangler import (
    load_schema_config, recommend_mappings, split_column, 
    fill_missing, rename_and_export, anonymize_column
)
from src.loaders import load_data
from src.profiler import scan_for_pii

# --- CONFIG ---
SCHEMAS_DIR = "data/schemas"
SAMPLES_BASE = "data/samples" # Base folder for samples

st.set_page_config(page_title="Data Bridge", layout="wide")

st.title("🛠️ Data Bridge")
st.markdown("### Prepare. Align. Secure.")

# --- STEP 0: INITIALIZATION & SCHEMA LOAD ---
if not os.path.exists(SCHEMAS_DIR):
    os.makedirs(SCHEMAS_DIR, exist_ok=True)
    
available_schemas = [f for f in os.listdir(SCHEMAS_DIR) if f.endswith('.yml')]

if not available_schemas:
    st.error(f"❌ No schemas found in `{SCHEMAS_DIR}`.")
    st.stop()

# Task Selection
col_task, col_desc = st.columns([1, 2])
with col_task:
    selected_schema_file = st.selectbox("1. Select Target Task", available_schemas)
    
schema = load_schema_config(os.path.join(SCHEMAS_DIR, selected_schema_file))

with col_desc:
    st.info(f"**Target:** {schema.get('target_name')} \n\n {schema.get('description', 'No description.')}")

st.divider()

# --- STEP 1: INGESTION (Task Specific) ---
if 'bridge_df' not in st.session_state:
    st.session_state['bridge_df'] = None

col_upload, col_sample = st.columns([1, 1])

# --- OPTION A: UPLOAD ---
with col_upload:
    st.markdown("#### Option A: Upload New File")
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=['csv', 'xlsx'], key="bridge_uploader")
    if uploaded_file:
        try:
            df = load_data(uploaded_file, uploaded_file.name)
            st.session_state['bridge_df'] = df
            st.rerun() # Refresh to show analysis immediately
        except Exception as e:
            st.error(f"Load Error: {e}")

# --- OPTION B: SAMPLES (Dynamic Folder Selection) ---
with col_sample:
    st.markdown("#### Option B: Use Task Sample")
    
    # Determine the correct sample sub-folder based on schema filename
    if "sales" in selected_schema_file.lower():
        target_sample_folder = os.path.join(SAMPLES_BASE, "sales_bridge")
    elif "customer" in selected_schema_file.lower():
        target_sample_folder = os.path.join(SAMPLES_BASE, "customer_bridge")
    else:
        target_sample_folder = SAMPLES_BASE # Fallback
    
    # Check if folder exists and has files
    sample_options = []
    if os.path.exists(target_sample_folder):
        sample_options = [f for f in os.listdir(target_sample_folder) if f.endswith(('.csv', '.xlsx'))]
    
    if sample_options:
        # Add a placeholder at the start
        selected_sample = st.selectbox("Select a Sample File", ["-- Select --"] + sample_options)
        
        if selected_sample != "-- Select --":
            # Load Button to confirm choice
            if st.button(f"Load {selected_sample}", type="secondary"):
                try:
                    full_path = os.path.join(target_sample_folder, selected_sample)
                    df = load_data(full_path, selected_sample)
                    st.session_state['bridge_df'] = df
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading sample: {e}")
    else:
        st.info(f"No samples found in `{target_sample_folder}`.")
        if not os.path.exists(target_sample_folder):
            os.makedirs(target_sample_folder, exist_ok=True) # Create it so user knows where to put files

# --- MAIN WORKFLOW ---
if st.session_state['bridge_df'] is not None:
    df = st.session_state['bridge_df']
    
    # --- STEP 2: PRIMARY ANALYSIS (Gap & Privacy Check) ---
    st.header("3. Primary Analysis")
    
    # A. Schema Fit
    recommendations = recommend_mappings(df, schema)
    req_cols = [c for c in schema['columns'] if c['required']]
    found_count = sum(1 for c in req_cols if recommendations.get(c['name']))
    
    # B. PII Scan
    pii_results = scan_for_pii(df)
    
    # Display Dashboard
    c1, c2, c3 = st.columns(3)
    
    c1.metric("Row Count", df.shape[0])
    
    c2.metric("Schema Fit", f"{found_count}/{len(req_cols)} Required")
    if found_count == len(req_cols):
        c2.success("Structure Matches ✅")
    else:
        c2.warning(f"Missing {len(req_cols) - found_count} columns")
        
    c3.metric("Privacy Risk", f"{len(pii_results)} Flags")
    if pii_results:
        c3.error("Sensitive Data Detected")
    else:
        c3.success("No PII Detected")

    # Details Expanders
    col_gap, col_pii = st.columns(2)
    
    with col_gap:
        with st.expander("🔎 View Schema Gap Analysis", expanded=True):
            gap_data = []
            for col in schema['columns']:
                status = "✅ Found" if recommendations.get(col['name']) else "❌ Missing"
                gap_data.append({"Target": col['name'], "Status": status, "Suggested Map": recommendations.get(col['name'], "-")})
            st.dataframe(pd.DataFrame(gap_data), use_container_width=True, hide_index=True)

    with col_pii:
        with st.expander("🛡️ View Privacy Risks", expanded=True):
            if pii_results:
                st.dataframe(pd.DataFrame(list(pii_results.items()), columns=["Column", "Detected Type"]), use_container_width=True, hide_index=True)
                st.caption("Use the 'Privacy & Anonymization' tool below to fix these.")
            else:
                st.success("Clean. No standard PII patterns found.")

    st.divider()

    # --- STEP 3: ALIGNMENT WORKBENCH ---
    st.header("4. Alignment Workbench")
    
    tab_map, tab_wrangle = st.tabs(["🔗 Schema Mapping", "🛠️ Transformation Tools"])
    
    # --- TAB A: MAPPING ---
    final_map = {}
    missing_required = []
    
    with tab_map:
        st.caption("Map your columns to the target schema.")
        col_container = st.container()
        
        # Grid Layout for Mapping
        for target_col in schema['columns']:
            t_name = target_col['name']
            t_req = target_col['required']
            suggested = recommendations.get(t_name)
            
            c_lbl, c_inp, c_stat = st.columns([2, 2, 0.5])
            
            label = f"**{t_name}**" + (" <span style='color:red'>*</span>" if t_req else "")
            c_lbl.markdown(label, unsafe_allow_html=True)
            
            options = ["-- MISSING --"] + list(df.columns)
            default_idx = options.index(suggested) if suggested in options else 0
            
            selection = c_inp.selectbox(f"Map {t_name}", options, index=default_idx, key=f"map_{t_name}", label_visibility="collapsed")
            final_map[t_name] = selection
            
            if selection == "-- MISSING --":
                if t_req:
                    c_stat.write("❌")
                    missing_required.append(t_name)
                else:
                    c_stat.write("⚠️")
            else:
                c_stat.write("✅")

    # --- TAB B: WRANGLING TOOLS ---
    with tab_wrangle:
        st.info("Modifications here update the Active Dataset immediately.")
        
        # Tool 1: Split
        with st.expander("✂️ Split Column"):
            c_s1, c_s2, c_s3 = st.columns(3)
            split_target = c_s1.selectbox("Column to Split", df.columns)
            delimiter = c_s2.text_input("Delimiter", "_")
            new_names = c_s3.text_input("New Names (comma sep)", "Part1,Part2")
            
            if st.button("Apply Split"):
                try:
                    df = split_column(df, split_target, delimiter, [x.strip() for x in new_names.split(',')])
                    st.session_state['bridge_df'] = df
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        # Tool 2: Fill
        with st.expander("🩸 Fill Missing Values"):
            c_f1, c_f2, c_f3 = st.columns(3)
            fill_target = c_f1.selectbox("Column", df.columns, key='fill')
            method = c_f2.radio("Method", ["Static Value", "Mean", "Forward Fill"])
            val = c_f3.text_input("Value (if Static)")
            
            if st.button("Apply Fill"):
                df = fill_missing(df, fill_target, method, val)
                st.session_state['bridge_df'] = df
                st.rerun()
                
        # Tool 3: Anonymization
        with st.expander("🛡️ Privacy & Anonymization"):
            c_p1, c_p2 = st.columns(2)
            anon_target = c_p1.selectbox("Sensitive Column", df.columns, key='anon')
            anon_method = c_p2.selectbox("Technique", ["Masking (***)", "Hashing (SHA256)", "Generalization (Numeric Bins)"])
            
            st.warning(f"This will permanently alter '{anon_target}' in the export.")
            if st.button("Apply Anonymization"):
                try:
                    df = anonymize_column(df, anon_target, anon_method)
                    st.session_state['bridge_df'] = df
                    st.success(f"Applied {anon_method} to {anon_target}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()

    # --- STEP 4: TRANSPORT ---
    st.header("5. Transport")
    
    if missing_required:
        st.error(f"⛔ Cannot export. Missing Required Columns: {', '.join(missing_required)}")
        st.button("💾 Export & Launch", disabled=True)
    else:
        if st.button("💾 Export Standardized Dataset", type="primary"):
            final_df = rename_and_export(df, final_map)
            
            os.makedirs("assets", exist_ok=True)
            save_path = "assets/ready_for_transport.csv"
            final_df.to_csv(save_path, index=False)
            
            st.success("File Standardized & Saved!")
            
            target_url = schema.get('url', '#')
            st.markdown(f"""
                <a href="{target_url}" target="_blank">
                    <button style="background-color: #4CAF50; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer;">
                        🚀 Launch {schema['target_name']}
                    </button>
                </a>
            """, unsafe_allow_html=True)

else:
    st.info("👆 Please upload a file or select a sample to begin.")