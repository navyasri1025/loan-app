"""
Application Processing API Endpoints

Handles workflow execution, status tracking, and human approval.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.application import Application
from app.models.human_review import HumanReview
from app.agents.workflow import WorkflowOrchestrator
from app.agents import InputPayload, WorkflowOutput
from app.core.exceptions import NotFoundException, AuthorizationException
from app.core.logging import get_logger

logger = get_logger("routers.processing")

router = APIRouter(prefix="/api/applications", tags=["application-processing"])

# Initialize workflow orchestrator
orchestrator = WorkflowOrchestrator()


async def _run_workflow_background(
    application_id: int,
    payload: InputPayload,
    db: Session,
):
    """Execute the LangGraph workflow in the background and persist results."""
    try:
        result = await orchestrator.execute_workflow(payload)

        # Re-open a fresh DB connection in the background task
        from app.database import SessionLocal
        bg_db = SessionLocal()
        try:
            application = bg_db.query(Application).filter(
                Application.id == application_id
            ).first()

            if not application:
                logger.error(f"Background task: application {application_id} not found")
                return

            if result.errors:
                application.status = "FAILED"
                logger.warning(
                    f"Workflow failed for application {application_id}: {result.errors}"
                )
            else:
                application.status = result.final_status or "PENDING_REVIEW"
                if result.ai_recommendation:
                    from app.models.recommendation import Recommendation as DBRecommendation
                    existing_rec = bg_db.query(DBRecommendation).filter(
                        DBRecommendation.application_id == application_id
                    ).first()

                    citations = result.ai_recommendation.policy_citations
                    citations_json = citations if isinstance(citations, list) else []
                    explanation = (
                        result.ai_recommendation.reason
                        or result.ai_recommendation.explanation
                        or "No explanation provided"
                    )

                    if existing_rec:
                        existing_rec.recommendation = result.ai_recommendation.recommendation or "REFER"
                        existing_rec.confidence_score = result.ai_recommendation.confidence or 0.8
                        existing_rec.explanation = explanation
                        existing_rec.policy_citations = citations_json
                        existing_rec.generated_at = datetime.utcnow()
                    else:
                        db_rec = DBRecommendation(
                            application_id=application_id,
                            recommendation=result.ai_recommendation.recommendation or "REFER",
                            confidence_score=result.ai_recommendation.confidence or 0.8,
                            explanation=explanation,
                            policy_citations=citations_json,
                        )
                        bg_db.add(db_rec)

            application.updated_at = datetime.utcnow()
            bg_db.commit()
            logger.info(
                f"Background workflow completed for application {application_id}: {result.final_status}"
            )
        finally:
            bg_db.close()

    except Exception as e:
        logger.error(
            f"Background workflow exception for application {application_id}: {e}",
            exc_info=True,
        )
        # Mark application as FAILED so the frontend polling terminates
        from app.database import SessionLocal
        err_db = SessionLocal()
        try:
            application = err_db.query(Application).filter(
                Application.id == application_id
            ).first()
            if application:
                application.status = "FAILED"
                application.updated_at = datetime.utcnow()
                err_db.commit()
        finally:
            err_db.close()


@router.post("/{application_id}/process")
async def process_application(
    application_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Start the AI workflow for an application (non-blocking).

    Returns 202 Accepted immediately and runs the LangGraph pipeline
    (Intake → OCR → Validation → Policy → Decision → Fairness → Governance)
    in the background.

    Poll GET /{application_id}/workflow-status to track progress.
    """

    logger.info(
        f"Processing application {application_id}",
        extra={"application_id": application_id, "user_id": current_user.id},
    )

    # Get application
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not application:
        raise NotFoundException(detail=f"Application {application_id} not found")

    # Applicants can only process their own applications
    if current_user.role == "Applicant" and application.applicant_id != current_user.id:
        raise AuthorizationException(detail="You can only process your own applications")

    # Mark as processing immediately so UI can reflect the change
    application.status = "SUBMITTED"
    application.updated_at = datetime.utcnow()
    db.commit()

    # Build documents list
    documents = [
        {
            "file_id": str(doc.id),
            "file_name": doc.file_path,
            "document_type": doc.document_type,
        }
        for doc in application.documents
    ]

    payload = InputPayload(
        application_id=application_id,
        applicant_id=application.applicant_id,
        user_id=current_user.id,
        documents=documents,
    )

    # Schedule workflow in background — returns 202 immediately
    background_tasks.add_task(_run_workflow_background, application_id, payload, db)

    logger.info(f"Workflow queued for application {application_id}")

    return {
        "application_id": application_id,
        "status": "SUBMITTED",
        "message": "Workflow started. Poll /workflow-status for progress.",
    }


