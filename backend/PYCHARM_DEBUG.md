# PyCharm 调试配置指南

## 快速开始

### 方式一：使用 debug.py（推荐）

这是最简单的方式，已经预配置好调试选项。

1. 在 PyCharm 中打开 `backend/debug.py`
2. 右键点击文件中的任意位置
3. 选择 **Debug 'debug'**
4. 或者点击编辑器右上角的 🐛 图标

服务器将启动，你可以设置断点并使用 PyCharm 的调试功能。

---

### 方式二：手动配置运行/调试配置

如果需要自定义配置，请按照以下步骤操作：

#### 创建 Debug 配置

1. 在 PyCharm 中，点击右上角的 **Add Configuration...**（或 `Run > Edit Configurations...`）
2. 点击左上角的 **+** 按钮
3. 选择 **Python**

配置以下参数：

**Name**: `Debug Backend`

**Script path**: `$ProjectFileDir$/backend/debug.py`

**Python interpreter**: 选择你的项目 Python 解释器

**Working directory**: `$ProjectFileDir$/backend`

**Environment variables**: 点击右侧的文件夹图标，添加：
```
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

**点击 Apply 和 OK** 保存配置

#### 创建 Run 配置

如果需要不调试直接运行，可以创建单独的 Run 配置：

**Name**: `Run Backend`

**Script path**: `$ProjectFileDir$/backend/run.py`

**Python interpreter**: 选择你的项目 Python 解释器

**Working directory**: `$ProjectFileDir$/backend`

**点击 Apply 和 OK** 保存配置

---

## 使用调试功能

### 设置断点

在代码行号旁边点击，设置断点（🔴 红点）：

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/test")  # 在这里设置断点 👈
async def test_endpoint():
    result = do_something()  # 或在这里设置断点 👈
    return {"result": result}
```

### 调试操作

1. **Start Debugging**: 点击 🐛 按钮或按 `Shift + F9`
2. **Step Over**: 跳过当前行（F8）
3. **Step Into**: 进入函数内部（F7）
4. **Step Out**: 跳出当前函数（Shift + F8）
5. **Resume Program**: 继续运行（F9）
6. **View Variables**: 在调试面板中查看当前变量值
7. **Evaluate Expression**: 按 `Alt + F8` 计算表达式

### 调试技巧

1. **查看请求对象**: 在路由处理函数中设置断点，查看 `request` 对象的内容

   ```python
   @router.post("/query")
   async def query_documents(request: QueryRequest):  # 在这里设置断点
       # 查看请求参数
       print(request.question)
   ```

2. **调试异步函数**: 在 async 函数中设置断点，PyCharm 会正确处理

   ```python
   async def process_data(data):  # 可以在这里设置断点
       result = await some_async_operation()
       return result
   ```

3. **查看 WebSocket 消息**: 在 WebSocket 端点中设置断点，查看收到的消息

   ```python
   @router.websocket("/")
   async def websocket_endpoint(websocket: WebSocket):  # 在这里设置断点
       data = await websocket.receive_text()
   ```

---

## 不同启动方式对比

| 文件 | 用途 | PyCharm 调试 | 热重载 | 适用场景 |
|------|------|--------------|--------|----------|
| `debug.py` | 调试模式 | ✅ 支持 | ❌ 不支持 | 开发调试 |
| `run.py` | 生产/开发 | ⚠️ 有限支持 | ✅ 支持 | 日常开发、生产 |
| `main.py` (via uvicorn CLI) | 命令行 | ❌ 不支持 | ✅ 支持 | 命令行启动 |

---

## PyCharm 项目配置建议

### 设置 Python 解释器

1. 打开 **File > Settings** (Windows/Linux) 或 **PyCharm > Settings** (macOS)
2. 导航到 **Project > Python Interpreter**
3. 点击右上角的 **Add Interpreter**
4. 选择 **Existing environment**
5. 选择你的虚拟环境或系统 Python 解释器

### 配置代码风格

1. 打开 **File > Settings**
2. 导航到 **Editor > Code Style > Python**
3. 选择你喜欢的代码风格

### 安装必要插件

推荐安装以下 PyCharm 插件：

- **Rainbow Brackets**: 彩虹括号，更容易匹配括号
- **Python Docstrings**: 快速生成文档字符串
- **String Manipulation**: 字符串处理工具

---

## 常见问题

### Q: 调试时服务器启动很慢？

**A**: 这是正常的，PyCharm 调试器会增加一些开销。如果需要更快的启动，可以：
- 使用 `run.py` 进行快速开发
- 只在需要调试时使用 `debug.py`

### Q: 断点不起作用？

**A**: 检查以下几点：
1. 确认使用的是 `debug.py` 启动的
2. 确认断点在可执行的代码行上（不是空行或注释）
3. 检查断点是否被禁用（灰色图标）
4. 确认 Python 解释器路径正确

### Q: 如何调试前端代码？

**A**: 前端是 React 应用，需要在浏览器中调试：
1. 在浏览器中打开开发者工具（F12）
2. 切换到 **Sources** 标签
3. 在 JavaScript/TypeScript 代码中设置断点
4. 或使用 VS Code 的 React 开发者工具插件

### Q: 可以同时调试前端和后端吗？

**A**: 可以，但需要：
1. 在一个终端中用 `debug.py` 启动后端调试
2. 在另一个终端中用 `npm run dev` 启动前端
3. 使用浏览器开发者工具调试前端
4. 使用 PyCharm 调试后端

### Q: 热重载在调试模式下不可用？

**A**: 是的，这是设计选择。热重载会干扰调试器的工作。在调试时：
- 修改代码后，需要停止并重新启动调试会话
- PyCharm 的 **Rerun** 按钮（🔄）可以快速重启

---

## 性能监控

### 查看 API 响应时间

在调试时，可以测量关键代码段的执行时间：

```python
import time

start_time = time.time()

# 你的代码
result = await some_async_operation()

elapsed = time.time() - start_time
print(f"Execution time: {elapsed:.2f}s")
```

### 使用 PyCharm Profiler

1. 选择 **Run > Profile 'debug'**
2. 运行一些 API 请求
3. 查看性能分析报告
4. 找出性能瓶颈

---

## 下一步

配置完成后，你可以：

1. ✅ 在 PyCharm 中点击 Debug 按钮开始调试
2. ✅ 在代码中设置断点
3. ✅ 发送 API 请求触发断点
4. ✅ 使用调试工具逐步执行代码
5. ✅ 查看和修改变量值
6. ✅ 评估表达式和调用栈

祝调试愉快！🐛
