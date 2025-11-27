from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime
from .data_base_shema import BaseDocument, DocumentType
from .invoice_shema import LineItem


class Receipt(BaseDocument):
    """Schema for receipt documents"""
    document_type: DocumentType = DocumentType.RECEIPT
    
    receipt_number: Optional[str] = None
    merchant_name: str
    merchant_address: Optional[str] = None
    
    purchase_date: datetime
    purchase_time: Optional[str] = None
    
    items: List[LineItem] = []
    
    subtotal: float
    tax_amount: float
    tip_amount: Optional[float] = 0.0
    total_amount: float
    currency: str = "USD"
    
    payment_method: Optional[str] = None  # "Credit Card", "Cash"
    card_last_4: Optional[str] = None
    
    category: Optional[str] = None  # "Food", "Transportation", "Office Supplies"