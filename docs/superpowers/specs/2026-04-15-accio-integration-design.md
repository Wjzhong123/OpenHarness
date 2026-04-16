# OpenHarness REST API 与 Accio Frontend 对接设计

**日期**: 2026-04-15
**状态**: 已批准

## 概述

为 OpenHarness 实现 REST API Server，使 Accio Frontend 能够通过 HTTP/SSE 调用 OpenHarness 的完整 Agent 能力（工具调用、Skills、多 Agent 协调、后台任务）。

## 部署架构

```
┌─────────────────────────────────────────────────────────┐
│                    Accio Frontend                        │
│  ┌──────────────────┐    ┌──────────────────────────┐  │
│  │   原有 UI 界面    │    │   新增: Agent 面板        │  │
│  └──────────────────┘    │  (调用 OpenHarness API)   │  │
│                          └──────────────────────────┘  │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP/SSE
                             ▼
┌─────────────────────────────────────────────────────────┐
│               OpenHarness REST API                       │
│  Base URL: http://localhost:8080/api/v1                  │
└─────────────────────────────────────────────────────────┘
```

## 部署模式

- **本地开发模式**: OpenHarness API 和 Accio Frontend 在同一台机器上运行
- **端口**: 8080（可配置）

## 技术选型

| 组件 | 方案 | 理由 |
|------|------|------|
| API 框架 | FastAPI | 高性能、自动 OpenAPI 文档、类型安全 |
| 流式传输 | Server-Sent Events (SSE) | 简单可靠，前端易集成 |
| 异步运行时 | asyncio | 与 OpenHarness 现有架构兼容 |
| 认证 | API Key Header | 适合本地开发，支持扩展 |

## API 端点设计

### 1. 聊天接口

```
POST /api/v1/chat
```

发送消息并获取流式响应。

**请求**:
```json
{
  "session_id": "optional-session-id",
  "message": "用户消息内容",
  "stream": true,
  "model": "optional-model-override",
  "system_prompt": "optional-system-prompt"
}
```

**响应**: SSE Stream

```
event: message
data: {"type": "text", "content": "部分响应文本"}

event: tool_call
data: {"type": "tool_call", "tool": "Read", "args": {"file_path": "example.txt"}}

event: tool_result
data: {"type": "tool_result", "tool": "Read", "result": "file content", "success": true}

event: done
data: {"type": "done", "session_id": "...", "usage": {"input_tokens": 100, "output_tokens": 200}}

event: error
data: {"type": "error", "message": "错误信息"}
```

### 2. 会话管理

```
GET /api/v1/sessions
```
列出所有会话。

**响应**:
```json
{
  "sessions": [
    {"id": "xxx", "created_at": "...", "updated_at": "...", "message_count": 5}
  ]
}
```

```
POST /api/v1/sessions
```
创建新会话。

**响应**:
```json
{"id": "new-session-id", "created_at": "..."}
```

```
GET /api/v1/sessions/:id
```
获取会话详情和历史消息。

```
DELETE /api/v1/sessions/:id
```
删除会话。

### 3. 工具执行（独立接口）

```
POST /api/v1/tools/execute
```

手动执行单个工具（通常由聊天自动触发）。

**请求**:
```json
{
  "tool": "Read",
  "args": {"file_path": "example.txt"}
}
```

**响应**:
```json
{
  "success": true,
  "result": "file content"
}
```

### 4. Skills 管理

```
GET /api/v1/skills
```

列出所有可用的 Skills。

**响应**:
```json
{
  "skills": [
    {"name": "brainstorming", "description": "..."},
    {"name": "debug", "description": "..."}
  ]
}
```

### 5. 权限审批（WebSocket）

```
WS /api/v1/approve
```

实时权限审批通道。

**服务端推送**:
```json
{"type": "permission_request", "tool": "Bash", "command": "rm -rf /tmp/*"}
```

**客户端响应**:
```json
{"type": "approve"}  // 或 {"type": "deny", "reason": "安全考虑"}
```

### 6. 健康检查

```
GET /api/v1/health
```

**响应**:
```json
{"status": "ok", "version": "0.1.6"}
```

## 错误处理

