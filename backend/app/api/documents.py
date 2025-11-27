"""
Document Processing API Endpoints with AG-UI Protocol
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from app.models.schemas import (
    DocumentUploadResponse,
    DocumentProcessRequest,
    DocumentProcessResponse,
    DocumentHistoryResponse,
    AgentInteraction
)
from app.services.auth import get_current_user
from app.services.document_processing import document_processor
from app.config import settings
from pathlib import Path

router = APIRouter(prefix="/documents", tags=["Documents"])
security = HTTPBearer()

async def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user from JWT"""
    return await get_current_user(credentials.credentials)

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Upload a document for processing
    
    - **file**: PDF, PNG, JPG, or JPEG file
    
    Returns document metadata with pending status
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Validate file size
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)
    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Upload document
    try:
        document = await document_processor.upload_document(
            file_bytes=file_bytes,
            filename=file.filename,
            user_id=current_user['id']
        )
        
        return DocumentUploadResponse(
            id=document['id'],
            filename=document['filename'],
            file_path=document['file_path'],
            status=document['status'],
            upload_timestamp=document['upload_timestamp'],
            message="Document uploaded successfully. Use /process endpoint to start processing."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.post("/process", response_model=DocumentProcessResponse)
async def process_document(
    request: DocumentProcessRequest,
    auto_approve: bool = Query(default=True, description="Auto-approve agent actions"),
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Process an uploaded document with AG-UI Protocol
    
    - **document_id**: ID of uploaded document
    - **auto_approve**: If true, agent actions are auto-approved (default: true)
    
    Returns extraction results with AG-UI interaction history
    """
    try:
        result = await document_processor.process_document(
            document_id=request.document_id,
            user_id=current_user['id'],
            auto_approve=auto_approve
        )
        
        return DocumentProcessResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )

@router.get("/history", response_model=List[DocumentHistoryResponse])
async def get_history(
    limit: int = Query(default=50, le=100),
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Get user's document processing history
    
    - **limit**: Maximum number of documents to return (max 100)
    
    Returns list of processed documents with results
    """
    try:
        history = await document_processor.get_document_history(
            user_id=current_user['id'],
            limit=limit
        )
        
        return [
            DocumentHistoryResponse(
                id=doc['id'],
                filename=doc['filename'],
                status=doc['status'],
                document_type=doc.get('document_type'),
                upload_timestamp=doc['upload_timestamp'],
                processed_at=doc.get('processed_at'),
                result_summary={
                    'vendor': doc.get('extraction_results', [{}])[0].get('vendor_name') if doc.get('extraction_results') else None,
                    'total': doc.get('extraction_results', [{}])[0].get('total_amount') if doc.get('extraction_results') else None
                }
            )
            for doc in history
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch history: {str(e)}"
        )

@router.get("/{document_id}/result")
async def get_result(
    document_id: str,
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Get extraction result for a specific document
    
    - **document_id**: Document ID
    
    Returns full extraction data
    """
    result = await document_processor.get_document_result(document_id, current_user['id'])
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found for this document"
        )
    
    return result

@router.get("/{document_id}/agui-history", response_model=List[dict])
async def get_agui_history(
    document_id: str,
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Get AG-UI interaction history for a document
    
    Shows the conversation between user and agents during processing
    """
    from app.agui.protocol import _active_sessions
    
    key = f"{current_user['id']}:{document_id}"
    if key in _active_sessions:
        session = _active_sessions[key]
        return session.get_history()
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AG-UI session not found (document may not be processed yet or session expired)"
        )
