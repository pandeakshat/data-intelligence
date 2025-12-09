import pandas as pd
import re
import yaml
import hashlib

def load_schema_config(filepath: str) -> dict:
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def recommend_mappings(df: pd.DataFrame, schema: dict) -> dict:
    """
    Matches DF columns to Schema columns using Exact Name & Regex.
    FIXED: Handles inline regex flags properly.
    """
    recommendations = {}
    df_cols = list(df.columns)
    used_cols = set()

    for target in schema['columns']:
        t_name = target['name']
        
        # FIX: Clean the regex string (Python re doesn't like inline (?i) in compile)
        raw_regex = target.get('regex', '')
        if raw_regex:
            clean_regex = raw_regex.replace('(?i)', '')
        else:
            clean_regex = None
            
        match = None

        # Strategy 1: Exact Name Match
        if t_name in df_cols:
            match = t_name
        
        # Strategy 2: Regex Pattern Match
        elif clean_regex:
            try:
                # Compile with IGNORECASE flag
                pattern = re.compile(clean_regex, re.IGNORECASE)
                for col in df_cols:
                    if col not in used_cols:
                        if pattern.search(col):
                            match = col
                            break
            except re.error:
                pass # Skip bad regex
        
        if match:
            recommendations[t_name] = match
            used_cols.add(match)
        else:
            recommendations[t_name] = None
            
    return recommendations

# --- WRANGLING TOOLS ---

def split_column(df: pd.DataFrame, col: str, delimiter: str, new_names: list) -> pd.DataFrame:
    try:
        split_data = df[col].astype(str).str.split(delimiter, expand=True)
        for i, name in enumerate(new_names):
            if i < split_data.shape[1]:
                df[name] = split_data[i]
            else:
                df[name] = None
        return df
    except Exception as e:
        raise ValueError(f"Split failed: {e}")

def fill_missing(df: pd.DataFrame, col: str, method: str, value=None) -> pd.DataFrame:
    if method == "Static Value":
        df[col] = df[col].fillna(value)
    elif method == "Forward Fill":
        df[col] = df[col].ffill()
    elif method == "Mean":
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].mean())
    return df

def anonymize_column(df: pd.DataFrame, col: str, method: str) -> pd.DataFrame:
    """
    Implements Basic K-Anonymity concepts.
    """
    if col not in df.columns:
        return df

    if method == "Masking (***)":
        # Replaces all values with ***
        df[col] = "*****"
    
    elif method == "Hashing (SHA256)":
        # One-way hash for IDs
        df[col] = df[col].astype(str).apply(
            lambda x: hashlib.sha256(x.encode()).hexdigest() if x and x != 'nan' else x
        )
        
    elif method == "Generalization (Numeric Bins)":
        # Convert exact age (24) to range (20-30)
        if pd.api.types.is_numeric_dtype(df[col]):
            # Auto-calculate bin size based on range
            min_v, max_v = df[col].min(), df[col].max()
            if pd.notnull(min_v):
                bins = list(range(int(min_v), int(max_v) + 10, 10))
                labels = [f"{i}-{i+10}" for i in bins[:-1]]
                df[col] = pd.cut(df[col], bins=bins, labels=labels).astype(str)
                
    return df

def rename_and_export(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    # Filter out None values
    valid_map = {v: k for k, v in mapping.items() if v is not None and v != "-- MISSING --"}
    df_clean = df.rename(columns=valid_map)
    final_cols = [k for k in mapping.keys() if k in df_clean.columns]
    return df_clean[final_cols]