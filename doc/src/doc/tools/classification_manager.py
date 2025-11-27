"""
Document Classification Manager
Classifies documents into Invoice, Receipt, or Purchase Order using GPT-4o Vision
"""
import os
import sys
import base64
from pathlib import Path
from datetime import datetime

# Add the src directory to Python path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from openai import AzureOpenAI
from config.data_model.data_base_shema import DocumentType, BaseDocument
from pdf2image import convert_from_path
from PIL import Image
import io


class DocumentClassifier:
    """
    Document Classification Manager using Azure OpenAI GPT-4o Vision
    """
    
    def __init__(self, api_key: str, endpoint: str, api_version: str = "2024-12-01-preview"):
        """
        Initialize the Document Classifier
        
        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint URL
            api_version: API version
        """
        self.client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=api_key,
        )
        self.model = "gpt-4o"
   
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image file to base64 string"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
     
   
    def pdf_to_image_base64(self, pdf_path: str) -> str:
        """Convert first page of PDF to base64 encoded image"""
        images = convert_from_path(pdf_path, first_page=1, last_page=1)
        
        if not images:
            raise ValueError("Could not convert PDF to image")
        
        img = images[0]
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def classify_document(self, path: str) -> BaseDocument:
        """
        Classify document type and return BaseDocument with all metadata
        
        Args:
            path: Path to the document file (PDF, PNG, JPG, etc.)
            
        Returns:
            BaseDocument: The classified document with all metadata
        """
        file_path = Path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        # Get file info
        file_size = os.path.getsize(path)
        file_name = file_path.name
        file_extension = file_path.suffix.lower()
        
        # Convert to base64
        if file_extension == '.pdf':
            base64_image = self.pdf_to_image_base64(path)
            image_format = "png"
        elif file_extension in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            base64_image = self.encode_image_to_base64(path)
            image_format = file_extension[1:]
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        # Classification prompt
        prompt = """Analyze this document image and classify it into ONE category:

1. **invoice** - Bill for goods/services with line items, payment terms
2. **receipt** - Payment acknowledgment, simpler format, transaction details
3. **purchase_order** - Order document with PO number, vendor, delivery details

Respond with ONLY ONE WORD (lowercase): invoice, receipt, purchase_order, or unknown"""

        # Call GPT-4o
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert document classification assistant."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/{image_format};base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=50,
            temperature=0.0,
        )

        # Map result to DocumentType
        classification = response.choices[0].message.content.strip().lower()
        classification_map = {
            "invoice": DocumentType.INVOICE,
            "receipt": DocumentType.RECEIPT,
            "purchase_order": DocumentType.PURCHASE_ORDER,
            "unknown": DocumentType.UNKNOWN
        }
        document_type = classification_map.get(classification, DocumentType.UNKNOWN)
        
        # Create BaseDocument
        current_time = datetime.now()
        return BaseDocument(
            document_id=f"{document_type.value}_{current_time.strftime('%Y%m%d_%H%M%S')}_{file_path.stem}",
            document_type=document_type,
            upload_timestamp=current_time,
            file_name=file_name,
            file_size_bytes=file_size,
            processing_status="classified",
            confidence_score=0.95,
            extracted_at=current_time
        )
    
    def save_to_json(self, base_document: BaseDocument, output_path: str = "classification.json"):
        """Save BaseDocument to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(base_document.model_dump_json(indent=2))
        print(f"✓ Saved to: {output_path}")
