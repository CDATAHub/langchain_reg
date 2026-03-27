# Verification Guide

This guide helps you verify the implementation of the FastAPI web application.

## Backend Verification

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Environment Variables
Create a `.env` file in the backend directory:
```env
DASHSCOPE_API_KEY=your_api_key_here
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### 3. Initialize Services
```bash
python init.py
```

Expected output:
```
🚀 Initializing LangChain + LlamaIndex Insurance Document Q&A System
==================================================

Step 1: Setting up LlamaIndex...
✅ LlamaIndex initialized successfully

Step 2: Setting up LangChain...
✅ LangChain initialized successfully

Step 3: Checking for documents...
No documents found in upload directory

Step 4: Checking existing index...
Index status: {'indexed': False, 'document_count': 0, 'last_updated': None, 'storage_path': './combined_storage'}

==================================================
✅ All services initialized successfully!
```

### 4. Start Backend Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```
Expected response:
```json
{"status":"healthy","timestamp":"2024-03-26T..."}
```

#### API Documentation
Visit http://localhost:8000/docs to see the Swagger UI.

#### Test Document Upload
Create a test document `test.txt`:
```bash
echo "这是一个测试文档。测试内容关于保险产品。" > test.txt
```

Then upload it:
```bash
curl -X POST "http://localhost:8000/api/upload/file" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.txt" \
  -F "index_after_upload=true"
```

#### Test Query
```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{"question":"保险是什么？","stream":false}'
```

## Frontend Verification

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Frontend
```bash
npm run dev
```

### 3. Test Frontend Features

#### Document Management
1. Open http://localhost:5173
2. Navigate to "文档管理" tab
3. Upload a test document
4. Verify it appears in the document list

#### Query Interface
1. Navigate to "智能问答" tab
2. Enter a question about insurance
3. Submit the query
4. Verify the response appears

#### Report Generation
1. Navigate to "报告生成" tab
2. Fill in question and answer
3. Generate a report
4. Verify it appears in the history

## Docker Verification

### 1. Build and Start Services
```bash
docker-compose up -d
```

### 2. Check Service Status
```bash
docker-compose ps
```

### 3. Test Services
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## WebSocket Verification

### 1. Test WebSocket Connection
Use the browser's developer tools to check the WebSocket connection in the QueryInterface.

### 2. Test Real-time Communication
1. Open the browser's console
2. Navigate to the QueryInterface
3. Submit a query
4. Check for WebSocket messages in the console

## Common Issues

### 1. Backend Import Errors
If you encounter import errors, ensure you're running from the correct directory:
```bash
cd backend
python init.py
```

### 2. DASHSCOPE API Key Missing
```bash
export DASHSCOPE_API_KEY=your_key_here
```

### 3. Frontend CORS Errors
The backend should automatically handle CORS for localhost:5173.

### 4. WebSocket Connection Failed
Check that the backend is running on port 8000 and the frontend environment variables are set correctly.

## Performance Testing

### 1. Document Upload Test
```bash
# Create a large test file
dd if=/dev/zero of=large_test.txt bs=1M count=10

# Time the upload
time curl -X POST "http://localhost:8000/api/upload/file" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@large_test.txt"
```

### 2. Query Response Time
```bash
time curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{"question":"保险是什么？","stream":false}'
```

### 3. Multiple Concurrent Queries
```bash
# Open multiple terminals and run queries simultaneously
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{"question":"什么是寿险？","stream":false}'
```

## Security Verification

### 1. Input Validation
Test with invalid inputs:
- Empty queries
- Very long queries
- Special characters in file names

### 2. File Upload Security
- Test with different file extensions
- Test with large files
- Test with potentially malicious content

### 3. API Rate Limiting
The backend should handle multiple requests gracefully.

## Integration Testing Checklist

- [ ] Backend starts successfully
- [ ] Frontend starts successfully
- [ ] Documents can be uploaded
- [ ] Documents are indexed correctly
- [ ] Queries return relevant answers
- [ ] Streaming responses work
- [ ] Reports can be generated
- [ ] WebSocket connections work
- [ ] All endpoints return appropriate status codes
- [ ] Error handling works correctly

## Deployment Verification

### 1. Production Build
```bash
cd frontend
npm run build
```

### 2. Docker Production Build
```bash
docker-compose -f docker-compose.yml up -d --build
```

### 3. Health Check
```bash
curl http://localhost:8000/health
```

## Monitoring and Logging

### 1. Check Logs
```bash
# Backend logs
docker-compose logs backend

# Frontend logs
docker-compose logs frontend
```

### 2. Monitor Performance
- CPU and memory usage
- Response times
- Error rates
- WebSocket connections

## Conclusion

If all tests pass, your FastAPI web application is ready for production!