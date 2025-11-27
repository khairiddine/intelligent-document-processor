"""
Purchase Order Extraction Manager
Extracts purchase order data using Azure Document Intelligence and maps to Pydantic model using Gemini
"""
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add the src directory to Python path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from config.data_model.Purchase_order_shema import PurchaseOrder
from openai import AzureOpenAI


class PurchaseOrderManager:
    """
    Purchase Order Extraction and Processing Manager
    """
    
    def __init__(self, azure_endpoint: str, azure_key: str, gemini_api_key: str = None):
        """
        Initialize the Purchase Order Manager
        
        Args:
            azure_endpoint: Azure Document Intelligence endpoint
            azure_key: Azure Document Intelligence API key
            gemini_api_key: Deprecated, kept for compatibility
        """
        self.azure_client = DocumentIntelligenceClient(
            endpoint=azure_endpoint,
            credential=AzureKeyCredential(azure_key)
        )
        
        # Initialize Azure OpenAI for data mapping
        self.azure_openai_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-12-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
    
    def analyze_document(self, file_path: str = None, file_url: str = None):
        """
        Analyze purchase order document using Azure Document Intelligence
        
        Args:
            file_path: Local file path (PDF, PNG, JPG, etc.)
            file_url: URL to the document
            
        Returns:
            Analysis result from Azure Document Intelligence
        """
        if file_path:
            print(f"Analyzing local file: {file_path}")
            with open(file_path, "rb") as f:
                file_data = f.read()
            poller = self.azure_client.begin_analyze_document(
                "prebuilt-invoice",  # Azure uses invoice model for POs
                body=file_data,
                content_type="application/octet-stream"
            )
        elif file_url:
            print(f"Analyzing URL: {file_url}")
            poller = self.azure_client.begin_analyze_document(
                "prebuilt-invoice",
                AnalyzeDocumentRequest(url_source=file_url)
            )
        else:
            raise ValueError("Either file_path or file_url must be provided")
        
        return poller.result()
    
    def extract_data(self, azure_result) -> dict:
        """
        Extract all purchase order data from Azure result
        
        Args:
            azure_result: Azure Document Intelligence analysis result
            
        Returns:
            dict: Extracted purchase order data with fields, items, and tables
        """
        extracted_data = []
        
        # DEBUG info
        print("\n" + "="*60)
        print("DEBUG: Full Azure Response Structure")
        print("="*60)
        print(f"Number of documents: {len(azure_result.documents) if azure_result.documents else 0}")
        print(f"Has tables: {hasattr(azure_result, 'tables') and azure_result.tables is not None}")
        if hasattr(azure_result, 'tables') and azure_result.tables:
            print(f"Number of tables: {len(azure_result.tables)}")
        print("="*60 + "\n")
        
        for idx, po in enumerate(azure_result.documents):
            print(f"--------Analyzing Purchase Order #{idx + 1}--------")
            print(f"Document type: {po.doc_type}")
            
            po_dict = {
                "po_number": idx + 1,
                "doc_type": po.doc_type,
                "fields": {},
                "items": [],
                "tables": []
            }
            
            # Extract fields
            for name, field in po.fields.items():
                field_value = field.content if hasattr(field, 'content') else field.value
                print(f"\tField '{name}' = '{field_value}' (confidence: {field.confidence})")
                
                # Handle Items field
                if name == "Items" and hasattr(field, 'value') and field.value is not None and isinstance(field.value, list):
                    print(f"\t✓ Processing {len(field.value)} items from Items field...")
                    for item_idx, item in enumerate(field.value):
                        if hasattr(item, 'value') and isinstance(item.value, dict):
                            item_data = {}
                            for item_field_name, item_field in item.value.items():
                                item_value = item_field.content if hasattr(item_field, 'content') else item_field.value
                                item_data[item_field_name] = {
                                    "value": item_value,
                                    "confidence": item_field.confidence if hasattr(item_field, 'confidence') else None
                                }
                            po_dict["items"].append(item_data)
                            print(f"\t\t✓ Item {item_idx + 1}: {item_data}")
                else:
                    po_dict["fields"][name] = {
                        "value": field_value,
                        "confidence": field.confidence,
                        "type": field.value_type if hasattr(field, 'value_type') else None
                    }
            
            # Extract tables
            if hasattr(azure_result, 'tables') and azure_result.tables:
                print(f"\n📊 Found {len(azure_result.tables)} table(s)")
                for table_idx, table in enumerate(azure_result.tables):
                    print(f"\n  Table {table_idx + 1}: {table.row_count} rows × {table.column_count} columns")
                    
                    table_data = {
                        "row_count": table.row_count,
                        "column_count": table.column_count,
                        "cells": []
                    }
                    
                    # Organize cells by row
                    rows = {}
                    for cell in table.cells:
                        if cell.row_index not in rows:
                            rows[cell.row_index] = {}
                        rows[cell.row_index][cell.column_index] = cell.content
                    
                    # Convert to list of rows
                    for row_idx in sorted(rows.keys()):
                        row_data = [rows[row_idx].get(col_idx, "") for col_idx in range(table.column_count)]
                        table_data["cells"].append(row_data)
                    
                    po_dict["tables"].append(table_data)
                    
                    # Parse table as line items
                    if table.row_count > 1:
                        print(f"\n  🔄 Parsing table as line items...")
                        header_row = table_data["cells"][0]
                        
                        # Find column indices
                        desc_idx = next((i for i, h in enumerate(header_row) if 'description' in h.lower() or 'item' in h.lower()), 0)
                        qty_idx = next((i for i, h in enumerate(header_row) if 'qty' in h.lower() or 'quantity' in h.lower()), None)
                        price_idx = next((i for i, h in enumerate(header_row) if 'price' in h.lower() or 'unit' in h.lower()), None)
                        total_idx = next((i for i, h in enumerate(header_row) if 'total' in h.lower() or 'amount' in h.lower()), None)
                        
                        # Parse data rows
                        for row_idx in range(1, len(table_data["cells"])):
                            row = table_data["cells"][row_idx]
                            if len(row) > desc_idx and row[desc_idx].strip():
                                item = {
                                    "Description": {"value": row[desc_idx], "confidence": 0.9},
                                    "Quantity": {"value": row[qty_idx] if qty_idx and qty_idx < len(row) else "1", "confidence": 0.9},
                                    "UnitPrice": {"value": row[price_idx] if price_idx and price_idx < len(row) else "0", "confidence": 0.9},
                                    "Amount": {"value": row[total_idx] if total_idx and total_idx < len(row) else "0", "confidence": 0.9}
                                }
                                po_dict["items"].append(item)
                                print(f"      ✓ Parsed: {item['Description']['value']}")
            
            extracted_data.append(po_dict)
            
            # Summary
            print(f"\n📋 Extraction Summary:")
            print(f"   Fields: {len(po_dict['fields'])}")
            print(f"   Items: {len(po_dict['items'])}")
            print(f"   Tables: {len(po_dict['tables'])}")
        
        return extracted_data[0] if len(extracted_data) == 1 else {"purchase_orders": extracted_data}
    
    def map_to_pydantic(self, extracted_data: dict) -> PurchaseOrder:
        """
        Map extracted data to Pydantic PurchaseOrder model using Azure OpenAI
        
        Args:
            extracted_data: Extracted purchase order data
            
        Returns:
            PurchaseOrder: Validated Pydantic model
        """
        po_schema = PurchaseOrder.model_json_schema()
        
        prompt = """You are an expert data mapper. Convert the extracted purchase order data to match the PurchaseOrder schema.

RULES:
1. Convert dates to ISO format (YYYY-MM-DDTHH:MM:SS)
2. Parse line items: description, quantity, unit_price, total
3. Map fields: InvoiceId→po_number, InvoiceDate→po_date, VendorName→supplier, CustomerName→buyer
4. Create VendorInfo objects for supplier and buyer with name, address, tax_id, email, phone
5. Set document_type="purchase_order", status="pending"
6. Generate unique document_id, set timestamps
7. Calculate confidence_score (0.0-1.0)
8. Return ONLY a single JSON object, no markdown

PurchaseOrder Schema:
{schema}

Extracted Data:
{data}

Return a single JSON object matching the schema.""".format(
            schema=json.dumps(po_schema, indent=2),
            data=json.dumps(extracted_data, indent=2, default=str)
        )
        
        print("\n🤖 Mapping with Azure OpenAI GPT-4o...")
        
        try:
            response = self.azure_openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert data mapper. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            mapped_data = json.loads(response.choices[0].message.content)
            print("✓ Azure OpenAI mapping successful")
            
        except Exception as error:
            print(f"❌ Azure OpenAI mapping failed: {error}")
            raise
        
        # Handle list response
        if isinstance(mapped_data, list):
            if len(mapped_data) == 0:
                raise ValueError("Azure OpenAI returned empty list")
            mapped_data = mapped_data[0]
        
        print("✓ Mapped successfully")
        
        # Validate with Pydantic
        try:
            purchase_order = PurchaseOrder(**mapped_data)
            print("✓ Pydantic validation passed")
            return purchase_order
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            print(f"Data: {json.dumps(mapped_data, indent=2)}")
            raise
    
    def process_purchase_order(self, file_path: str = None, file_url: str = None, 
                               save_raw: bool = True, save_pydantic: bool = True) -> PurchaseOrder:
        """
        Complete purchase order processing pipeline
        
        Args:
            file_path: Local file path
            file_url: Document URL
            save_raw: Save raw extracted data to JSON
            save_pydantic: Save Pydantic model to JSON
            
        Returns:
            PurchaseOrder: Processed purchase order model
        """
        print("\n" + "="*60)
        print("PURCHASE ORDER EXTRACTION")
        print("="*60)
        
        # Step 1: Analyze with Azure
        print("\nSTEP 1: Analyzing with Azure Document Intelligence...")
        azure_result = self.analyze_document(file_path, file_url)
        
        # Step 2: Extract data
        print("\nSTEP 2: Extracting data...")
        extracted_data = self.extract_data(azure_result)
        
        if save_raw:
            with open('extracted_po_data.json', 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=2, default=str)
            print("✓ Raw data saved to: extracted_po_data.json")
        
        # Step 3: Map to Pydantic
        print("\nSTEP 3: Mapping to Pydantic model...")
        po_model = self.map_to_pydantic(extracted_data)
        
        if save_pydantic:
            with open('purchase_order_pydantic.json', 'w', encoding='utf-8') as f:
                f.write(po_model.model_dump_json(indent=2))
            print("✓ Pydantic model saved to: purchase_order_pydantic.json")
        
        # Display summary
        self.display_summary(po_model)
        
        return po_model
    
    def display_summary(self, po_model: PurchaseOrder):
        """Display purchase order summary"""
        print("\n" + "="*60)
        print("PURCHASE ORDER SUMMARY")
        print("="*60)
        print(f"📋 PO Number: {po_model.po_number}")
        print(f"📅 PO Date: {po_model.po_date}")
        if po_model.delivery_date:
            print(f"🚚 Delivery Date: {po_model.delivery_date}")
        print(f"💰 Total: {po_model.currency} {po_model.total_amount}")
        print(f"📊 Status: {po_model.status}")
        
        print(f"\n🏢 Buyer: {po_model.buyer.name}")
        print(f"🏭 Supplier: {po_model.supplier.name}")
        
        if po_model.items:
            print(f"\n📦 Items ({len(po_model.items)}):")
            for idx, item in enumerate(po_model.items, 1):
                print(f"   {idx}. {item.description} - Qty: {item.quantity} × ${item.unit_price} = ${item.total}")
        
        print(f"\n💵 Financial:")
        print(f"   Subtotal: ${po_model.subtotal:.2f}")
        print(f"   Tax:      ${po_model.tax_amount:.2f}")
        if po_model.shipping_cost:
            print(f"   Shipping: ${po_model.shipping_cost:.2f}")
        print(f"   Total:    ${po_model.total_amount:.2f}")
        print(f"\n🎯 Confidence: {po_model.confidence_score:.2%}")