所有错误返回统一格式：

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "详细错误信息"
  }
}
```

错误码：
- `INVALID_REQUEST`: 请求参数错误
- `SESSION_NOT_FOUND`: 会话不存在
- `TOOL_NOT_FOUND`: 工具不存在
- `PERMISSION_DENIED`: 权限被拒绝
- `INTERNAL_ERROR`: 服务器内部错误

## 配置项

通过环境变量或配置文件：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `OPENHARNESS_API_PORT` | 8080 | API 服务端口 |
| `OPENHARNESS_API_HOST` | 0.0.0.0 | 监听地址 |
| `OPENHARNESS_API_KEY` | (无) | API 密钥（可选） |
| `OPENHARNESS_PERMISSION_MODE` | default | 权限模式 |

## 插件化架构（重要）

为保证与官方 OpenHarness 仓库独立升级，API Server 采用**插件化架构**：

### 设计原则

1. **不修改官方代码** - 通过 Python 导入使用 OpenHarness 核心模块
2. **独立 pip 包** - `oh-api` 作为独立包发布
3. **版本兼容** - 依赖 `openharness >= 0.1.6`，自动兼容未来版本

### 架构图

```
┌──────────────────────────────────────────────────────────────┐
│                    oh-api (独立 pip 包)                       │
│  纯通过 `from openharness.xxx import yyy` 使用核心能力         │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│              OpenHarness (官方仓库，独立升级)                   │
│  oh CLI  │  Engine  │  Tools  │  Skills  │  Memory          │
│                                                              │
│  升级方式: pip install --upgrade openharness                   │
└──────────────────────────────────────────────────────────────┘
```

### 版本管理策略

| 组件 | 包名 | 升级方式 |
|------|------|----------|
| OpenHarness | `openharness-ai` | `pip install --upgrade openharness-ai` |
| API Server | `oh-api` | `pip install --upgrade oh-api` |

`oh-api` 在 `pyproject.toml` 中声明对 `openharness` 的依赖范围，官方升级后只需同步更新依赖声明即可。

### oh-api 包结构

```
oh-api/
├── pyproject.toml              # 依赖: openharness >= 0.1.6
├── README.md
├── src/
│   └── oh_api/
│       ├── __init__.py
│       ├── main.py             # FastAPI 应用入口
│       ├── config.py           # 配置管理
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── chat.py         # /chat 端点
│       │   ├── sessions.py     # 会话管理端点
│       │   ├── tools.py       # 工具执行端点
│       │   └── skills.py      # Skills 端点
│       ├── models/
│       │   ├── __init__.py
│       │   ├── requests.py    # 请求模型
│       │   ├── responses.py   # 响应模型
│       │   └── events.py      # SSE 事件模型
│       ├── services/
│       │   ├── __init__.py
│       │   ├── agent_service.py  # Agent 核心服务封装
│       │   ├── session_store.py  # 会话存储
│       │   └── openharness_bridge.py  # OpenHarness 桥接层
│       └── auth/
│           ├── __init__.py
│           └── api_key.py     # API Key 认证
```

### 核心桥接层设计

`openharness_bridge.py` 负责将 OpenHarness 核心能力桥接到 API 层：

```python
# 伪代码示例
from openharness.engine.query_engine import QueryEngine
from openharness.tools.registry import ToolRegistry
from openharness.memory.session import Session

class OpenHarnessBridge:
    def __init__(self):
        self.query_engine = QueryEngine()
        self.tool_registry = ToolRegistry()
        self.session_store = Session()

    async def chat(self, messages, tools, stream_callback):
        """封装 OpenHarness QueryEngine"""
        async for event in self.query_engine.stream(messages, tools):
            stream_callback(event)

    def list_tools(self):
        """获取 OpenHarness 工具列表"""
        return self.tool_registry.list_tools()

    def list_skills(self):
        """获取 OpenHarness Skills 列表"""
        from openharness.skills.loader import SkillLoader
        return SkillLoader.list_available_skills()
```

这种方式确保：
- API Server 代码与 OpenHarness 核心解耦
- 官方升级时，桥接层可能需要小幅调整（如果 API 变化）
- 独立发布 `oh-api` 包，不影响官方仓库

## 实现顺序

1. **Phase 1: 基础框架**
   - 创建 `oh-api` 项目结构
   - FastAPI 应用入口
   - 健康检查接口
   - 基础错误处理
   - `pyproject.toml` 依赖声明

2. **Phase 2: OpenHarness 桥接层**
   - 实现 `openharness_bridge.py`
   - 封装 QueryEngine, ToolRegistry, Session
   - 测试与 OpenHarness 核心的集成

3. **Phase 3: 会话管理**
   - 会话 CRUD 接口
   - 会话存储（SQLite/JSON）

4. **Phase 4: 聊天核心**
   - 聊天接口（同步版本）
   - SSE 流式响应
   - 工具调用事件推送

5. **Phase 5: 工具调用**
   - 工具执行接口
   - 权限审批 WebSocket

6. **Phase 6: 高级功能**
   - Skills 列表接口
   - 多 Agent 支持
   - 后台任务接口

7. **Phase 7: 发布与集成**
   - `pip install oh-api` 本地安装测试
   - Accio Frontend Agent 面板开发
   - 端到端集成测试

## 测试计划

- 单元测试: 各模块独立测试
- 集成测试: API 端到端测试
- SSE 流式响应测试
- 权限审批流程测试
- 兼容性测试: 与不同版本 OpenHarness 的兼容性

## 发布计划

```
oh-api/
├── pyproject.toml
├── src/oh_api/
│   └── ...
├── tests/
│   └── ...
└── README.md
```

发布命令：
```bash
# 本地开发
pip install -e .

# 发布到 PyPI（需要账号）
python -m build
python -m twine upload dist/*
```
