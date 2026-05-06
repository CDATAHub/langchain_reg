from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Enum, Integer, String, Index
from sqlalchemy.orm import DeclarativeBase

Base = DeclarativeBase()


class UserTenantMapping(Base):
    __tablename__ = "user_tenant_mapping"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False)
    tenant_id = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_user_tenant", "user_id", "tenant_id", unique=True),
    )


class ChatTrace(Base):
    __tablename__ = "chat_trace"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), nullable=False)
    user_id = Column(String(64), nullable=False)
    session_id = Column(String(128), nullable=False)
    langfuse_trace_id = Column(String(128), unique=True)
    trace_url = Column(String(512))
    question_summary = Column(String(1024))
    answer_summary = Column(String(1024))
    model_name = Column(String(64))
    status = Column(Enum("success", "error", "timeout"), nullable=False)
    error_type = Column(String(64))
    latency_ms = Column(Integer)
    created_at = Column(DateTime(3), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_tenant_status_created", "tenant_id", "status", "created_at"),
        Index("idx_session", "session_id"),
    )
