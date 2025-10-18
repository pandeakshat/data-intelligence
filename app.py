import streamlit as st
import pandas as pd
from utils.validate_data import audit_dataset
from utils.load_data import load_dataset

st.set_page_config(page_title="Data Audit Tool", layout="wide")

st.title("🔍 Data Audit & Validation Dashboard")
st.caption("Streamlit-based diagnostic tool that audits datasets — not alters them.")

uploaded_file = st.file_uploader("Upload your dataset (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    try:
        df = load_dataset(uploaded_file)
        st.success(f"✅ File loaded successfully: {uploaded_file.name}")

        # Tabs
        summary_tab, cleaning_tab, ml_tab = st.tabs(["📊 Summary", "🧼 Cleaning Standards", "🤖 ML Readiness"])

        # ===============================
        # TAB 1: SUMMARY
        # ===============================
        with summary_tab:
            st.subheader("Dataset Summary")
            st.markdown("A quick overview of structure, missing values, and data types.")
            
            report = audit_dataset(df)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Rows", report["shape"][0])
            with col2:
                st.metric("Columns", report["shape"][1])

            st.write("**Data Types**")
            st.json(report["data_types"])

            st.write("**Missing Values (%)**")
            missing_percent = (df.isnull().mean() * 100).round(2)
            st.bar_chart(missing_percent)

            st.caption("💡 Tip: Columns with >30% missing data may need imputation or removal.")

        # ===============================
        # TAB 2: DATA CLEANING STANDARDS
        # ===============================
        with cleaning_tab:
            st.subheader("Data Cleaning Standards & Summary")
            st.markdown("Summary of missing values, averages, and outlier detection readiness.")

            st.write("**Null Values Summary**")
            st.dataframe(df.isnull().sum().reset_index().rename(columns={0: "Null Count"}))

            st.write("**Numeric Columns Summary (Mean, Std, etc.)**")
            st.dataframe(df.describe())

            st.caption("💡 Tip: Consider imputing numeric columns using mean/median if missing <10%, else review column importance.")

        # ===============================
        # TAB 3: ML READINESS
        # ===============================
        with ml_tab:
            st.subheader("Machine Learning Readiness Overview")
            st.markdown("Evaluates dataset structure and readiness for ML models.")

            st.metric("ML Readiness Score", report["ml_readiness_score"])

            st.write("**Feature Insights**")
            st.json({
                "Numeric Columns": list(df.select_dtypes(include=['number']).columns),
                "Categorical Columns": list(df.select_dtypes(include=['object', 'category']).columns)
            })

            st.markdown("### Model Compatibility Check")
            st.info("💡 For example, tree-based models (like Random Forest) handle missing values better than linear regression. Upcoming versions will analyze per-model readiness.")

        # ===============================
        # FOOTER
        # ===============================
        st.markdown("---")
        st.markdown("Need professional data preparation? [Hire me for dataset correction and ML prep.](mailto:mail@pandeakshat.com)")

    except Exception as e:
        st.error(f"⚠️ {e}")
