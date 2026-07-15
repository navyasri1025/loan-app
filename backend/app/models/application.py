from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from app.database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False, index=True)
    loan_amount = Column(Float, nullable=False)
    loan_purpose = Column(String(255), nullable=True)
    term_months = Column(Integer, nullable=False)
    monthly_debt_obligations = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False) # DRAFT, SUBMITTED, IN_PROGRESS, PENDING_REVIEW, APPROVED, DECLINED, REFER
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    # Relationships
    applicant = relationship("Applicant", back_populates="applications", lazy="select")
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan", lazy="select")
    validation_reports = relationship("ValidationReport", back_populates="application", cascade="all, delete-orphan", lazy="select")
    scores = relationship("Scores", back_populates="application", cascade="all, delete-orphan", lazy="select")
    recommendations = relationship("Recommendation", back_populates="application", cascade="all, delete-orphan", lazy="select")
    fairness_checks = relationship("FairnessCheck", back_populates="application", cascade="all, delete-orphan", lazy="select")
    human_reviews = relationship("HumanReview", back_populates="application", cascade="all, delete-orphan", lazy="select")
    audit_logs = relationship("AuditLog", back_populates="application", cascade="all, delete-orphan", lazy="select")
