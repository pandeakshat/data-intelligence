import pandas as pd
from io import BytesIO

def load_data(source, filename: str) -> pd.DataFrame:
    """
    Pure Python: Loads data from a buffer (Upload) or a path (Sample).
    """
    try:
        # Determine if source is a file path (str) or buffer
        is_path = isinstance(source, str)

        if filename.endswith('.csv'):
            try:
                # Try UTF-8 first
                return pd.read_csv(source, encoding='utf-8')
            except UnicodeDecodeError:
                # Fallback to Latin-1
                if not is_path and hasattr(source, 'seek'): 
                    source.seek(0) # Reset buffer pointer
                return pd.read_csv(source, encoding='latin-1')
                
        elif filename.endswith(('.xls', '.xlsx')):
            return pd.read_excel(source)
        else:
            raise ValueError(f"Unsupported file format: {filename}")
            
    except Exception as e:
        raise RuntimeError(f"Data Load Error: {e}")