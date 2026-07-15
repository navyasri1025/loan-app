from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class ValidationReportBase(BaseModel):
    name_match_score: float = 1.0
    dob_match_score: float = 1.0
    income_consistency_pass: bool = True
    is_expired: bool = False
    is_unreadable: bool = False
    status: str = "PASS"
    details_json: Optional[Any] = None

class ValidationReportCreate(ValidationReportBase):
    application_id: int

class ValidationReportOut(ValidationReportBase):
    id: int
    application_id: int
    created_at: datetime

    class Config:
        from_attributes = True
