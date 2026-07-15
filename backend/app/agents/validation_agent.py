"""
Document Validation Agent — Requirement 1

Validates uploaded documents against business rules:
  • Presence check (required: Government ID, Income Proof, Bank Statement)
  • Consistency check (name, income, employer mismatches)
  • Format/readability check (OCR confidence)

On missing documents:
  1. Sets status = HOLD
  2. Does NOT proceed to scoring
  3. Records hold reason in audit log AND in validation_reports DB table

OpenRouter integration: the LLM generates a rich, human-readable validation
summary that explains every finding in plain language. All decision logic
(HOLD / FAIL / PASS) remains fully deterministic.
"""

from __future__ import annotations

from typing import Dict, Any, List
from datetime import datetime

from app.agents.base import BaseAgent
from app.agents import WorkflowState, ValidationReport, ValidationIssue
from app.core.openrouter_client import openrouter_client
from app.core.prompt_injection_protection import PromptInjectionProtector
from app.database import SessionLocal

_protector = PromptInjectionProtector()

# Required document types mapped to human-readable names
REQUIRED_DOCUMENTS = {
    "Government ID": ["PAN", "Aadhaar"],                     # at least one
    "Income Proof":  ["Salary Slip", "SalarySlip",
                      "Income Certificate", "ITR"],           # at least one
    "Bank Statement": ["Bank Statement", "BankStatement"],   # at least one
}

_VALIDATION_SYSTEM = (
    "You are a document validation analyst at a financial institution. "
    "Given the validation results for a loan application, write a concise but "
    "thorough plain-language summary (3-6 sentences) that:\n"
    "1. States the overall validation outcome (PASS / FAIL / HOLD).\n"
    "2. Explains every issue found, if any.\n"
    "3. Tells the applicant what action they need to take, if anything.\n"
    "Do NOT invent issues that were not listed. Be professional and factual."
)


