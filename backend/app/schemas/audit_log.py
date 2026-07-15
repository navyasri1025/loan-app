from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class AuditLogBase(BaseModel):
    action: str
    details_json: Optional[Any] = None
    snapshot_hash: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    application_id: Optional[int] = None
    user_id: Optional[int] = None

class AuditLogOut(AuditLogBase):
    id: int
    application_id: Optional[int] = None
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
