from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
import os
import shutil
from datetime import datetime

from schemas.schemas import DocumentList, DocumentResponse, DocumentMetadata
from services.llamaindex_service import llamaindex_service
from core.config import settings

router = APIRouter()


def get_index_status():
    """Get current index status"""
    return llamaindex_service.get_index_status()


@router.get("/", response_model=DocumentList)
def list_documents():
    """List all documents in the system"""
    # This would normally query a database or filesystem
    # For now, we'll return a mock response
    return DocumentList(
        documents=[],
        total_count=0
    )


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    index_after_upload: bool = True
):
    """Upload a new document for indexing"""
    if not file.filename.lower().endswith(('.txt', '.pdf', '.md')):
        raise HTTPException(
            status_code=400,
            detail="Only .txt, .pdf, and .md files are supported"
        )

    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(settings.UPLOAD_DIR, datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(upload_dir, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    # Add document to index if requested
    document_id = file.filename  # Simplified ID for now
    indexed = False

    if index_after_upload:
        success = await llamaindex_service.add_document(file_path, file.filename)
        if success:
            indexed = True

    metadata = DocumentMetadata(
        file_name=file.filename,
        size=os.path.getsize(file_path),
        uploaded_at=datetime.now(),
        indexed=indexed
    )

    return DocumentResponse(
        message=f"Document '{file.filename}' uploaded successfully",
        document_id=document_id,
        metadata=metadata
    )


@router.post("/{document_id}/index")
async def index_document(document_id: str):
    """Manually trigger indexing for a document"""
    # This would normally find the document by ID and index it
    # For now, we'll trigger a rebuild of the index

    try:
        # Load documents from upload directory
        upload_dir = settings.UPLOAD_DIR
        if os.path.exists(upload_dir):
            docs = await llamaindex_service.load_documents(upload_dir)
            if docs:
                await llamaindex_service.build_index(docs)
                return {"message": f"Document {document_id} indexed successfully"}
            else:
                raise HTTPException(status_code=404, detail="No documents found to index")
        else:
            raise HTTPException(status_code=404, detail="Upload directory not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error indexing document: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from the system"""
    # This would normally remove the document from storage and index
    # For now, we'll return success
    return {"message": f"Document {document_id} deleted successfully"}


@router.post("/rebuild-index")
async def rebuild_index():
    """Rebuild the entire index from all documents"""
    try:
        # Clear existing index
        await llamaindex_service.clear_index()

        # Load all documents and build new index
        upload_dir = settings.UPLOAD_DIR
        if os.path.exists(upload_dir):
            docs = await llamaindex_service.load_documents(upload_dir)
            if docs:
                index = await llamaindex_service.build_index(docs)
                return {"message": "Index rebuilt successfully", "document_count": len(docs)}
            else:
                return {"message": "No documents to index", "document_count": 0}
        else:
            return {"message": "No documents directory found"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rebuilding index: {str(e)}")


@router.get("/status", response_model=DocumentMetadata)
async def get_document_status():
    """Get current index status"""
    status = llamaindex_service.get_index_status()
    return DocumentMetadata(
        file_name="system_status",
        size=0,
        uploaded_at=datetime.now(),
        indexed=status["indexed"],
        chunks_count=status["document_count"]
    )