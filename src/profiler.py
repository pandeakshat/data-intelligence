import pandas as pd
import numpy as np

def generate_profile(df: pd.DataFrame) -> dict:
    """
    Generates the 'Schema' view of the dataset.
    """
    profile = {}
    
    for col in df.columns:
        col_data = df[col]
        
        # Detect Type
        dtype = str(col_data.dtype)
        if np.issubdtype(col_data.dtype, np.number):
            kind = "Numeric"
        elif np.issubdtype(col_data.dtype, np.datetime64):
            kind = "DateTime"
        else:
            kind = "Categorical"
            
        # Stats
        unique_count = col_data.nunique()
        missing_count = int(col_data.isnull().sum())
        
        profile[col] = {
            "type": dtype,
            "kind": kind,
            "unique": unique_count,
            "missing": missing_count,
            "missing_pct": round((missing_count / len(df)) * 100, 1)
        }
        
    return profile


import pandas as pd
import re

def scan_for_pii(df: pd.DataFrame) -> dict:
    """
    Scans columns for potential PII (Personally Identifiable Information).
    Returns a dict of {column_name: pii_type}.
    """
    pii_report = {}
    
    # Regex Patterns for common PII
    patterns = {
        "Email": r"(?i)[^@]+@[^@]+\.[^@]+",
        "Phone": r"(?i)(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}",
        "SSN/ID": r"(?i)\b\d{3}-\d{2}-\d{4}\b",  # Simple US SSN
        "Credit Card": r"(?i)\b(?:\d[ -]*?){13,16}\b",
        "IPv4": r"(?i)\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
    }
    
    # Keyword fallback (if regex is too slow for big data, check names)
    keyword_triggers = ["password", "secret", "dob", "birth", "social", "tax", "credit"]

    for col in df.columns:
        # 1. Check Column Name Context
        if any(k in col.lower() for k in keyword_triggers):
            pii_report[col] = "Potential Sensitive Keyword"
            continue
            
        # 2. Check Content (Sample first 20 non-null rows)
        if df[col].dtype == object:
            sample = df[col].dropna().head(20).astype(str)
            for p_name, p_regex in patterns.items():
                # If any value in sample matches
                if sample.str.contains(p_regex, regex=True).any():
                    pii_report[col] = p_name
                    break
                    
    return pii_report