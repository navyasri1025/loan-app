import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="Applicant", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    # Relationships
    applicant_profile = relationship(
        "Applicant",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="select"
    )
    audit_logs = relationship(
        "AuditLog",
        foreign_keys="AuditLog.user_id",
        back_populates="user",
        lazy="select"
    )
    human_reviews = relationship(
        "HumanReview",
        foreign_keys="HumanReview.reviewer_id",
        back_populates="reviewer",
        lazy="select"
    )
