# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LangChain + LlamaIndex insurance document intelligent Q&A system with a FastAPI backend and React + TypeScript frontend. The system enables real-time document-based question answering with streaming responses, report generation, and email delivery.

## Common Development Commands

### Backend (FastAPI)
```bash
# Install dependencies
cd backend
pip install -r requirements.txt
# OR using uv (preferred):
uv add -r requirements.txt

# Two-step startup (REQUIRED for first-time setup):
# Step 1: Initialize services and build document index
python init.py

# Step 2: Start the FastAPI server
python run.py
# OR directly:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Test CORS and WebSocket connectivity
python test_cors_ws.py

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

The backend follows a three-layer architecture with a dual framework integration:

**1. API Layer** (`backend/app/api/`)
- `documents.py` - Document CRUD operations and list management
- `queries.py` - Query endpoints (streaming and non-streaming) for Q&A
- `reports.py` - Report generation workflow with email delivery
- `upload.py` - File upload handling with automatic indexing
- `websocket.py` - WebSocket connections for real-time streaming responses

**2. Service Layer** (`backend/app/services/`)
- `llamaindex_service.py` - Vector retrieval and document indexing using LlamaIndex
  - Manages document indexing and persistence in `combined_storage/`
  - Handles semantic search and document retrieval with DashScope embeddings
  - Automatic chunking with configurable size and overlap
- `langchain_service.py` - LLM orchestration and response generation using LangChain
  - Chains for QA and structured report generation
  - Email delivery integration (simulated)
  - Streaming response generation

**3. Configuration Layer** (`backend/app/core/`)
- `config.py` - Centralized settings using Pydantic Settings
  - Loads from `.env` file in backend directory
  - Configures LLM models, embedding models, chunking parameters, and CORS settings

### Key Backend Flow

1. **Initialization** (two-step process):
   - Run `python init.py` to setup services, load existing index, and build index from documents in `uploads/`
   - Run `python run.py` to start the FastAPI server
   - The system loads persisted index from `backend/combined_storage/` if available

2. **Query Flow**:
   - Query API request → LlamaIndex retrieves relevant documents via semantic search
   - Retrieved context → LangChain generates answer using prompt engineering
   - Response returned with source document references

3. **Streaming Flow**:
   - WebSocket connection established on `ws://localhost:8000/api/ws`
   - LLM response streamed in real-time chunks
   - Frontend displays progressive response updates

4. **Report Flow**:
   - Query API → LlamaIndex retrieves relevant documents
   - LangChain generates structured answer
   - Report chain creates formatted report with sections
   - Save to `backend/reports/` and optionally send email

5. **Document Upload Flow**:
   - Frontend uploads file → Backend saves to `backend/uploads/`
   - Document added to LlamaIndex via `add_document()`
   - Index persisted to `backend/combined_storage/`
   - Document immediately available for queries

### Frontend Architecture

**Components** (`frontend/src/components/`)
- `QueryInterface.tsx` - Q&A interface with real-time streaming support
- `DocumentManager.tsx` - Document upload, list management, and indexing
- `ReportGenerator.tsx` - Report creation with email delivery options

**Services** (`frontend/src/services/`)
- `api.ts` - HTTP API client for backend communication
- `websocket.ts` - WebSocket client for real-time streaming

**Hooks** (`frontend/src/hooks/`)
- `useDocuments.ts` - Document management state and operations
- `useStreamingQuery.ts` - Real-time query state and WebSocket management

**Frontend Patterns:**
- Custom hooks for reusable logic and state management
- Class-based WebSocket manager for connection lifecycle management
- Automatic reconnection with exponential backoff (max 5 attempts)
- Server-Sent Events (SSE) parsing for HTTP streaming responses
- Environment variable configuration for flexible deployment
- Type-safe TypeScript interfaces for all API communications

**Key Technologies**: React 19, TypeScript, Vite, Tailwind CSS 4, Socket.IO client, Axios

### Data Types and Communication Patterns

**TypeScript Types** (`frontend/src/types/index.ts`):
- `SourceDocument` - Retrieved document chunks with metadata (content, file_name, score, page_number)
- `QueryResponse` - Complete query response (answer, sources, confidence, timestamp)
- `DocumentMetadata` - Document information (file_name, size, uploaded_at, indexed, chunks_count)
- `UploadResponse` - Upload confirmation (message, file_name, file_size, file_path, uploaded_at)
- `ReportRequest` - Report generation request (question, answer, sources, report_type, send_email)
- `ReportResponse` - Generated report info (report_id, report_content, timestamp, file_path, email_sent)
- `WebSocketMessage` - WebSocket message types (query, stream, status, error, sources, chunk, end, pong, connected)
- `QueryParams` - Query parameters (question, stream, top_k)
- `ConnectionStatus` - WebSocket connection state (connected, session_id, message)

