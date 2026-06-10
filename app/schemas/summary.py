from pydantic import BaseModel, ConfigDict
from uuid import UUID
from decimal import Decimal
from typing import List

class JobSummaryBase(BaseModel):
    total_spend_inr: Decimal
    total_spend_usd: Decimal
    top_merchants: List[str]
    anomaly_count: int
    narrative: str
    risk_level: str

class JobSummaryCreate(JobSummaryBase):
    job_id: UUID

class JobSummaryResponse(JobSummaryBase):
    id: UUID
    job_id: UUID

    model_config = ConfigDict(from_attributes=True)
