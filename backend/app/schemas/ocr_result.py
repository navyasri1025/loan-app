from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class OCRResultBase(BaseModel):
    raw_text: str
    parsed_json: Optional[Any] = None
    confidence_score: float = 1.0

class OCRResultCreate(OCRResultBase):
    document_id: int

class OCRResultOut(OCRResultBase):
    id: int
    document_id: int
    extracted_at: datetime

    class Config:
        from_attributes = True
