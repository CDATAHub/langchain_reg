from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.utils.pii import summarize_text

logger = get_logger(__name__)


class AuditService:
    async def save_chat_trace(
        self,
        *,
        tenant_id: str,
        user_id: str,
        session_id: str,
        trace_id: Optional[str],
        question: str,
        answer: str,
        model_name: str,
        status: str,
        latency_ms: int,
        error_type: Optional[str] = None,
    ) -> None:
        question_summary = summarize_text(question, 256)
        answer_summary = summarize_text(answer, 256)

        if settings.MYSQL_DSN:
            try:
                from app.db.connection import get_session
                from app.db.models import ChatTrace
                from sqlalchemy import insert

                async with get_session() as session:
                    stmt = insert(ChatTrace).values(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        session_id=session_id,
                        langfuse_trace_id=trace_id,
                        trace_url=f"{settings.LANGFUSE_HOST}/trace/{trace_id}" if settings.LANGFUSE_HOST and trace_id else None,
                        question_summary=question_summary,
                        answer_summary=answer_summary,
                        model_name=model_name,
                        status=status,
                        error_type=error_type,
                        latency_ms=latency_ms,
                    )
                    await session.execute(stmt)
                    logger.info("Chat trace saved to database: tenant_id=%s, status=%s", tenant_id, status)
            except Exception as exc:
                logger.exception("Failed to save chat trace to database: %s", exc)
        else:
            logger.info(
                "Chat trace audit: tenant_id=%s user_id=%s session_id=%s trace_id=%s status=%s latency_ms=%s question=%s answer=%s",
                tenant_id,
                user_id,
                session_id,
                trace_id,
                status,
                latency_ms,
                question_summary,
                answer_summary,
            )


audit_service = AuditService()
