from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentBase(BaseModel):
    document_type: str
    file_path: str
    status: str = "UPLOADED"
    error_message: Optional[str] = None

class DocumentCreate(BaseModel):
    document_type: str
    file_path: str

class DocumentUpdate(BaseModel):
    status: Optional[str] = None
    error_message: Optional[str] = None

class DocumentOut(DocumentBase):
    id: int
    application_id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True
