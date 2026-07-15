from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
import datetime
from app.database import Base

class FairnessCheck(Base):
    __tablename__ = "fairness_checks"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    blind_recommendation = Column(String(50), nullable=False) # APPROVE, REFER, DECLINE
    is_fair = Column(Boolean, default=True, nullable=False) # True if recommendation matches
    fairness_status = Column(String(50), default="PASS", nullable=False) # PASS, FAIRNESS_FAILURE
    blind_scores_json = Column(JSON, nullable=True) # Scores calculated under blind simulation
    checked_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    application = relationship("Application", back_populates="fairness_checks")
