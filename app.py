import streamlit as st
import pandas as pd
from utils.validate import audit_dataset
from utils.load import load_dataset
import os
import seaborn as sns

# List available sample datasets
# Example: load and save a few
datasets = ["titanic", "iris", "tips", "flights"]
for name in datasets:
    df = sns.load_dataset(name)
    df.to_csv(f"assets/{name}.csv", index=False)

st.set_page_config(page_title="Data Audit Tool", layout="wide")

st.title("Data Audit & Validation Dashboard")
st.caption("Streamlit-based diagnostic tool that audits datasets — not alters them.")

# -----------------------------
# SIDEBAR: DATA LOADING OPTIONS
# -----------------------------
st.sidebar.subheader("Load Data")
data_choice = st.sidebar.radio("Choose Data Source", ["Upload Your Own", "Use Example Dataset"])

df = None
if data_choice == "Use Example Dataset":
    sample_files = [f for f in os.listdir("assets") if f.endswith((".csv", ".xlsx"))]
    if sample_files:
        sample_selected = st.sidebar.selectbox("Select a sample file:", sample_files)
        df = load_dataset(f"assets/{sample_selected}")
        st.success(f"Loaded example dataset: {sample_selected}")
    else:
        st.warning("No example datasets found in the assets folder.")
else:
    uploaded_file = st.sidebar.file_uploader("Upload your dataset (CSV or Excel)", type=["csv", "xlsx"])
    if uploaded_file:
        df = load_dataset(uploaded_file)
        st.success(f"File loaded successfully: {uploaded_file.name}")

# -----------------------------
# MAIN APP LOGIC
# -----------------------------
if df is not None:
    try:
        report = audit_dataset(df)
        summary_tab, cleaning_tab, readiness_tab = st.tabs(["Summary", "Data Cleaning Standards", "Readiness"])

        # SUMMARY TAB
        with summary_tab:
            st.subheader("Dataset Summary")
            st.markdown("Overview of structure, missing values, and data types.")
            col1, col2 = st.columns(2)
            with col1: st.metric("Rows", report["shape"][0])
            with col2: st.metric("Columns", report["shape"][1])

            st.write("Data Types and Classification")
            st.dataframe(pd.DataFrame({
                "Column": df.columns,
                "Data Type": [report["data_types"][c] for c in df.columns],
                "Category": [report["column_classification"][c] for c in df.columns]
            }))

            st.write("Missing Values (%)")
            missing_percent = (df.isnull().mean() * 100).round(2)
            st.bar_chart(missing_percent)

            st.write("Non-Conforming Columns")
            st.dataframe(pd.DataFrame.from_dict(report["type_conformity_filtered"], orient="index", columns=["Assessment"]))

            st.caption("Columns with high missing data or misclassified types may affect analysis quality.")

        # CLEANING TAB
        with cleaning_tab:
            st.subheader("Data Cleaning Standards & Summary")
            null_summary = df.isnull().sum()
            null_summary = null_summary[null_summary > 0]
            if not null_summary.empty:
                st.write("Columns with Missing Values")
                st.dataframe(null_summary.rename("Null Count"))
            else:
                st.success("No missing values found.")

            st.write("Numeric Columns Summary")
            st.dataframe(df.describe())

            st.write("Outlier Overview")
            st.dataframe(pd.DataFrame.from_dict(report["outliers"], orient="index"))

            st.subheader("Additional Data Quality Issues")
            st.json(report["additional_quality_issues"])

        # READINESS TAB
        with readiness_tab:
            st.subheader("Readiness Overview")
            readiness_type = st.radio("Select Readiness Type", ["Analysis", "Dashboard", "Machine Learning"], horizontal=True)

            if readiness_type == "Analysis":
                st.write("Focus: Clean, complete, interpretable data for exploration and descriptive analytics.")
                st.metric("Readiness Score", report["readiness_score"])
                st.caption(report["readiness_interpretation"])

            elif readiness_type == "Dashboard":
                dash = report["dashboard_readiness"]
                st.write("Focus: Temporal, categorical, and PII consistency for business dashboards.")
                st.metric("Dashboard Readiness Score", dash["dashboard_readiness_score"])
                st.caption(dash["interpretation"])
                st.write("Detected Temporal Columns:", dash["temporal_columns"])
                st.write("Detected Categorical Columns:", dash["categorical_columns"])
                st.write("Detected PII Columns:", dash["pii_columns"])

            elif readiness_type == "Machine Learning":
                st.write("Focus: Suitability for ML algorithms such as regression, classification, or clustering.")
                st.metric("Overall ML Readiness Score", report["readiness_score"])
                st.caption(report["readiness_interpretation"])
                st.subheader("Model-Specific Readiness")
                model_df = pd.DataFrame([
                    {"Model": m, "Score": report["model_readiness"][m]["score"], "Interpretation": report["model_readiness"][m]["interpretation"]}
                    for m in report["model_readiness"]
                ])
                st.dataframe(model_df)

        # FLOATING CONTACT BAR
        st.markdown("""
            <style>
            .contact-bar {
                position: fixed;
                bottom: 20px;
                right: 25px;
                background-color: #2c3e50;
                color: white;
                padding: 10px 18px;
                border-radius: 8px;
                font-size: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                z-index: 100;
            }
            .contact-bar a {
                color: #ffffff;
                text-decoration: none;
                font-weight: 500;
            }
            .contact-bar:hover {
                background-color: #34495e;
            }
            </style>
            <div class="contact-bar">
                For Professional Assistance — <a href="mailto:mail@pandeakshat.com" target="_blank">Contact</a>
            </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error processing dataset: {e}")
else:
    st.info("Please upload a dataset or select an example to begin.")
