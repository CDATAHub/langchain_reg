from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from api import documents, queries, reports, upload, websocket
from app.core.config import settings
from app.core.logging import get_logger
from app.observability.langfuse_service import langfuse_service

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.connection import setup_database, close_database

    langfuse_service.setup()
    await setup_database()
    yield
    langfuse_service.flush()
    await close_database()

app = FastAPI(
    title="LangChain + LlamaIndex Insurance Document Q&A",
    description="Web application for insurance document Q&A with streaming support",
    version="1.0.0",
    lifespan=lifespan,
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
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务处理异常，已记录日志",
            "trace_id": langfuse_service.get_current_trace_id(),
            "timestamp": datetime.now().isoformat(),
        },
    )
