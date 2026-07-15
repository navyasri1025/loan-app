from sqlalchemy import Column, Integer, Text, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
import datetime
from app.database import Base

class OCRResult(Base):
    __tablename__ = "ocr_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_text = Column(Text, nullable=False)
    parsed_json = Column(JSON, nullable=True) # Extracted fields: name, ID number, monthly figures, etc.
    confidence_score = Column(Float, default=1.0, nullable=False)
    extracted_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="ocr_results")
