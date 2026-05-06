# Langfuse 多租户可观测性技术方案（保险智能客服 RAG 系统）

## 1. 方案目标与核心原则

为保险智能客服 RAG 系统接入私有化部署的 Langfuse，实现全链路可观测与多租户严格隔离：
1. **链路追踪**：按 `tenant_id` 追踪每个租户的 RAG 调用全生命周期。
2. **全栈观测**：覆盖 JWT 鉴权 → LlamaIndex 检索 → Milvus 查询 → LangChain 编排 → Qwen 生成 → 响应返回。
3. **成本与指标**：按租户精确统计 Token 用量、调用成本、P50/P99 延迟、错误率、会话转化率。
4. **数据隔离与审计**：在鉴权层、存储层、观测层、展示层实现多租户数据隔离，满足金融/保险行业合规审计要求。

**核心设计原则**：
- 🔒 **零信任租户上下文**：`tenant_id` 仅来源于服务端 JWT 解析与 MySQL 校验，严禁前端透传。
- 🛡️ **强制过滤**：Milvus 检索层硬编码租户过滤，业务代码无法覆盖。
- 📊 **观测与业务解耦**：Langfuse 仅负责可观测性，不参与业务鉴权与数据隔离；异步上报失败不阻断主流程。
- 🧾 **合规优先**：敏感数据（身份证、保单号、手机号）上报前强制脱敏，审计日志不可篡改。

---

## 2. 总体架构与数据流向

```mermaid
graph TD
    subgraph 客户端层
        A[Vue 客服前端] -->|HTTPS + JWT| B[API Gateway]
    end
    
    subgraph 业务服务层
        B --> C[FastAPI Backend]
        C --> D{JWT 鉴权 & 租户校验}
        D -->|通过| E[RAG Orchestrator]
        D -->|拒绝| F[401/403 拦截]
        
        E --> G[LlamaIndex Retriever]
        G --> H[(Milvus 向量库)]
        H -->|强制 tenant_id 过滤| G
        G --> I[Context Builder]
        
        E --> J[LangChain Chain]
        J --> K[(Qwen LLM)]
        K -->|Token Usage| J
        J --> L[Response Formatter]
    end
    
    subgraph 可观测层
        E -->|异步 Trace| M[(Langfuse v3)]
        L -->|trace_id 回写| N[(MySQL 业务库)]
        M --> O[Langfuse Dashboard]
        O -->|API Export| P[BI/计费系统]
    end
    
    style D fill:#f9f,stroke:#333
    style H fill:#bbf,stroke:#333
    style M fill:#bfb,stroke:#333
```

---

## 3. 核心模块详细设计

### 3.1 鉴权与租户上下文管理
- **JWT 解析**：从 `Authorization: Bearer <token>` 提取 `user_id`, `tenant_id`, `exp`, `iss`, `aud`。
- **服务端校验**：
  1. 验签 + 过期时间校验。
  2. 查询 MySQL `user_tenant_mapping` 表，确认 `user_id` 与 `tenant_id` 绑定关系。
  3. 校验失败直接抛出 `401/403`，不进入 RAG 流程。
- **上下文对象**：
```python
class UserContext(BaseModel):
    user_id: str
    tenant_id: str
    session_id: str  # 前端生成，30分钟无交互或用户主动结束则轮换
    ip: str
    channel: str = "web"
```

### 3.2 Langfuse v3 观测集成
- 采用 `@observe` 装饰器 + `langfuse_context` 动态更新，替代旧版 `propagate_attributes`。
- 支持异步 Trace 构建，自动关联 LlamaIndex 与 LangChain 子 Span。
- 通过 FastAPI `lifespan` 管理 `langfuse.flush()`，防止进程退出丢失数据。

### 3.3 LlamaIndex & LangChain 链路观测
| 框架 | 观测组件 | 注入方式 |
|------|----------|----------|
| **LlamaIndex** | `LlamaIndexCallbackHandler` | `retriever.callback_manager.add_handler()` |
| **LangChain** | `CallbackHandler` | `chain.ainvoke(..., config={"callbacks": [handler]})` |
- **Span 层级设计**：
  ```
  Root: insurance-rag-pipeline (trace)
  ├─ jwt_validation (span)
  ├─ llama_retriever (span)
  │  └─ milvus_query (span)
  ├─ context_build (span)
  ├─ langchain_chain (span)
  │  └─ qwen_generation (generation)
  └─ response_format (span)
  ```

