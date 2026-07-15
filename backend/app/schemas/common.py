from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime

class APIError(BaseModel):
    """Standard API error response"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: datetime

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    database: str
    version: str = "1.0.0"

class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    success: bool
    data: list
    total: int
    page: int
    page_size: int
    timestamp: datetime
