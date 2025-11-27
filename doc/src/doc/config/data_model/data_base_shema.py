from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class DocumentType(str, Enum):
    INVOICE = "invoice"
    RECEIPT = "receipt"
    PURCHASE_ORDER = "purchase_order"
    UNKNOWN = "unknown"

class BaseDocument(BaseModel):
    """Base schema shared by all documents"""
    document_id: str
    document_type: DocumentType
    upload_timestamp: datetime
    file_name: str
    file_size_bytes: int
    processing_status: str  # "pending", "processing", "completed", "failed"
    confidence_score: float = Field(ge=0.0, le=1.0)
    extracted_at: Optional[datetime] = None