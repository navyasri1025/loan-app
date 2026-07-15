from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.application import Application
from app.models.scores import Scores
from app.models.fairness_check import FairnessCheck
from app.models.human_review import HumanReview

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get aggregated analytics for dashboard metrics:
    - Total, Pending, Approved, Declined, Referred counts
    - Average Risk Score
    - Average Decision Time (in hours)
    - Total Fairness Failures
    """
    # 1. Status Counts
    status_counts = db.query(
        Application.status, func.count(Application.id)
    ).group_by(Application.status).all()
    
    counts = {
        "DRAFT": 0,
        "SUBMITTED": 0,
        "IN_PROGRESS": 0,
        "PENDING_REVIEW": 0,
        "APPROVED": 0,
        "DECLINED": 0,
        "REFER": 0
    }
    
    total = 0
    for status_str, count in status_counts:
        if status_str in counts:
            counts[status_str] = count
        else:
            counts[status_str] = count
        total += count

    counts["TOTAL"] = total

    # 2. Average Risk Score
    avg_risk = db.query(func.avg(Scores.overall_risk_score)).scalar() or 0.0

    # 3. Average Decision Time (between Application.created_at and HumanReview.reviewed_at)
    time_diffs = db.query(
        Application.created_at,
        HumanReview.reviewed_at
    ).join(
        HumanReview, Application.id == HumanReview.application_id
    ).all()

    avg_decision_hours = 0.0
    if time_diffs:
        total_hours = 0.0
        for created, reviewed in time_diffs:
            diff = reviewed - created
            total_hours += diff.total_seconds() / 3600.0
        avg_decision_hours = total_hours / len(time_diffs)

    # 4. Fairness Failures
    fairness_failures = db.query(FairnessCheck).filter(
        FairnessCheck.status == "FAIRNESS_FAILURE"
    ).count()

    # 5. Monthly Submissions (Past 6 Months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_data = db.query(
        func.strftime("%Y-%m", Application.created_at).label("month"),
        func.count(Application.id).label("count")
    ).filter(
        Application.created_at >= six_months_ago
    ).group_by(
        "month"
    ).order_by(
        "month"
    ).all()

    monthly_stats = [{"month": row.month, "count": row.count} for row in monthly_data]

    # 6. Status distribution for charts
    status_distribution = [
        {"name": "Approved", "value": counts["APPROVED"]},
        {"name": "Declined", "value": counts["DECLINED"]},
        {"name": "Pending Review", "value": counts["PENDING_REVIEW"]},
        {"name": "Referred", "value": counts["REFER"] + counts.get("REFERRAL", 0)}
    ]

    return {
        "status_counts": counts,
        "average_risk_score": round(avg_risk, 2),
        "average_decision_time_hours": round(avg_decision_hours, 2),
        "fairness_failures": fairness_failures,
        "monthly_stats": monthly_stats,
        "status_distribution": status_distribution
    }
