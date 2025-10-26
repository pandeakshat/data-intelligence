import pandas as pd

def load_dataset(uploaded_file_or_path):
    """
    Reads CSV or Excel file and returns a pandas DataFrame.
    Handles encoding, Excel sheets, and Streamlit uploads automatically.
    """
    try:
        # Handle both Streamlit UploadedFile and file paths
        if hasattr(uploaded_file_or_path, "name"):
            filename = uploaded_file_or_path.name
        else:
            filename = str(uploaded_file_or_path)

        # CSV loader with fallback encodings
        if filename.endswith(".csv"):
            try:
                df = pd.read_csv(uploaded_file_or_path, encoding="utf-8")
            except UnicodeDecodeError:
                if hasattr(uploaded_file_or_path, "seek"):
                    uploaded_file_or_path.seek(0)
                df = pd.read_csv(uploaded_file_or_path, encoding="latin-1")

        # Excel loader
        elif filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(uploaded_file_or_path)

        else:
            raise ValueError("Unsupported file type. Please upload a CSV or Excel file.")

        return df

    except Exception as e:
        raise RuntimeError(f"Error loading dataset: {e}")
