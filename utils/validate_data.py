import pandas as pd
import numpy as np

def audit_dataset(df: pd.DataFrame):
    report = {}

    # Basic info
    report["shape"] = df.shape
    report["columns"] = list(df.columns)

    # Missing values
    report["missing_values"] = df.isnull().sum().to_dict()

    # Data types
    report["data_types"] = df.dtypes.astype(str).to_dict()

    # Numeric column stats
    numeric_cols = df.select_dtypes(include=np.number).columns
    report["numeric_summary"] = df[numeric_cols].describe().to_dict()

    # Duplicate check
    report["duplicates"] = df.duplicated().sum()

    # ML Readiness (simple heuristic)
    completeness = 1 - (df.isnull().sum().sum() / (df.shape[0] * df.shape[1]))
    type_diversity = len(set(df.dtypes))
    readiness_score = round(0.6 * completeness + 0.4 * (1 / (1 + np.exp(type_diversity - 4))), 2)
    report["ml_readiness_score"] = readiness_score

    return report
