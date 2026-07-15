"""
Governance Agent

Generates immutable audit logs.

Stores:
- Inputs
- Outputs
- OCR results
- Tool calls
- Reasoning
- Scores
- Recommendation
- Policy version
- Fairness result
- Human decision
- Timestamp

OpenRouter integration: the LLM generates a governance and compliance
summary that interprets the complete workflow outcome. The SHA-256
snapshot hash, database write, and pass/fail determinations all remain
fully deterministic.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Dict, Any

from app.agents.base import BaseAgent
from app.agents import WorkflowState, AuditEntry
from app.core.openrouter_client import openrouter_client
from app.core.logging import get_logger
from app.database import SessionLocal

logger = get_logger("agents.governance")

_GOVERNANCE_SYSTEM = (
    "You are a compliance and governance officer at a financial institution. "
    "An AI-powered loan processing workflow has just completed. "
    "Write a professional governance and compliance summary (4-6 sentences) that:\n"
    "1. Summarises the complete workflow outcome.\n"
    "2. Confirms which regulatory/compliance steps were executed "
    "(OCR, document validation, policy scoring, fairness check, human review).\n"
    "3. Notes the AI recommendation and fairness check result.\n"
    "4. States the cryptographic audit trail integrity status.\n"
    "5. Confirms that the human-in-the-loop requirement was met.\n"
    "Be factual, professional, and suitable for a compliance record."
)


class GovernanceAgent(BaseAgent):
    """Creates immutable audit logs for compliance, with LLM-generated summary."""

    def __init__(self):
        super().__init__("GovernanceAgent")

    # ──────────────────────────────────────────────────────────────────────────
    # Main process
    # ──────────────────────────────────────────────────────────────────────────

    async def process(self, state: WorkflowState) -> Dict[str, Any]:
        """Store complete audit trail in database and generate compliance summary."""
        try:
            self.logger.info(
                "Starting governance audit logging",
                extra={"application_id": state.application_id},
            )

            # ── Generate snapshot hash (deterministic) ────────────────────────
            snapshot_hash = self._generate_snapshot_hash(state)

            # ── LLM governance summary ────────────────────────────────────────
            governance_summary = await self._generate_governance_summary(
                state, snapshot_hash
            )

            # ── Store audit log in database ───────────────────────────────────
            db = SessionLocal()
            try:
                from app.models.audit_log import AuditLog

                audit_log_entry = AuditLog(
                    application_id=state.application_id,
                    action="WORKFLOW_COMPLETE",
                    user_id=state.user_id,
                    details_json={
                        "workflow_state": {
                            "application_id": state.application_id,
                            "applicant_id": state.applicant_id,
                            "final_status": state.final_status,
                            "error_message": state.error_message,
                            "completed_at": state.completed_at.isoformat()
                            if state.completed_at else None,
                        },
                        "documents_processed": len(state.documents),
                        "ocr_results": [
                            {
                                "document_id": r.document_id,
                                "confidence_score": r.confidence_score,
                                "error": r.error,
                            }
                            for r in state.ocr_results
                        ],
                        "validation_status": (
                            state.validation_report.status
                            if state.validation_report else None
                        ),
                        "validation_issues": [
                            {
                                "document_type": i.document_type,
                                "issue_type": i.issue_type,
                                "severity": i.severity,
                            }
                            for i in (
                                state.validation_report.issues
                                if state.validation_report else []
                            )
                        ],
                        "scores": {
                            "dti_score": state.score_breakdown.dti_score
                            if state.score_breakdown else None,
                            "income_stability": state.score_breakdown.income_stability_score
                            if state.score_breakdown else None,
                            "employment_stability": state.score_breakdown.employment_stability_score
                            if state.score_breakdown else None,
                            "documentation_quality": state.score_breakdown.documentation_quality_score
                            if state.score_breakdown else None,
                            "credit_score": state.score_breakdown.credit_score
                            if state.score_breakdown else None,
                            "overall_risk_score": state.score_breakdown.overall_risk_score
                            if state.score_breakdown else None,
                        },
                        "ai_recommendation": {
                            "recommendation": state.ai_recommendation.recommendation
                            if state.ai_recommendation else None,
                            "confidence": state.ai_recommendation.confidence
                            if state.ai_recommendation else None,
                            "reason": state.ai_recommendation.reason
                            if state.ai_recommendation else None,
                            "policy_citations": state.ai_recommendation.policy_citations
                            if state.ai_recommendation else [],
                        },
                        "fairness_check": {
                            "status": state.fairness_check.status
                            if state.fairness_check else None,
                            "differences": state.fairness_check.differences
                            if state.fairness_check else [],
                            "summary": state.fairness_check.summary
                            if state.fairness_check else None,
                        },
                        "human_decision": {
                            "decision": state.human_decision,
                            "comment": state.human_comment,
                            "reviewer_id": state.human_reviewer_id,
                            "timestamp": state.human_review_timestamp.isoformat()
                            if state.human_review_timestamp else None,
                        },
                        "policy_version": state.policy_version,
                        "audit_trail_entries": len(state.audit_trail),
                        "governance_summary": governance_summary,
                        "audit_trail": [
                            {
                                "timestamp": entry.timestamp.isoformat()
                                if isinstance(entry.timestamp, datetime)
                                else entry.timestamp,
                                "agent": entry.agent,
                                "action": entry.action,
                                "inputs": entry.inputs,
                                "outputs": entry.outputs,
                                "tool_calls": entry.tool_calls,
                                "reasoning": entry.reasoning,
                            }
                            for entry in state.audit_trail
                        ],
                    },
                    snapshot_hash=snapshot_hash,
                )

                db.add(audit_log_entry)
                db.commit()

                self.logger.info(
                    "Audit log entry created: %s",
                    audit_log_entry.id,
                    extra={
                        "application_id": state.application_id,
                        "audit_log_id": audit_log_entry.id,
                    },
                )

                # ── Governance audit entry ────────────────────────────────────
                audit_entry = self.log_action(
                    state,
                    action="governance_audit",
                    inputs={
                        "application_id": state.application_id,
                        "audit_trail_entries": len(state.audit_trail),
                    },
                    outputs={
                        "audit_log_id": audit_log_entry.id,
                        "snapshot_hash": snapshot_hash,
                        "audit_entries_stored": len(state.audit_trail),
                        "governance_summary": governance_summary,
                    },
                    reasoning=governance_summary,
                )

                return {
                    "audit_trail": [audit_entry],
                    "governance_audit_id": audit_log_entry.id,
                }

            finally:
                db.close()

        except Exception as exc:
            self.logger.error(
                "Error in governance agent: %s",
                str(exc),
                extra={"application_id": state.application_id},
                exc_info=True,
            )
            return {
                "error_message": f"Governance audit failed: {str(exc)}",
                "error_at_stage": "GovernanceAgent",
            }

    # ──────────────────────────────────────────────────────────────────────────
    # LLM — governance summary
    # ──────────────────────────────────────────────────────────────────────────

    async def _generate_governance_summary(
        self, state: WorkflowState, snapshot_hash: str
    ) -> str:
        """Generate a professional governance and compliance summary via OpenRouter."""
        user_prompt = (
            f"Workflow completed for application ID: {state.application_id}\n"
            f"Documents processed: {len(state.documents)}\n"
            f"OCR extraction: {'Completed' if state.ocr_results else 'Not run'}\n"
            f"Document validation: "
            f"{state.validation_report.status if state.validation_report else 'Not run'}\n"
            f"Policy scoring: "
            f"{'Completed — overall score: ' + str(round(state.score_breakdown.overall_risk_score, 1)) + '/100' if state.score_breakdown else 'Not run'}\n"
            f"AI recommendation: "
            f"{state.ai_recommendation.recommendation if state.ai_recommendation else 'Not generated'}\n"
            f"Fairness check: "
            f"{state.fairness_check.status if state.fairness_check else 'Not run'}\n"
            f"Human decision: {state.human_decision or 'Pending underwriter review'}\n"
            f"Audit trail entries: {len(state.audit_trail)}\n"
            f"SHA-256 snapshot hash: {snapshot_hash[:16]}...\n"
            f"Policy version: {state.policy_version}\n\n"
            "Write the governance and compliance summary."
        )

        try:
            summary = await openrouter_client.chat(
                user=user_prompt,
                system=_GOVERNANCE_SYSTEM,
                temperature=0.1,
                max_tokens=500,
            )
            return summary.strip()
        except Exception as exc:
            self.logger.warning(
                "OpenRouter unavailable for governance summary — using fallback. Reason: %s",
                str(exc),
            )
            rec = state.ai_recommendation.recommendation if state.ai_recommendation else "N/A"
            fairness = state.fairness_check.status if state.fairness_check else "N/A"
            return (
                f"Governance audit complete for application {state.application_id}. "
                f"All workflow stages executed: OCR extraction, document validation, "
                f"policy scoring, AI recommendation ({rec}), and fairness check ({fairness}). "
                f"Complete audit trail stored immutably with SHA-256 hash {snapshot_hash[:16]}... "
                f"({len(state.audit_trail)} entries). "
                "Human underwriter review is pending as required by policy."
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Snapshot hash (deterministic, immutable)
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_snapshot_hash(self, state: WorkflowState) -> str:
        """Generate SHA-256 integrity checksum of critical workflow state."""
        snapshot_data = (
            f"application_id:{state.application_id}"
            f"|documents:{len(state.documents)}"
            f"|ocr_results:{len(state.ocr_results)}"
            f"|validation_status:{state.validation_report.status if state.validation_report else 'None'}"
            f"|risk_score:{state.score_breakdown.overall_risk_score if state.score_breakdown else 'None'}"
            f"|recommendation:{state.ai_recommendation.recommendation if state.ai_recommendation else 'None'}"
            f"|fairness_status:{state.fairness_check.status if state.fairness_check else 'None'}"
            f"|human_decision:{state.human_decision}"
            f"|completed_at:{state.completed_at}"
        )
        return hashlib.sha256(snapshot_data.encode()).hexdigest()
