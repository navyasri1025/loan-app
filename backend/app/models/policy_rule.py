from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from app.database import Base

class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False)
    rule_key = Column(String(50), unique=True, index=True, nullable=False) # e.g., MIN_CREDIT_SCORE, MAX_DTI, MIN_EMPLOYMENT_MONTHS
    threshold_value = Column(Float, nullable=False)
    rule_description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
