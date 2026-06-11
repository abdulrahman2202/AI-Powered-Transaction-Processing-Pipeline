import json
from typing import List
from app.core.logging import logger
from app.core.gemini import gemini_client
from app.models.transaction import Transaction

class AIClassificationService:
    @staticmethod
    def classify_transactions(transactions: List[Transaction], batch_size: int = 20) -> List[Transaction]:
        """Classifies transactions with 'Uncategorised' category in batches using Gemini API.
        Updates transaction objects in-place with 'llm_category', 'llm_raw_response', and 'llm_failed'.
        """
        # Filter transactions that need classification
        unclassified = [t for t in transactions if t.category == "Uncategorised" or not t.category]
        
        if not unclassified:
            logger.info("No unclassified transactions to process.")
            return transactions

        logger.info(f"Found {len(unclassified)} unclassified transactions. Starting AI classification in batches of {batch_size}...")

        system_instruction = (
            "You are a precise financial transaction classifier. Your job is to read list of financial transactions "
            "and classify each transaction into one of these exact categories: "
            "['Food', 'Shopping', 'Travel', 'Transport', 'Utilities', 'Cash Withdrawal', 'Entertainment', 'Other']. "
            "You must return a JSON object where the key is the transaction's 'txn_id' and the value is the classified category. "
            "Do not include any explanation or extra text. Format must be exactly: { \"txn_id\": \"Category\" }"
        )

        for i in range(0, len(unclassified), batch_size):
            batch = unclassified[i:i + batch_size]
            logger.info(f"Processing classification batch {i//batch_size + 1} ({len(batch)} transactions)...")
            
            # Prepare prompt data
            prompt_data = [
                {
                    "txn_id": t.txn_id,
                    "merchant": t.merchant,
                    "amount": float(t.amount),
                    "currency": t.currency,
                    "notes": t.notes or ""
                }
                for t in batch
            ]
            
            prompt = f"Classify these transactions:\n{json.dumps(prompt_data, indent=2)}"
            
            raw_response = ""
            try:
                # Call Gemini
                raw_response = gemini_client.generate_json_response(
                    prompt=prompt,
                    system_instruction=system_instruction
                )
                
                # Parse JSON
                classification_map = json.loads(raw_response)
                
                # Update transactions in-place
                for t in batch:
                    category_val = classification_map.get(t.txn_id)
                    if category_val:
                        t.llm_category = str(category_val).strip()
                        # Verify it's one of the allowed categories, else default to 'Other'
                        allowed = {'Food', 'Shopping', 'Travel', 'Transport', 'Utilities', 'Cash Withdrawal', 'Entertainment', 'Other'}
                        if t.llm_category not in allowed:
                            t.llm_category = 'Other'
                        t.llm_raw_response = raw_response
                        t.llm_failed = False
                    else:
                        # Missing from mapping
                        t.llm_category = 'Other'
                        t.llm_raw_response = raw_response
                        t.llm_failed = True
                        logger.warning(f"Gemini did not return classification for txn_id {t.txn_id}")
                        
            except Exception as e:
                logger.error(f"Error classifying batch {i//batch_size + 1}: {e}")
                # Update all transactions in this batch to failed
                for t in batch:
                    t.llm_failed = True
                    t.llm_raw_response = raw_response or str(e)
                    t.llm_category = 'Other'

        logger.info("AI transaction classification completed.")
        return transactions