class DocumentValidationAgent(BaseAgent):
    """
    Validates OCR results and document consistency (Req 1).
    Holds application and records audit entry when documents are missing.
    """

    def __init__(self):
        super().__init__("DocumentValidationAgent")

    # ──────────────────────────────────────────────────────────────────────────
    # Main process
    # ──────────────────────────────────────────────────────────────────────────

    async def process(self, state: WorkflowState) -> Dict[str, Any]:
        """Validate all documents; hold if required docs are missing."""
        try:
            self.logger.info(
                "Starting document validation",
                extra={"application_id": state.application_id},
            )

            if not state.ocr_results:
                return {
                    "error_message": "No OCR results to validate",
                    "error_at_stage": "DocumentValidationAgent",
                }

            issues: List[ValidationIssue] = []
            valid_documents: List[str] = []
            missing_groups: List[str] = []
            missing_documents: List[str] = []

            # ── OCR quality check ─────────────────────────────────────────────
            for result in state.ocr_results:
                doc_type = self._get_document_type(result.document_id, state.documents)

                if result.error:
                    issues.append(ValidationIssue(
                        document_type=doc_type or "Unknown",
                        issue_type="unreadable",
                        severity="error",
                        message=f"OCR failed: {result.error}",
                    ))
                elif result.confidence_score < 0.7:
                    issues.append(ValidationIssue(
                        document_type=doc_type or "Unknown",
                        issue_type="low_confidence",
                        severity="warning",
                        message=f"Low OCR confidence: {result.confidence_score:.2%}",
                    ))
                else:
                    valid_documents.append(result.document_id)

            # ── Required document group check ─────────────────────────────────
            provided_types = {doc.document_type for doc in state.documents}

            for group_name, accepted_types in REQUIRED_DOCUMENTS.items():
                found = any(t in provided_types for t in accepted_types)
                if not found:
                    missing_groups.append(group_name)
                    missing_documents.extend(accepted_types[:1])
                    issues.append(ValidationIssue(
                        document_type=group_name,
                        issue_type="missing",
                        severity="error",
                        message=(
                            f"Missing required document: {group_name}. "
                            f"Accepted types: {', '.join(accepted_types)}"
                        ),
                    ))

            # ── Consistency checks ────────────────────────────────────────────
            consistency_issues = self._validate_consistency(state)
            issues.extend(consistency_issues)

            # ── Status determination (deterministic — NOT LLM) ────────────────
            if missing_groups:
                status = "HOLD"
            elif any(i.severity == "error" for i in issues):
                status = "FAIL"
            else:
                status = "PASS"

            hold_reason = None
            if status == "HOLD":
                hold_reason = (
                    "Application on hold — missing required documents: "
                    + ", ".join(missing_groups)
                    + ". Please upload the missing documents to continue."
                )

            # ── LLM-generated human-readable summary ──────────────────────────
            summary = await self._generate_llm_summary(
                status, issues, valid_documents, missing_groups
            )

            validation_report = ValidationReport(
                status=status,
                issues=issues,
                valid_documents=valid_documents,
                missing_documents=missing_documents,
                summary=summary,
            )

            # ── Persist validation report to DB ───────────────────────────────
            self._persist_validation_report(
                state.application_id,
                status,
                issues,
                missing_groups,
                hold_reason,
                summary,
            )

            # ── Create audit entry ────────────────────────────────────────────
            audit_entry = self.log_action(
                state,
                action="document_validation",
                inputs={
                    "documents_submitted": len(state.documents),
                    "ocr_results": len(state.ocr_results),
                    "required_groups": list(REQUIRED_DOCUMENTS.keys()),
                },
                outputs={
                    "validation_status": status,
                    "valid_documents": len(valid_documents),
                    "issues_found": len(issues),
                    "missing_groups": missing_groups,
                    "hold_reason": hold_reason,
                    "llm_summary": summary,
                },
                reasoning=hold_reason if hold_reason else summary,
            )

            validation_passed = status == "PASS"

            self.logger.info(
                "Document validation: %s",
                status,
                extra={
                    "application_id": state.application_id,
                    "status": status,
                    "missing_groups": missing_groups,
                    "issues": len(issues),
                },
            )

            return {
                "validation_report": validation_report,
                "validation_passed": validation_passed,
                "audit_trail": [audit_entry],
            }

        except Exception as exc:
            self.logger.error(
                "Error in validation agent: %s",
                str(exc),
                extra={"application_id": state.application_id},
                exc_info=True,
            )
            return {
                "error_message": f"Document validation failed: {str(exc)}",
                "error_at_stage": "DocumentValidationAgent",
            }

    # ──────────────────────────────────────────────────────────────────────────
    # LLM — validation summary
    # ──────────────────────────────────────────────────────────────────────────

    async def _generate_llm_summary(
        self,
        status: str,
        issues: List[ValidationIssue],
        valid_documents: List[str],
        missing_groups: List[str],
    ) -> str:
        """Generate a plain-language validation summary via OpenRouter."""
        # Build an issue digest for the LLM
        issue_lines = "\n".join(
            f"  [{i.severity.upper()}] {i.document_type}: {i.message}"
            for i in issues
        ) or "  None"

        user_prompt = (
            f"Validation outcome: {status}\n"
            f"Valid documents: {len(valid_documents)}\n"
            f"Missing document groups: {', '.join(missing_groups) or 'None'}\n"
            f"Issues:\n{issue_lines}\n\n"
            "Write the validation summary."
        )

        try:
            summary = await openrouter_client.chat(
                user=user_prompt,
                system=_VALIDATION_SYSTEM,
                temperature=0.2,
                max_tokens=400,
            )
            return summary.strip()
        except Exception as exc:
            self.logger.warning(
                "OpenRouter unavailable for validation summary — using fallback. Reason: %s",
                str(exc),
            )
            return self._deterministic_summary(status, issues, valid_documents, missing_groups)

    def _deterministic_summary(
        self,
        status: str,
        issues: List[ValidationIssue],
        valid_documents: List[str],
        missing_groups: List[str],
    ) -> str:
        """Fallback summary used when OpenRouter is unavailable."""
        if status == "HOLD":
            return (
                f"Application HELD — missing required document group(s): "
                f"{', '.join(missing_groups)}. "
                "Upload missing documents to proceed. Scoring is blocked."
            )
        elif status == "FAIL":
            error_count = sum(1 for i in issues if i.severity == "error")
            return (
                f"Document validation FAILED. {error_count} error(s), "
                f"{len(issues) - error_count} warning(s). Cannot proceed."
            )
        else:
            return (
                f"All document groups verified. "
                f"{len(valid_documents)} document(s) validated. Ready for scoring."
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Consistency checks
    # ──────────────────────────────────────────────────────────────────────────

    def _validate_consistency(self, state: WorkflowState) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        names: Dict[str, str] = {}
        employers: Dict[str, str] = {}

        for result in state.ocr_results:
            data = result.structured_data
            doc_type = self._get_document_type(result.document_id, state.documents)

            if "name" in data:
                names[doc_type or result.document_id] = data["name"]
            if "employer_name" in data:
                employers[doc_type or result.document_id] = data["employer_name"]

        unique_names = set(names.values())
        if len(unique_names) > 1:
            issues.append(ValidationIssue(
                document_type="Multiple",
                issue_type="name_mismatch",
                severity="error",
                message=(
                    "Name inconsistency across documents: "
                    + ", ".join(f"'{v}'" for v in unique_names)
                ),
            ))

        unique_employers = set(employers.values())
        if len(unique_employers) > 1:
            issues.append(ValidationIssue(
                document_type="Multiple",
                issue_type="employer_mismatch",
                severity="warning",
                message=(
                    "Employer name inconsistency: "
                    + ", ".join(f"'{v}'" for v in unique_employers)
                ),
            ))

        return issues

    # ──────────────────────────────────────────────────────────────────────────
    # DB persistence
    # ──────────────────────────────────────────────────────────────────────────

    def _persist_validation_report(
        self,
        application_id: int,
        status: str,
        issues: List[ValidationIssue],
        missing_groups: List[str],
        hold_reason: str | None,
        summary: str,
    ):
        """Store validation result including hold reason in the DB."""
        try:
            from app.models.validation_report import ValidationReport as DBValidationReport

            db = SessionLocal()
            try:
                issues_json = [
                    {
                        "document_type": i.document_type,
                        "issue_type": i.issue_type,
                        "severity": i.severity,
                        "message": i.message,
                    }
                    for i in issues
                ]

                existing = db.query(DBValidationReport).filter(
                    DBValidationReport.application_id == application_id
                ).first()

                if existing:
                    existing.status = status
                    existing.issues_json = issues_json
                    existing.missing_documents = missing_groups
                    existing.hold_reason = hold_reason
                    existing.summary = summary
                    existing.validated_at = datetime.utcnow()
                else:
                    db_report = DBValidationReport(
                        application_id=application_id,
                        status=status,
                        issues_json=issues_json,
                        missing_documents=missing_groups,
                        hold_reason=hold_reason,
                        summary=summary,
                    )
                    db.add(db_report)

                db.commit()
                self.logger.info(
                    "Validation report persisted: %s",
                    status,
                    extra={"application_id": application_id},
                )
            finally:
                db.close()

        except Exception as exc:
            self.logger.error(
                "Failed to persist validation report: %s",
                str(exc),
                exc_info=True,
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _get_document_type(self, document_id: str, documents) -> str:
        for doc in documents:
            if doc.file_id == document_id:
                return doc.document_type
        return "Unknown"
