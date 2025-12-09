import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

def detect_anomalies(df: pd.DataFrame) -> dict:
    """
    Runs Dual-Method Outlier Detection:
    1. IQR (Univariate): Good for simple range checks.
    2. Isolation Forest (Multivariate): Good for weird combinations of valid values.
    """
    report = {"summary": {}, "rows": []}
    
    # Select only numeric columns
    numeric_df = df.select_dtypes(include=[np.number]).dropna()
    
    if numeric_df.empty:
        return report

    # --- Method 1: Isolation Forest (ML) ---
    # Contamination=0.05 means we guess ~5% of data might be anomalous
    iso = IsolationForest(contamination=0.05, random_state=42)
    try:
        preds = iso.fit_predict(numeric_df)
        # -1 indicates anomaly, 1 indicates normal
        anomaly_indices = numeric_df.index[preds == -1].tolist()
        report["ml_anomalies"] = len(anomaly_indices)
        report["ml_indices"] = anomaly_indices
    except Exception as e:
        report["ml_error"] = str(e)
        report["ml_anomalies"] = 0

    # --- Method 2: IQR (Statistical) ---
    iqr_counts = {}
    for col in numeric_df.columns:
        q1 = numeric_df[col].quantile(0.25)
        q3 = numeric_df[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        count = ((numeric_df[col] < lower_bound) | (numeric_df[col] > upper_bound)).sum()
        if count > 0:
            iqr_counts[col] = int(count)
            
    report["iqr_outliers"] = iqr_counts
    
    return report