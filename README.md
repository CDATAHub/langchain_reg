# LangChain + LlamaIndex 保险文档智能问答系统

一个基于 FastAPI + React 的现代化 Web 应用，用于保险文档的智能问答、报告生成和邮件发送。

## 🚀 功能特性

### 核心功能
- **智能问答**：基于上传的保险文档进行实时问答
- **实时流式回答**：支持 WebSocket 实时流式响应
- **文档管理**：支持上传、管理和索引 PDF、TXT、MD 文档
- **报告生成**：自动生成结构化分析报告
- **邮件发送**：报告通过邮件发送给指定收件人
- **向量检索**：使用 LlamaIndex 进行语义搜索
- **响应式设计**：适配桌面和移动设备

### 技术栈
- **后端**：FastAPI, LlamaIndex, LangChain, DashScope API
- **前端**：React + TypeScript, Vite, Tailwind CSS, Socket.IO
- **部署**：Docker + Docker Compose

## 📁 项目结构

```
langchain_reg/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── services/      # 核心服务
│   │   ├── schemas/       # Pydantic 模型
│   │   └── core/          # 配置文件
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/   # React 组件
│   │   ├── services/     # API 客户端
│   │   ├── hooks/        # 自定义 Hooks
│   │   └── types/        # TypeScript 类型定义
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml      # 服务编排
├── .env.example           # 环境变量模板
└── README.md             # 项目文档
```

## 🛠️ 快速开始

### 1. 环境准备

#### 后端环境变量
复制 `.env.example` 为 `.env` 并配置 API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件，添加您的 DashScope API Key：

```env
DASHSCOPE_API_KEY=your_api_key_here
```

#### 前端环境变量
创建 `.env` 文件（如果需要修改 API 地址）：

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 2. 使用 Docker Compose（推荐）

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 3. 本地开发

#### 启动后端
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 启动前端
```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 查看前端应用。

## 📖 使用指南

### 1. 文档管理
1. 进入「文档管理」标签页
2. 点击「上传文档」按钮上传 PDF、TXT 或 MD 文件
3. 上传后文档会自动进行索引
4. 可以手动「重建索引」来重新处理所有文档

### 2. 智能问答
1. 进入「智能问答」标签页
2. 输入关于保险产品的问题
3. 选择「实时回答」来获得流式响应
4. 查看参考文档和答案的置信度

### 3. 报告生成
1. 在「报告生成」标签页填写问题和答案
2. 选择报告类型（结构化/详细）
3. 可选择通过邮件发送报告
4. 查看和管理历史报告

## 🔧 API 文档

后端 API 文档可在 http://localhost:8000/docs 查看。

### 主要 API 端点

- `GET /api/documents` - 获取文档列表
- `POST /api/upload/file` - 上传文档
- `POST /api/query/` - 普通查询
- `POST /api/query/stream` - 流式查询
- `POST /api/report/` - 生成报告
- `GET /api/ws/` - WebSocket 连接

## 🏗️ 架构说明

### 后端架构
```
FastAPI
├── API 路由层
│   ├── documents.py  - 文档管理
│   ├── queries.py    - 查询接口
│   ├── reports.py    - 报告生成
│   ├── upload.py     - 文件上传
│   └── websocket.py  - WebSocket
├── 服务层
│   ├── llamaindex_service.py - 向量检索
│   └── langchain_service.py  - LLM 编排
└── 配置层
    └── config.py     - 应用配置
```

### 前端架构
```
React + TypeScript
├── 组件层
│   ├── QueryInterface.tsx    - 问答界面
│   ├── DocumentManager.tsx   - 文档管理
│   └── ReportGenerator.tsx  - 报告生成
├── 服务层
│   ├── api.ts               - HTTP API 客户端
│   └── websocket.ts         - WebSocket 客户端
└── 钩子层
    ├── useStreamingQuery.ts  - 流式查询钩子
    └── useDocuments.ts      - 文档管理钩子
```

## 🚀 部署

### 生产环境部署

1. **准备环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 配置生产环境参数
   ```

2. **构建镜像**
   ```bash
   docker-compose build
   ```

3. **启动服务**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://frontend:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /api/ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 🧪 测试

### 后端测试
```bash
cd backend
pytest tests/
```

### 前端测试
```bash
cd frontend
npm test
```

## 📋 待办事项

- [ ] 添加用户认证系统
- [ ] 实现多租户支持
- [ ] 添加缓存层
- [ ] 实现文件批量上传
- [ ] 添加搜索功能
- [ ] 实现日志聚合
- [ ] 添加性能监控

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果您遇到问题或有建议，请：

1. 查看 [Issues](https://github.com/your-repo/issues)
2. 创建新的 Issue
3. 联系维护者

---

**Note**: 本项目需要有效的 DashScope API Key 才能正常运行。请确保在部署前正确配置 API Key。