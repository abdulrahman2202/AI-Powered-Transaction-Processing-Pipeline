import uuid
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Numeric, Integer, Text, Uuid, ForeignKey, JSON, String
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
from db.session import Base

class JobSummary(Base):
    __tablename__ = "job_summaries"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    job_id = Column(Uuid, ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    total_spend_inr = Column(Numeric(15, 2), nullable=False)
    total_spend_usd = Column(Numeric(15, 2), nullable=False)
    top_merchants = Column(JSON, nullable=False)  # List of dicts/strings
    anomaly_count = Column(Integer, default=0, nullable=False)
    narrative = Column(Text, nullable=False)
    risk_level = Column(String(20), nullable=False)  # low, medium, high

    # Relationships
    job = relationship("Job", back_populates="summary")
