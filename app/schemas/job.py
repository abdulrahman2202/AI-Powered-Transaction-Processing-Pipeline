from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict
from app.schemas.summary import JobSummaryResponse
from app.schemas.transaction import TransactionResponse

class JobBase(BaseModel):
    filename: str

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: UUID
    status: str
    row_count_raw: Optional[int] = None
    row_count_clean: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class JobStatusResponse(BaseModel):
    job: JobResponse
    summary: Optional[JobSummaryResponse] = None

class JobResultsResponse(BaseModel):
    cleaned_transactions: List[TransactionResponse]
    anomalies: List[TransactionResponse]
    category_breakdown: Dict[str, int]
    ai_summary: Optional[JobSummaryResponse] = None
