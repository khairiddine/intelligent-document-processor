from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime
from .data_base_shema import BaseDocument, DocumentType
from .invoice_shema import LineItem, VendorInfo

class PurchaseOrder(BaseDocument):
    """Schema for purchase order documents"""
    document_type: DocumentType = DocumentType.PURCHASE_ORDER
    
    po_number: str
    po_date: datetime
    delivery_date: Optional[datetime] = None
    
    buyer: VendorInfo
    supplier: VendorInfo
    
    items: List[LineItem] = []
    
    subtotal: float
    tax_amount: float
    shipping_cost: Optional[float] = 0.0
    total_amount: float
    currency: str = "USD"
    
    shipping_address: Optional[str] = None
    billing_address: Optional[str] = None
    
    terms_and_conditions: Optional[str] = None
    status: str = "pending"  # "pending", "approved", "fulfilled"
