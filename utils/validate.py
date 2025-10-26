import pandas as pd
import numpy as np

# --------------------------------------------------------------------
# Column classification
# --------------------------------------------------------------------
def classify_column(col_name, series):
    """Classify a column as Numeric, Categorical, Temporal, or PII."""
    col_lower = col_name.lower()

    # Temporal detection (by dtype or name keywords)
    if np.issubdtype(series.dtype, np.datetime64) or any(k in col_lower for k in ["date", "time", "year", "month"]):
        return "Temporal"

    # PII detection (by column name keywords)
    pii_keywords = ["name", "email", "id", "phone", "address", "mobile", "user"]
    if any(k in col_lower for k in pii_keywords):
        return "PII"

    # Numeric vs categorical
    if np.issubdtype(series.dtype, np.number):
        return "Numeric"
    return "Categorical"


# --------------------------------------------------------------------
# Model-specific readiness evaluation
# --------------------------------------------------------------------
def evaluate_model_readiness(df, model_type):
    """Compute readiness for specific ML model categories."""
    numeric_ratio = len(df.select_dtypes(include=np.number).columns) / max(1, len(df.columns))
    missing_ratio = df.isnull().mean().mean()

    if model_type == "Regression":
        score = round((0.6 * numeric_ratio + 0.4 * (1 - missing_ratio)), 2)
        note = "Regression models require mostly numeric and complete data."

    elif model_type == "Classification":
        cat_ratio = len(df.select_dtypes(include=["object", "category"]).columns) / max(1, len(df.columns))
        score = round((0.5 * numeric_ratio + 0.3 * cat_ratio + 0.2 * (1 - missing_ratio)), 2)
        note = "Classification models need categorical balance and limited missing values."

    elif model_type == "Clustering":
        score = round((0.7 * numeric_ratio + 0.3 * (1 - missing_ratio)), 2)
        note = "Clustering algorithms prefer numeric data and consistent scaling."

    else:
        score = round(1 - missing_ratio, 2)
        note = "General ML readiness based on data completeness."

    if score >= 0.85:
        interp = "Excellent readiness for this model type."
    elif score >= 0.6:
        interp = "Moderate readiness; consider cleaning or encoding improvements."
    else:
        interp = "Low readiness; data requires significant preparation."

    return {"model_type": model_type, "score": score, "note": note, "interpretation": interp}


# --------------------------------------------------------------------
# Dashboard readiness evaluation
# --------------------------------------------------------------------
def evaluate_dashboard_readiness(df, classification_report):
    """
    Evaluate dashboard readiness based on:
    - Temporal consistency
    - Categorical diversity
    - PII presence
    - Duplicate integrity
    """
    score = 0
    max_score = 4

    temporal_cols = [c for c, v in classification_report.items() if v == "Temporal"]
    cat_cols = [c for c, v in classification_report.items() if v == "Categorical"]
    pii_cols = [c for c, v in classification_report.items() if v == "PII"]

    # Temporal consistency
    if temporal_cols:
        temporal_quality = 1
        for col in temporal_cols:
            null_ratio = df[col].isnull().mean()
            if null_ratio > 0.2:
                temporal_quality = 0.5
        score += temporal_quality

    # Categorical diversity
    if cat_cols:
        diversity_scores = []
        for col in cat_cols:
            unique_ratio = df[col].nunique() / len(df)
            if 0.01 <= unique_ratio <= 0.5:
                diversity_scores.append(1)
            elif unique_ratio < 0.01:
                diversity_scores.append(0.5)
            else:
                diversity_scores.append(0.7)
        score += np.mean(diversity_scores)

    # PII penalty
    pii_penalty = 0.8 if not pii_cols else 0.4
    score += pii_penalty

    # Duplicates penalty
    duplicate_ratio = df.duplicated().mean()
    duplicate_score = 1 - duplicate_ratio
    score += duplicate_score

    readiness_score = round(score / max_score, 2)

    if readiness_score >= 0.85:
        interp = "Excellent dashboard readiness — consistent and structured."
    elif readiness_score >= 0.6:
        interp = "Moderate readiness — review temporal and categorical consistency."
    else:
        interp = "Low readiness — dashboarding may require additional preparation."

    return {
        "dashboard_readiness_score": readiness_score,
        "interpretation": interp,
        "pii_columns": pii_cols,
        "temporal_columns": temporal_cols,
        "categorical_columns": cat_cols
    }


