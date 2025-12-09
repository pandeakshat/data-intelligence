import pandas as pd
import numpy as np

def run_global_audit(df: pd.DataFrame) -> dict:
    """
    General health check: Types, Nulls, Duplicates, Outliers.
    """
    report = {
        "shape": df.shape,
        "duplicates": int(df.duplicated().sum()),
        "columns": {}
    }
    
    numeric_cols = df.select_dtypes(include=np.number).columns
    
    for col in df.columns:
        # 1. Basic Stats
        null_count = int(df[col].isnull().sum())
        dtype = str(df[col].dtype)
        
        # 2. Outlier Detection (IQR)
        outliers = 0
        if col in numeric_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            outliers = int(((df[col] < (q1 - 1.5 * iqr)) | (df[col] > (q3 + 1.5 * iqr))).sum())

        report["columns"][col] = {
            "type": dtype,
            "nulls": null_count,
            "null_percent": round((null_count / len(df)) * 100, 1),
            "outliers": outliers
        }
        
    return report