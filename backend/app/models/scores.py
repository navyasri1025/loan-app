from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from app.database import Base

class Scores(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    debt_to_income_ratio = Column(Float, nullable=False) # DTI ratio (monthly debt payments / monthly income)
    employment_stability_months = Column(Integer, nullable=False)
    credit_score = Column(Integer, nullable=False)
    income_stability_rating = Column(Float, nullable=False) # Rating from 0.0 to 1.0 based on consistent deposits
    documentation_quality_score = Column(Float, nullable=False) # Document readability / checksum verification
    risk_score = Column(Float, nullable=False) # Composite risk score (0 to 100)
    calculated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    application = relationship("Application", back_populates="scores")
