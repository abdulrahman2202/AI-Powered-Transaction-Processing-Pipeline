from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date
from decimal import Decimal
from typing import Optional

class TransactionBase(BaseModel):
    txn_id: str
    date: date
    merchant: str
    amount: Decimal
    currency: str
    status: str
    category: str
    account_id: str
    notes: Optional[str] = None
    is_anomaly: bool = False
    anomaly_reason: Optional[str] = None
    llm_category: Optional[str] = None
    llm_raw_response: Optional[str] = None
    llm_failed: bool = False

class TransactionCreate(TransactionBase):
    job_id: UUID

class TransactionResponse(TransactionBase):
    id: UUID
    job_id: UUID

    model_config = ConfigDict(from_attributes=True)
