from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn
import json
import os
from datetime import datetime
from typing import List, Dict, Any

# 支持相对导入
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from api import documents, queries, reports, upload, websocket
from core.config import settings

app = FastAPI(
    title="LangChain + LlamaIndex Insurance Document Q&A",
    description="Web application for insurance document Q&A with streaming support",
    version="1.0.0"
)

# Configure CORS with standard middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routers
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(queries.router, prefix="/api/queries", tags=["queries"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(websocket.router, prefix="/api/ws", tags=["websocket"])


@app.get("/")
async def root():
    """Root endpoint with basic system info"""
    return {
        "message": "LangChain + LlamaIndex Insurance Document Q&A API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    error_msg = f"Internal server error: {str(exc)}"
    print(f"ERROR: {error_msg}")
    raise HTTPException(status_code=500, detail=error_msg)