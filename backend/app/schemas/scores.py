from pydantic import BaseModel
from datetime import datetime

class ScoresBase(BaseModel):
    debt_to_income_ratio: float
    employment_stability_months: int
    credit_score: int
    income_stability_rating: float
    documentation_quality_score: float
    risk_score: float

class ScoresCreate(ScoresBase):
    application_id: int

class ScoresOut(ScoresBase):
    id: int
    application_id: int
    calculated_at: datetime

    class Config:
        from_attributes = True
