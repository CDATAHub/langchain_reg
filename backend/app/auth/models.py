from pydantic import BaseModel


class UserContext(BaseModel):
    user_id: str
    tenant_id: str
    session_id: str
    ip: str
    channel: str = "web"
