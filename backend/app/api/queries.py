from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from schemas.schemas import QueryRequest, QueryResponse, StreamingChunk, SourceDocument
from services.llamaindex_service import llamaindex_service
from services.langchain_service import langchain_service
from core.config import settings

router = APIRouter()


@router.post("/", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Perform a query on indexed documents"""
    try:
        # Step 1: Retrieve relevant documents using LlamaIndex
        sources = await llamaindex_service.query(
            query_text=request.question,
            top_k=request.top_k
        )

        if not sources:
            return QueryResponse(
                answer="抱歉，没有找到与您的问题相关的文档。",
                sources=[],
                confidence=0.0,
                timestamp=datetime.now()
            )

        # Step 2: Prepare context for LangChain
        context = "\n\n".join(
            f"[来源: {source['metadata']['file_name']}]\n{source['content']}"
            for source in sources
        )

        # Step 3: Generate answer using LangChain
        answer = await langchain_service.answer_question(
            question=request.question,
            context=context,
            stream=False  # For non-streaming response
        )

        # Convert sources to SourceDocument format
        source_docs = []
        for source in sources:
            source_docs.append(SourceDocument(
                content=source["content"],
                file_name=source["metadata"]["file_name"],
                score=source["score"],
                page_number=source["metadata"].get("page_label")
            ))

        # Calculate confidence score (simplified)
        confidence = len(answer) / (len(context) + 1) if context else 0.5

        return QueryResponse(
            answer=answer,
            sources=source_docs,
            confidence=min(confidence, 1.0),
            timestamp=datetime.now()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.post("/stream")
async def query_stream(request: QueryRequest):
    """Perform a streaming query on indexed documents"""
    try:
        # Step 1: Retrieve relevant documents
        sources = await llamaindex_service.query(
            query_text=request.question,
            top_k=request.top_k
        )

        if not sources:
            # Return empty stream if no sources found
            async def empty_stream():
                yield json.dumps({
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

            yield json.dumps({
                "type": "sources",
                "data": [doc.dict() for doc in source_docs]
            })

            # Stream the answer
            async for chunk in langchain_service.stream_answer(
                question=request.question,
                context=context
            ):
                yield json.dumps({
                    "type": "chunk",
                    "content": chunk,
                    "done": False
                })

            # Send end signal
            yield json.dumps({
                "type": "end",
                "content": "",
                "done": True
            })

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream"
        )

    except Exception as e:
        async def error_stream():
            yield json.dumps({
                "type": "error",
                "message": f"Error processing query: {str(e)}"
            })
        return StreamingResponse(error_stream(), media_type="text/event-stream")
