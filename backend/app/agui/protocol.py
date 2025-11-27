"""
AG-UI Protocol Implementation
Agent-User Interaction Standard
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from app.models.schemas import (
    AgentMessage,
    AgentInteraction,
    AgentActionType,
    UserResponse,
    DocumentType
)

class AGUISession:
    """
    AG-UI Protocol Session Manager
    Handles agent-user interaction lifecycle
    """
    
    def __init__(self, document_id: str, user_id: str):
        self.session_id = str(uuid.uuid4())
        self.document_id = document_id
        self.user_id = user_id
        self.interactions: List[AgentInteraction] = []
        self.current_step = 0
        self.state = "active"
    
    def create_agent_message(
        self,
        action_type: AgentActionType,
        message: str,
        confidence: Optional[float] = None,
        requires_approval: bool = False
    ) -> AgentMessage:
        """
        Create an agent message announcing next action
        
        Args:
            action_type: Type of action agent will perform
            message: Human-readable description
            confidence: Agent's confidence in the action (0.0-1.0)
            requires_approval: Whether user must approve before execution
            
        Returns:
            AgentMessage object
        """
        return AgentMessage(
            action_type=action_type,
            message=message,
            confidence=confidence,
            requires_approval=requires_approval,
            can_undo=True
        )
    
    def add_interaction(
        self,
        agent_message: AgentMessage,
        user_response: Optional[UserResponse] = None,
        agent_result: Optional[Dict[str, Any]] = None
    ) -> AgentInteraction:
        """
        Add a new interaction to the session
        
        Args:
            agent_message: Agent's announced action
            user_response: User's response (approve/reject/modify)
            agent_result: Result after agent execution
            
        Returns:
            AgentInteraction object
        """
        interaction = AgentInteraction(
            session_id=self.session_id,
            document_id=self.document_id,
            agent_message=agent_message,
            user_response=user_response,
            agent_result=agent_result,
            timestamp=datetime.utcnow()
        )
        
        self.interactions.append(interaction)
        self.current_step += 1
        
        return interaction
    
    def get_current_interaction(self) -> Optional[AgentInteraction]:
        """Get the current (latest) interaction"""
        if self.interactions:
            return self.interactions[-1]
        return None
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return len(self.interactions) > 0 and self.interactions[-1].agent_message.can_undo
    
    def undo_last_action(self) -> bool:
        """
        Undo the last agent action
        
        Returns:
            True if undo successful, False otherwise
        """
        if not self.can_undo():
            return False
        
        # Remove last interaction
        self.interactions.pop()
        self.current_step -= 1
        return True
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get interaction history as list of dicts"""
        return [
            {
                "step": idx + 1,
                "action": interaction.agent_message.action_type,
                "message": interaction.agent_message.message,
                "user_response": interaction.user_response,
                "timestamp": interaction.timestamp.isoformat()
            }
            for idx, interaction in enumerate(self.interactions)
        ]
    
    def close_session(self):
        """Close the AG-UI session"""
        self.state = "closed"


class AGUIWorkflow:
    """
    AG-UI Workflow for Document Processing
    Defines the interaction flow for document classification and extraction
    """
    
    @staticmethod
    def create_classification_message(document_name: str) -> AgentMessage:
        """Step 1: Classification announcement"""
        return AgentMessage(
            action_type=AgentActionType.CLASSIFY,
            message=f"I will analyze '{document_name}' to classify its type (invoice, receipt, or purchase order).",
            confidence=None,
            requires_approval=False,  # Auto-approve classification
            can_undo=True
        )
    
    @staticmethod
    def create_classification_result_message(
        document_type: DocumentType,
        confidence: float
    ) -> AgentMessage:
        """Step 2: Classification result announcement"""
        return AgentMessage(
            action_type=AgentActionType.CLASSIFY,
            message=f"Document classified as '{document_type}' with {confidence:.1%} confidence. Proceed with extraction?",
            confidence=confidence,
            requires_approval=True,  # User can approve/reject
            can_undo=True
        )
    
    @staticmethod
    def create_extraction_message(document_type: DocumentType) -> AgentMessage:
        """Step 3: Extraction announcement"""
        agent_name = {
            DocumentType.INVOICE: "Invoice Processing Specialist",
            DocumentType.RECEIPT: "Receipt Processing Specialist",
            DocumentType.PURCHASE_ORDER: "Purchase Order Processing Specialist"
        }.get(document_type, "Document Specialist")
        
        return AgentMessage(
            action_type=AgentActionType.EXTRACT,
            message=f"{agent_name} will extract all relevant data from the document.",
            confidence=None,
            requires_approval=False,
            can_undo=True
        )
    
    @staticmethod
    def create_validation_message(field_count: int) -> AgentMessage:
        """Step 4: Validation announcement"""
        return AgentMessage(
            action_type=AgentActionType.VALIDATE,
            message=f"Validating {field_count} extracted fields against schema...",
            confidence=None,
            requires_approval=False,
            can_undo=False
        )
    
    @staticmethod
    def create_completion_message(
        success: bool,
        extracted_fields: Optional[int] = None
    ) -> AgentMessage:
        """Step 5: Completion announcement"""
        if success:
            message = f"✓ Processing complete! Successfully extracted {extracted_fields} fields."
        else:
            message = "✗ Processing failed. Please review the errors."
        
        return AgentMessage(
            action_type=AgentActionType.COMPLETE,
            message=message,
            confidence=1.0 if success else 0.0,
            requires_approval=False,
            can_undo=False
        )


# Global session store (in production, use Redis or database)
_active_sessions: Dict[str, AGUISession] = {}

def get_session(document_id: str, user_id: str) -> AGUISession:
    """Get or create AG-UI session for document"""
    key = f"{user_id}:{document_id}"
    if key not in _active_sessions:
        _active_sessions[key] = AGUISession(document_id, user_id)
    return _active_sessions[key]

def close_session(document_id: str, user_id: str):
    """Close and remove session"""
    key = f"{user_id}:{document_id}"
    if key in _active_sessions:
        _active_sessions[key].close_session()
        del _active_sessions[key]
