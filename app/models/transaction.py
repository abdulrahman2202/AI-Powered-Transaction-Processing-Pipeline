import uuid
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Numeric, Boolean, Text, Uuid, ForeignKey, Date
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
from db.session import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    job_id = Column(Uuid, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    txn_id = Column(String(100), nullable=False, index=True)
    date = Column(Date, nullable=False)
    merchant = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False)
    account_id = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    
    # Anomaly Detection Fields
    is_anomaly = Column(Boolean, default=False, nullable=False)
    anomaly_reason = Column(Text, nullable=True)
    
    # AI Classification Fields
    llm_category = Column(String(100), nullable=True)
    llm_raw_response = Column(Text, nullable=True)
    llm_failed = Column(Boolean, default=False, nullable=False)

    # Relationships
    job = relationship("Job", back_populates="transactions")
