@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo 🚀 Starting LangChain + LlamaIndex Insurance Document Q&A System
echo ==================================================

:: Check if DASHSCOPE_API_KEY is set
if "%DASHSCOPE_API_KEY%"=="" (
    echo ❌ Error: DASHSCOPE_API_KEY environment variable is not set
    echo Please set it in your .env file or environment variables
    pause
    exit /b 1
)

:: Create necessary directories
echo 📁 Creating necessary directories...
if not exist "uploads" mkdir uploads
if not exist "combined_storage" mkdir combined_storage
if not exist "reports" mkdir reports

:: Initialize services
echo 🔄 Initializing services...
python init.py

:: Start the FastAPI server
echo 🚀 Starting FastAPI server...
echo Server will be available at: http://localhost:8000
echo API documentation at: http://localhost:8000/docs
echo WebSocket at: ws://localhost:8000/api/ws
echo ==================================================

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause