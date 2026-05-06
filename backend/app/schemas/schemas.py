from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# Document schemas
class DocumentMetadata(BaseModel):
    file_name: str
    size: int
    uploaded_at: datetime
    indexed: bool = False
    chunks_count: int = 0


class DocumentList(BaseModel):
    documents: List[DocumentMetadata]
    total_count: int


class DocumentResponse(BaseModel):
    message: str
    document_id: str
    metadata: DocumentMetadata


# Query schemas
class QueryRequest(BaseModel):
    question: str = Field(..., description="The question to ask")
    stream: bool = Field(default=False, description="Whether to stream the response")
    top_k: int = Field(default=5, description="Number of documents to retrieve")
    session_id: Optional[str] = Field(default=None, description="Client conversation session id")


class SourceDocument(BaseModel):
    content: str
    file_name: str
    score: Optional[float] = None
    page_number: Optional[int] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    confidence: float
    timestamp: datetime
    trace_id: Optional[str] = None
    session_id: Optional[str] = None


class StreamingChunk(BaseModel):
    type: str = "chunk"
    content: str
    done: bool = False
    sources: Optional[List[SourceDocument]] = None


# Report schemas
class ReportRequest(BaseModel):
    question: str
    answer: str
    sources: List[str]
    report_type: str = Field(default="structured", description="structured or detailed")
    send_email: bool = False
    email_recipient: Optional[str] = None


class ReportResponse(BaseModel):
    report_id: str
    report_content: str
    timestamp: datetime
    file_path: Optional[str] = None
    email_sent: bool = False


# WebSocket schemas
class WebSocketMessage(BaseModel):
    type: str  # query, stream, status, error
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


# Upload schemas
class UploadResponse(BaseModel):
    message: str
    file_name: str
    file_size: int
    file_path: str
    uploaded_at: datetime


# Index schemas
class IndexStatus(BaseModel):
    indexed: bool
    document_count: int
    last_updated: Optional[datetime] = None
    storage_path: str
