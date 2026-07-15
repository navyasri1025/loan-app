from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PolicyRuleBase(BaseModel):
    rule_name: str
    rule_key: str
    threshold_value: float
    rule_description: Optional[str] = None
    is_active: bool = True

class PolicyRuleCreate(PolicyRuleBase):
    pass

class PolicyRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    threshold_value: Optional[float] = None
    rule_description: Optional[str] = None
    is_active: Optional[bool] = None

class PolicyRuleOut(PolicyRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
