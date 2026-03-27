# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LangChain + LlamaIndex insurance document intelligent Q&A system with a FastAPI backend and React + TypeScript frontend. The system enables real-time document-based question answering with streaming responses, report generation, and email delivery.

## Common Development Commands

### Backend (FastAPI)
```bash
# Initialize services and build document index
cd backend
python init.py

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the run script
uv run run.py

# Install dependencies
uv add -r requirements.txt

# Run tests
pytest tests/
```

### Frontend (React + Vite)
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint

# Preview production build
npm run preview
```

### Docker Compose (Full Stack)
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Architecture Overview

### Backend Architecture

The backend follows a three-layer architecture:

**1. API Layer** (`backend/app/api/`)
- `documents.py` - Document CRUD operations
- `queries.py` - Query endpoints (streaming and non-streaming)
- `reports.py` - Report generation workflow
- `upload.py` - File upload handling
- `websocket.py` - WebSocket connections for real-time streaming

**2. Service Layer** (`backend/app/services/`)
- `llamaindex_service.py` - Vector retrieval using LlamaIndex
  - Manages document indexing and storage in `combined_storage/`
  - Handles semantic search and document retrieval
  - Configured with DashScope embeddings
- `langchain_service.py` - LLM orchestration using LangChain
  - Chains for QA and report generation
  - Report saving and email delivery (simulated)

**3. Configuration Layer** (`backend/app/core/`)
- `config.py` - Centralized settings using Pydantic Settings
  - Loads from `.env` file
  - Configures LLM, embedding models, chunking parameters

### Key Backend Flow

1. **Initialization**: Run `python init.py` to setup services and build the vector index from documents in `uploads/`
2. **Query Flow**: Query API → LlamaIndex retrieves relevant documents → LangChain generates answer using retrieved context
3. **Streaming**: WebSocket endpoint streams LLM responses in real-time
4. **Report Flow**: Query API → LlamaIndex retrieves → LangChain generates answer → Report chain generates structured report → Save to `reports/` and optionally send email

### Frontend Architecture

**Components** (`frontend/src/components/`)
- `QueryInterface.tsx` - Q&A interface with streaming support
- `DocumentManager.tsx` - Document upload and management
- `ReportGenerator.tsx` - Report creation and email delivery

**Key Technologies**: React 19, TypeScript, Vite, Tailwind CSS 4, Socket.IO client

## Important Implementation Details

### Dual Framework Architecture

This project uses **both** LlamaIndex and LangChain for different purposes:
- **LlamaIndex**: Vector storage, document indexing, semantic search
- **LangChain**: LLM orchestration, prompt engineering, response generation

Both services use DashScope API but with different integrations:
- LlamaIndex: `DashScopeEmbedding` and `DashScope` LLM
- LangChain: `ChatTongyi` from `langchain_community`

### Index Persistence

The vector index is persisted to `backend/combined_storage/`. On startup, the system:
1. Attempts to load existing index from storage
2. If loading fails, builds new index from documents in `uploads/`
3. Newly uploaded documents are inserted into existing index

### Async Design

The backend uses async/await throughout:
- Service methods are async
- Blocking operations (like LLM calls) use `asyncio.to_thread()`
- WebSocket streaming uses async generators

### Environment Configuration

Required environment variables in `.env`:
- `DASHSCOPE_API_KEY` - Required for LLM and embedding API calls
- `STORAGE_DIR` - Vector index storage path (default: `./combined_storage`)
- `UPLOAD_DIR` - Document upload directory (default: `./uploads`)
- `REPORTS_DIR` - Report output directory (default: `./reports`)
- `CHUNK_SIZE` / `CHUNK_OVERLAP` - Document chunking parameters (default: 1024/100)
- `MAX_SEARCH_RESULTS` - Number of documents to retrieve (default: 5)

### CORS Handling

A custom `SimpleCORSMiddleware` in `main.py` adds CORS headers directly to all responses. Origins are configured in `settings.ALLOWED_ORIGINS`.

### Document Processing

Documents are automatically chunked using LlamaIndex's `SentenceSplitter` with configurable `CHUNK_SIZE` and `CHUNK_OVERLAP`. Each document node stores metadata including `file_name` and `uploaded_at`.

## File Upload Flow

1. Frontend uploads file to `/api/upload/file`
2. Backend saves to `uploads/` directory
3. Document is added to LlamaIndex via `add_document()`
4. Index is persisted to `combined_storage/`
5. Document becomes immediately available for queries

## API Endpoints Reference

- `GET /` - Root endpoint with system info
- `GET /health` - Health check
- `GET /api/documents` - List all documents
- `POST /api/upload/file` - Upload a document
- `POST /api/queries/` - Query documents (non-streaming)
- `POST /api/queries/stream` - Query with streaming response
- `POST /api/reports/` - Generate a report
- `WS /api/ws/` - WebSocket for real-time streaming
- `/docs` - Interactive API documentation (Swagger UI)
