from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class RecommendationBase(BaseModel):
    recommendation: str
    confidence_score: float
    explanation: str
    policy_citations: Optional[Any] = None
    reasons_json: Optional[Any] = None

class RecommendationCreate(RecommendationBase):
    application_id: int

class RecommendationOut(RecommendationBase):
    id: int
    application_id: int
    generated_at: datetime

    class Config:
        from_attributes = True
