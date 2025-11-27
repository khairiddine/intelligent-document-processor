"""
Pydantic Models for API Request/Response
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

# ============================================================================
# Authentication Models
# ============================================================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

# ============================================================================
# Document Models
# ============================================================================

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentType(str, Enum):
    INVOICE = "invoice"
    RECEIPT = "receipt"
    PURCHASE_ORDER = "purchase_order"
    UNKNOWN = "unknown"

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    file_path: str
    status: DocumentStatus
    upload_timestamp: datetime
    message: str

class DocumentProcessRequest(BaseModel):
    document_id: str

class DocumentProcessResponse(BaseModel):
    document_id: str
    status: DocumentStatus
    document_type: Optional[DocumentType] = None
    result_data: Optional[Dict[str, Any]] = None
    phoenix_trace_url: Optional[str] = None
    processing_duration: Optional[float] = None
    error_message: Optional[str] = None

class DocumentHistoryResponse(BaseModel):
    id: str
    filename: str
    status: DocumentStatus
    document_type: Optional[DocumentType]
    upload_timestamp: datetime
    processed_at: Optional[datetime]
    result_summary: Optional[Dict[str, Any]]

# ============================================================================
# AG-UI Protocol Models
# ============================================================================

class AgentActionType(str, Enum):
    CLASSIFY = "classify"
    EXTRACT = "extract"
    VALIDATE = "validate"
    COMPLETE = "complete"

class AgentMessage(BaseModel):
    """AG-UI Protocol: Agent announces what it will do"""
    action_type: AgentActionType
    message: str
    confidence: Optional[float] = None
    requires_approval: bool = False
    can_undo: bool = True

class UserResponse(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    SKIP = "skip"

class AgentInteraction(BaseModel):
    """AG-UI Protocol: Complete interaction cycle"""
    session_id: str
    document_id: str
    agent_message: AgentMessage
    user_response: Optional[UserResponse] = None
    agent_result: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AgentApprovalRequest(BaseModel):
    """AG-UI Protocol: Request user approval for agent action"""
    interaction_id: str
    user_response: UserResponse
    modification_data: Optional[Dict[str, Any]] = None

# ============================================================================
# Processing Result Models
# ============================================================================

class ExtractionResult(BaseModel):
    document_id: str
    document_type: DocumentType
    extracted_data: Dict[str, Any]
    confidence_score: float
    vendor_name: Optional[str] = None
    total_amount: Optional[float] = None
    invoice_date: Optional[str] = None
    processing_agent: str
    phoenix_trace_id: Optional[str] = None