@router.get("/{application_id}/workflow-status")
async def get_workflow_status(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current workflow status and recommendation"""
    
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()
    
    if not application:
        raise NotFoundException(detail=f"Application {application_id} not found")
    
    return {
        "application_id": application.id,
        "status": application.status,
        "current_stage": "pending_human_review" if application.status == "PENDING_REVIEW" else application.status,
        "created_at": application.created_at,
        "updated_at": application.updated_at
    }


@router.post("/{application_id}/human-review")
async def submit_human_review(
    application_id: int,
    decision: str,  # APPROVE, REFER, or DECLINE — Req 4
    comment: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Submit human underwriter decision — Requirement 4: Human Gate.

    The AI workflow only makes RECOMMENDATIONS.
    The final decision is ALWAYS made by a qualified human underwriter.

    Supported decisions:
      APPROVE  — Underwriter approves the loan
      REFER    — Underwriter refers for additional review / escalation
      DECLINE  — Underwriter declines the loan

    This endpoint enforces the human-in-the-loop requirement.
    """

    logger.info(
        f"Human review submitted for application {application_id}: {decision}",
        extra={"application_id": application_id, "decision": decision}
    )

    # Get application
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not application:
        raise NotFoundException(detail=f"Application {application_id} not found")

    # Check authorization
    if current_user.role not in ["Underwriter", "CreditManager"]:
        raise AuthorizationException(
            detail="Only underwriters can submit decisions"
        )

    # Validate decision — now supports APPROVE, REFER, DECLINE (Req 4)
    if decision not in ["APPROVE", "REFER", "DECLINE"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Decision must be APPROVE, REFER, or DECLINE"
        )

    # Create human review record
    review = HumanReview(
        application_id=application_id,
        reviewer_id=current_user.id,
        decision=decision,
        comments=comment,
        reviewed_at=datetime.utcnow()
    )

    db.add(review)

    # Update application status
    status_map = {
        "APPROVE": "APPROVED",
        "DECLINE": "DECLINED",
        "REFER": "REFER",
    }
    application.status = status_map[decision]
    application.updated_at = datetime.utcnow()

    # Write audit log entry for the human decision (Req 6)
    from app.models.audit_log import AuditLog
    import hashlib, json

    decision_details = {
        "human_decision": {
            "decision": decision,
            "reviewer_id": current_user.id,
            "reviewer_name": current_user.full_name,
            "comment": comment,
            "timestamp": datetime.utcnow().isoformat(),
        },
        "application_status_updated_to": status_map[decision],
    }

    snapshot_data = (
        f"application_id:{application_id}"
        f"|decision:{decision}"
        f"|reviewer:{current_user.id}"
    )
    snap_hash = hashlib.sha256(snapshot_data.encode()).hexdigest()

    audit = AuditLog(
        application_id=application_id,
        action="HUMAN_DECISION",
        user_id=current_user.id,
        details_json=decision_details,
        snapshot_hash=snap_hash,
    )
    db.add(audit)

    db.commit()

    logger.info(
        f"Application {application_id} decision={decision} by reviewer {current_user.id}",
        extra={"application_id": application_id, "reviewer_id": current_user.id}
    )

    return {
        "application_id": application_id,
        "decision": decision,
        "status": application.status,
        "reviewed_at": review.reviewed_at,
        "reviewer": current_user.full_name,
        "comment": comment,
    }


@router.get("/{application_id}/audit-trail")
async def get_audit_trail(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get complete audit trail for the application.
    
    Shows all AI agent actions, scores, recommendations, fairness checks,
    and human decisions.
    """
    
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()
    
    if not application:
        raise NotFoundException(detail=f"Application {application_id} not found")
    
    # Get audit logs from database
    from app.models.audit_log import AuditLog
    
    logs = db.query(AuditLog).filter(
        AuditLog.application_id == application_id
    ).order_by(AuditLog.created_at).all()
    
    return {
        "application_id": application_id,
        "audit_logs": [
            {
                "id": log.id,
                "action": log.action,
                "timestamp": log.created_at,
                "details": log.details_json,
                "hash": log.snapshot_hash
            }
            for log in logs
        ],
        "total_entries": len(logs)
    }


@router.get("/{application_id}/recommendation")
async def get_recommendation(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get AI recommendation and explanation.
    
    Shows:
    - Recommendation (APPROVE, REFER, or DECLINE)
    - Confidence score
    - Score breakdown
    - Policy citations
    - Fairness check results
    - Detailed reasoning
    """
    
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()
    
    if not application:
        raise NotFoundException(detail=f"Application {application_id} not found")
    
    # Get most recent audit log with recommendation
    from app.models.audit_log import AuditLog
    
    log = db.query(AuditLog).filter(
        AuditLog.application_id == application_id,
        AuditLog.action == "WORKFLOW_COMPLETE"
    ).order_by(AuditLog.created_at.desc()).first()
    
    if not log:
        return {
            "application_id": application_id,
            "recommendation": None,
            "message": "No recommendation available yet. Process the application first."
        }
    
    details = log.details_json or {}
    recommendation = details.get("ai_recommendation", {})
    fairness = details.get("fairness_check", {})
    
    return {
        "application_id": application_id,
        "recommendation": recommendation.get("recommendation"),
        "confidence": recommendation.get("confidence"),
        "reason": recommendation.get("reason"),
        "score_breakdown": details.get("scores", {}),
        "policy_citations": recommendation.get("policy_citations", []),
        "fairness_status": fairness.get("status"),
        "fairness_summary": fairness.get("summary"),
        "full_details": details
    }
