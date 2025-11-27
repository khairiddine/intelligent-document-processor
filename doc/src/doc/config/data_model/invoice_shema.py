from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime
from .data_base_shema import BaseDocument, DocumentType

class VendorInfo(BaseModel):
    name: str
    address: Optional[str] = None
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float
    tax_rate: Optional[float] = None

class Invoice(BaseDocument):
    """Schema for invoice documents"""
    document_type: DocumentType = DocumentType.INVOICE
    
    # Invoice-specific fields
    invoice_number: str
    invoice_date: datetime
    due_date: Optional[datetime] = None
    
    # Parties
    vendor: VendorInfo
    customer: Optional[VendorInfo] = None
    
    # Financial data
    subtotal: float
    tax_amount: float
    total_amount: float
    currency: str = "USD"
    
    # Items
    line_items: List[LineItem] = []
    
    # Payment info
    payment_terms: Optional[str] = None  # "Net 30", "Due on receipt"
    payment_method: Optional[str] = None
    bank_details: Optional[dict] = None
    
    # Metadata
    notes: Optional[str] = None
    purchase_order_number: Optional[str] = None