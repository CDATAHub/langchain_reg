# CORS 和 WebSocket 问题修复说明

## 修复内容

### 1. CORS 配置修复

#### 问题
- 自定义的 `SimpleCORSMiddleware` 没有正确处理 OPTIONS 预检请求
- CORS 头的添加方式不够规范

#### 修复
- 移除了自定义的 `SimpleCORSMiddleware` 类
- 使用 FastAPI 标准的 `CORSMiddleware`
- 正确配置了所有必要的 CORS 参数

#### 修改的文件
- `backend/app/main.py`

#### 修改详情
```python
# 之前：自定义中间件
app.add_middleware(SimpleCORSMiddleware)

# 修复后：标准中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

---

### 2. WebSocket 配置修复

#### 问题
- `queries.py` 和 `websocket.py` 中存在重复的 WebSocket 路由定义
- 可能导致路由冲突
- 前端 WebSocket URL 硬编码，不够灵活

#### 修复
- 移除了 `queries.py` 中的重复 WebSocket 路由和 ConnectionManager
- 保留 `websocket.py` 作为唯一的 WebSocket 实现
- 更新前端环境变量配置
- 前端组件使用环境变量而不是硬编码 URL

#### 修改的文件
- `backend/app/api/queries.py` - 移除 WebSocket 相关代码
- `frontend/.env` - 更新 WebSocket URL
- `frontend/src/components/QueryInterface.tsx` - 使用环境变量

#### 修改详情

**queries.py (清理前):**
```python
@router.websocket("/ws/{session_id}")  # 重复的路由
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    # ... 处理 WebSocket
```

**queries.py (清理后):**
```python
# 只保留 HTTP 路由
@router.post("/", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    # ...

@router.post("/stream")
async def query_stream(request: QueryRequest):
    # ...
```

**前端环境变量:**
```env
# 之前
VITE_WS_URL=ws://localhost:8000

# 修复后
VITE_WS_URL=ws://localhost:8000/api/ws
```

**前端组件:**
```typescript
// 之前
wsRef.current = new WebSocketManager('ws://localhost:8000/api/ws', {...})

// 修复后
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/ws';
wsRef.current = new WebSocketManager(WS_URL, {...})
```

---

## 验证修复

### 运行测试脚本
```bash
cd backend
python test_cors_ws.py
```

测试脚本会验证：
1. 健康检查端点
2. CORS 头是否正确配置
3. WebSocket 连接是否正常

### 手动测试

#### 测试 CORS
1. 启动后端服务
2. 在浏览器中访问 `http://localhost:8000/docs`
3. 打开浏览器开发者工具 → Network
4. 发送一个 API 请求
5. 检查响应头中是否有正确的 CORS 头：
   - `Access-Control-Allow-Origin`
   - `Access-Control-Allow-Methods`
   - `Access-Control-Allow-Headers`
   - `Access-Control-Allow-Credentials`

#### 测试 WebSocket
1. 启动后端和前端服务
2. 打开前端应用 `http://localhost:5173`
3. 进入"智能问答"页面
4. 检查页面顶部的 WebSocket 连接状态指示器
5. 应该显示绿色的"实时连接已建立"
6. 提交一个问题，观察是否收到实时流式回答

---

## 后端启动步骤

### 完整启动流程
```bash
# 1. 进入后端目录
cd backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化服务（如果需要）
python init.py

# 4. 启动后端
python run.py
# 或
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Compose 启动
```bash
# 确保在项目根目录
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

---

## 前端启动步骤
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

---

## 注意事项

1. **环境变量**：确保 `.env` 文件中 `DASHSCOPE_API_KEY` 已正确配置
2. **端口配置**：
   - 后端默认端口：8000
   - 前端默认端口：5173
   - WebSocket 路径：`ws://localhost:8000/api/ws`
3. **CORS 配置**：确保 `settings.ALLOWED_ORIGINS` 包含前端开发服务器的 URL
4. **WebSocket 重连**：前端实现了自动重连机制，最多尝试 5 次
5. **文档索引**：首次启动时，确保 `backend/uploads/` 目录中有文档，或者通过前端上传文档

---

## 故障排查

### CORS 错误
如果遇到 CORS 错误：
1. 检查 `.env` 文件中的 `ALLOWED_ORIGINS` 配置
2. 确保前端 URL 在允许的来源列表中
3. 查看后端日志中的 CORS 相关信息

### WebSocket 连接失败
如果 WebSocket 连接失败：
1. 检查后端是否正在运行
2. 确认 WebSocket URL 配置正确（应为 `ws://localhost:8000/api/ws`）
3. 检查浏览器控制台的错误信息
4. 验证是否有防火墙或代理阻止 WebSocket 连接

### 文档查询无结果
如果查询没有返回结果：
1. 检查 `backend/uploads/` 目录中是否有文档
2. 运行 `python init.py` 重新构建索引
3. 查看后端日志中的检索相关信息
