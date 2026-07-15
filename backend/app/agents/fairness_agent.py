"""
Fairness Agent

Implements bias testing through identity-blind application.

Process:
1. Create identity-blind copy (remove: name, gender, phone, email, address)
2. Run scoring again with identity-blind data
3. Compare recommendations
4. Flag if recommendation changes (FAIRNESS FAILURE)
5. Store comparison with LLM-generated fairness analysis

OpenRouter integration: the LLM generates a thorough fairness analysis
explaining what was checked, what was found, and what it means. All
pass/fail logic remains deterministic.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, Any

from app.agents.base import BaseAgent
from app.agents import WorkflowState, FairnessCheckResult
from app.core.openrouter_client import openrouter_client

_FAIRNESS_SYSTEM = (
    "You are a fairness and bias auditor at a financial institution. "
    "Your role is to analyse whether an AI loan recommendation could be influenced "
    "by protected identity attributes (name, gender, address, etc.).\n\n"
    "Write a concise but thorough fairness audit summary (4-6 sentences) that:\n"
    "1. States the fairness outcome (PASS or FAIRNESS_FAILURE).\n"
    "2. Explains what identity attributes were removed for the blind test.\n"
    "3. States whether the recommendation changed and what that means.\n"
    "4. Provides an expert interpretation of the result.\n"
    "Be professional, factual, and objective."
)


class FairnessAgent(BaseAgent):
    """Checks for bias in recommendations via identity-blind re-scoring."""

    def __init__(self):
        super().__init__("FairnessAgent")

    # ──────────────────────────────────────────────────────────────────────────
    # Main process
    # ──────────────────────────────────────────────────────────────────────────

    async def process(self, state: WorkflowState) -> Dict[str, Any]:
        """Run fairness check with LLM-generated audit summary."""
        try:
            self.logger.info(
                "Starting fairness check",
                extra={"application_id": state.application_id},
            )

            if not state.ai_recommendation:
                return {
                    "error_message": "No recommendation to check for fairness",
                    "error_at_stage": "FairnessAgent",
                }

            # ── Identity-blind re-scoring ─────────────────────────────────────
            blind_state = self._create_identity_blind_state(state)
            blind_recommendation = await self._rescore_blind_application(
                state, blind_state
            )

            original_rec = state.ai_recommendation.recommendation
            recommendation_changed = blind_recommendation != original_rec

            # ── Deterministic pass/fail ───────────────────────────────────────
            if recommendation_changed:
                status = "FAIRNESS_FAILURE"
                differences = [
                    f"Original recommendation: {original_rec}",
                    f"Identity-blind recommendation: {blind_recommendation}",
                    "Recommendation differs based on identity — potential bias detected.",
                ]
            else:
                status = "PASS"
                differences = []

            # ── LLM-generated fairness summary ────────────────────────────────
            summary = await self._generate_fairness_summary(
                status,
                original_rec,
                blind_recommendation,
                recommendation_changed,
                state.score_breakdown.overall_risk_score if state.score_breakdown else None,
            )

            fairness_check = FairnessCheckResult(
                status=status,
                identity_blind_recommendation=(
                    blind_recommendation if recommendation_changed else None
                ),
                original_recommendation=original_rec,
                differences=differences,
                summary=summary,
            )

            # ── Audit entry ───────────────────────────────────────────────────
            audit_entry = self.log_action(
                state,
                action="fairness_check",
                inputs={
                    "original_recommendation": original_rec,
                    "original_score": round(
                        state.ai_recommendation.score_breakdown.overall_risk_score, 2
                    ),
                    "pii_fields_removed": [
                        "name", "email", "phone", "gender",
                        "address", "date_of_birth", "pan_number", "aadhaar_number",
                    ],
                },
                outputs={
                    "fairness_status": status,
                    "blind_recommendation": blind_recommendation,
                    "recommendation_changed": recommendation_changed,
                    "llm_summary": summary,
                },
                reasoning=summary,
            )

            self.logger.info(
                "Fairness check completed: %s (changed=%s)",
                status,
                recommendation_changed,
                extra={
                    "application_id": state.application_id,
                    "status": status,
                    "recommendation_changed": recommendation_changed,
                },
            )

            return {
                "fairness_check": fairness_check,
                "audit_trail": [audit_entry],
            }

        except Exception as exc:
            self.logger.error(
                "Error in fairness agent: %s",
                str(exc),
                extra={"application_id": state.application_id},
                exc_info=True,
            )
            return {
                "error_message": f"Fairness check failed: {str(exc)}",
                "error_at_stage": "FairnessAgent",
            }

    # ──────────────────────────────────────────────────────────────────────────
    # LLM — fairness summary
    # ──────────────────────────────────────────────────────────────────────────

    async def _generate_fairness_summary(
        self,
        status: str,
        original_rec: str,
        blind_rec: str,
        recommendation_changed: bool,
        original_score: float | None,
    ) -> str:
        """Generate a plain-language fairness audit summary via OpenRouter."""
        user_prompt = (
            f"Fairness check outcome: {status}\n"
            f"Original recommendation: {original_rec}\n"
            f"Identity-blind recommendation: {blind_rec}\n"
            f"Recommendation changed: {recommendation_changed}\n"
            f"Overall risk score: {original_score:.1f}/100 (if available)\n"
            f"PII removed for blind test: name, gender, phone, email, address, "
            "date of birth, PAN number, Aadhaar number.\n\n"
            "Write the fairness audit summary."
        )

        try:
            summary = await openrouter_client.chat(
                user=user_prompt,
                system=_FAIRNESS_SYSTEM,
                temperature=0.2,
                max_tokens=400,
            )
            return summary.strip()
        except Exception as exc:
            self.logger.warning(
                "OpenRouter unavailable for fairness summary — using fallback. Reason: %s",
                str(exc),
            )
            if recommendation_changed:
                return (
                    f"ALERT: Fairness check FAILED. Recommendation would change from "
                    f"{original_rec} to {blind_rec} without identity information. "
                    "This indicates potential bias in the scoring or data. "
                    "Manual review is required."
                )
            return (
                f"Fairness check PASSED. Recommendation remains {original_rec} "
                "even with all identity attributes (name, gender, address, PAN, "
                "Aadhaar) removed. No identity-based bias detected."
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Identity-blind state creation
    # ──────────────────────────────────────────────────────────────────────────

    def _create_identity_blind_state(self, state: WorkflowState) -> WorkflowState:
        """Create deep copy of state with all PII removed from OCR data."""
        blind_state = deepcopy(state)

        _PII_FIELDS = [
            "name", "email", "phone", "gender", "address",
            "date_of_birth", "pan_number", "aadhaar_number",
            "employee_name", "account_holder",
        ]

        for result in blind_state.ocr_results:
            for field in _PII_FIELDS:
                result.structured_data.pop(field, None)
            result.structured_data["_identity_blind"] = True

        return blind_state

    # ──────────────────────────────────────────────────────────────────────────
    # Blind re-scoring
    # ──────────────────────────────────────────────────────────────────────────

    async def _rescore_blind_application(
        self,
        original_state: WorkflowState,
        blind_state: WorkflowState,
    ) -> str:
        """Re-score without identity information and return the recommendation."""
        from app.agents.policy_engine_agent import PolicyEngineAgent
        from app.agents.decision_agent import DecisionAgent

        policy_agent = PolicyEngineAgent()
        policy_result = await policy_agent.process(blind_state)

        if "error_message" in policy_result:
            self.logger.warning(
                "Fairness check: Policy scoring failed on blind data — using original"
            )
            return original_state.ai_recommendation.recommendation

        blind_state.score_breakdown = policy_result.get(
            "score_breakdown", blind_state.score_breakdown
        )

        decision_agent = DecisionAgent()
        decision_result = await decision_agent.process(blind_state)

        if "error_message" in decision_result:
            self.logger.warning(
                "Fairness check: Decision generation failed on blind data — using original"
            )
            return original_state.ai_recommendation.recommendation

        blind_rec = decision_result.get("ai_recommendation")
        if blind_rec:
            return blind_rec.recommendation

        return original_state.ai_recommendation.recommendation
