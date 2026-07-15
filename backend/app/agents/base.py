"""
Base Agent Class for LangGraph Workflow

Provides common functionality for all agents.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.agents import WorkflowState, AuditEntry
from app.core.logging import get_logger

logger = get_logger("agents.base")


class BaseAgent(ABC):
    """Base class for all workflow agents"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = get_logger(f"agents.{agent_name.lower()}")
    
    @abstractmethod
    async def process(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Process the state and return updates.
        
        Should return a dict with keys that update the WorkflowState.
        """
        pass
    
    def log_action(
        self,
        state: WorkflowState,
        action: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        reasoning: Optional[str] = None
    ) -> AuditEntry:
        """Create an audit entry for this agent's action"""
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            agent=self.agent_name,
            action=action,
            inputs=inputs,
            outputs=outputs,
            tool_calls=tool_calls or [],
            reasoning=reasoning
        )
        
        self.logger.info(
            f"Action completed: {action}",
            extra={
                "agent": self.agent_name,
                "action": action,
                "timestamp": entry.timestamp.isoformat()
            }
        )
        
        return entry
    
    def add_audit_entry(self, state: WorkflowState, entry: AuditEntry) -> WorkflowState:
        """Add audit entry to state"""
        state.audit_trail.append(entry)
        return state
    
    def set_error(
        self,
        state: WorkflowState,
        error_message: str
    ) -> WorkflowState:
        """Set error state"""
        state.error_message = error_message
        state.error_at_stage = self.agent_name
        self.logger.error(
            f"Error in {self.agent_name}: {error_message}",
            extra={"agent": self.agent_name}
        )
        return state
