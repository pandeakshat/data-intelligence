import pandas as pd
import io

def load_dataset(uploaded_file):
    """
    Reads CSV or Excel file and returns a pandas DataFrame.
    Handles encoding and sheet detection automatically.
    """
    try:
        if uploaded_file.name.endswith('.csv'):
            # Try utf-8 first, fallback to latin-1 if fails
            try:
                df = pd.read_csv(uploaded_file)
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='latin-1')
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            raise ValueError("Unsupported file type. Please upload a CSV or Excel file.")

        return df

    except Exception as e:
        raise RuntimeError(f"Error loading dataset: {e}")
