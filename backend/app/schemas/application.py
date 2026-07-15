from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.applicant import ApplicantOut

class ApplicationBase(BaseModel):
    loan_amount: float
    loan_purpose: Optional[str] = None
    term_months: int
    monthly_debt_obligations: float = 0.0

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    loan_amount: Optional[float] = None
    loan_purpose: Optional[str] = None
    term_months: Optional[int] = None
    monthly_debt_obligations: Optional[float] = None

class ApplicationOut(ApplicationBase):
    id: int
    applicant_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ApplicationDetailOut(ApplicationOut):
    applicant: Optional[ApplicantOut] = None
    
    class Config:
        from_attributes = True
