from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class FairnessCheckBase(BaseModel):
    blind_recommendation: str
    is_fair: bool
    fairness_status: str
    blind_scores_json: Optional[Any] = None

class FairnessCheckCreate(FairnessCheckBase):
    application_id: int

class FairnessCheckOut(FairnessCheckBase):
    id: int
    application_id: int
    checked_at: datetime

    class Config:
        from_attributes = True
