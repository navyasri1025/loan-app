from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ApplicantBase(BaseModel):
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[str] = None
    monthly_income: float = 0.0
    employer_name: Optional[str] = None
    employment_type: str = "Salaried"
    employment_stability_months: int = 0
    credit_score: int = 0

class ApplicantCreate(ApplicantBase):
    id: int # Extends existing User ID

class ApplicantUpdate(BaseModel):
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[str] = None
    monthly_income: Optional[float] = None
    employer_name: Optional[str] = None
    employment_type: Optional[str] = None
    employment_stability_months: Optional[int] = None
    credit_score: Optional[int] = None

class ApplicantOut(ApplicantBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