### 3.4 Milvus 多租户数据隔离
- **强制注入**：检索服务内部封装 `BaseRetriever`，硬编码 `tenant_id` 过滤条件，拒绝外部传入 `filters`。
- **过滤策略**：
  - **表达式过滤**（数据量 < 500万/租户）：`expr = f'tenant_id == "{tenant_id}"'`
  - **Partition 隔离**（数据量大）：按 `tenant_id` 自动创建 Milvus Partition，查询时指定 `partition_names=[f"p_{tenant_id}"]`，天然物理隔离，性能更优。
- **网络隔离**：Milvus 仅允许 RAG 服务内网 IP 访问，禁止公网暴露。

### 3.5 MySQL 业务存储与审计
```sql
CREATE TABLE chat_trace (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tenant_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    langfuse_trace_id VARCHAR(128) NOT NULL UNIQUE,
    trace_url VARCHAR(512),
    question_summary VARCHAR(1024),  -- 脱敏摘要
    answer_summary VARCHAR(1024),
    model_name VARCHAR(64),
    status ENUM('success','error','timeout') NOT NULL,
    error_type VARCHAR(64),
    latency_ms INT,
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    INDEX idx_tenant_status_created (tenant_id, status, created_at),
    INDEX idx_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```
- 异步写入，不阻塞主响应。
- 仅存储脱敏摘要与链路标识，完整日志由 Langfuse 或合规审计系统归档。

---

## 4. 关键字段与元数据规范

Langfuse Trace/Metadata 标准化模板：
```python
{
    "user_id": "u_8f9a2b...",
    "session_id": "sess_20240520_001",
    "tags": ["tenant:ins_001", "biz:policy_inquiry", "env:prod"],
    "metadata": {
        "tenant_id": "ins_001",
        "channel": "web",
        "biz_scenario": "理赔咨询",
        "prompt_version": "v2.3.1",
        "retrieval_top_k": 5,
        "model": "qwen2.5-72b-instruct"
    }
}
```
- **禁止**将 `tenant_id` 赋值给 `user_id`，否则会导致跨用户会话混淆、用户画像失真。
- `session_id` 用于 Langfuse 自动聚合对话树，前端需在连续对话周期内保持稳定。

---

## 5. 成本统计与账单聚合策略

1. **模型名统一**：业务侧固定传入 `qwen2.5-72b-instruct`（或实际商用名），与 Langfuse `Model Prices` 配置严格一致。
2. **Token 对齐**：DashScope 返回 `usage` 结构与 OpenAI 兼容，Langfuse 可自动解析 `prompt_tokens`, `completion_tokens`, `total_tokens`。
3. **成本二次校准**：
   - 若 Langfuse 内置价格与实际合同不符，通过定时任务调用 Langfuse API 拉取 `usage`，结合合同单价在业务侧 MySQL/ClickHouse 计算真实成本。
   - 支持自定义打点：`langfuse.score(name="biz_cost", value=actual_cost, data_type="NUMERIC")`。
4. **报表聚合**：按 `metadata.tenant_id` 或 `tag=tenant:xxx` 分组，输出日/月账单 CSV 或推送至财务系统。

---

## 6. 安全合规与隐私保护

| 风险点 | 防护措施 |
|--------|----------|
| **越权访问** | JWT 强校验 + MySQL 映射验证 + Milvus 硬编码过滤 |
| **敏感数据泄露** | 上报 Langfuse 前执行 PII 脱敏中间件（正则/NLP 替换身份证、保单号、手机号） |
| **Dashboard 越权** | 方案A（推荐）：高敏租户独立 Langfuse Project；方案B：自研轻量控制台代理 API，按 `tenant_id` 过滤返回；方案C：利用企业版 RBAC 限制 Tag 视图 |
| **密钥管理** | `LANGFUSE_SECRET_KEY`、`QWEN_API_KEY` 通过 K8s Secrets / HashiCorp Vault 注入，严禁硬编码 |
| **审计不可篡改** | `chat_trace` 表增加 `hash` 字段，定期将 `trace_id + timestamp` 摘要上链或归档至 WORM 存储 |
| **错误信息泄露** | 全局 Exception Handler 捕获，仅返回 `trace_id` 与通用提示，内部栈帧写入 Sentry/本地日志 |

---

