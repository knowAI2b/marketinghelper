# 小红书助手 · 开发框架说明

> **理念**：内容即人格，真诚即策略
>
> **目标**：帮助每一位创作者讲好自己的故事

---

## 我们相信

在信息过载的时代，好的营销内容不是"生产"出来的，而是"生长"出来的。

我们相信：
- **每个人都有独特的故事**，不应该被模板淹没
- **真诚是最好的策略**，套路终将被识破
- **内容是人格的延伸**，而非流量的工具

## 核心原则

```
三个不做：
❌ 不做千篇一律 → 每个人都有自己的声音
❌ 不做AI痕迹   → 技术是手段，真实是底线
❌ 不做空洞内容 → 好内容要能打动人，更要能转化

三个做到：
✅ 有辨识度 → 一眼就能认出是你
✅ 有温度   → 读起来像真人在说话
✅ 有效果   → 既走心，也走量
```

## 技术理念

这套系统不仅是一个内容生成工具，而是一个**创作伙伴**：

| 传统工具 | 本项目 |
|---------|--------|
| 填模板 → 输出 | 理解意图 → 规划 → 创作的人 |
| 千人一面 | 基于人设的个性化 |
| 单次交互 | 多轮协作，越用越懂你 |
| 纯生成 | 生成 + 评估 + 迭代 |

---

本目录为基于 [需求分析与Planner技术调研.md](需求分析与Planner技术调研.md) 与 [意图识别与Planner示例.md](意图识别与Planner示例.md) 实现的**可运行代码骨架**，对应计划「开发框架设计与构建」。

## 数据流

```
用户请求 → 意图理解 → [needs_clarification?] → 可执行性检查 → [can_fulfill?] → Planner → 多 Agent 执行 → Verifier → 发布/存档
```

## 项目结构

```
marketinghelper/
├── api/                        # FastAPI 入口
│   ├── main.py                # API 路由定义
│   └── auth_db.py             # 认证数据库
│
├── src/xhs_assistant/          # 核心业务包
│   ├── backends/              # ✅ Agent 后端（native/nanobot/nanoclaw）
│   │   ├── base.py            # AgentBackend 抽象基类
│   │   ├── native_backend.py  # 本地实现
│   │   ├── nanobot_backend.py # LiteLLM 实现
│   │   └── manager.py         # 后端管理器
│   │
│   ├── mcp/                   # 📋 MCP Server（计划中）
│   │   ├── server.py          # MCP 服务入口
│   │   ├── tools/             # MCP Tools
│   │   ├── resources/         # MCP Resources
│   │   └── prompts/           # MCP Prompts
│   │
│   ├── intent/                # 意图理解
│   │   ├── schema.py          # IntentOutput 数据结构
│   │   └── service.py         # IntentService
│   │
│   ├── fulfillability/        # 可执行性检查
│   │   ├── schema.py          # FulfillabilityResult
│   │   └── service.py         # FulfillabilityService
│   │
│   ├── planner/               # LangGraph Plan-and-Execute
│   │   ├── graph.py           # build_workflow()
│   │   └── schema.py          # Plan, Step
│   │
│   ├── agents/                # 五类 Agent + registry
│   │   ├── account_strategy.py    # 账号战略
│   │   ├── topic_planning.py      # 选题策划
│   │   ├── content_generation.py  # 内容生成
│   │   ├── ads_planning.py        # 投流
│   │   ├── content_eval.py        # 内容评估与检验
│   │   └── registry.py            # Agent 注册表
│   │
│   ├── services/              # 平台服务
│   │   └── rednote.py         # RedNote 内容服务
│   │
│   ├── verifier/              # VerifierService
│   │   └── service.py
│   │
│   └── shared/                # 共享模块
│       ├── config.py          # ✅ 配置管理（含 AgentBackendConfig）
│       ├── llm.py             # LLM 工具
│       └── logging_config.py  # 日志配置
│
├── webui/                     # Vite + React + TS + Tailwind
│   ├── src/
│   │   ├── components/        # UI 组件
│   │   │   ├── home/          # 首页
│   │   │   ├── session/       # 会话页
│   │   │   ├── auth/          # 登录注册
│   │   │   ├── xhs/           # 小红书预览
│   │   │   └── ui/            # 通用组件
│   │   ├── contexts/          # Auth Context
│   │   ├── stores/            # 状态管理
│   │   └── types/             # TypeScript 类型
│   └── package.json
│
├── data/                      # 运行时数据（.gitignore）
│   ├── auth.db                # 认证数据库
│   └── uploads/               # 上传文件
│
├── docs/                      # 设计文档
│   ├── 集成计划.md            # Agent 后端集成计划
│   └── 架构设计.md            # 系统架构设计
│
└── tests/                     # 测试用例
    └── e2e_test.py            # 端到端测试
```

## 环境要求

- Python **>= 3.13**
- Node.js **>= 18**

## 安装与运行

### 安装依赖

```bash
# 后端依赖（含 dev）
pip install -e ".[dev]"

# 前端依赖
cd webui && npm install && cd ..
```

### 配置环境变量

```bash
# 复制模板
cp .env.example .env

# 编辑 .env
# 必填：XHS_NANOBOT_API_KEY 或 ANTHROPIC_API_KEY 或 OPENAI_API_KEY
```

### 验证安装

```bash
python -c "from xhs_assistant.intent.service import IntentService; from xhs_assistant.planner.graph import build_workflow; w = build_workflow(); print('OK')"
```

### 启动服务

```bash
# 方式一：一键启动
./start_all.sh

# 方式二：分别启动
uvicorn api.main:app --reload --host 0.0.0.0 --port 5173  # 后端
cd webui && npm run dev  # 前端
```

