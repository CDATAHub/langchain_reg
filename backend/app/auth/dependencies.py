import base64
import hashlib
import hmac
import json
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import Header, HTTPException, Request, status

from app.auth.models import UserContext
from app.core.config import settings


def _decode_base64url(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _decode_jwt(token: str) -> Dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed JWT")

    signing_input = f"{parts[0]}.{parts[1]}".encode("utf-8")
    signature = _decode_base64url(parts[2])

    if settings.JWT_SECRET_KEY:
        if settings.JWT_ALGORITHM != "HS256":
            raise ValueError("Unsupported JWT algorithm")
        expected = hmac.new(
            settings.JWT_SECRET_KEY.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid JWT signature")

    payload = json.loads(_decode_base64url(parts[1]).decode("utf-8"))
    return payload


async def verify_user_tenant_mapping(user_id: str, tenant_id: str) -> bool:
    if not settings.AUTH_REQUIRED:
        return True

    from app.db.connection import get_session
    from app.db.models import UserTenantMapping
    from sqlalchemy import select

    async with get_session() as session:
        stmt = select(UserTenantMapping).where(
            UserTenantMapping.user_id == user_id,
            UserTenantMapping.tenant_id == tenant_id,
        )
        result = await session.execute(stmt)
        return result.scalars().first() is not None


async def get_current_user_context(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    x_session_id: Optional[str] = Header(default=None),
    x_channel: Optional[str] = Header(default="web"),
) -> UserContext:
    client_ip = request.client.host if request.client else "unknown"
    session_id = x_session_id or str(uuid4())

    if not authorization:
        if settings.AUTH_REQUIRED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization token",
            )
        return UserContext(
            user_id=settings.DEFAULT_USER_ID,
            tenant_id=settings.DEFAULT_TENANT_ID,
            session_id=session_id,
            ip=client_ip,
            channel=x_channel or "web",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    try:
        payload = _decode_jwt(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc

    user_id = str(payload.get("sub") or payload.get("user_id") or "")
    tenant_id = str(payload.get("tenant_id") or "")
    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required claims",
        )

    issuer = payload.get("iss")
    audience = payload.get("aud")
    if settings.JWT_ISSUER and issuer != settings.JWT_ISSUER:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")
    if settings.JWT_AUDIENCE and audience != settings.JWT_AUDIENCE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token audience")

    is_valid_mapping = await verify_user_tenant_mapping(user_id=user_id, tenant_id=tenant_id)
    if not is_valid_mapping:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to tenant",
        )

    return UserContext(
        user_id=user_id,
        tenant_id=tenant_id,
        session_id=session_id,
        ip=client_ip,
        channel=x_channel or str(payload.get("channel") or "web"),
    )
