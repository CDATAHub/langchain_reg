#!/bin/bash

# FastAPI + LangChain + LlamaIndex Insurance Document Q&A System Startup Script

set -e

echo "🚀 Starting LangChain + LlamaIndex Insurance Document Q&A System"
echo "=================================================="

# Check if DASHSCOPE_API_KEY is set
if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "❌ Error: DASHSCOPE_API_KEY environment variable is not set"
    echo "Please set it in your .env file or environment variables"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p uploads combined_storage reports

# Initialize services
echo "🔄 Initializing services..."
python init.py

# Start the FastAPI server
echo "🚀 Starting FastAPI server..."
echo "Server will be available at: http://localhost:8000"
echo "API documentation at: http://localhost:8000/docs"
echo "WebSocket at: ws://localhost:8000/api/ws"
echo "=================================================="

exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000