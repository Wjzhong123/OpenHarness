# oh-api

REST API Server for OpenHarness - 使 Accio Frontend 能够通过 HTTP/SSE 调用 OpenHarness 的完整 Agent 能力。

## 特性

- **流式响应**: SSE (Server-Sent Events) 支持实时流式输出
- **会话管理**: 支持多会话、会话历史、会话恢复
- **完整 Agent**: 工具调用、Skills、多 Agent 协调
- **权限审批**: WebSocket 实时权限审批
- **插件化架构**: 独立 pip 包，不修改官方 OpenHarness 代码

## 安装

```bash
# 本地开发安装
pip install -e .

# 或安装发布版本
pip install oh-api
```

## 快速开始

### 启动服务

```bash
oh-api
# 或
python -m oh_api.main
```

默认端口 8080，可通过环境变量配置：

```bash
export OPENHARNESS_API_PORT=9000
oh-api
```

### API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/chat` | POST | 发送消息 (SSE 流式) |
| `/api/v1/sessions` | GET | 列出会话 |
| `/api/v1/sessions` | POST | 创建会话 |
| `/api/v1/sessions/:id` | GET | 获取会话 |
| `/api/v1/sessions/:id` | DELETE | 删除会话 |
| `/api/v1/tools/execute` | POST | 执行工具 |
| `/api/v1/skills` | GET | 列出 Skills |

### 使用示例

```bash
# 健康检查
curl http://localhost:8080/api/v1/health

# 发送消息 (流式)
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "stream": true}'

# 列出会话
curl http://localhost:8080/api/v1/sessions

# 列出 Skills
curl http://localhost:8080/api/v1/skills
```

## 配置

| 环境变量 | 默认值 | 描述 |
|----------|--------|------|
| `OPENHARNESS_API_HOST` | 0.0.0.0 | 监听地址 |
| `OPENHARNESS_API_PORT` | 8080 | 端口 |
| `OPENHARNESS_API_KEY` | (无) | API 密钥 |
| `OPENHARNESS_PERMISSION_MODE` | default | 权限模式 |

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行服务
python -m oh_api.main
```

## 架构

```
oh-api/
├── main.py          # FastAPI 应用入口
├── config.py        # 配置管理
├── routes/          # API 路由
├── models/          # 数据模型
├── services/        # 业务逻辑
│   ├── agent_service.py       # Agent 服务
│   ├── session_store.py       # 会话存储
│   └── openharness_bridge.py   # OpenHarness 桥接层
└── auth/            # 认证
```

## 与 OpenHarness 独立升级

oh-api 作为独立 pip 包，依赖 `openharness >= 0.1.6`：

```bash
# 升级 OpenHarness
pip install --upgrade openharness

# 升级 oh-api
pip install --upgrade oh-api
```

## License

MIT
