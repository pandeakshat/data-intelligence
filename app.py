# app.py
import streamlit as st
import pandas as pd
import os
from src.loaders import load_data

st.set_page_config(page_title="Data Intelligence Hub", layout="wide")
SAMPLES_DIR = "data/samples"

st.title("Data Intelligence Hub")

# --- SIDEBAR (Keep existing logic) ---
with st.sidebar:
    st.header("Data Source")
    mode = st.radio("Input Method", ["Upload File", "Use Sample Data"])
    
    df = None
    filename = None
    
    if mode == "Upload File":
        uploaded_file = st.file_uploader("Upload CSV or Excel", type=['csv', 'xlsx'])
        if uploaded_file:
            try:
                df = load_data(uploaded_file, uploaded_file.name)
                filename = uploaded_file.name
            except Exception as e:
                st.error(f"Error: {e}")
                
    elif mode == "Use Sample Data":
        if not os.path.exists(SAMPLES_DIR):
            os.makedirs(SAMPLES_DIR, exist_ok=True)
        available_files = [f for f in os.listdir(SAMPLES_DIR) if f.endswith(('.csv', '.xlsx'))]
        if available_files:
            selected_sample = st.selectbox("Select a Sample", available_files)
            if selected_sample:
                df = load_data(os.path.join(SAMPLES_DIR, selected_sample), selected_sample)
                filename = selected_sample

    if df is not None:
        st.session_state['df'] = df
        st.session_state['filename'] = filename

# --- MAIN SCREEN SNAPSHOT ---
if st.session_state.get('df') is not None:
    df = st.session_state['df']
    fname = st.session_state['filename']
    
    # 1. Header
    st.success(f"**Active Dataset:** {fname}")
    
    # 2. The "Quick Profile" Container
    with st.container(border=True):
        st.subheader("⚡ Data Snapshot")
        
        # Row 1: Big Numbers
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", df.shape[0])
        c2.metric("Columns", df.shape[1])
        
        # Calculate Missing %
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        missing_pct = (missing_cells / total_cells) * 100
        c3.metric("Global Missingness", f"{missing_pct:.1f}%")
        
        # Calculate Type Dominance
        numeric_cols = len(df.select_dtypes(include='number').columns)
        c4.metric("Numeric Columns", f"{numeric_cols} / {df.shape[1]}")

        # Row 2: Type Breakdown & Head
        col_types, col_head = st.columns([1, 2])
        
        with col_types:
            st.markdown("**Column Types:**")
            st.write(df.dtypes.value_counts())
            
        with col_head:
            st.markdown("**Preview (First 3 Rows):**")
            st.dataframe(df.head(3), use_container_width=True, hide_index=True)

    st.info("👈 Use the sidebar navigation to access the **Audit Dashboard** or **Data Bridge**.")

else:
    st.markdown("### Welcome to Data Intelligence.")
    st.write("Please select a dataset to see the analysis.")