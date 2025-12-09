import pandas as pd
import numpy as np

def calculate_readiness_score(df: pd.DataFrame) -> dict:
    """
    Computes a 0-100 score based on 3 pillars:
    1. Completeness (Are values missing?)
    2. Type Stability (Are columns pure types?)
    3. Dimensionality (Cardinality/Shape)
    """
    score = 100.0
    penalties = []
    
    total_cells = df.size
    if total_cells == 0:
        return {"score": 0, "grade": "F", "breakdown": ["Empty Dataset"]}

    # --- Pillar 1: Completeness (Max Penalty: 40) ---
    missing_total = df.isnull().sum().sum()
    missing_ratio = missing_total / total_cells
    
    p_completeness = min(40, missing_ratio * 100 * 1.5) # Penalty multiplier
    score -= p_completeness
    if p_completeness > 5:
        penalties.append(f"-{p_completeness:.1f} pts: High missing values ({missing_ratio:.1%})")

    # --- Pillar 2: Cardinality / Constant Columns (Max Penalty: 20) ---
    # Check for columns with only 1 unique value (useless for ML)
    constant_cols = [c for c in df.columns if df[c].nunique() <= 1]
    if constant_cols:
        p_const = 5 * len(constant_cols)
        score -= p_const
        penalties.append(f"-{p_const} pts: {len(constant_cols)} Constant columns found (No info gain)")

    # --- Pillar 3: Type Interpretation (Max Penalty: 20) ---
    # Penalize Object columns that look like numbers
    # (Simple heuristic implementation)
    obj_cols = df.select_dtypes(include=['object']).columns
    bad_types = 0
    for col in obj_cols:
        # If >80% are numbers but it's an object, it's a dirty column
        try:
            numeric_rate = pd.to_numeric(df[col], errors='coerce').notnull().mean()
            if numeric_rate > 0.8:
                bad_types += 1
        except:
            pass
            
    if bad_types > 0:
        p_types = 5 * bad_types
        score -= p_types
        penalties.append(f"-{p_types} pts: {bad_types} columns have mixed types (Numbers stored as text)")

    # --- Final Grade ---
    final_score = max(0, round(score))
    
    grade = "A"
    if final_score < 90: grade = "B"
    if final_score < 75: grade = "C"
    if final_score < 60: grade = "D"
    if final_score < 40: grade = "F"

    return {
        "score": final_score,
        "grade": grade,
        "penalties": penalties
    }


def assess_model_suitability(df: pd.DataFrame) -> dict:
    """
    Evaluates dataset against specific ML Model requirements.
    """
    report = {}
    
    num_cols = df.select_dtypes(include='number').columns
    cat_cols = df.select_dtypes(include='object').columns
    missing_ratio = df.isnull().mean().mean()
    rows = df.shape[0]

    # 1. REGRESSION (Needs numeric data, high correlation potential)
    reg_score = 100
    if len(num_cols) < 2: reg_score -= 50 # Need at least target + 1 feature
    if missing_ratio > 0.1: reg_score -= 20
    if rows < 50: reg_score -= 30
    report["Regression"] = {
        "score": max(0, reg_score),
        "desc": "Requires numeric features and targets. Sensitive to outliers and missing data."
    }

    # 2. CLASSIFICATION (Needs categorical targets, balance)
    clf_score = 100
    if len(cat_cols) == 0: clf_score -= 40 # Likely need a categorical target
    if missing_ratio > 0.2: clf_score -= 20
    if rows < 50: clf_score -= 30
    report["Classification"] = {
        "score": max(0, clf_score),
        "desc": "Requires labeled data. Sensitive to class imbalance (check target distribution)."
    }

    # 3. GENETIC ALGORITHMS / OPTIMIZATION (Needs clean bounds, low noise)
    # GA requires strict numeric bounds and low noise to converge
    ga_score = 100
    if len(num_cols) == 0: 
        ga_score = 0
    else:
        # Check for infinite values
        if np.isinf(df[num_cols]).values.any(): ga_score -= 50
        # High dimensionality hurts GA convergence
        if len(num_cols) > 100: ga_score -= 20 
    
    report["Genetic / Optimization"] = {
        "score": max(0, ga_score),
        "desc": "Requires defined numeric search spaces. High dimensionality and Infinite values are fatal."
    }

    return report