import pandas as pd
from datetime import datetime, date
import hashlib
import re
from core.logging import logger

def parse_date(date_str) -> date:
    """Parse a date string in various formats and return a datetime.date object.
    Supports DD-MM-YYYY, YYYY/MM/DD, DD/MM/YYYY, YYYY-MM-DD.
    """
    if pd.isna(date_str):
        return date.today()
        
    date_str = str(date_str).strip()
    if not date_str:
        return date.today()

    # Define known formats to try
    formats = [
        "%d-%m-%Y", 
        "%Y/%m/%d", 
        "%d/%m/%Y", 
        "%Y-%m-%d",
        "%d-%b-%Y", # e.g. 10-Jun-2026
        "%d/%b/%Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
            
    # Try generic pandas datetime parsing
    try:
        return pd.to_datetime(date_str).date()
    except Exception as e:
        logger.warning(f"Could not parse date '{date_str}': {e}. Defaulting to today's date.")
        return date.today()

def clean_amount(amount_val) -> float:
    """Removes currency symbols and returns amount as a float."""
    if pd.isna(amount_val):
        return 0.0
    
    val_str = str(amount_val).strip()
    if not val_str:
        return 0.0
        
    # Remove common currency symbols, commas, and spaces
    val_str = re.sub(r'[₹\$€£,\s]', '', val_str)
    
    try:
        return float(val_str)
    except ValueError:
        logger.warning(f"Could not parse amount '{amount_val}'. Defaulting to 0.0.")
        return 0.0

def generate_txn_id(row) -> str:
    """Generates a unique transaction ID if missing based on other fields or hash."""
    txn_id_val = row.get('txn_id')
    if not pd.isna(txn_id_val) and str(txn_id_val).strip():
        return str(txn_id_val).strip()
        
    # Create a stable MD5 hash based on row attributes
    date_str = str(row.get('date', ''))
    merchant_str = str(row.get('merchant', '')).lower().strip()
    amount_str = str(row.get('amount', '0.0'))
    account_str = str(row.get('account_id', '')).lower().strip()
    
    unique_str = f"{date_str}_{merchant_str}_{amount_str}_{account_str}"
    hash_object = hashlib.md5(unique_str.encode())
    return f"TXN-{hash_object.hexdigest()[:12].upper()}"

class DataCleaningService:
    @staticmethod
    def clean_csv(file_path: str) -> pd.DataFrame:
        """Loads and cleans the CSV transaction file.
        Returns a cleaned Pandas DataFrame.
        """
        logger.info(f"Starting CSV cleaning for file: {file_path}")
        
        # Load CSV
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            logger.error(f"Failed to read CSV file: {e}")
            raise ValueError(f"Invalid CSV format: {e}")

        # Check required columns
        required_cols = {'date', 'merchant', 'amount', 'currency', 'status', 'account_id'}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns in CSV: {missing_cols}")

        # 1. Remove exact duplicate rows
        df = df.drop_duplicates()

        # 2. Normalize dates
        df['date'] = df['date'].apply(parse_date)

        # 3. Clean and convert amounts
        df['amount'] = df['amount'].apply(clean_amount)

        # 4. Normalize casing
        df['currency'] = df['currency'].astype(str).str.strip().str.upper()
        df['status'] = df['status'].astype(str).str.strip().str.lower()

        # 5. Fill missing categories
        if 'category' not in df.columns:
            df['category'] = 'Uncategorised'
        else:
            df['category'] = df['category'].fillna("Uncategorised")
            df['category'] = df['category'].apply(
                lambda x: str(x).strip() if str(x).strip() else "Uncategorised"
            )

        # 6. Generate txn_id if missing
        df['txn_id'] = df.apply(generate_txn_id, axis=1)

        # If notes column doesn't exist, create it as empty
        if 'notes' not in df.columns:
            df['notes'] = None
        else:
            df['notes'] = df['notes'].apply(lambda x: None if pd.isna(x) else str(x).strip())

        logger.info(f"Completed CSV cleaning. Row count: {len(df)}")
        return df