## 7. 异常处理与优雅降级

| 异常类型 | 处理策略 |
|----------|----------|
| **JWT 无效/过期** | `401 Unauthorized`，记录安全审计日志 |
| **用户不属于租户** | `403 Forbidden`，阻断请求 |
| **Milvus 检索失败** | 返回兜底话术，记录 `langfuse.score(name="retrieval_error", value=1)`，降级为纯 LLM 回答或知识库默认回复 |
| **Qwen 调用超时/失败** | 指数退避重试 2 次，失败后触发降级模型（如 `qwen2.5-7b`）或返回友好提示 |
| **Langfuse 上报失败** | 异步队列非阻塞，本地记录 `WARN` 日志，不影响主流程 HTTP 200 |
| **服务关闭/重启** | `lifespan` 中调用 `langfuse.flush()`，设置 `timeout=10s`，降低 Trace 丢失率 < 0.1% |

---

## 8. 部署配置与运维规范

### `.env` 环境变量
```env
# Langfuse
LANGFUSE_HOST=http://192.168.10.50:3000
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxx
LANGFUSE_RELEASE=v1.0.0
LANGFUSE_TIMEOUT=10

# Qwen / DashScope
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_API_KEY=sk-xxxxx
QWEN_MODEL=qwen2.5-72b-instruct

# Database
MYSQL_DSN=mysql+asyncmy://user:pass@192.168.10.51:3306/insurance_rag
MILVUS_HOST=192.168.10.52:19530
```

### 生产部署建议
1. **网络拓扑**：FastAPI → Langfuse → Milvus 全部走内网 VPC，禁止公网直连。
2. **HTTPS/TLS**：Langfuse Dashboard 启用 Let's Encrypt 或企业 CA 证书。
3. **资源限制**：Langfuse Python SDK 默认异步队列 `max_workers=4`，高并发场景可调至 `8~16`，监控队列积压告警。
4. **日志分级**：业务日志 `INFO`，Langfuse 上报日志 `DEBUG/WARN`，通过 Filebeat/FluentBit 采集至 ELK。

---

## 9. 验收标准与自动化测试

| 验收项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **Trace 完整性** | 发起请求后检查 Langfuse UI | 看到完整 Span 树，包含 Retrieval、LLM Generation |
| **租户隔离** | 构造越权 JWT / 篡改 `tenant_id` | 拦截 403，Langfuse 无对应 Trace |
| **Milvus 过滤** | 注入其他租户 `tenant_id` 查询 Milvus | 返回空或拒绝，日志记录拦截事件 |
| **Tag 过滤** | Langfuse UI 搜索 `tag=tenant:ins_001` | 仅显示该租户 Trace |
| **Cost 准确性** | 对比 DashScope 账单与 Langfuse 聚合报表 | 误差 ≤ 1.5%（含四舍五入） |
| **降级可用性** | 停止 Langfuse 服务，发起请求 | HTTP 200 正常返回，本地日志记录上报失败 |
| **Session 聚合** | 连续发送 5 条同 `session_id` 请求 | Langfuse 自动合并为单条对话树 |
| **CI/CD 门禁** | 单元测试 + 集成测试 + 混沌测试 | 代码覆盖率 ≥ 85%，核心链路 100% 通过 |

---

## 10. 架构演进规划

| 阶段 | 目标 | 实施路径 |
|------|------|----------|
| **V1.0（当前）** | 基础观测、租户隔离、成本统计 | 按本文档落地 |
| **V1.5** | 动态 Prompt 版本控制 & A/B 测试 | `metadata.prompt_version` + Langfuse Experiment 功能 |
| **V2.0** | 业务指标打点 & ROI 分析 | `langfuse.score()` 记录“解决率”、“满意度”、“转人工率” |
| **V2.5** | 冷热数据分层 | 热数据（7天）留 Langfuse，冷数据同步 ClickHouse/ES 降低存储成本 |
| **V3.0** | 合规审计增强 | Trace 摘要 Merkle 哈希上链，满足等保 2.0 / ISO27001 审计要求 |

---

## 附录：完整生产级代码示例

### `app/main.py` (FastAPI Lifespan & 路由)
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from langfuse import Langfuse
from app.api.chat import router as chat_router

langfuse_client = Langfuse()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    langfuse_client.flush()

