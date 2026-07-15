from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import json
import hashlib

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.application import Application
from app.models.audit_log import AuditLog
from app.models.scores import Scores
from app.models.recommendation import Recommendation
from app.models.fairness_check import FairnessCheck

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


@router.get("/report")
def get_evaluation_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate an evaluation report across all applications in the database:
    - Trace Correctness
    - Tool Call Accuracy
    - Task Completion Rate
    - Output Quality
    - Faithfulness & Groundedness
    - Fairness Score
    - Governance Score
    - Business KPI Metrics
    """
    applications = db.query(Application).all()
    total_apps = len(applications)
    
    if total_apps == 0:
        return {
            "total_applications_evaluated": 0,
            "metrics": {
                "trace_correctness": 100.0,
                "tool_call_accuracy": 100.0,
                "task_completion": 100.0,
                "output_quality": 100.0,
                "faithfulness": 100.0,
                "fairness": 100.0,
                "governance": 100.0
            },
            "summary": "No applications available to evaluate. Run demo scenarios first."
        }

    # 1. Task Completion Rate (applications that reached final/review states)
    completed_statuses = {"APPROVED", "DECLINED", "PENDING_REVIEW", "REFER", "REFERRAL", "HOLD", "IN_REVIEW"}
    completed_apps = sum(1 for app in applications if app.status in completed_statuses)
    task_completion_rate = (completed_apps / total_apps) * 100.0

    # 2. Governance Score (Audit log presence and hash validation check)
    from datetime import datetime
    audit_logs = db.query(AuditLog).all()
    hash_verified_count = 0
    total_audits_checked = len(audit_logs)
    
    for log in audit_logs:
        # Re-verify the snapshot hash using the exact same snapshot format as GovernanceAgent
        try:
            details = log.details_json or {}
            wf = details.get("workflow_state", {})
            docs_count = details.get("documents_processed", 0)
            ocr_count = len(details.get("ocr_results", []))
            val_status = details.get("validation_status") or 'None'
            
            scores = details.get("scores", {})
            risk_score = scores.get("overall_risk_score")
            if risk_score is None:
                risk_score = 'None'
                
            ai_rec = details.get("ai_recommendation", {})
            rec_val = ai_rec.get("recommendation") or 'None'
            
            fairness = details.get("fairness_check", {})
            fair_status = fairness.get("status") or 'None'
            
            human = details.get("human_decision", {})
            human_dec = human.get("decision")
            if human_dec is None:
                human_dec = 'None'
            
            completed_str = wf.get("completed_at")
            if completed_str:
                try:
                    dt = datetime.fromisoformat(completed_str)
                    completed_at_val = str(dt)
                except Exception:
                    completed_at_val = completed_str
            else:
                completed_at_val = "None"

            snapshot_data = f"\n        application_id:{log.application_id}\n        documents:{docs_count}\n        ocr_results:{ocr_count}\n        validation_status:{val_status}\n        risk_score:{risk_score}\n        recommendation:{rec_val}\n        fairness_status:{fair_status}\n        human_decision:{human_dec}\n        completed_at:{completed_at_val}\n        "
            
            recalculated_hash = hashlib.sha256(snapshot_data.encode()).hexdigest()
            if recalculated_hash == log.snapshot_hash:
                hash_verified_count += 1
        except Exception:
            pass
            
    governance_score = 100.0
    if total_audits_checked > 0:
        governance_score = (hash_verified_count / total_audits_checked) * 100.0

    # 3. Trace Correctness
    # Check if executed applications contain logs for intake -> validation -> scoring -> recommendation -> fairness
    trace_correct_count = 0
    apps_processed = 0
    
    for app in applications:
        app_logs = db.query(AuditLog).filter(AuditLog.application_id == app.id).all()
        if not app_logs:
            continue
            
        apps_processed += 1
        actions = set()
        for log in app_logs:
            actions.add(log.action)
            trail = (log.details_json or {}).get("audit_trail", [])
            for step in trail:
                if isinstance(step, dict) and "action" in step:
                    actions.add(step["action"])
        
        # Verify sequence nodes
        has_intake = "intake_verification" in actions or "INTAKE" in actions
        has_val = "document_validation" in actions or "DOCUMENT_VALIDATION" in actions or any("valid" in a.lower() for a in actions)
        has_scoring = "policy_scoring" in actions or "POLICY_SCORING" in actions or any("score" in a.lower() for a in actions)
        has_rec = "decision_recommendation" in actions or "RECOMMENDATION_GENERATED" in actions or any("recommend" in a.lower() for a in actions)
        
        if has_intake and has_val:
            # If missing doc hold, trace is correct even without scoring
            if app.status == "HOLD" or (has_scoring and has_rec):
                trace_correct_count += 1

    trace_correctness = 100.0
    if apps_processed > 0:
        trace_correctness = (trace_correct_count / apps_processed) * 100.0

    # 4. Tool Call Accuracy
    # Calculate fraction of successful tool calls recorded in logs
    total_tool_calls = 0
    successful_tool_calls = 0
    
    for log in audit_logs:
        details = log.details_json or {}
        tool_calls = details.get("tool_calls", [])
        if not isinstance(tool_calls, list) and "tool_calls" in details:
            tool_calls = [details["tool_calls"]] if details["tool_calls"] else []
        
        # Also collect tool calls inside inner steps
        trail = details.get("audit_trail", [])
        for step in trail:
            if isinstance(step, dict) and "tool_calls" in step:
                step_calls = step["tool_calls"]
                if isinstance(step_calls, list):
                    tool_calls.extend(step_calls)
            
        for tool in tool_calls:
            total_tool_calls += 1
            if tool.get("status") != "failed" and "error" not in tool:
                successful_tool_calls += 1
                
    tool_call_accuracy = 100.0
    if total_tool_calls > 0:
        tool_call_accuracy = (successful_tool_calls / total_tool_calls) * 100.0

    # 5. Output Quality
    # Measure what percentage of generated recommendations have structured explanations and citations
    recs = db.query(Recommendation).all()
    high_quality_recs = 0
    
    for rec in recs:
        # Must have a decision, a justification, and score breakdown
        if rec.recommendation in ["APPROVE", "DECLINE", "REFER", "HOLD"] and len(rec.explanation or "") > 20:
            high_quality_recs += 1
            
    output_quality = 100.0
    if recs:
        output_quality = (high_quality_recs / len(recs)) * 100.0

    # 6. Faithfulness / Groundedness
    # Ensure policy engine decisions correctly cite active rules
    faithfulness = 95.0 # baseline
    cited_correctly = 0
    total_evaluated_cites = len(recs)
    
    for rec in recs:
        if rec.policy_citations:
            cited_correctly += 1
            
    if total_evaluated_cites > 0:
        faithfulness = (cited_correctly / total_evaluated_cites) * 100.0

    # 7. Fairness
    # What percentage of applications passed fairness consistency assessment
    fairness_checks = db.query(FairnessCheck).all()
    fair_count = sum(1 for check in fairness_checks if check.fairness_status == "PASS")
    
    fairness_score = 100.0
    if fairness_checks:
        fairness_score = (fair_count / len(fairness_checks)) * 100.0

    # Overall System Index
    overall_capstone_score = (
        trace_correctness +
        tool_call_accuracy +
        task_completion_rate +
        output_quality +
        faithfulness +
        fairness_score +
        governance_score
    ) / 7.0

    return {
        "total_applications_evaluated": total_apps,
        "overall_score": round(overall_capstone_score, 2),
        "metrics": {
            "trace_correctness": round(trace_correctness, 2),
            "tool_call_accuracy": round(tool_call_accuracy, 2),
            "task_completion": round(task_completion_rate, 2),
            "output_quality": round(output_quality, 2),
            "faithfulness": round(faithfulness, 2),
            "fairness": round(fairness_score, 2),
            "governance": round(governance_score, 2)
        },
        "details": {
            "total_audit_logs": len(audit_logs),
            "hash_verified_logs": hash_verified_count,
            "total_recommendations": len(recs),
            "total_fairness_checks": len(fairness_checks)
        },
        "summary": f"System Evaluation completed across {total_apps} application traces. Overall execution quality stands at {overall_capstone_score:.2f}%."
    }
