"""
Receipt Manager
Extracts and processes receipt data using Azure Document Intelligence and Gemini AI
"""
import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add the src directory to Python path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from config.data_model.Receipt_shema import Receipt
from openai import AzureOpenAI


class ReceiptManager:
    """
    Receipt extraction and processing manager using Azure Document Intelligence and Azure OpenAI
    """
    
    def __init__(self, azure_endpoint: str, azure_key: str, gemini_api_key: str = None):
        """
        Initialize Receipt Manager
        
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
    
    def extract_from_url(self, url: str) -> Dict[str, Any]:
        """Extract receipt data from URL"""
        poller = self.azure_client.begin_analyze_document(
            "prebuilt-receipt",
            AnalyzeDocumentRequest(url_source=url)
        )
        result = poller.result()
        return self._process_extraction(result)
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """Extract receipt data from local file"""
        with open(file_path, "rb") as f:
            file_data = f.read()
        poller = self.azure_client.begin_analyze_document(
            "prebuilt-receipt",
            body=file_data,
            content_type="application/octet-stream"
        )
        result = poller.result()
        return self._process_extraction(result)
    
    def _process_extraction(self, receipts) -> Dict[str, Any]:
        """Process Azure Document Intelligence extraction results"""
        extracted_data = []
        
        for idx, receipt in enumerate(receipts.documents):
            receipt_dict = {
                "receipt_number": idx + 1,
                "doc_type": receipt.doc_type,
                "fields": {},
                "items": [],
                "tables": []
            }
            
            # Extract fields
            for name, field in receipt.fields.items():
                field_value = field.content if hasattr(field, 'content') else field.value
                
                # Handle Items field
                if name == "Items" and hasattr(field, 'value') and field.value is not None and isinstance(field.value, list):
                    for item in field.value:
                        item_data = {}
                        if hasattr(item, 'value') and isinstance(item.value, dict):
                            for item_field_name, item_field in item.value.items():
                                item_value = item_field.content if hasattr(item_field, 'content') else item_field.value
                                item_data[item_field_name] = {
                                    "value": item_value,
                                    "confidence": item_field.confidence if hasattr(item_field, 'confidence') else None
                                }
                            receipt_dict["items"].append(item_data)
                else:
                    receipt_dict["fields"][name] = {
                        "value": field_value,
                        "confidence": field.confidence,
                        "type": field.value_type if hasattr(field, 'value_type') else None
                    }
            
            # Extract tables
            if hasattr(receipts, 'tables') and receipts.tables:
                for table in receipts.tables:
                    table_data = {
                        "row_count": table.row_count,
                        "column_count": table.column_count,
                        "cells": []
                    }
                    
                    rows = {}
                    for cell in table.cells:
                        row_idx = cell.row_index
                        if row_idx not in rows:
                            rows[row_idx] = {}
                        rows[row_idx][cell.column_index] = cell.content
                    
                    for row_idx in sorted(rows.keys()):
                        row_data = [rows[row_idx].get(col_idx, "") for col_idx in range(table.column_count)]
                        table_data["cells"].append(row_data)
                    
                    receipt_dict["tables"].append(table_data)
                    
                    # Parse table as line items
                    if table.row_count > 1:
                        header_row = table_data["cells"][0] if table_data["cells"] else []
                        desc_idx = next((i for i, h in enumerate(header_row) if 'description' in h.lower() or 'item' in h.lower()), 0)
                        qty_idx = next((i for i, h in enumerate(header_row) if 'qty' in h.lower() or 'quantity' in h.lower()), None)
                        price_idx = next((i for i, h in enumerate(header_row) if 'price' in h.lower() or 'unit' in h.lower()), None)
                        total_idx = next((i for i, h in enumerate(header_row) if 'total' in h.lower() or 'amount' in h.lower()), None)
                        
                        for row_idx in range(1, len(table_data["cells"])):
                            row = table_data["cells"][row_idx]
                            if len(row) > desc_idx and row[desc_idx].strip():
                                item = {
                                    "Description": {"value": row[desc_idx], "confidence": 0.9},
                                    "Quantity": {"value": row[qty_idx] if qty_idx is not None and qty_idx < len(row) else "1", "confidence": 0.9},
                                    "UnitPrice": {"value": row[price_idx] if price_idx is not None and price_idx < len(row) else "0", "confidence": 0.9},
                                    "Amount": {"value": row[total_idx] if total_idx is not None and total_idx < len(row) else "0", "confidence": 0.9}
                                }
                                receipt_dict["items"].append(item)
            
            extracted_data.append(receipt_dict)
        
        return extracted_data[0] if len(extracted_data) == 1 else {"receipts": extracted_data}
    
    def map_to_pydantic(self, extracted_data: Dict[str, Any]) -> Receipt:
        """Map extracted data to Pydantic Receipt model using Azure OpenAI"""
        receipt_schema = Receipt.model_json_schema()
        
        prompt = """You are an expert data mapper that converts raw receipt data into structured Pydantic models.

IMPORTANT RULES:
1. Extract and map ALL available fields from the input data
2. Convert date strings to ISO format (YYYY-MM-DDTHH:MM:SS) for purchase_date
3. Extract purchase_time separately if available (HH:MM format)
4. Parse line items carefully from the "Items" or "items" array
5. Map financial fields: MerchantName → merchant_name, Subtotal → subtotal, TotalTax → tax_amount, Total → total_amount
6. Set document_type to "receipt"
7. Return ONLY a SINGLE JSON object matching the Receipt schema

Receipt Pydantic Schema:
{schema}

Extracted Receipt Data:
{data}

Task: Map the extracted data to match the Receipt schema. Return ONLY a single JSON object, no markdown.""".format(
            schema=json.dumps(receipt_schema, indent=2),
            data=json.dumps(extracted_data, indent=2, default=str)
        )
        
        print("🤖 Mapping with Azure OpenAI GPT-4o...")
        
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
            mapped_data_str = response.choices[0].message.content
            print("✓ Azure OpenAI mapping successful")
            
        except Exception as error:
            print(f"❌ Azure OpenAI mapping failed: {error}")
            raise
        
        if mapped_data_str.startswith("```json"):
            mapped_data_str = mapped_data_str.split("```json")[1].split("```")[0].strip()
        elif mapped_data_str.startswith("```"):
            mapped_data_str = mapped_data_str.split("```")[1].split("```")[0].strip()
        
        mapped_data = json.loads(mapped_data_str)
        
        if isinstance(mapped_data, list):
            if len(mapped_data) == 0:
                raise ValueError("Gemini returned an empty list")
            mapped_data = mapped_data[0]
        
        return Receipt(**mapped_data)
    
    def process_receipt(self, source: str, is_url: bool = False) -> Receipt:
        """
        Complete receipt processing pipeline
        
        Args:
            source: URL or file path to receipt
            is_url: True if source is URL, False if file path
            
        Returns:
            Receipt: Processed and validated Receipt object
        """
        if is_url:
            extracted_data = self.extract_from_url(source)
        else:
            extracted_data = self.extract_from_file(source)
        
        receipt = self.map_to_pydantic(extracted_data)
        return receipt
    
    def save_to_json(self, receipt: Receipt, output_path: str = "receipt_output.json"):
        """Save Receipt to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(receipt.model_dump_json(indent=2))
        print(f"✓ Receipt saved to: {output_path}")
