"""
LangGraph Workflow State Management

Defines the state objects passed between agents in the workflow.
"""

from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime
from pydantic import BaseModel, Field
from operator import add


class DocumentInfo(BaseModel):
    """Information about uploaded documents"""
    file_id: str
    file_name: str
    document_type: str  # PAN, Aadhaar, Salary Slip, Employment Letter, Bank Statement
    upload_time: datetime
    extracted_text: Optional[str] = None
    confidence_score: Optional[float] = None


class OCRResult(BaseModel):
    """Result from OCR agent"""
    document_id: str
    raw_text: str
    structured_data: Dict[str, Any]
    confidence_score: float
    error: Optional[str] = None


class ValidationIssue(BaseModel):
    """Individual validation issue"""
    document_type: str
    issue_type: str  # missing, unreadable, expired, name_mismatch, etc
    severity: str  # error, warning
    message: str


class ValidationReport(BaseModel):
    """Report from document validation agent"""
    status: str  # PASS, FAIL, HOLD
    issues: List[ValidationIssue] = []
    valid_documents: List[str] = []
    missing_documents: List[str] = []
    summary: str


class PolicyCriterion(BaseModel):
    """A single scored policy criterion with clause reference (Req 2)"""
    name: str                  # e.g. "Debt-to-Income Ratio"
    clause: str                # e.g. "Clause 3.1"
    score: float               # Raw score
    max_score: float           # Maximum possible score for this criterion
    weight: float              # Weight as a fraction, e.g. 0.40
    weighted_score: float      # score * weight
    max_weighted: float        # max_score * weight
    pass_fail: str             # "PASS" or "FAIL"
    threshold_description: str # Human-readable threshold description


class ScoreBreakdown(BaseModel):
    """Score breakdown for policy scoring — Req 2: transparent, weighted, clause-referenced"""
    dti_score: float
    income_stability_score: float
    employment_stability_score: float
    documentation_quality_score: float
    credit_score: float
    overall_risk_score: float
    policy_thresholds: Dict[str, float] = {}

    # Req 2 additions: per-criterion breakdown with clauses and weights
    criteria: List[PolicyCriterion] = []
    total_weighted_score: float = 0.0
    max_total_weighted_score: float = 100.0


class Recommendation(BaseModel):
    """Decision agent recommendation"""
    recommendation: str  # APPROVE, REFER, DECLINE
    confidence: float
    reason: str
    score_breakdown: ScoreBreakdown
    policy_citations: List[str] = []
    explanation: str


class FairnessCheckResult(BaseModel):
    """Fairness agent result"""
    status: str  # PASS, FAIRNESS_FAILURE
    identity_blind_recommendation: Optional[str] = None
    original_recommendation: str
    differences: List[str] = []
    summary: str


class AuditEntry(BaseModel):
    """Single audit log entry"""
    timestamp: datetime
    agent: str
    action: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    tool_calls: List[Dict[str, Any]] = []
    reasoning: Optional[str] = None


class WorkflowState(BaseModel):
    """Complete state for LangGraph workflow"""
    application_id: int
    applicant_id: int
    user_id: int
    
    # Uploaded documents
    documents: List[DocumentInfo] = []
    
    # OCR Results
    ocr_results: List[OCRResult] = []
    
    # Validation
    validation_report: Optional[ValidationReport] = None
    validation_passed: bool = False
    
    # Scoring & Policy
    policy_version: str = "1.0"
    score_breakdown: Optional[ScoreBreakdown] = None
    
    # AI Recommendation
    ai_recommendation: Optional[Recommendation] = None
    
    # Fairness Check
    fairness_check: Optional[FairnessCheckResult] = None
    
    # Human Review (Req 4: APPROVE, REFER, DECLINE)
    human_decision: Optional[str] = None  # APPROVE, REFER, DECLINE
    human_comment: Optional[str] = None
    human_reviewer_id: Optional[int] = None
    human_review_timestamp: Optional[datetime] = None
    
    # Audit Trail
    audit_trail: Annotated[List[AuditEntry], add] = []
    
    # Final Status
    final_status: str = "DRAFT"  # DRAFT, IN_REVIEW, APPROVED, DECLINED, PENDING_REVIEW
    completed_at: Optional[datetime] = None
    
    # Error Handling
    error_message: Optional[str] = None
    error_at_stage: Optional[str] = None


class InputPayload(BaseModel):
    """Input payload for workflow execution"""
    application_id: int
    applicant_id: int
    user_id: int
    documents: List[Dict[str, Any]]  # File info from database


class WorkflowOutput(BaseModel):
    """Output from completed workflow"""
    application_id: int
    final_status: str
    ai_recommendation: Optional[Recommendation] = None
    fairness_check: Optional[FairnessCheckResult] = None
    validation_report: Optional[ValidationReport] = None
    score_breakdown: Optional[ScoreBreakdown] = None
    audit_trail: List[AuditEntry] = []
    errors: List[str] = []
