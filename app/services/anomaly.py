import pandas as pd
from app.core.logging import logger

class AnomalyDetectionService:
    @staticmethod
    def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
        """Runs rule-based anomaly detection on a cleaned DataFrame.
        Adds 'is_anomaly' and 'anomaly_reason' columns.
        """
        logger.info("Starting rule-based anomaly detection...")

        # Initialize columns
        df['is_anomaly'] = False
        df['anomaly_reason'] = ""

        if df.empty:
            return df

        # Calculate account-level median amounts
        # Fill NA with 0 to prevent division or comparison errors
        account_medians = df.groupby('account_id')['amount'].median().to_dict()

        domestic_merchants = {'swiggy', 'ola', 'irctc'}

        reasons = []

        for idx, row in df.iterrows():
            row_reasons = []
            amount = row['amount']
            account_id = row['account_id']
            currency = str(row['currency']).upper()
            merchant = str(row['merchant']).lower().strip()

            # Rule 1: Amount > 3 * account median
            median = account_medians.get(account_id, 0.0)
            # Avoid flagging normal small transactions if median is 0
            if median > 0 and amount > 3 * median:
                row_reasons.append(
                    f"Amount ({amount}) is greater than 3x the account median ({median:.2f}) for account {account_id}."
                )

            # Rule 2: USD transaction from domestic merchants (Swiggy, Ola, IRCTC)
            if currency == 'USD' and merchant in domestic_merchants:
                row_reasons.append(
                    f"USD transaction detected for domestic merchant: {row['merchant']}."
                )

            if row_reasons:
                df.at[idx, 'is_anomaly'] = True
                df.at[idx, 'anomaly_reason'] = " | ".join(row_reasons)
                logger.warning(f"Anomaly flagged for txn {row.get('txn_id')}: {df.at[idx, 'anomaly_reason']}")

        logger.info(f"Anomaly detection complete. Flagged anomalies: {df['is_anomaly'].sum()}")
        return df
