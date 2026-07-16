"""
LangGraph Workflow Orchestration

Defines the complete workflow graph:
Upload → OCR → Validation → Policy Engine → Decision → Fairness → Governance → Human Approval → Final Status
"""

from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel

from app.agents import WorkflowState, InputPayload, WorkflowOutput
from app.agents.intake_agent import IntakeAgent
from app.agents.ocr_agent import OCRAgent
from app.agents.validation_agent import DocumentValidationAgent
from app.agents.policy_engine_agent import PolicyEngineAgent
from app.agents.decision_agent import DecisionAgent
from app.agents.fairness_agent import FairnessAgent
from app.agents.governance_agent import GovernanceAgent
from app.core.logging import get_logger

logger = get_logger("workflow")


class WorkflowOrchestrator:
    """Orchestrates the complete LangGraph workflow"""
    
    def __init__(self):
        self.intake_agent = IntakeAgent()
        self.ocr_agent = OCRAgent()
        self.validation_agent = DocumentValidationAgent()
        self.policy_agent = PolicyEngineAgent()
        self.decision_agent = DecisionAgent()
        self.fairness_agent = FairnessAgent()
        self.governance_agent = GovernanceAgent()
        
        self.graph = self._build_workflow_graph()
    
    def _build_workflow_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("intake", self._node_intake)
        workflow.add_node("ocr", self._node_ocr)
        workflow.add_node("validation", self._node_validation)
        workflow.add_node("policy", self._node_policy)
        workflow.add_node("decision", self._node_decision)
        workflow.add_node("fairness", self._node_fairness)
        workflow.add_node("governance", self._node_governance)
        workflow.add_node("waiting_human", self._node_waiting_human)
        # Error terminal node — all conditional "error" edges land here
        workflow.add_node("error", self._node_error)
        
        # Add edges
        workflow.add_edge(START, "intake")
        workflow.add_conditional_edges("intake", self._check_intake_success)
        
        workflow.add_conditional_edges("ocr", self._check_ocr_success)
        
        workflow.add_conditional_edges("validation", self._check_validation_success)
        
        workflow.add_conditional_edges("policy", self._check_policy_success)
        
        workflow.add_conditional_edges("decision", self._check_decision_success)
        
        workflow.add_conditional_edges("fairness", self._check_fairness_success)
        
        workflow.add_edge("governance", "waiting_human")
        workflow.add_edge("waiting_human", END)
        workflow.add_edge("error", END)
        
        return workflow.compile()
    
    # Node implementations
    async def _node_intake(self, state: WorkflowState) -> Dict[str, Any]:
        """Intake node"""
        logger.info(f"Intake node for application {state.application_id}")
        return await self.intake_agent.process(state)
    
    async def _node_ocr(self, state: WorkflowState) -> Dict[str, Any]:
        """OCR node"""
        logger.info(f"OCR node for application {state.application_id}")
        return await self.ocr_agent.process(state)
    
    async def _node_validation(self, state: WorkflowState) -> Dict[str, Any]:
        """Validation node"""
        logger.info(f"Validation node for application {state.application_id}")
        return await self.validation_agent.process(state)
    
    async def _node_policy(self, state: WorkflowState) -> Dict[str, Any]:
        """Policy engine node"""
        logger.info(f"Policy engine node for application {state.application_id}")
        return await self.policy_agent.process(state)
    
    async def _node_decision(self, state: WorkflowState) -> Dict[str, Any]:
        """Decision node"""
        logger.info(f"Decision node for application {state.application_id}")
        return await self.decision_agent.process(state)
    
    async def _node_fairness(self, state: WorkflowState) -> Dict[str, Any]:
        """Fairness check node"""
        logger.info(f"Fairness check node for application {state.application_id}")
        return await self.fairness_agent.process(state)
    
    async def _node_governance(self, state: WorkflowState) -> Dict[str, Any]:
        """Governance audit node"""
        logger.info(f"Governance audit node for application {state.application_id}")
        state.completed_at = datetime.utcnow()
        return await self.governance_agent.process(state)
    
    async def _node_waiting_human(self, state: WorkflowState) -> Dict[str, Any]:
        """Waiting for human approval node"""
        logger.info(f"Workflow complete. Waiting for human underwriter for application {state.application_id}")
        return {
            "final_status": "PENDING_REVIEW"
        }

    async def _node_error(self, state: WorkflowState) -> Dict[str, Any]:
        """Terminal error node — workflow ends here when any agent sets error_message"""
        logger.error(
            f"Workflow terminated with error for application {state.application_id}: "
            f"{state.error_message} (stage: {state.error_at_stage})"
        )
        return {
            "final_status": "FAILED"
        }
    
    # Conditional edge checkers
    def _check_intake_success(self, state: WorkflowState) -> str:
        """Check if intake succeeded"""
        if state.error_message:
            return "error"
        return "ocr"
    
    def _check_ocr_success(self, state: WorkflowState) -> str:
        """Check if OCR succeeded"""
        if state.error_message:
            return "error"
        return "validation"
    
    def _check_validation_success(self, state: WorkflowState) -> str:
        """Check if validation succeeded"""
        if state.error_message:
            return "error"
        if not state.validation_passed:
            return "waiting_human"  # Hold pending validation
        return "policy"
    
    def _check_policy_success(self, state: WorkflowState) -> str:
        """Check if policy scoring succeeded"""
        if state.error_message:
            return "error"
        return "decision"
    
    def _check_decision_success(self, state: WorkflowState) -> str:
        """Check if decision succeeded"""
        if state.error_message:
            return "error"
        return "fairness"
    
    def _check_fairness_success(self, state: WorkflowState) -> str:
        """Check if fairness check succeeded"""
        if state.error_message:
            return "error"
        return "governance"
    
    async def execute_workflow(self, payload: InputPayload) -> WorkflowOutput:
        """Execute the complete workflow"""
        
        logger.info(
            f"Starting workflow for application {payload.application_id}",
            extra={"application_id": payload.application_id}
        )
        
        # Initialize state
        from app.agents import DocumentInfo
        
        documents = [
            DocumentInfo(
                file_id=doc.get("file_id", f"doc_{i}"),
                file_name=doc.get("file_name", f"document_{i}"),
                document_type=doc.get("document_type", "Unknown"),
                upload_time=datetime.utcnow()
            )
            for i, doc in enumerate(payload.documents)
        ]
        
        initial_state = WorkflowState(
            application_id=payload.application_id,
            applicant_id=payload.applicant_id,
            user_id=payload.user_id,
            documents=documents
        )
        
        # Execute workflow
        try:
            result = await self.graph.ainvoke(initial_state)
            
            logger.info(
                f"Workflow completed for application {payload.application_id}. Result type: {type(result)}. Keys if dict: {result.keys() if isinstance(result, dict) else 'N/A'}",
                extra={"application_id": payload.application_id}
            )
            logger.info(f"Raw LangGraph result: {str(result)[:800]}")
            
            # Prepare output
            if isinstance(result, dict):
                app_id = result.get("application_id")
                final_status = result.get("final_status", "DRAFT")
                ai_rec = result.get("ai_recommendation")
                fairness = result.get("fairness_check")
                val_rep = result.get("validation_report")
                scores = result.get("score_breakdown")
                audit = result.get("audit_trail", [])
                err_msg = result.get("error_message")
            else:
                app_id = getattr(result, "application_id", payload.application_id)
                final_status = getattr(result, "final_status", "DRAFT")
                ai_rec = getattr(result, "ai_recommendation", None)
                fairness = getattr(result, "fairness_check", None)
                val_rep = getattr(result, "validation_report", None)
                scores = getattr(result, "score_breakdown", None)
                audit = getattr(result, "audit_trail", [])
                err_msg = getattr(result, "error_message", None)

            output = WorkflowOutput(
                application_id=app_id or payload.application_id,
                final_status=final_status,
                ai_recommendation=ai_rec,
                fairness_check=fairness,
                validation_report=val_rep,
                score_breakdown=scores,
                audit_trail=audit,
                errors=[err_msg] if err_msg else []
            )
            
            return output
        
        except Exception as e:
            logger.error(
                f"Workflow execution failed for application {payload.application_id}: {str(e)}",
                extra={"application_id": payload.application_id},
                exc_info=True
            )
            
            return WorkflowOutput(
                application_id=payload.application_id,
                final_status="FAILED",
                errors=[str(e)]
            )
    
    def get_graph(self):
        """Return the compiled graph for visualization"""
        return self.graph
