from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from app.database import Base

class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    phone = Column(String(20), nullable=True)
    date_of_birth = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    gender = Column(String(20), nullable=True)
    monthly_income = Column(Float, default=0.0, nullable=False)
    employer_name = Column(String(100), nullable=True)
    employment_type = Column(String(50), default="Salaried", nullable=False) # Salaried, Self-Employed, Unemployed
    employment_stability_months = Column(Integer, default=0, nullable=False)
    credit_score = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    # Relationships
    user = relationship(
        "User",
        back_populates="applicant_profile",
        lazy="select"
    )
    applications = relationship(
        "Application",
        back_populates="applicant",
        cascade="all, delete-orphan",
        lazy="select"
    )
