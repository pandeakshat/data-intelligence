# Data Audit & Validation Dashboard

A **Streamlit-based data validation and readiness auditing tool** that provides structured insights on dataset quality, structure, and suitability for analysis, dashboards, and machine learning.

This tool is diagnostic — it does **not modify** data, but helps you understand what’s wrong, what’s missing, and how ready your dataset is for real-world use.

---

## 🚀 Features

### 1. **Dataset Summary**
- Basic structure and column overview
- Missing value percentages and visual chart
- Data type and semantic classification (Numeric, Categorical, Temporal, PII)
- Non-conforming column detection

### 2. **Data Cleaning Standards**
- Lists columns with missing values
- Numeric statistics summary
- Outlier detection overview
- Additional data quality issues:
  - Constant columns
  - High-cardinality columns
  - Mixed-type columns

### 3. **Readiness Evaluation**
Readiness is evaluated in three contexts:

| Mode | Focus | Scoring Basis |
|------|--------|---------------|
| **Analysis** | General data completeness and consistency | Nulls, data types, duplicates |
| **Dashboard** | Suitability for BI dashboards | Temporal coverage, categorical diversity, PII exposure |
| **Machine Learning** | Model-level audit for ML tasks | Numeric ratio, categorical ratio, missing values |

Each mode includes a readiness score (0–1) and a human-readable interpretation.

---

## 🧠 Model-Specific Readiness

For ML Readiness, the system evaluates how well the dataset fits three major model families:

| Model | Checks Performed | Scoring Logic |
|--------|------------------|---------------|
| **Regression** | Numeric data coverage and missing ratio | 0.6 × numeric ratio + 0.4 × completeness |
| **Classification** | Mix of numeric & categorical features + missing ratio | 0.5 × numeric + 0.3 × categorical + 0.2 × completeness |
| **Clustering** | Emphasis on numeric features and uniform completeness | 0.7 × numeric + 0.3 × completeness |

Each returns:
- **Score (0–1)** — overall readiness measure  
- **Note** — what the model type prefers  
- **Interpretation** — qualitative evaluation (Excellent / Moderate / Low)

This helps identify which types of ML workflows your data is *naturally suited* for, before any transformation or cleaning.

---

## 🧩 Tech Stack

- **Frontend**: Streamlit  
- **Data Processing**: Pandas, NumPy  
- **Language**: Python 3.10+  

---

## 📦 Project Structure

```
data-audit-app/
│
├── app.py                     # Streamlit frontend logic
├── utils/
│   ├── load.py                # Data loader with encoding fallback
│   └── validate.py            # Core validation and readiness logic
│
├── assets/                    # Example datasets (CSV/XLSX)
├── requirements.txt
└── README.md
```

---

## 🧮 How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

---

## 💡 Vision

A plug-and-play **data audit assistant** that helps teams:
- Diagnose dataset issues instantly
- Understand readiness for analytics or ML
- Streamline data quality assessment before heavy modeling

The app also includes a floating “Contact for Assistance” bar for professionals seeking help with deeper cleaning or preparation.

---

## 🧑‍💻 Author

**Akshat Pande**  
Data Scientist & AI Engineer  
📧 [mail@pandeakshat.com](mailto:mail@pandeakshat.com)  
🌐 [pandeakshat.com](https://pandeakshat.com)
