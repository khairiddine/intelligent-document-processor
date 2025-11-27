"""
Document Processing Service
Integrates with your existing CrewAI document processing system
"""
import sys
import os
from pathlib import Path

# Disable CrewAI interactive prompts for API mode
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
from typing import Dict, Any, Optional
from datetime import datetime
import json
import tempfile
from app.database import get_supabase, get_supabase_admin
from app.models.schemas import DocumentStatus, DocumentType
from app.agui.protocol import AGUISession, AGUIWorkflow, get_session, close_session

# Add paths for doc processing modules - must include parent to support "doc.src.doc" imports
projet_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(projet_root))

# Import your existing CrewAI code
from doc.src.doc.crew import DocCrew

class DocumentProcessor:
    """
    Document Processing Service with AG-UI Protocol Integration
    """
    
    def __init__(self):
        self.supabase = get_supabase()
        self.supabase_admin = get_supabase_admin()  # For operations that need to bypass RLS
        self.crew = None
    
    async def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Upload document to Supabase Storage
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename
            user_id: User ID
            
        Returns:
            Document metadata
        """
        # Upload to Supabase Storage
        file_path = f"{user_id}/{datetime.utcnow().timestamp()}_{filename}"
        
        response = self.supabase.storage.from_('documents').upload(
            file_path,
            file_bytes,
            file_options={"content-type": "application/pdf"}
        )
        
        # Save metadata to database
        document_data = {
            "user_id": user_id,
            "filename": filename,
            "file_path": file_path,
            "file_size": len(file_bytes),
            "status": DocumentStatus.PENDING.value,
            "upload_timestamp": datetime.utcnow().isoformat()
        }
        
        result = self.supabase.table('documents').insert(document_data).execute()
        
        return result.data[0] if result.data else None
    
    async def process_document(
        self,
        document_id: str,
        user_id: str,
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Process document with AG-UI Protocol
        
        Args:
            document_id: Document ID from database
            user_id: User ID
            auto_approve: If True, skip approval steps
            
        Returns:
            Processing result with AG-UI interactions
        """
        # Get document from database
        doc_response = self.supabase.table('documents').select('*').eq('id', document_id).execute()
        if not doc_response.data:
            raise ValueError(f"Document {document_id} not found")
        
        document = doc_response.data[0]
        
        # Initialize AG-UI session
        agui_session = get_session(document_id, user_id)
        
        # Step 1: AG-UI - Announce classification
        classification_msg = AGUIWorkflow.create_classification_message(document['filename'])
        agui_session.add_interaction(classification_msg)
        
        # Update status to processing
        self.supabase.table('documents').update({
            'status': DocumentStatus.PROCESSING.value
        }).eq('id', document_id).execute()
        
        try:
            # Download file from Supabase Storage
            file_data = self.supabase.storage.from_('documents').download(document['file_path'])
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(document['filename']).suffix) as tmp_file:
                tmp_file.write(file_data)
                tmp_path = tmp_file.name
            
            # Initialize CrewAI
            if not self.crew:
                self.crew = DocCrew()
            
            # Run document processing
            inputs = {'document_path': tmp_path}
            result = self.crew.crew().kickoff(inputs=inputs)
            
            # Extract results from tasks_output
            classification_result = None
            processing_result = None
            document_type = None
            
            if hasattr(result, 'tasks_output') and result.tasks_output:
                for idx, task_output in enumerate(result.tasks_output):
                    output_text = task_output.raw if hasattr(task_output, 'raw') else str(task_output)
                    
                    # Classification result
                    if idx == 0:
                        try:
                            classification_result = json.loads(output_text)
                            document_type = classification_result.get('document_type', 'unknown')
                        except:
                            # Try to extract document type from text
                            if 'invoice' in output_text.lower():
                                document_type = 'invoice'
                            elif 'receipt' in output_text.lower():
                                document_type = 'receipt'
                            elif 'purchase' in output_text.lower():
                                document_type = 'purchase_order'
                            else:
                                document_type = 'unknown'
                    
                    # Processing result (first non-skipped task)
                    elif "SKIPPED_NO_OUTPUT" not in output_text and processing_result is None:
                        try:
                            processing_result = json.loads(output_text)
                        except:
                            processing_result = {"raw": output_text}
            
            # Step 2: AG-UI - Classification result (ask approval if needed)
            if document_type and not auto_approve:
                classification_result_msg = AGUIWorkflow.create_classification_result_message(
                    DocumentType(document_type),
                    classification_result.get('confidence_score', 0.9) if classification_result else 0.9
                )
                agui_session.add_interaction(classification_result_msg)
            
            # Step 3: AG-UI - Announce extraction
            if document_type != 'unknown':
                extraction_msg = AGUIWorkflow.create_extraction_message(DocumentType(document_type))
                agui_session.add_interaction(extraction_msg)
            
            # Step 4: AG-UI - Validation
            if processing_result:
                field_count = len(processing_result.keys()) if isinstance(processing_result, dict) else 0
                validation_msg = AGUIWorkflow.create_validation_message(field_count)
                agui_session.add_interaction(validation_msg)
            
            # Step 5: AG-UI - Completion
            completion_msg = AGUIWorkflow.create_completion_message(
                success=processing_result is not None,
                extracted_fields=len(processing_result.keys()) if processing_result else 0
            )
            agui_session.add_interaction(completion_msg)
            
            # Save results to database
            extraction_data = {
                'document_id': document_id,
                'result_data': processing_result,
                'vendor_name': processing_result.get('vendor', {}).get('name') if processing_result else None,
                'total_amount': processing_result.get('total_amount') if processing_result else None,
                'invoice_date': processing_result.get('invoice_date') if processing_result else None,
                'confidence_score': classification_result.get('confidence_score', 0.9) if classification_result else 0.9
            }
            
            # Use admin client to bypass RLS for extraction_results
            self.supabase_admin.table('extraction_results').insert(extraction_data).execute()
            
            # Update document status
            self.supabase.table('documents').update({
                'status': DocumentStatus.COMPLETED.value,
                'document_type': document_type
            }).eq('id', document_id).execute()
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            # Close AG-UI session
            close_session(document_id, user_id)
            
            return {
                'document_id': document_id,
                'status': DocumentStatus.COMPLETED.value,
                'document_type': document_type,
                'result_data': processing_result,
                'agui_history': agui_session.get_history(),
                'phoenix_trace_url': f"https://app.phoenix.arize.com/s/khairibou20/traces"
            }
            
        except Exception as e:
            # Update document status to failed
            self.supabase.table('documents').update({
                'status': DocumentStatus.FAILED.value
            }).eq('id', document_id).execute()
            
            # AG-UI - Error completion
            error_msg = AGUIWorkflow.create_completion_message(success=False)
            agui_session.add_interaction(error_msg)
            
            # Close session
            close_session(document_id, user_id)
            
            raise Exception(f"Processing failed: {str(e)}")
    
    async def get_document_history(self, user_id: str, limit: int = 50) -> list:
        """
        Get user's document processing history
        
        Args:
            user_id: User ID
            limit: Maximum number of documents to return
            
        Returns:
            List of documents with results
        """
        response = self.supabase.table('documents').select(
            '*', 'extraction_results(*)'
        ).eq('user_id', user_id).order('upload_timestamp', desc=True).limit(limit).execute()
        
        return response.data if response.data else []
    
    async def get_document_result(self, document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get extraction result for a specific document
        
        Args:
            document_id: Document ID
            user_id: User ID
            
        Returns:
            Extraction result data
        """
        response = self.supabase.table('extraction_results').select(
            '*'
        ).eq('document_id', document_id).execute()
        
        return response.data[0] if response.data else None

# Singleton instance
document_processor = DocumentProcessor()
