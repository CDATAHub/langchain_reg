#!/usr/bin/env python
# coding: utf-8
"""
Backend initialization script
Sets up the index and loads documents on startup
"""

import os
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.llamaindex_service import llamaindex_service
from app.services.langchain_service import langchain_service
from datetime import datetime


async def initialize_services():
    """Initialize backend services"""
    print("🚀 Initializing LangChain + LlamaIndex Insurance Document Q&A System")
    print("=" * 60)

    try:
        # Step 1: Setup LlamaIndex
        print("\nStep 1: Setting up LlamaIndex...")
        await llamaindex_service.setup()
        print("✅ LlamaIndex initialized successfully")

        # Step 2: Setup LangChain
        print("\nStep 2: Setting up LangChain...")
        await langchain_service.setup()
        print("✅ LangChain initialized successfully")

        # Step 3: Load and index documents if available
        print("\nStep 3: Checking for documents...")
        upload_dir = settings.UPLOAD_DIR

        if os.path.exists(upload_dir):
            documents = await llamaindex_service.load_documents(upload_dir)
            if documents:
                print(f"Found {len(documents)} documents, building index...")
                await llamaindex_service.build_index(documents)
                print("✅ Index built successfully")
            else:
                print("No documents found in upload directory")
        else:
            print(f"Upload directory {upload_dir} not found")

        # Step 4: Check existing index
        print("\nStep 4: Checking existing index...")
        status = llamaindex_service.get_index_status()
        print(f"Index status: {status}")

        print("\n" + "=" * 60)
        print("✅ All services initialized successfully!")
        print("You can now start the FastAPI server with:")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Initialization failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(initialize_services())