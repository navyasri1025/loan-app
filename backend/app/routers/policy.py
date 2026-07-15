from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.policy_rule import PolicyRule
from app.schemas.policy_rule import PolicyRuleOut, PolicyRuleUpdate
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from typing import List

router = APIRouter(prefix="/api/policy", tags=["Underwriting Policy Rules"])

@router.get("/rules", response_model=List[PolicyRuleOut])
def get_all_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Any authenticated user can read the policy rules
    return db.query(PolicyRule).all()

@router.put("/rules/{rule_key}", response_model=PolicyRuleOut)
def update_policy_rule(
    rule_key: str,
    rule_in: PolicyRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["CreditManager"]))
):
    rule = db.query(PolicyRule).filter(PolicyRule.rule_key == rule_key).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy rule with key '{rule_key}' not found"
        )
        
    # Update properties if provided
    if rule_in.rule_name is not None:
        rule.rule_name = rule_in.rule_name
    if rule_in.threshold_value is not None:
        rule.threshold_value = rule_in.threshold_value
    if rule_in.rule_description is not None:
        rule.rule_description = rule_in.rule_description
    if rule_in.is_active is not None:
        rule.is_active = rule_in.is_active
        
    db.commit()
    db.refresh(rule)
    return rule
