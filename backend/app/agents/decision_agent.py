"""
Decision Agent — Requirement 3: Recommendation Agent

The AI ONLY recommends — it NEVER makes final decisions.

Possible recommendations: APPROVE | REFER | DECLINE

Every recommendation includes:
  • Overall score
  • Triggered policy clauses (Clause 3.1–3.4)
  • Per-clause detailed explanation (LLM-generated)
  • Human-readable summary (LLM-generated)

The APPROVE / REFER / DECLINE logic is fully deterministic; the LLM is used
to generate the natural-language explanation and per-clause rationale only.
No unexplained recommendations are returned.
"""

from __future__ import annotations

from typing import Dict, Any, List, Tuple

from app.agents.base import BaseAgent
from app.agents import WorkflowState, Recommendation, ScoreBreakdown, PolicyCriterion
from app.core.openrouter_client import openrouter_client
from app.core.prompt_injection_protection import PromptInjectionProtector
from app.models.policy_rule import PolicyRule
from app.database import SessionLocal

_protector = PromptInjectionProtector()

_RECOMMENDATION_SYSTEM = (
    "You are a senior credit underwriter at a financial institution. "
    "An AI system has scored a loan application using four policy criteria. "
    "Your job is to write a detailed, professional recommendation report that:\n"
    "1. States the AI recommendation clearly (APPROVE / REFER / DECLINE).\n"
    "2. Explains EVERY policy clause with its score and whether it passed or failed.\n"
    "3. Provides a plain-language rationale for each clause outcome.\n"
    "4. Ends with a clear statement that this is an AI recommendation only and that "
    "a licensed human underwriter must make the final decision.\n\n"
    "Rules:\n"
    "- Be factual and cite the specific scores from the data provided.\n"
    "- Do NOT ignore any clause — explain each one.\n"
    "- Use professional financial language.\n"
    "- Do NOT mention any PII (names, addresses, etc.).\n"
    "- Maximum 500 words."
)


