from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False) # Aadhaar, PAN, SalarySlip, BankStatement, EmploymentLetter
    file_path = Column(String(255), nullable=False)
    status = Column(String(50), default="UPLOADED", nullable=False) # UPLOADED, PROCESSING, PASSED, FAILED
    error_message = Column(String(255), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    application = relationship("Application", back_populates="documents", lazy="select")
    ocr_results = relationship("OCRResult", back_populates="document", cascade="all, delete-orphan", lazy="select")
