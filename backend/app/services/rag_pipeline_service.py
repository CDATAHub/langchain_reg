from time import perf_counter
from typing import Any, Dict, List

from app.auth.models import UserContext
from app.core.config import settings
from app.observability.langfuse_service import langfuse_service, observe
from app.services.audit_service import audit_service
from app.services.langchain_service import langchain_service
from app.services.llamaindex_service import llamaindex_service


def _build_context(sources: List[Dict[str, Any]]) -> str:
    return "\n\n".join(
        f"[来源: {source['metadata']['file_name']}]\n{source['content']}"
        for source in sources
    )


@observe(name="insurance-rag-pipeline")
async def run_rag_pipeline(
    *,
    question: str,
    user_context: UserContext,
    top_k: int,
) -> Dict[str, Any]:
    started_at = perf_counter()
    langfuse_service.update_current_trace(
        user_id=user_context.user_id,
        session_id=user_context.session_id,
        tags=[
            f"tenant:{user_context.tenant_id}",
            "insurance-cs",
            f"env:{settings.LANGFUSE_ENV}",
        ],
        input={"question": question},
        metadata={
            "tenant_id": user_context.tenant_id,
            "channel": user_context.channel,
            "biz_scenario": settings.BIZ_SCENARIO,
            "prompt_version": settings.PROMPT_VERSION,
            "retrieval_top_k": top_k,
            "model": settings.LLM_MODEL,
            "client_ip": user_context.ip,
        },
    )

    try:
        sources = await llamaindex_service.query(
            query_text=question,
            top_k=top_k,
            tenant_id=user_context.tenant_id,
            callback_handler=langfuse_service.get_current_llama_index_handler(),
        )

        if not sources:
            latency_ms = int((perf_counter() - started_at) * 1000)
            await audit_service.save_chat_trace(
                tenant_id=user_context.tenant_id,
                user_id=user_context.user_id,
                session_id=user_context.session_id,
                trace_id=langfuse_service.get_current_trace_id(),
                question=question,
                answer="",
                model_name=settings.LLM_MODEL,
                status="success",
                latency_ms=latency_ms,
            )
            return {
                "answer": "抱歉，没有找到与您的问题相关的文档。",
                "sources": [],
                "confidence": 0.0,
                "trace_id": langfuse_service.get_current_trace_id(),
            }

        context = _build_context(sources)
        answer = await langchain_service.answer_question(
            question=question,
            context=context,
            stream=False,
            callback_handler=langfuse_service.get_current_langchain_handler(),
        )

        confidence = len(answer) / (len(context) + 1) if context else 0.5
        latency_ms = int((perf_counter() - started_at) * 1000)
        trace_id = langfuse_service.get_current_trace_id()

        langfuse_service.update_current_trace(output={"answer": answer, "sources_count": len(sources)})
        await audit_service.save_chat_trace(
            tenant_id=user_context.tenant_id,
            user_id=user_context.user_id,
            session_id=user_context.session_id,
            trace_id=trace_id,
            question=question,
            answer=answer,
            model_name=settings.LLM_MODEL,
            status="success",
            latency_ms=latency_ms,
        )

        return {
            "answer": answer,
            "sources": sources,
            "confidence": min(confidence, 1.0),
            "trace_id": trace_id,
        }
    except Exception as exc:
        latency_ms = int((perf_counter() - started_at) * 1000)
        langfuse_service.update_current_trace(status_message="RAG_FAILED", output=str(exc))
        await audit_service.save_chat_trace(
            tenant_id=user_context.tenant_id,
            user_id=user_context.user_id,
            session_id=user_context.session_id,
            trace_id=langfuse_service.get_current_trace_id(),
            question=question,
            answer="",
            model_name=settings.LLM_MODEL,
            status="error",
            latency_ms=latency_ms,
            error_type=type(exc).__name__,
        )
        raise
