"""
Invoice Manager
Extracts and processes invoice data using Azure Document Intelligence and Gemini AI
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
from config.data_model.invoice_shema import Invoice
from openai import AzureOpenAI


class InvoiceManager:
    """
    Invoice extraction and processing manager using Azure Document Intelligence and Azure OpenAI
    """
    
    def __init__(self, azure_endpoint: str, azure_key: str, gemini_api_key: str = None):
        """
        Initialize Invoice Manager
        
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
        """
        Extract invoice data from URL
        
        Args:
            url: URL to the invoice document
            
        Returns:
            dict: Extracted invoice data
        """
        poller = self.azure_client.begin_analyze_document(
            "prebuilt-invoice",
            AnalyzeDocumentRequest(url_source=url)
        )
        result = poller.result()
        return self._process_extraction(result)
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract invoice data from local file
        
        Args:
            file_path: Path to the invoice document
            
        Returns:
            dict: Extracted invoice data
        """
        with open(file_path, "rb") as f:
            file_data = f.read()
        poller = self.azure_client.begin_analyze_document(
            "prebuilt-invoice",
            body=file_data,
            content_type="application/octet-stream"
        )
        result = poller.result()
        return self._process_extraction(result)
    
    def _process_extraction(self, invoices) -> Dict[str, Any]:
        """
        Process Azure Document Intelligence extraction results
        
        Args:
            invoices: Azure extraction results
            
        Returns:
            dict: Processed invoice data with fields, items, and tables
        """
        extracted_data = []
        
        for idx, invoice in enumerate(invoices.documents):
            invoice_dict = {
                "invoice_number": idx + 1,
                "doc_type": invoice.doc_type,
                "fields": {},
                "items": [],
                "tables": []
            }
            
            # Extract fields
            for name, field in invoice.fields.items():
                field_value = field.content if hasattr(field, 'content') else field.value
                
                # Handle Items field specially
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
                            invoice_dict["items"].append(item_data)
                else:
                    invoice_dict["fields"][name] = {
                        "value": field_value,
                        "confidence": field.confidence,
                        "type": field.value_type if hasattr(field, 'value_type') else None
                    }
            
            # Extract tables
            if hasattr(invoices, 'tables') and invoices.tables:
                for table in invoices.tables:
                    table_data = {
                        "row_count": table.row_count,
                        "column_count": table.column_count,
                        "cells": []
                    }
                    
                    # Organize cells by row
                    rows = {}
                    for cell in table.cells:
                        row_idx = cell.row_index
                        if row_idx not in rows:
                            rows[row_idx] = {}
                        rows[row_idx][cell.column_index] = cell.content
                    
                    # Convert to list of rows
                    for row_idx in sorted(rows.keys()):
                        row_data = [rows[row_idx].get(col_idx, "") for col_idx in range(table.column_count)]
                        table_data["cells"].append(row_data)
                    
                    invoice_dict["tables"].append(table_data)
                    
                    # Parse table as line items
                    if table.row_count > 1:
                        header_row = table_data["cells"][0] if table_data["cells"] else []
                        
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
                                    "Quantity": {"value": row[qty_idx] if qty_idx is not None and qty_idx < len(row) else "1", "confidence": 0.9},
                                    "UnitPrice": {"value": row[price_idx] if price_idx is not None and price_idx < len(row) else "0", "confidence": 0.9},
                                    "Amount": {"value": row[total_idx] if total_idx is not None and total_idx < len(row) else "0", "confidence": 0.9}
                                }
                                invoice_dict["items"].append(item)
            
            extracted_data.append(invoice_dict)
        
        return extracted_data[0] if len(extracted_data) == 1 else {"invoices": extracted_data}
    
    def map_to_pydantic(self, extracted_data: Dict[str, Any]) -> Invoice:
        """
        Map extracted data to Pydantic Invoice model using Azure OpenAI
        
        Args:
            extracted_data: Extracted invoice data from Azure
            
        Returns:
            Invoice: Validated Pydantic Invoice object
        """
        invoice_schema = Invoice.model_json_schema()
        
        prompt = """You are an expert data mapper that converts raw invoice data into structured Pydantic models.
You will receive raw invoice data extracted from Azure Document Intelligence and must map it to the provided Invoice schema.

IMPORTANT RULES:
1. Extract and map ALL available fields from the input data
2. Convert date strings to ISO format (YYYY-MM-DDTHH:MM:SS)
3. Parse line items carefully, extracting description, quantity, unit_price, and total
4. Calculate missing values when possible (e.g., subtotal from line items)
5. Use "USD" as default currency if not specified
6. Set document_type to "invoice"
7. Return ONLY a SINGLE JSON object (not an array) matching the Invoice schema, no additional text or markdown

Invoice Pydantic Schema:
{schema}

Extracted Invoice Data from Azure Document Intelligence:
{data}

Task: Map the extracted data to match the Invoice schema structure. Return ONLY a single JSON object (NOT an array), no markdown code blocks or additional text.""".format(
            schema=json.dumps(invoice_schema, indent=2),
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
        
        # Clean up markdown formatting (just in case)
        if mapped_data_str.startswith("```json"):
            mapped_data_str = mapped_data_str.split("```json")[1].split("```")[0].strip()
        elif mapped_data_str.startswith("```"):
            mapped_data_str = mapped_data_str.split("```")[1].split("```")[0].strip()
        
        mapped_data = json.loads(mapped_data_str)
        
        # Handle list response
        if isinstance(mapped_data, list):
            if len(mapped_data) == 0:
                raise ValueError("Gemini returned an empty list")
            mapped_data = mapped_data[0]
        
        return Invoice(**mapped_data)
    
    def process_invoice(self, source: str, is_url: bool = False) -> Invoice:
        """
        Complete invoice processing pipeline
        
        Args:
            source: URL or file path to invoice
            is_url: True if source is URL, False if file path
            
        Returns:
            Invoice: Processed and validated Invoice object
        """
        # Extract data
        if is_url:
            extracted_data = self.extract_from_url(source)
        else:
            extracted_data = self.extract_from_file(source)
        
        # Map to Pydantic
        invoice = self.map_to_pydantic(extracted_data)
        
        return invoice
    
    def save_to_json(self, invoice: Invoice, output_path: str = "invoice_output.json"):
        """
        Save Invoice to JSON file
        
        Args:
            invoice: Invoice object to save
            output_path: Output file path
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(invoice.model_dump_json(indent=2))
        print(f"✓ Invoice saved to: {output_path}")