**Communication Patterns:**
- HTTP requests use Axios with type-safe interfaces
- WebSocket messages follow structured format with type field for message routing
- Streaming responses use Server-Sent Events (SSE) with JSON data chunks
- All API responses include timestamps for tracking and debugging
- Connection status is continuously monitored and displayed in UI

## Important Implementation Details

### Dual Framework Architecture

This project uses **both** LlamaIndex and LangChain for different specialized purposes:

**LlamaIndex** (`llamaindex_service.py`):
- Vector storage and document indexing
- Semantic search and document retrieval
- Automatic document chunking with `SentenceSplitter`
- Uses DashScope API for embeddings (`DashScopeEmbedding`) and LLM (`DashScope`)
- Index persistence to `backend/combined_storage/`

**LangChain** (`langchain_service.py`):
- LLM orchestration and prompt engineering
- Response generation using `ChatTongyi` from `langchain_community`
- Structured chain composition for QA and reports
- Streaming response generation
- Email delivery integration (currently simulated)

The two frameworks complement each other: LlamaIndex handles the retrieval-augmented generation (RAG) pipeline, while LangChain manages the LLM interaction and response formatting.

### Index Persistence and Document Management

The vector index is persisted to `backend/combined_storage/` using LlamaIndex's storage system:
1. On startup, `init.py` attempts to load existing index from storage
2. If loading fails or no index exists, builds new index from documents in `backend/uploads/`
3. Newly uploaded documents are inserted into the existing index and persisted automatically
4. Documents are chunked using configurable `CHUNK_SIZE` (default: 1024) and `CHUNK_OVERLAP` (default: 100)

**Important Storage Paths**:
- `backend/uploads/` - Source documents for indexing
- `backend/combined_storage/` - Persisted vector index
- `backend/reports/` - Generated report files

### Async Design Patterns

The backend extensively uses async/await patterns:
- All service methods are async
- Blocking LLM calls use `asyncio.to_thread()` to avoid blocking the event loop
- WebSocket streaming uses async generators for real-time response chunks
- Document loading and indexing operations are non-blocking

This design ensures the FastAPI server can handle multiple concurrent requests without blocking.

### Environment Configuration

**Backend** (`backend/.env`):
- `DASHSCOPE_API_KEY` - Required for LLM and embedding API calls
- `STORAGE_DIR` - Vector index storage path (default: `./combined_storage`)
- `UPLOAD_DIR` - Document upload directory (default: `./uploads`)
- `REPORTS_DIR` - Report output directory (default: `./reports`)
- `CHUNK_SIZE` / `CHUNK_OVERLAP` - Document chunking parameters (default: 1024/100)
- `MAX_SEARCH_RESULTS` - Number of documents to retrieve per query (default: 5)
- `LLM_MODEL` - Model name for LLM (default: "deepseek-v3")
- `TEMPERATURE` / `TOP_P` - LLM generation parameters (default: 0.1/0.8)

**Frontend** (`frontend/.env`):
- `VITE_API_URL` - Backend API base URL (default: `http://localhost:8000`)
- `VITE_WS_URL` - WebSocket connection URL (default: `ws://localhost:8000/api/ws/`)

### CORS and WebSocket Configuration

CORS is handled using FastAPI's standard `CORSMiddleware` in `main.py`:
- Origins configured in `settings.ALLOWED_ORIGINS` (includes localhost ports 3000, 5173, 5174, 8080)
- All methods, headers, and credentials are allowed
- Exposes all headers for client access

WebSocket connections are handled via `websocket.py`:
- Single WebSocket endpoint at `/api/ws/`
- Connection management with session tracking
- Real-time streaming of LLM responses
- Automatic disconnection handling

### Document Processing Pipeline

Documents are processed automatically upon upload:
1. File received at `/api/upload/file` endpoint
2. Document parsed (supports PDF, TXT, MD, DOCX formats)
3. Automatic chunking using LlamaIndex's `SentenceSplitter`
4. Each chunk becomes a document node with metadata:
   - `file_name` - Original filename
   - `uploaded_at` - Upload timestamp
   - Additional file metadata