- Web UI: http://localhost:8000
- API 文档: http://localhost:5173/docs

## API 接口

### 核心接口

#### POST /intent

意图理解，返回结构化 IntentOutput。

```json
{
  "user_input": "帮我写一篇咖啡种草笔记",
  "account_context": {
    "platform": "小红书",
    "industry": "美食"
  }
}
```

响应：

```json
{
  "demand_summary": "生成咖啡种草笔记",
  "intent_type": "content_generation",
  "slots": {
    "platform": "小红书",
    "industry": "美食",
    "topic": "咖啡",
    "content_form": "图文"
  },
  "needs_clarification": false,
  "suggested_agents": ["内容生成"]
}
```

#### POST /planner/run

执行规划与内容生成。

```json
{
  "intent_output": { ... },
  "account_context": {},
  "past_steps": []
}
```

#### POST /fulfillability

可执行性检查。

### 认证接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/auth/register` | POST | 注册 |
| `/auth/login` | POST | 登录，返回 token |
| `/auth/logout` | POST | 登出 |
| `/auth/me` | GET | 获取当前用户 |

### 后端管理接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/backend/info` | GET | 后端配置信息 |
| `/backend/status` | GET | 健康状态检查 |
| `/backend/agents` | GET | Agent 注册表信息 |
| `/backend/clear-cache` | POST | 清空后端缓存 |

### 文件上传

#### POST /upload/image

上传图片，支持 `multipart/form-data`。

## Agent 后端配置

### 后端类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| `native` | 纯本地实现 | 离线运行、测试 |
| `nanobot` | LiteLLM 调用 | **推荐**，生产环境 |
| `nanoclaw` | 后续扩展 | - |

### 配置示例

```bash
# 使用 nanobot（推荐）
XHS_AGENT_BACKEND_TYPE=nanobot
XHS_NANOBOT_MODEL=anthropic/claude-sonnet-4-20250514
XHS_NANOBOT_API_KEY=your-api-key

# 使用 OpenAI
XHS_NANOBOT_MODEL=openai/gpt-4o
OPENAI_API_KEY=your-key

# 使用阿里云 DashScope
XHS_NANOBOT_API_BASE=https://coding.dashscope.aliyuncs.com/v1
XHS_NANOBOT_MODEL=openai/qwen-max
```

### 模块级覆盖

支持为不同模块指定不同后端：

```bash
XHS_AGENT_BACKEND_TYPE=nanobot
XHS_INTENT_BACKEND=nanobot    # 意图识别用 nanobot
XHS_PLANNER_BACKEND=native    # 规划用 native
XHS_EXECUTOR_BACKEND=nanobot  # 执行用 nanobot
```

### 混合模式

```bash
# 后端 A/B 测试
XHS_AGENT_BACKEND_TYPE=nanobot
XHS_INTENT_BACKEND=nanobot
XHS_PLANNER_BACKEND=nanobot
XHS_EXECUTOR_BACKEND=native
```

## MCP Server 配置

### 启用 MCP Server

```bash
XHS_MCP_SERVER_ENABLED=true
XHS_MCP_TRANSPORT=sse        # 或 stdio
XHS_MCP_SSE_PORT=5174
```

### 客户端配置

#### OpenClaw

```json
{
  "mcpServers": {
    "xhs-marketing": {
      "url": "http://localhost:5174/sse"
    }
  }
}
```

#### Claude Desktop

```json
{
  "mcpServers": {
    "xhs-marketing": {
      "command": "python",
      "args": ["-m", "xhs_assistant.mcp.server"],
      "env": {
        "XHS_MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

详细设计见 [docs/集成计划.md](./docs/集成计划.md)

## WebUI 开发

### 技术栈

- React 19
- TypeScript
- Tailwind CSS 4
- Vite 7
- React Router 7
- Lucide Icons

### 目录结构

```
webui/src/
├── components/
│   ├── home/          # 首页组件
│   │   └── CentralInput.tsx
│   ├── session/       # 会话页
│   │   ├── SessionPage.tsx
│   │   └── SessionResult.tsx
│   ├── auth/          # 认证
│   │   ├── LoginPage.tsx
│   │   └── RegisterPage.tsx
│   ├── xhs/           # 小红书预览
│   │   └── XhsPreview.tsx
│   └── ui/            # 通用组件
├── contexts/
│   └── AuthContext.tsx
├── stores/
├── types/
│   └── intent.ts
└── App.tsx
```

### 开发命令

```bash
cd webui

# 开发服务器
npm run dev

# 构建
npm run build

# 代码检查
npm run lint
```

## 测试

### 单元测试

```bash
pytest tests/ -v
```

### 端到端测试

```bash
python tests/e2e_test.py
```

## 日志系统

日志文件位置：`data/logs/`

- `app.log` - 应用日志
- `api.log` - API 请求日志
- `user_actions.log` - 用户行为日志

获取日志统计：

```bash
curl http://localhost:5173/api/logs/stats
```

## 后续扩展

### 短期

- [ ] backends 模块单元测试
- [ ] 端到端测试完善
- [ ] MCP Server 实现

### 中期

- [ ] OpenClaw 集成测试
- [ ] Claude Desktop 集成
- [ ] Web 搜索集成

### 长期

- [ ] 会话持久化
- [ ] 多轮对话记忆
- [ ] 多平台扩展（微信、抖音）
- [ ] RAG/经验库集成

## 相关文档

- [集成计划.md](./docs/集成计划.md) - Agent 后端与 MCP 集成详细设计
- [架构设计.md](./docs/架构设计.md) - 系统架构设计
- [需求分析与Planner技术调研.md](./需求分析与Planner技术调研.md) - 技术调研报告
- [技术调研.md](./技术调研.md) - 详细技术选型分析