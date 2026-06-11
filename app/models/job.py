import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Uuid
from sqlalchemy.orm import relationship
from db.session import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, processing, completed, failed
    row_count_raw = Column(Integer, nullable=True)
    row_count_clean = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    transactions = relationship("Transaction", back_populates="job", cascade="all, delete-orphan")
    summary = relationship("JobSummary", back_populates="job", uselist=False, cascade="all, delete-orphan")
