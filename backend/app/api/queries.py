from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from app.auth.dependencies import get_current_user_context
from app.auth.models import UserContext
from app.schemas.schemas import QueryRequest, QueryResponse, StreamingChunk, SourceDocument
from app.services.llamaindex_service import llamaindex_service
from app.services.langchain_service import langchain_service
from app.services.rag_pipeline_service import run_rag_pipeline
from app.core.config import settings

router = APIRouter()


def _sse_event(payload: Dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    user_context: UserContext = Depends(get_current_user_context),
):
    """Perform a query on indexed documents"""
    try:
        if request.session_id:
            user_context = user_context.model_copy(update={"session_id": request.session_id})

        result = await run_rag_pipeline(
            question=request.question,
            user_context=user_context,
            top_k=request.top_k
        )

        # Convert sources to SourceDocument format
        source_docs = []
        for source in result["sources"]:
            source_docs.append(SourceDocument(
                content=source["content"],
                file_name=source["metadata"]["file_name"],
                score=source["score"],
                page_number=source["metadata"].get("page_label")
            ))

        return QueryResponse(
            answer=result["answer"],
            sources=source_docs,
            confidence=result["confidence"],
            timestamp=datetime.now(),
            trace_id=result.get("trace_id"),
            session_id=user_context.session_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.post("/stream")
async def query_stream(
    request: QueryRequest,
    user_context: UserContext = Depends(get_current_user_context),
):
    """Perform a streaming query on indexed documents"""
    try:
        if request.session_id:
            user_context = user_context.model_copy(update={"session_id": request.session_id})

        # Step 1: Retrieve relevant documents
        sources = await llamaindex_service.query(
            query_text=request.question,
            top_k=request.top_k,
            tenant_id=user_context.tenant_id,
            callback_handler=None,
        )

        if not sources:
            # Return empty stream if no sources found
            async def empty_stream():
                yield _sse_event({
                    "type": "error",
                    "message": "没有找到相关文档"
                })
            return StreamingResponse(empty_stream(), media_type="text/event-stream")

        # Step 2: Prepare context
        context = "\n\n".join(
            f"[来源: {source['metadata']['file_name']}]\n{source['content']}"
            for source in sources
        )

        # Step 3: Create streaming response
        async def generate_stream():
            # Send initial sources
            source_docs = []
            for source in sources:
                source_docs.append(SourceDocument(
                    content=source["content"],
                    file_name=source["metadata"]["file_name"],
                    score=source["score"],
                    page_number=source["metadata"].get("page_label")
                ))

            yield _sse_event({
                "type": "sources",
                "data": [doc.dict() for doc in source_docs]
            })

            # Stream the answer
            async for chunk in langchain_service.stream_answer(
                question=request.question,
                context=context,
                callback_handler=None,
            ):
                yield _sse_event({
                    "type": "chunk",
                    "content": chunk,
                    "done": False
                })

            # Send end signal
            yield _sse_event({
                "type": "end",
                "content": "",
                "done": True,
                "session_id": user_context.session_id,
            })

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream"
        )

    except Exception as e:
        async def error_stream():
            yield _sse_event({
                "type": "error",
                "message": f"Error processing query: {str(e)}"
            })
        return StreamingResponse(error_stream(), media_type="text/event-stream")