# --------------------------------------------------------------------
# Core audit function
# --------------------------------------------------------------------
def audit_dataset(df: pd.DataFrame):
    """Comprehensive dataset audit."""
    report = {}

    # ---------------- BASIC STRUCTURE ----------------
    report["shape"] = df.shape
    report["columns"] = list(df.columns)
    report["duplicates"] = int(df.duplicated().sum())

    # ---------------- MISSING VALUES ----------------
    missing_count = df.isnull().sum()
    missing_percent = (df.isnull().mean() * 100).round(2)
    report["missing_values"] = {
        col: {"count": int(missing_count[col]), "percent": float(missing_percent[col])}
        for col in df.columns
    }

    # ---------------- DATA TYPES & CONFORMITY ----------------
    data_types = df.dtypes.astype(str).to_dict()
    conformity = {}
    for col, dtype in df.dtypes.items():
        try:
            if dtype == object:
                converted = pd.to_numeric(df[col], errors="coerce")
                numeric_ratio = converted.notnull().mean()
                if numeric_ratio > 0.9:
                    conformity[col] = "Mostly numeric but stored as text"
                else:
                    conformity[col] = "Categorical/Text"
            elif np.issubdtype(dtype, np.number):
                conformity[col] = "Numeric"
            elif np.issubdtype(dtype, np.datetime64):
                conformity[col] = "Date/Time"
            else:
                conformity[col] = "Other / Unsupported type"
        except Exception:
            conformity[col] = "Could not evaluate"

    report["data_types"] = data_types
    report["type_conformity"] = conformity
    non_conforming = {
        col: status for col, status in conformity.items()
        if status not in ["Numeric", "Categorical/Text", "Date/Time"]
    }
    report["type_conformity_filtered"] = non_conforming if non_conforming else {
        "All Columns": "Conform to expected types"
    }

    # ---------------- COLUMN CLASSIFICATION ----------------
    classification_report = {col: classify_column(col, df[col]) for col in df.columns}
    report["column_classification"] = classification_report

    # ---------------- OUTLIER DETECTION ----------------
    numeric_cols = df.select_dtypes(include=np.number)
    outlier_summary = {}
    for col in numeric_cols.columns:
        q1, q3 = numeric_cols[col].quantile(0.25), numeric_cols[col].quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = numeric_cols[(numeric_cols[col] < lower) | (numeric_cols[col] > upper)]
        outlier_summary[col] = {"count": len(outliers), "percent": round((len(outliers) / len(df)) * 100, 2)}
    report["outliers"] = outlier_summary

    # ---------------- ADDITIONAL QUALITY CHECKS ----------------
    constant_cols = [col for col in df.columns if df[col].nunique(dropna=False) == 1]
    high_cardinality = [
        col for col in df.select_dtypes(include="object").columns
        if df[col].nunique(dropna=False) > df.shape[0] * 0.5
    ]
    mixed_type_cols = [
        col for col in df.select_dtypes(include="object").columns
        if df[col].dropna().map(type).nunique() > 1
    ]
    report["additional_quality_issues"] = {
        "constant_columns": constant_cols or ["None"],
        "high_cardinality_columns": high_cardinality or ["None"],
        "mixed_type_columns": mixed_type_cols or ["None"]
    }

    # ---------------- READINESS SCORING ----------------
    completeness = 1 - (missing_count.sum() / (df.shape[0] * df.shape[1]))
    conformity_score = sum(
        status in ["Numeric", "Categorical/Text", "Date/Time"] for status in conformity.values()
    ) / len(conformity)
    duplicate_penalty = 1 - min(1.0, (report["duplicates"] / df.shape[0]) if df.shape[0] > 0 else 0)
    base_score = round((0.6 * completeness + 0.3 * conformity_score + 0.1 * duplicate_penalty), 2)
    report["readiness_score"] = base_score
    report["readiness_interpretation"] = (
        "Excellent overall readiness."
        if base_score > 0.85
        else "Moderate readiness; some cleaning recommended."
        if base_score > 0.6
        else "Low readiness; significant cleaning required."
    )

    # ---------------- MODEL-SPECIFIC READINESS ----------------
    model_types = ["Regression", "Classification", "Clustering"]
    report["model_readiness"] = {m: evaluate_model_readiness(df, m) for m in model_types}

    # ---------------- DASHBOARD READINESS ----------------
    report["dashboard_readiness"] = evaluate_dashboard_readiness(df, classification_report)

    return report
