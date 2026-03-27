#!/usr/bin/env python
# coding: utf-8
"""
PyCharm Debug Startup Script
使用此脚本在 PyCharm 中进行调试
"""

import os
import sys
import asyncio
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables for development
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("HOST", "0.0.0.0")
os.environ.setdefault("PORT", "8000")

from app.main import app
from app.core.config import settings


def run_debug_server():
    """
    Run Uvicorn server in debug mode.
    This allows PyCharm debugger to attach to the process.
    """
    import uvicorn

    print("=" * 60)
    print("🐛 DEBUG MODE - PyCharm Compatible")
    print("=" * 60)
    print(f"📍 Host: {settings.HOST}")
    print(f"🔌 Port: {settings.PORT}")
    print(f"🔄 Reload: {settings.DEBUG}")
    print(f"📚 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 60)
    print("\n⚠️  Debug Tips:")
    print("   • Set breakpoints in your code")
    print("   • Click the Debug button in PyCharm")
    print("   • Make requests to test your breakpoints")
    print("=" * 60)
    print()

    # Run with reload disabled in debug mode for better stability
    # PyCharm will handle hot-reloading when needed
    try:
        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
            reload=False,  # Disable reload for debug mode
            log_level="debug",
            use_colors=True,
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n\n❌ Server error: {e}")
        raise


if __name__ == "__main__":
    run_debug_server()
