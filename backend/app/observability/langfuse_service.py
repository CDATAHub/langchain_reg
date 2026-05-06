from contextlib import contextmanager
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    from langfuse import Langfuse
    from langfuse.decorators import langfuse_context, observe
    LANGFUSE_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - optional dependency fallback
    Langfuse = None
    langfuse_context = None
    LANGFUSE_IMPORT_ERROR = exc

    def observe(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


class LangfuseService:
    def __init__(self):
        self.client: Optional[Langfuse] = None
        self.enabled = False

    def setup(self) -> None:
        if not settings.LANGFUSE_ENABLED:
            self.enabled = False
            return

        if LANGFUSE_IMPORT_ERROR is not None or Langfuse is None:
            logger.warning("Langfuse disabled because SDK is unavailable: %s", LANGFUSE_IMPORT_ERROR)
            self.enabled = False
            return

        if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
            logger.warning("Langfuse disabled because keys are missing")
            self.enabled = False
            return

        self.client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST or None,
            release=settings.LANGFUSE_RELEASE or None,
            timeout=settings.LANGFUSE_TIMEOUT,
        )
        self.enabled = True

    def flush(self) -> None:
        if self.enabled and self.client is not None:
            self.client.flush()

    def update_current_trace(self, **kwargs: Any) -> None:
        if self.enabled and langfuse_context is not None:
            langfuse_context.update_current_trace(**kwargs)

    def update_current_observation(self, **kwargs: Any) -> None:
        if self.enabled and langfuse_context is not None:
            langfuse_context.update_current_observation(**kwargs)

    def get_current_trace_id(self) -> Optional[str]:
        if self.enabled and langfuse_context is not None:
            return langfuse_context.get_current_trace_id()
        return None

    def get_current_langchain_handler(self) -> Any:
        if self.enabled and langfuse_context is not None:
            return langfuse_context.get_current_langchain_handler()
        return None

    def get_current_llama_index_handler(self) -> Any:
        if self.enabled and langfuse_context is not None:
            return langfuse_context.get_current_llama_index_handler()
        return None

    @contextmanager
    def span(self, name: str, input_data: Any = None, output_data: Any = None):
        if not self.enabled or self.client is None:
            yield None
            return

        with self.client.start_as_current_span(name=name, input=input_data) as span:
            try:
                yield span
                if output_data is not None:
                    span.update(output=output_data)
            except Exception as exc:
                span.update(level="ERROR", status_message=str(exc))
                raise


langfuse_service = LangfuseService()
