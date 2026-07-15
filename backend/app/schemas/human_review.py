from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class HumanReviewBase(BaseModel):
    decision: str
    comments: Optional[str] = None

class HumanReviewCreate(HumanReviewBase):
    application_id: int

class HumanReviewOut(HumanReviewBase):
    id: int
    application_id: int
    reviewer_id: Optional[int] = None
    reviewed_at: datetime

    class Config:
        from_attributes = True
