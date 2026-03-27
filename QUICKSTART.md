# 快速开始指南

## 🚀 5分钟快速启动

### 1. 环境准备

确保已安装：
- Python 3.11+
- Node.js 18+
- Docker 和 Docker Compose（可选）

### 2. 配置 API Key

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入您的 DashScope API Key
# DASHSCOPE_API_KEY=your_api_key_here
```

### 3. 上传测试文档

将 `sample-docs/` 目录下的测试文档复制到 `backend/uploads/`：

```bash
# 创建上传目录
mkdir -p backend/uploads

# 复制测试文档
cp sample-docs/*.txt backend/uploads/
```

### 4. 启动服务

#### 方式一：使用 Docker Compose（推荐）

```bash
docker-compose up -d
```

服务将运行在：
- 前端：http://localhost:5173
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs

#### 方式二：本地开发

**启动后端：**
```bash
cd backend
pip install -r requirements.txt
python init.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**启动前端：**
```bash
cd frontend
npm install
npm run dev
```

### 5. 使用应用

1. **打开浏览器**访问 http://localhost:5173

2. **文档管理**
   - 切换到「文档管理」标签
   - 上传保险文档（支持 .txt, .pdf, .md）
   - 等待索引完成

3. **智能问答**
   - 切换到「智能问答」标签
   - 输入问题，例如："什么是雇主责任险？"
   - 查看实时流式回答和参考文档

4. **报告生成**
   - 切换到「报告生成」标签
   - 填写问题和答案
   - 生成分析报告

## 💡 示例问题

基于提供的测试文档，您可以尝试以下问题：

1. "雇主责任险的保障范围是什么？"
2. "意外伤害险有哪些主要保障？"
3. "如何选择合适的医疗保险？"
4. "医疗保险的理赔流程是怎样的？"
5. "投保医疗保险需要注意什么？"

## 📊 查看系统状态

### 后端健康检查
```bash
curl http://localhost:8000/health
```

### 查看文档列表
访问后端 API 文档：http://localhost:8000/docs

### 测试 WebSocket 连接
在浏览器中打开开发者工具，进入 QueryInterface，检查 Console 中的 WebSocket 消息。

## 🐛 常见问题

### 1. 后端启动失败
**问题**：`ModuleNotFoundError: No module named 'llama_index'`
**解决**：
```bash
cd backend
pip install -r requirements.txt
```

### 2. 前端连接失败
**问题**：CORS 错误或连接被拒绝
**解决**：确保后端正在运行，检查 `frontend/.env` 中的 API 地址配置。

### 3. DashScope API 错误
**问题**：API Key 无效或超出限额
**解决**：检查 `.env` 文件中的 `DASHSCOPE_API_KEY` 是否正确配置。

### 4. 文档索引失败
**问题**：上传文档后索引失败
**解决**：
- 检查文档格式是否支持
- 查看后端日志获取详细错误信息
- 尝试手动重建索引

## 🔧 高级配置

### 自定义 LLM 参数

编辑 `backend/app/core/config.py`：

```python
LLM_MODEL = "deepseek-v3"
TEMPERATURE = 0.1
TOP_P = 0.8
```

### 修改文档分块参数

```python
CHUNK_SIZE = 1024
CHUNK_OVERLAP = 100
MAX_SEARCH_RESULTS = 5
```

### 调整 CORS 设置

```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
]
```

## 📈 性能优化

### 1. 使用向量数据库
对于大量文档，建议使用专业向量数据库：
- Pinecone
- Milvus
- Qdrant
- Chroma

### 2. 缓存常用查询
在 LangChain 中添加缓存层以减少 API 调用。

### 3. 异步处理
实现文档上传的异步处理，避免阻塞用户界面。

## 🚀 生产部署

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://frontend:5173;
    }

    location /api/ {
        proxy_pass http://backend:8000;
    }

    location /api/ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 环境变量

确保在生产环境中设置以下变量：
- `DASHSCOPE_API_KEY` - API 密钥
- `DEBUG=false` - 关闭调试模式
- `ALLOWED_ORIGINS` - 允许的域名

## 📚 进一步学习

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [React 官方文档](https://react.dev/)
- [LlamaIndex 文档](https://docs.llamaindex.ai/)
- [LangChain 文档](https://python.langchain.com/)

## 🆘 获取帮助

遇到问题？请查看：

1. **README.md** - 完整项目文档
2. **VERIFICATION.md** - 验证指南
3. **后端日志** - `docker-compose logs backend`
4. **前端日志** - 浏览器开发者工具 Console

---

准备好开始了吗？按照上面的步骤启动服务，然后访问 http://localhost:5173 开始体验！