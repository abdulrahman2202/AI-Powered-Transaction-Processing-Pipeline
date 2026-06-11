from typing import List, Optional, Any
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import select
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.summary import JobSummary
from app.core.logging import logger

class JobRepository:
    @staticmethod
    def create_job(db: Session, filename: str) -> Job:
        job = Job(filename=filename, status="pending")
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_job(db: Session, job_id: Any) -> Optional[Job]:
        stmt = select(Job).where(Job.id == job_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def update_job(db: Session, job_id: Any, **kwargs) -> Optional[Job]:
        job = JobRepository.get_job(db, job_id)
        if job:
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            db.commit()
            db.refresh(job)
        return job

    @staticmethod
    def list_jobs(db: Session, status: Optional[str] = None) -> List[Job]:
        stmt = select(Job)
        if status:
            stmt = stmt.where(Job.status == status)
        stmt = stmt.order_by(Job.created_at.desc())
        return list(db.execute(stmt).scalars().all())


class TransactionRepository:
    @staticmethod
    def bulk_create_transactions(db: Session, transactions_data: List[dict]) -> List[Transaction]:
        """Inserts transactions in bulk for performance."""
        logger.info(f"Bulk inserting {len(transactions_data)} transactions...")
        txns = [Transaction(**data) for data in transactions_data]
        db.add_all(txns)
        db.commit()
        return txns

    @staticmethod
    def get_transactions_by_job(db: Session, job_id: Any) -> List[Transaction]:
        stmt = select(Transaction).where(Transaction.job_id == job_id)
        return list(db.execute(stmt).scalars().all())


class JobSummaryRepository:
    @staticmethod
    def create_summary(db: Session, summary: JobSummary) -> JobSummary:
        db.add(summary)
        db.commit()
        db.refresh(summary)
        return summary

    @staticmethod
    def get_summary_by_job(db: Session, job_id: Any) -> Optional[JobSummary]:
        stmt = select(JobSummary).where(JobSummary.job_id == job_id)
        return db.execute(stmt).scalar_one_or_none()
