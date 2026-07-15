from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
import datetime
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False) # e.g. UPLOAD, OCR_EXTRACT, POLICY_CHECK, BIAS_TEST, HUMAN_DECISION
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    details_json = Column(JSON, nullable=True) # Full contextual state snapshot
    snapshot_hash = Column(String(64), nullable=True) # Integrity checksum of the log state
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    application = relationship(
        "Application",
        back_populates="audit_logs",
        lazy="select"
    )
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="audit_logs",
        lazy="select"
    )
