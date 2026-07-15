"""
ValidationReport Model — upgraded for Requirement 1.

Added fields:
  - hold_reason: stores the specific reason why the application is on hold
  - issues_json:  structured list of all validation issues
  - missing_documents: list of missing document group names
  - summary: human-readable summary
  - validated_at: timestamp of validation run
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
import datetime
from app.database import Base


class ValidationReport(Base):
    __tablename__ = "validation_reports"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)

    # Legacy fields (kept for backward compatibility)
    name_match_score = Column(Float, default=1.0, nullable=False)
    dob_match_score = Column(Float, default=1.0, nullable=False)
    income_consistency_pass = Column(Boolean, default=True, nullable=False)
    is_expired = Column(Boolean, default=False, nullable=False)
    is_unreadable = Column(Boolean, default=False, nullable=False)

    # Primary status: PASS, FAIL, HOLD
    status = Column(String(50), default="PASS", nullable=False)

    # Requirement 1: hold reason stored in audit DB table (Req 1)
    hold_reason = Column(Text, nullable=True)

    # Structured issues list
    issues_json = Column(JSON, nullable=True)

    # Names of the missing document groups (e.g. ["Income Proof"])
    missing_documents = Column(JSON, nullable=True)

    # Human-readable summary
    summary = Column(Text, nullable=True)

    # Backward-compat details field
    details_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    validated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=True)

    # Relationships
    application = relationship("Application", back_populates="validation_reports")
