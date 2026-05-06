from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8080",
    ]

    # API Keys
    DASHSCOPE_API_KEY: str

    # Auth settings
    AUTH_REQUIRED: bool = False
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = ""
    JWT_AUDIENCE: str = ""
    DEFAULT_TENANT_ID: str = "public"
    DEFAULT_USER_ID: str = "anonymous"

    # Langfuse settings
    LANGFUSE_ENABLED: bool = False
    LANGFUSE_HOST: str = ""
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_RELEASE: str = ""
    LANGFUSE_TIMEOUT: int = 10
    LANGFUSE_ENV: str = "dev"

    # RAG metadata settings
    BIZ_SCENARIO: str = "policy_inquiry"
    PROMPT_VERSION: str = "v1"

    # Database settings
    MYSQL_DSN: str = ""

    # Multi-tenant retrieval settings
    MILVUS_TENANT_MODE: str = "metadata"

    # Storage settings
    STORAGE_DIR: str = "./combined_storage"
    UPLOAD_DIR: str = "./uploads"
    REPORTS_DIR: str = "./reports"

    # LLM settings
    LLM_MODEL: str = "deepseek-v3"
    EMBEDDING_MODEL: str = "text-embedding-v1"
    TEMPERATURE: float = 0.1
    TOP_P: float = 0.8

    # Chunking settings
    CHUNK_SIZE: int = 1024
    CHUNK_OVERLAP: int = 100
    MAX_SEARCH_RESULTS: int = 5

    # WebSocket settings
    WS_MAX_CONNECTIONS: int = 100
    WS_PING_INTERVAL: int = 30
    WS_PING_TIMEOUT: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