5. Vectors generated using DashScope embeddings
6. Index updated and persisted to storage

## API Endpoints Reference

### HTTP Endpoints
- `GET /` - Root endpoint with system info and version
- `GET /health` - Health check endpoint
- `GET /api/documents` - List all indexed documents with metadata
- `POST /api/upload/file` - Upload a document (auto-indexes)
- `POST /api/queries/` - Query documents (non-streaming response)
- `POST /api/queries/stream` - Query documents (streaming HTTP response)
- `POST /api/reports/` - Generate and optionally email a report

### WebSocket Endpoints
- `WS /api/ws/` - Real-time streaming connection for query responses

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## Troubleshooting and Debugging

### Common Issues and Solutions

**1. Backend startup fails with import errors**
```bash
# Ensure dependencies are installed
cd backend
pip install -r requirements.txt
# Or using uv:
uv add -r requirements.txt
```

**2. Index loading fails or queries return no results**
```bash
# Rebuild the index
cd backend
python init.py
```

**3. WebSocket connection fails**
- Check backend is running on port 8000
- Verify frontend `.env` has correct `VITE_WS_URL`
- Run connectivity test: `python backend/test_cors_ws.py`
- Check browser console for WebSocket error messages

**4. CORS errors in browser**
- Verify `backend/.env` has correct `DASHSCOPE_API_KEY`
- Check that frontend URL is in `settings.ALLOWED_ORIGINS` list
- Ensure backend CORS middleware is properly configured

**5. DashScope API errors**
- Verify API key is valid and has sufficient quota
- Check internet connectivity to DashScope endpoints
- Review backend logs for specific API error messages

### Testing and Validation

**Backend connectivity test:**
```bash
# Test CORS and WebSocket connectivity
cd backend
python test_cors_ws.py
```

**Frontend debugging:**
- Open browser DevTools Console for WebSocket and API errors
- Network tab shows HTTP requests and responses
- React DevTools for component state inspection

**Backend debugging:**
- Check console output for initialization messages
- Review logs for API call details and errors
- Use Swagger UI (`/docs`) to test endpoints directly

## Development Workflow and Conventions

### Project-Specific Patterns

**File Organization:**
- Backend code follows FastAPI patterns with separate API, service, and configuration layers
- Frontend uses React 19 with TypeScript and functional components
- All async functions use `async/await` consistently
- Error handling uses FastAPI's exception handling middleware

**Service Initialization Pattern:**
The backend uses a two-step initialization pattern:
1. **init.py**: Sets up LlamaIndex and LangChain services, loads/builds document index
2. **run.py**: Starts the FastAPI server with proper configuration

This separation ensures services are ready before the server accepts requests.

**WebSocket Connection Management:**
- WebSocket connections use session-based management
- Frontend implements automatic reconnection with exponential backoff
- Connection status is displayed in the QueryInterface component
- Streamed responses are chunked and appended to the response text

**Error Handling Strategy:**
- Global exception handler in `main.py` catches unexpected errors
- Service methods use try-except blocks with detailed error messages
- Frontend displays user-friendly error messages
- Logs contain detailed error information for debugging

### Making Changes

**Backend Development:**
1. Modify code in appropriate layer (API, service, or config)
2. If service logic changed, ensure `init.py` still initializes correctly
3. Test using `python backend/test_cors_ws.py` for connectivity
4. Use Swagger UI (`/docs`) to test API endpoints
5. Check backend logs for errors and warnings

**Frontend Development:**
1. Modify components, services, or hooks as needed
2. Ensure environment variables are properly used (no hardcoded URLs)
3. Test WebSocket connection status in QueryInterface
4. Verify responsive design on different screen sizes
5. Check browser console for errors and warnings

**Adding New Features:**
- Follow existing three-layer architecture for backend
- Create corresponding frontend components and services
- Update TypeScript types in `frontend/src/types/index.ts`
- Test with both streaming and non-streaming endpoints
- Add appropriate error handling and user feedback

### Key Dependencies and Versions

**Backend:**
- FastAPI 0.104+ for async web framework
- LlamaIndex 0.9+ for document indexing and retrieval
- LangChain 0.1+ for LLM orchestration
- DashScope SDK for AI model access

**Frontend:**
- React 19+ for UI framework
- TypeScript 5.9+ for type safety
- Vite 8+ for build tooling
- Socket.IO Client 4.8+ for WebSocket communication
- Axios for HTTP requests
