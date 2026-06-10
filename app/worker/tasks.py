import os
from datetime import datetime
import pandas as pd
from celery.exceptions import MaxRetriesExceededError
from app.core.celery import celery_app
from app.core.logging import logger
from app.db.session import SessionLocal
from app.services.cleaning import DataCleaningService
from app.services.anomaly import AnomalyDetectionService
from app.services.ai_classification import AIClassificationService
from app.services.ai_summary import AISummaryService
from app.services.repository import JobRepository, TransactionRepository, JobSummaryRepository

@celery_app.task(bind=True, max_retries=3)
def process_transaction_job(self, job_id: str, file_path: str):
    """Celery background task to process a transaction CSV upload."""
    logger.info(f"Background job {job_id} started processing file {file_path}")
    
    db = SessionLocal()
    
    # 1. Update Job status to 'processing'
    JobRepository.update_job(db, job_id, status="processing")
    
    try:
        # Determine raw row count
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found at {file_path}")
            
        try:
            raw_df = pd.read_csv(file_path)
            raw_row_count = len(raw_df)
        except Exception as e:
            logger.error(f"Failed to read raw CSV file to get count: {e}")
            raw_row_count = 0
            
        # 2. Clean Data
        cleaned_df = DataCleaningService.clean_csv(file_path)
        clean_row_count = len(cleaned_df)
        
        # 3. Detect Anomalies
        processed_df = AnomalyDetectionService.detect_anomalies(cleaned_df)
        
        # 4. Save base transactions into DB
        transactions_data = []
        for _, row in processed_df.iterrows():
            transactions_data.append({
                "job_id": job_id,
                "txn_id": row['txn_id'],
                "date": row['date'],
                "merchant": row['merchant'],
                "amount": row['amount'],
                "currency": row['currency'],
                "status": row['status'],
                "category": row['category'],
                "account_id": row['account_id'],
                "notes": row['notes'],
                "is_anomaly": row['is_anomaly'],
                "anomaly_reason": row['anomaly_reason']
            })
            
        txns_models = TransactionRepository.bulk_create_transactions(db, transactions_data)
        
        # 5. AI Category Classification (Batch)
        # Updates txns_models in-place and handles AI failures gracefully per batch
        AIClassificationService.classify_transactions(txns_models)
        db.commit()
        
        # 6. AI Summary Generation
        summary_model = AISummaryService.generate_summary(job_id, txns_models)
        JobSummaryRepository.create_summary(db, summary_model)
        
        # 7. Update Job status to 'completed'
        JobRepository.update_job(
            db, 
            job_id, 
            status="completed", 
            row_count_raw=raw_row_count, 
            row_count_clean=clean_row_count,
            completed_at=datetime.utcnow()
        )
        logger.info(f"Background job {job_id} successfully processed.")
        
    except Exception as exc:
        db.rollback()
        logger.error(f"Error processing job {job_id}: {exc}")
        
        # Calculate next exponential backoff retry delay (e.g. 10s, 20s, 40s)
        countdown = 10 * (2 ** self.request.retries)
        
        try:
            logger.info(f"Retrying task for job {job_id} in {countdown} seconds...")
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for job {job_id}. Marking job as failed.")
            JobRepository.update_job(
                db, 
                job_id, 
                status="failed", 
                error_message=str(exc),
                completed_at=datetime.utcnow()
            )
        except Exception as retry_err:
            # Fallback if self.retry fails outside Celery context
            logger.error(f"Failed to retry job {job_id}: {retry_err}")
            JobRepository.update_job(
                db, 
                job_id, 
                status="failed", 
                error_message=str(exc),
                completed_at=datetime.utcnow()
            )
            
    finally:
        db.close()
