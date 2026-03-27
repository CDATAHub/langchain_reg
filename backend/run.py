#!/usr/bin/env python
# coding: utf-8
"""
Backend Startup Script
用于生产环境和日常开发
"""

import os
import sys
from pathlib import Path
import uvicorn

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app
from app.core.config import settings


def run_server():
    """
    Run Uvicorn server with settings from config.
    Suitable for production and regular development.
    """
    print("=" * 60)
    print("🚀 Starting LangChain + LlamaIndex Backend")
    print("=" * 60)
    print(f"📍 Host: {settings.HOST}")
    print(f"🔌 Port: {settings.PORT}")
    print(f"🔄 Reload: {settings.DEBUG}")
    print(f"📚 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 60)
    print()

    try:
        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level="info" if settings.DEBUG else "warning",
            use_colors=True,
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n\n❌ Server error: {e}")
        raise


if __name__ == "__main__":
    run_server()
