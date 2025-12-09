import streamlit as st
import pandas as pd
import altair as alt

# Import our new Backend Brains
from src.profiler import generate_profile
from src.outliers import detect_anomalies
from src.scorer import calculate_readiness_score, assess_model_suitability


st.set_page_config(page_title="Audit Dashboard", layout="wide")

if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("Please upload a dataset on the Home Page first.")
    st.stop()

df = st.session_state['df']

st.title(f"📊 Audit Report: {st.session_state.get('filename', 'Dataset')}")

# --- SECTION 1: THE SCORECARD (Top Level) ---
score_data = calculate_readiness_score(df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("ML Readiness", f"{score_data['score']}/100", delta=score_data['grade'])
col2.metric("Rows", df.shape[0])
col3.metric("Columns", df.shape[1])
col4.metric("Duplicates", df.duplicated().sum())

if score_data['penalties']:
    with st.expander("📉 Why did I lose points?"):
        for p in score_data['penalties']:
            st.error(p)

# --- SECTION 2: DEEP DIVE TABS ---
tab_profile, tab_outliers, tab_stats = st.tabs(["📋 Schema Profile", "⚠️ Outlier Detection", "📈 Distributions"])

# --- TAB 1: SCHEMA PROFILE ---
with tab_profile:
    st.caption("Detailed breakdown of every column's health.")
    profile = generate_profile(df)
    
    # Convert dict to DF for display
    profile_df = pd.DataFrame.from_dict(profile, orient='index').reset_index()
    profile_df.columns = ['Column', 'DType', 'Kind', 'Unique Values', 'Nulls', 'Null %']
    
    # Style the dataframe (Highlight high nulls)
    st.dataframe(
        profile_df.style.background_gradient(subset=['Null %'], cmap='Reds'),
        use_container_width=True
    )

    st.subheader("🧠 Machine Learning Suitability")
    model_report = assess_model_suitability(df)

    tabs = st.tabs(model_report.keys())

    for tab, model_name in zip(tabs, model_report.keys()):
        with tab:
            data = model_report[model_name]
            
            # Display Score
            c1, c2 = st.columns([1, 3])
            c1.metric(f"{model_name} Score", f"{data['score']}/100")
            c2.info(data['desc'])
            
            # Add visual "Why" logic here if needed
            if data['score'] < 80:
                st.warning("Readiness is low. Check Missing Values tab for cleaning recommendations.")
# --- TAB 2: OUTLIER DETECTION (The "Hard Part") ---
with tab_outliers:
    st.caption("Using Isolation Forest (ML) and IQR (Statistical) to find anomalies.")
    
    if st.button("Run Advanced Outlier Detection"):
        with st.spinner("Training Isolation Forest..."):
            outlier_report = detect_anomalies(df)
            
        # Summary Metrics
        c1, c2 = st.columns(2)
        c1.metric("ML Anomalies Detected", outlier_report.get('ml_anomalies', 0))
        c2.metric("IQR Flags (Aggregated)", sum(outlier_report.get('iqr_outliers', {}).values()))
        
        # Visualization: If we have ML indices, let's plot them
        if 'ml_indices' in outlier_report and len(outlier_report['ml_indices']) > 0:
            st.subheader("Anomaly Visualization")
            
            # Create a subset with a label
            viz_df = df.select_dtypes(include='number').copy()
            viz_df['Status'] = 'Normal'
            viz_df.loc[outlier_report['ml_indices'], 'Status'] = 'Anomaly'
            
            # Scatter plot of the first two numeric columns (Simple Projection)
            if viz_df.shape[1] >= 3: # Need at least 2 numeric + status
                cols = viz_df.columns[:2]
                chart = alt.Chart(viz_df).mark_circle(size=60).encode(
                    x=cols[0],
                    y=cols[1],
                    color=alt.Color('Status', scale=alt.Scale(domain=['Normal', 'Anomaly'], range=['#dfe6e9', '#d63031'])),
                    tooltip=list(viz_df.columns)
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Not enough numeric columns to visualize scatter plot.")
                
            # Show the actual bad rows
            st.subheader("Inspect Flagged Rows")
            st.dataframe(df.iloc[outlier_report['ml_indices']].head(50))

# --- TAB 3: DISTRIBUTIONS ---
with tab_stats:
    numeric_cols = df.select_dtypes(include='number').columns
    if len(numeric_cols) > 0:
        target_col = st.selectbox("Visualize Distribution", numeric_cols)
        st.bar_chart(df[target_col].value_counts().sort_index())
    else:
        st.info("No numeric columns to visualize.")