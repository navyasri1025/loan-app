"""
Intake Agent

Receives application, verifies required fields, determines required documents,
and prepares workflow state.

OpenRouter integration: generates a natural-language intake summary and
identifies any data-quality concerns via the LLM.
"""

from typing import Dict, Any
from app.agents.base import BaseAgent
from app.agents import WorkflowState, DocumentInfo
from app.models.application import Application
from app.models.applicant import Applicant
from app.database import SessionLocal
from app.core.openrouter_client import openrouter_client
from app.core.prompt_injection_protection import PromptInjectionProtector
from datetime import datetime


# Prompt injection protector — used to sanitise user-supplied text before LLM call
_protector = PromptInjectionProtector()


class IntakeAgent(BaseAgent):
    """Processes incoming applications and verifies readiness"""

    def __init__(self):
        super().__init__("IntakeAgent")

    async def process(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Verify application structure, then use the LLM to generate an
        intake readiness summary and data-quality commentary.
        """
        try:
            self.logger.info(
                "Processing intake for application %s",
                state.application_id,
                extra={"application_id": state.application_id},
            )

            db = SessionLocal()
            try:
                application = db.query(Application).filter(
                    Application.id == state.application_id
                ).first()

                applicant = db.query(Applicant).filter(
                    Applicant.id == state.applicant_id
                ).first()

                if not application:
                    raise ValueError(f"Application {state.application_id} not found")
                if not applicant:
                    raise ValueError(f"Applicant {state.applicant_id} not found")

                # ── Deterministic field verification ──────────────────────────
                required_fields = self._verify_required_fields(applicant, application)
                if not required_fields["all_present"]:
                    return {
                        "error_message": (
                            f"Missing required fields: "
                            f"{', '.join(required_fields['missing'])}"
                        ),
                        "error_at_stage": "IntakeAgent",
                    }

                # ── Required document list ────────────────────────────────────
                required_documents = self._determine_required_documents(applicant)

                # ── LLM intake summary ────────────────────────────────────────
                llm_reasoning = await self._generate_intake_summary(
                    applicant, application, required_fields
                )

                # ── Audit entry ───────────────────────────────────────────────
                audit_entry = self.log_action(
                    state,
                    action="intake_verification",
                    inputs={
                        "application_id": state.application_id,
                        "applicant_id": state.applicant_id,
                        "loan_amount": float(application.loan_amount or 0),
                        "loan_purpose": application.loan_purpose,
                        "term_months": application.term_months,
                    },
                    outputs={
                        "required_documents": required_documents,
                        "fields_verified": True,
                        "status": "READY_FOR_OCR",
                        "llm_summary": llm_reasoning,
                    },
                    reasoning=llm_reasoning,
                )

                self.logger.info(
                    "Intake verification passed. Required documents: %s",
                    list(required_documents.keys()),
                    extra={"application_id": state.application_id},
                )

                return {
                    "audit_trail": [audit_entry],
                    "final_status": "IN_REVIEW",
                }

            finally:
                db.close()

        except Exception as exc:
            self.logger.error(
                "Error in intake agent: %s",
                str(exc),
                extra={"application_id": state.application_id},
                exc_info=True,
            )
            return {
                "error_message": f"Intake verification failed: {str(exc)}",
                "error_at_stage": "IntakeAgent",
            }

    # ──────────────────────────────────────────────────────────────────────────
    # LLM — intake summary
    # ──────────────────────────────────────────────────────────────────────────

    async def _generate_intake_summary(
        self,
        applicant: Applicant,
        application: Application,
        field_check: Dict[str, Any],
    ) -> str:
        """
        Ask the LLM to produce a concise intake-readiness summary.
        Falls back to a deterministic summary if OpenRouter is not configured.
        """
        # Build sanitised context for the LLM
        context = (
            f"Loan application intake:\n"
            f"  Loan amount:    ₹{application.loan_amount or 'N/A'}\n"
            f"  Loan purpose:   {_protector.sanitize_input(str(application.loan_purpose or 'N/A'))}\n"
            f"  Term (months):  {application.term_months or 'N/A'}\n"
            f"  Monthly debt:   ₹{application.monthly_debt_obligations or 0}\n"
            f"  Employment:     {applicant.employment_stability_months or 'N/A'} months\n"
            f"  Monthly income: ₹{applicant.monthly_income or 'N/A'}\n"
            f"  Credit score:   {applicant.credit_score or 'N/A'}\n"
            f"  Fields OK:      {field_check['all_present']}\n"
        )

        system_prompt = (
            "You are an intake analyst at a financial institution. "
            "Your role is to review incoming loan application data and provide "
            "a concise, professional intake readiness summary (2-4 sentences). "
            "Focus on data completeness and any initial observations about the "
            "application. Do NOT make a credit decision."
        )

        try:
            summary = await openrouter_client.chat(
                user=context,
                system=system_prompt,
                temperature=0.2,
                max_tokens=300,
            )
            return summary.strip()
        except Exception as exc:
            self.logger.warning(
                "OpenRouter unavailable for intake summary — using fallback. Reason: %s",
                str(exc),
            )
            return (
                "Intake verification completed. All required fields are present. "
                f"Application for ₹{application.loan_amount} over "
                f"{application.term_months} months received and ready for OCR processing."
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Deterministic helpers (unchanged business logic)
    # ──────────────────────────────────────────────────────────────────────────

    def _verify_required_fields(
        self, applicant: Applicant, application: Application
    ) -> Dict[str, Any]:
        """Verify all required fields are present"""
        required = {
            "applicant_name": applicant.user.full_name if applicant.user else None,
            "loan_amount": application.loan_amount,
            "loan_purpose": application.loan_purpose,
            "term_months": application.term_months,
        }

        missing = [k for k, v in required.items() if not v]

        return {
            "all_present": len(missing) == 0,
            "missing": missing,
            "fields": required,
        }

    def _determine_required_documents(self, applicant: Applicant) -> Dict[str, str]:
        """Determine which documents are required based on applicant profile"""
        return {
            "pan": "PAN card (Identity & Tax ID)",
            "aadhaar": "Aadhaar number (Government ID)",
            "salary_slip": "Recent salary slips (3 months)",
            "employment_letter": "Employment letter from employer",
            "bank_statement": "Bank statements (6 months)",
        }
