from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
import datetime
from app.database import Base

class HumanReview(Base):
    __tablename__ = "human_reviews"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    decision = Column(String(50), nullable=False) # APPROVED, DECLINED, REFER
    comments = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    application = relationship(
        "Application",
        back_populates="human_reviews",
        lazy="select"
    )
    reviewer = relationship(
        "User",
        foreign_keys=[reviewer_id],
        back_populates="human_reviews",
        lazy="select"
    )
