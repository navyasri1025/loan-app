from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
import datetime
from app.database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation = Column(String(50), nullable=False) # APPROVE, REFER, DECLINE
    confidence_score = Column(Float, nullable=False) # 0.0 to 1.0 confidence level
    explanation = Column(Text, nullable=False) # Detailed markdown text justifying decision
    policy_citations = Column(JSON, nullable=True) # Policies read and matched
    reasons_json = Column(JSON, nullable=True) # Key points (e.g. DTI too high)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    application = relationship("Application", back_populates="recommendations")