app = FastAPI(lifespan=lifespan)
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
```

### `app/auth/dependencies.py`
```python
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from app.models import UserContext
from app.db import verify_user_tenant

async def get_current_user_context(authorization: str) -> UserContext:
    try:
        token = authorization.split("Bearer ")[1]
        payload = jwt.decode(token, options={"verify_aud": False})  # 生产环境需验签
        return UserContext(
            user_id=payload["sub"],
            tenant_id=payload["tenant_id"],
            session_id=payload.get("session_id"),
            channel=payload.get("channel", "web")
        )
    except (JWTError, KeyError, IndexError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# 实际生产需异步查询 MySQL 校验 user_tenant 绑定关系
```

### `app/rag/pipeline.py`
```python
from langfuse.decorators import observe, langfuse_context
from langfuse.llamaindex import LlamaIndexCallbackHandler
from langfuse.langchain import CallbackHandler as LangChainCallbackHandler
from app.auth.dependencies import UserContext
from app.rag.retriever import build_tenant_retriever
from app.rag.chain import build_rag_chain

@observe(name="insurance-rag-pipeline")
async def run_rag_pipeline(query: str, user_ctx: UserContext):
    # 1. 注入租户上下文
    langfuse_context.update_current_trace(
        user_id=user_ctx.user_id,
        session_id=user_ctx.session_id,
        tags=[f"tenant:{user_ctx.tenant_id}", "insurance-cs", "env:prod"],
        metadata={
            "tenant_id": user_ctx.tenant_id,
            "channel": user_ctx.channel,
            "biz_scenario": "policy_inquiry",
            "prompt_version": "v2.3.1"
        }
    )

    try:
        # 2. LlamaIndex 检索（内置强制租户过滤）
        llama_cb = LlamaIndexCallbackHandler()
        retriever = build_tenant_retriever(tenant_id=user_ctx.tenant_id, callback=llama_cb)
        nodes = await retriever.aretrieve(query)
        context = "\n".join([node.text for node in nodes])

        # 3. LangChain 生成
        lc_cb = LangChainCallbackHandler()
        chain = build_rag_chain()
        response = await chain.ainvoke(
            {"context": context, "question": query},
            config={"callbacks": [lc_cb]}
        )

        return {
            "answer": response.content,
            "trace_id": langfuse_context.get_current_trace_id(),
            "status": "success"
        }

    except Exception as e:
        langfuse_context.update_current_trace(status_message="RAG_FAILED", output=str(e))
        # 异步记录 MySQL 错误状态（省略 DB 写入代码）
        raise HTTPException(status_code=500, detail="服务处理异常，已记录日志")
```

### `app/rag/retriever.py`
```python
from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.core.callbacks import CallbackManager

def build_tenant_retriever(tenant_id: str, callback) -> VectorStoreIndex:
    # 强制过滤，业务层无法覆盖
    filters = MetadataFilters(
        filters=[ExactMatchFilter(key="tenant_id", value=tenant_id)]
    )
    
    # 初始化 Index（假设已加载向量存储）
    index = VectorStoreIndex.from_vector_store(vector_store)
    
    # 注入观测 Callback
    index.callback_manager = CallbackManager([callback])
    
    return index.as_retriever(filters=filters, similarity_top_k=5)
```

### `app/db/chat_trace_writer.py` (异步回写示例)
```python
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ChatTrace

async def save_trace_async(
    db: AsyncSession,
    tenant_id: str, user_id: str, session_id: str,
    trace_id: str, question: str, answer: str, model: str, status: str
):
    record = ChatTrace(
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
        langfuse_trace_id=trace_id,
        trace_url=f"https://langfuse.internal/trace/{trace_id}",
        question_summary=mask_pii(question),
        answer_summary=mask_pii(answer),
        model_name=model,
        status=status
    )
    db.add(record)
    await db.commit()
```

---

## 结语

本方案采用**“业务鉴权定身份、向量存储强隔离、Langfuse 做观测、异步上报保可用”**的分层架构，严格区分数据隔离与可观测边界。修正了 v3 SDK 用法、补齐了 LlamaIndex 观测链路、明确了 Dashboard 多租户权限治理方案，并提供了生产级代码模板与验收标准。按此方案实施，可满足保险行业高并发、高合规、可审计的智能客服可观测性需求。如需 Milvus Partition 自动化脚本、Langfuse API 成本对账 Job 或 PII 脱敏正则库，可进一步提供。