class DecisionAgent(BaseAgent):
    """
    Generates AI recommendations (APPROVE / REFER / DECLINE) — never final decisions.
    Every recommendation cites specific policy clauses and includes LLM-generated
    explanations for each criterion.
    """

    def __init__(self):
        super().__init__("DecisionAgent")

    # ──────────────────────────────────────────────────────────────────────────
    # Main process
    # ──────────────────────────────────────────────────────────────────────────

    async def process(self, state: WorkflowState) -> Dict[str, Any]:
        """Generate clause-referenced recommendation with LLM-generated explanation."""
        try:
            self.logger.info(
                "Starting recommendation generation",
                extra={"application_id": state.application_id},
            )

            if not state.score_breakdown:
                return {
                    "error_message": "No score breakdown available for recommendation",
                    "error_at_stage": "DecisionAgent",
                }

            db = SessionLocal()
            try:
                policy_rules = db.query(PolicyRule).filter(
                    PolicyRule.is_active == True  # noqa: E712
                ).all()

                policy_dict = {rule.rule_key: rule for rule in policy_rules}

                # ── Core recommendation logic (deterministic) ─────────────────
                recommendation, confidence, triggered_clauses = self._evaluate(
                    state.score_breakdown, policy_dict
                )

                # ── Per-clause explanations (deterministic base) ───────────────
                clause_explanations = self._build_clause_explanations(
                    state.score_breakdown
                )

                # ── LLM-generated full explanation ────────────────────────────
                explanation = await self._generate_llm_explanation(
                    recommendation,
                    confidence,
                    state.score_breakdown,
                    clause_explanations,
                    triggered_clauses,
                )

                reason = self._short_reason(recommendation, triggered_clauses)

                recommendation_obj = Recommendation(
                    recommendation=recommendation,
                    confidence=confidence,
                    reason=reason,
                    score_breakdown=state.score_breakdown,
                    policy_citations=triggered_clauses,
                    explanation=explanation,
                )

                # ── Persist recommendation to DB ──────────────────────────────
                self._persist_recommendation(
                    db,
                    state.application_id,
                    recommendation_obj,
                    clause_explanations,
                )

                # Create audit entry
                audit_entry = self.log_action(
                    state,
                    action="decision_recommendation",
                    inputs={
                        "overall_score": round(state.score_breakdown.overall_risk_score, 2),
                        "total_weighted": round(
                            state.score_breakdown.total_weighted_score, 2
                        ) if state.score_breakdown.total_weighted_score else None,
                    },
                    outputs={
                        "recommendation": recommendation,
                        "confidence": round(confidence, 2),
                        "triggered_clauses": triggered_clauses,
                        "reason": reason,
                    },
                    reasoning=explanation,
                )

                self.logger.info(
                    "Recommendation: %s (confidence %.0f%%)",
                    recommendation,
                    confidence * 100,
                    extra={
                        "application_id": state.application_id,
                        "recommendation": recommendation,
                    },
                )

                return {
                    "ai_recommendation": recommendation_obj,
                    "audit_trail": [audit_entry],
                }

            finally:
                db.close()

        except Exception as exc:
            self.logger.error(
                "Error in decision agent: %s",
                str(exc),
                extra={"application_id": state.application_id},
                exc_info=True,
            )
            return {
                "error_message": f"Recommendation generation failed: {str(exc)}",
                "error_at_stage": "DecisionAgent",
            }

    # ──────────────────────────────────────────────────────────────────────────
    # LLM — recommendation explanation
    # ──────────────────────────────────────────────────────────────────────────

    async def _generate_llm_explanation(
        self,
        recommendation: str,
        confidence: float,
        scores: ScoreBreakdown,
        clause_explanations: List[Dict],
        triggered_clauses: List[str],
    ) -> str:
        """Use the LLM to generate a detailed recommendation explanation."""
        total = scores.total_weighted_score if scores.total_weighted_score else scores.overall_risk_score
        max_total = scores.max_total_weighted_score if scores.max_total_weighted_score else 100

        clause_text = "\n".join(
            f"  {ce['clause']} — {ce['criterion']}: "
            f"score {ce['score']}, weighted {ce['weighted_score']}, "
            f"result {ce['pass_fail']}"
            for ce in clause_explanations
        )

        user_prompt = (
            f"AI Recommendation: {recommendation}\n"
            f"Confidence: {confidence:.0%}\n"
            f"Overall score: {total:.1f} / {max_total:.0f}\n"
            f"Triggered clauses: {', '.join(triggered_clauses)}\n\n"
            f"Clause breakdown:\n{clause_text}\n\n"
            "Write the full recommendation report."
        )

        try:
            explanation = await openrouter_client.chat(
                user=user_prompt,
                system=_RECOMMENDATION_SYSTEM,
                temperature=0.2,
                max_tokens=700,
            )
            return explanation.strip()
        except Exception as exc:
            self.logger.warning(
                "OpenRouter unavailable for recommendation explanation — using fallback. Reason: %s",
                str(exc),
            )
            return self._format_fallback_explanation(
                recommendation, scores, clause_explanations, triggered_clauses
            )

    def _format_fallback_explanation(
        self,
        recommendation: str,
        scores: ScoreBreakdown,
        clause_explanations: List[Dict],
        triggered_clauses: List[str],
    ) -> str:
        """Deterministic fallback explanation when OpenRouter is unavailable."""
        total = scores.total_weighted_score if scores.total_weighted_score else scores.overall_risk_score
        max_total = scores.max_total_weighted_score if scores.max_total_weighted_score else 100

        lines = [
            "=" * 60,
            "RECOMMENDATION REPORT",
            "=" * 60,
            "",
            f"Recommendation:  {recommendation}",
            f"Overall Score:   {total:.1f} / {max_total:.0f}",
            "",
            "POLICY CLAUSE ANALYSIS:",
            "-" * 40,
        ]

        for ce in clause_explanations:
            lines += [
                "",
                f"{ce['clause']} — {ce['criterion']}",
                f"  Score:          {ce['score']}",
                f"  Weighted Score: {ce['weighted_score']}",
                f"  Result:         {ce['pass_fail']}",
                f"  Rationale:      {ce['rationale']}",
            ]

        lines += [
            "",
            "-" * 40,
            f"Triggered Clauses: {', '.join(triggered_clauses) if triggered_clauses else 'None'}",
            "",
            "IMPORTANT: This is an AI recommendation only.",
            "Final approval or decline must be made by a",
            "licensed human underwriter.",
            "=" * 60,
        ]

        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────────────────
    # Recommendation logic (deterministic — NOT LLM)
    # ──────────────────────────────────────────────────────────────────────────

    def _evaluate(
        self,
        scores: ScoreBreakdown,
        policy_dict: Dict[str, Any],
    ) -> Tuple[str, float, List[str]]:
        """
        Determine APPROVE / REFER / DECLINE based on:
        1. Failed policy clauses (hard failures → DECLINE)
        2. Borderline score range (65–75 → REFER)
        3. All clauses pass and score ≥ 75 → APPROVE
        """
        triggered = []
        failed_clauses = []

        for criterion in scores.criteria:
            if criterion.pass_fail == "FAIL":
                failed_clauses.append(criterion.clause)
                triggered.append(criterion.clause)

        overall = scores.overall_risk_score  # 0-100

        critical_fail = (
            "Clause 3.1" in failed_clauses or "Clause 3.2" in failed_clauses
        )

        if critical_fail and overall < 50:
            recommendation = "DECLINE"
            confidence = 0.92
            for c in scores.criteria:
                if c.clause not in triggered:
                    triggered.append(c.clause)

        elif overall >= 75 and not failed_clauses:
            recommendation = "APPROVE"
            confidence = 0.90
            for c in scores.criteria:
                if c.clause not in triggered:
                    triggered.append(c.clause)

        else:
            recommendation = "REFER"
            confidence = 0.78
            if not triggered:
                triggered = [c.clause for c in scores.criteria]

        return recommendation, confidence, triggered

    # ──────────────────────────────────────────────────────────────────────────
    # Clause explanation builders (deterministic base)
    # ──────────────────────────────────────────────────────────────────────────

    def _build_clause_explanations(
        self, scores: ScoreBreakdown
    ) -> List[Dict[str, str]]:
        explanations = []
        for c in scores.criteria:
            rationale = (
                self._pass_rationale(c) if c.pass_fail == "PASS"
                else self._fail_rationale(c)
            )
            explanations.append(
                {
                    "clause": c.clause,
                    "criterion": c.name,
                    "score": f"{c.score:.1f}/{c.max_score:.0f}",
                    "weighted_score": f"{c.weighted_score:.1f}/{c.max_weighted:.0f}",
                    "pass_fail": c.pass_fail,
                    "rationale": rationale,
                }
            )
        return explanations

    def _pass_rationale(self, c: PolicyCriterion) -> str:
        if "DTI" in c.name or "Debt" in c.name:
            return "DTI ratio is within acceptable policy limits."
        if "Credit" in c.name:
            return "Credit score meets or exceeds the minimum threshold."
        if "Income" in c.name:
            return "Income history shows consistent and stable deposits."
        if "Employment" in c.name:
            return "Applicant has sufficient employment tenure."
        return f"{c.name} meets policy requirements."

    def _fail_rationale(self, c: PolicyCriterion) -> str:
        if "DTI" in c.name or "Debt" in c.name:
            return (
                "DTI ratio exceeds the maximum permitted threshold. "
                "Monthly debt obligations are too high relative to income."
            )
        if "Credit" in c.name:
            return (
                "Credit score falls below the minimum required threshold. "
                "Credit history indicates elevated risk."
            )
        if "Income" in c.name:
            return (
                "Income shows significant variance across provided documents. "
                "Stable recurring income cannot be confirmed."
            )
        if "Employment" in c.name:
            return (
                "Employment tenure is below the minimum required period. "
                "Applicant may not have sufficient employment stability."
            )
        return f"{c.name} does not meet policy requirements."

    def _short_reason(
        self, recommendation: str, triggered_clauses: List[str]
    ) -> str:
        clause_list = ", ".join(triggered_clauses) if triggered_clauses else "N/A"
        if recommendation == "APPROVE":
            return f"All policy criteria satisfied. Clauses: {clause_list}"
        elif recommendation == "DECLINE":
            return f"Critical policy violations detected. Clauses: {clause_list}"
        else:
            return f"Borderline case — requires human underwriter review. Clauses: {clause_list}"

    # ──────────────────────────────────────────────────────────────────────────
    # DB persistence
    # ──────────────────────────────────────────────────────────────────────────

    def _persist_recommendation(
        self,
        db,
        application_id: int,
        rec: Recommendation,
        clause_explanations: List[Dict],
    ):
        """Persist or update recommendation in the DB."""
        from app.models.recommendation import Recommendation as DBRec

        reasons_json = [
            {
                "clause": ce["clause"],
                "criterion": ce["criterion"],
                "pass_fail": ce["pass_fail"],
                "rationale": ce["rationale"],
            }
            for ce in clause_explanations
        ]

        existing = db.query(DBRec).filter(
            DBRec.application_id == application_id
        ).first()

        if existing:
            existing.recommendation = rec.recommendation
            existing.confidence_score = rec.confidence
            existing.explanation = rec.explanation
            existing.policy_citations = rec.policy_citations
            existing.reasons_json = reasons_json
        else:
            db_rec = DBRec(
                application_id=application_id,
                recommendation=rec.recommendation,
                confidence_score=rec.confidence,
                explanation=rec.explanation,
                policy_citations=rec.policy_citations,
                reasons_json=reasons_json,
            )
            db.add(db_rec)

        db.flush()
        db.commit()
