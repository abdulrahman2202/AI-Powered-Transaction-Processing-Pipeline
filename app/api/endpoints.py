import os
import shutil
from typing import List, Optional, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings
from app.core.logging import logger
from app.worker.tasks import process_transaction_job
from app.services.repository import JobRepository, TransactionRepository, JobSummaryRepository
from app.schemas.job import JobResponse, JobStatusResponse, JobResultsResponse
from app.schemas.summary import JobSummaryResponse
from app.schemas.transaction import TransactionResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/upload", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def upload_csv(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    """Upload a transaction CSV file.
    Validates file extension, creates a Job record, saves the file,
    queues the background Celery task, and returns the Job details immediately.
    """
    logger.info(f"Received file upload request: {file.filename}")
    
    # Validate file extension
    if not file.filename.endswith('.csv'):
        logger.warning(f"File upload rejected. Invalid extension: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid file type. Only CSV files are supported."
        )

    # 1. Create Job record in pending state
    job = JobRepository.create_job(db, filename=file.filename)
    
    # 2. Save the uploaded file locally (using job_id to prevent collision)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{job.id}.csv")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File saved successfully for job {job.id} at {file_path}")
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        # Update job to failed immediately
        JobRepository.update_job(db, job.id, status="failed", error_message="Failed to write file to storage.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save file to disk."
        )

    # 3. Queue the Celery worker task asynchronously
    process_transaction_job.delay(str(job.id), file_path)
    logger.info(f"Queued background processing task for job {job.id}")
    
    return job


@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(
    job_id: UUID, 
    db: Session = Depends(get_db)
):
    """Retrieve the status of a specific job.
    Includes the aggregate summary if processing is completed.
    """
    job = JobRepository.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Job not found"
        )
        
    summary = None
    if job.status == "completed":
        summary = JobSummaryRepository.get_summary_by_job(db, job_id)
        
    return {
        "job": job,
        "summary": summary
    }


@router.get("/{job_id}/results", response_model=JobResultsResponse)
def get_job_results(
    job_id: UUID, 
    db: Session = Depends(get_db)
):
    """Retrieve detailed results of a completed job.
    Returns cleaned transactions, flagged anomalies, category distributions, and AI summary.
    """
    job = JobRepository.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Job not found"
        )
        
    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Job results are not available. Current status: {job.status}"
        )
        
    # Get all transactions
    transactions = TransactionRepository.get_transactions_by_job(db, job_id)
    
    # Separate cleaned transactions and anomalies
    cleaned_txns = [t for t in transactions if not t.is_anomaly]
    anomalies = [t for t in transactions if t.is_anomaly]
    
    # Calculate category breakdown
    category_breakdown: Dict[str, int] = {}
    for t in transactions:
        cat = t.llm_category or t.category
        category_breakdown[cat] = category_breakdown.get(cat, 0) + 1
        
    # Get summary
    summary = JobSummaryRepository.get_summary_by_job(db, job_id)
    
    return {
        "cleaned_transactions": cleaned_txns,
        "anomalies": anomalies,
        "category_breakdown": category_breakdown,
        "ai_summary": summary
    }


@router.get("", response_model=List[JobResponse])
def list_jobs(
    status: Optional[str] = Query(None, description="Filter jobs by status (pending, processing, completed, failed)"),
    db: Session = Depends(get_db)
):
    """List all transaction processing jobs, optionally filtered by status."""
    return JobRepository.list_jobs(db, status=status)
