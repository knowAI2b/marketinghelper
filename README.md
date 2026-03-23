# 内容营销助手

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

---

## 这个项目解决什么问题

营销内容创作面临三重困境：

| 困境 | 表现 | 我们的解法 |
|------|------|-----------|
| **同质化** | 千篇一律的标题、套路化的文案 | 基于账号人设的个性化生成 |
| **AI痕迹** | 机械生硬、缺乏真实感 | 模仿真人表达风格，保留"人味" |
| **转化低** | 有流量没转化，有曝光没认同 | 从需求出发，以价值为导向 |

---

## 核心原则

我们坚持三个"不做"：

```
❌ 不做千篇一律 → 每个人都有自己的声音
❌ 不做AI痕迹   → 技术是手段，真实是底线
❌ 不做空洞内容 → 好内容要能打动人，更要能转化
```

我们追求的三个"做到"：

```
✅ 有辨识度 → 一眼就能认出是你
✅ 有温度   → 读起来像真人在说话
✅ 有效果   → 既走心，也走量
```

---

## 功能特性

智能营销内容创作平台，支持小红书、抖音、微信等多平台。

### 核心能力

- **意图理解**：智能分析用户需求，自动识别营销意图类型
- **选题策划**：根据行业、目标生成高质量选题
- **内容生成**：一键生成小红书风格笔记、短视频脚本
- **账号战略**：提供人设定位、内容方向、运营策略建议
- **投流规划**：预算分配、投放策略、预期效果分析
- **内容评估**：质量评分、问题分析、改进建议

### 交互方式

- **Web UI**：现代化 React 界面，支持实时预览
- **REST API**：完整的 FastAPI 接口
- **MCP Server**：支持 OpenClaw、Claude Desktop、国内智能体开放平台 等工具调用

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.13, FastAPI, LangGraph, LiteLLM |
| 前端 | React 19, TypeScript, Tailwind CSS 4, Vite 7 |
| 数据库 | SQLite (认证) |
| 协议 | REST API, MCP (Model Context Protocol) |

## 快速开始

### 环境要求

- Python >= 3.13
- Node.js >= 18

### 安装

```bash
# 克隆项目
git clone https://github.com/your-org/marketinghelper.git
cd marketinghelper

# 安装后端依赖
pip install -e ".[dev]"

# 安装前端依赖
cd webui && npm install && cd ..
```

### 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，填入 API Key
# XHS_NANOBOT_API_KEY=your-api-key
```

### 启动

```bash
# 一键启动（后端 5173 + 前端 8000）
./start_all.sh

# 或分别启动
uvicorn api.main:app --reload --host 0.0.0.0 --port 5173  # 后端
cd webui && npm run dev  # 前端
```

访问：
- Web UI: http://localhost:8000
- API 文档: http://localhost:5173/docs

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     客户端层                                 │
│   WebUI (React)  │  OpenClaw  │  Claude Desktop  │  Cursor  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     服务层                                   │
│   FastAPI (REST)  │  MCP Server (SSE/stdio)                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Agent Backend Core                         │
│   意图理解 → 规划器 → 多Agent执行 → 验证器                   │
│   NativeBackend │ NanobotBackend (LiteLLM)                 │
└─────────────────────────────────────────────────────────────┘
```

## API 概览

### 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/intent` | POST | 意图理解 |
| `/planner/run` | POST | 执行规划与生成 |
| `/fulfillability` | POST | 可执行性检查 |

### 认证接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/auth/register` | POST | 用户注册 |
| `/auth/login` | POST | 用户登录 |
| `/auth/logout` | POST | 用户登出 |
| `/auth/me` | GET | 获取当前用户 |

### 后端管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/backend/info` | GET | 后端配置信息 |
| `/backend/status` | GET | 健康状态 |
| `/backend/agents` | GET | Agent 列表 |

详细文档见 [README_DEV.md](./README_DEV.md)

## MCP 集成

本产品支持作为 MCP Server，供外部工具调用：

### OpenClaw 配置

```json
{
  "mcpServers": {
    "xhs-marketing": {
      "url": "http://localhost:5174/sse"
    }
  }
}
```

### Claude Desktop 配置

```json
{
  "mcpServers": {
    "xhs-marketing": {
      "command": "python",
      "args": ["-m", "xhs_assistant.mcp.server"]
    }
  }
}
```

### MCP Tools

| Tool | 说明 |
|------|------|
| `xhs_content_generate` | 生成营销内容 |
| `xhs_topic_plan` | 选题策划 |
| `xhs_account_strategy` | 账号战略 |
| `xhs_ads_plan` | 投流规划 |
| `xhs_content_evaluate` | 内容评估 |
| `xhs_clarify` | 需求澄清 |

详细设计见 [docs/集成计划.md](./docs/集成计划.md)

## 项目结构

```
marketinghelper/
├── api/                    # FastAPI 入口
├── src/xhs_assistant/      # 核心业务
│   ├── backends/           # Agent 后端
│   ├── intent/             # 意图理解
│   ├── planner/            # 任务规划
│   ├── agents/             # Agent 实现
│   └── shared/             # 配置与工具
├── webui/                  # React 前端
├── docs/                   # 设计文档
└── tests/                  # 测试用例
```

## 配置说明

### Agent 后端

```bash
# 后端类型: native | nanobot | nanoclaw
XHS_AGENT_BACKEND_TYPE=nanobot

# LLM 模型
XHS_NANOBOT_MODEL=anthropic/claude-sonnet-4-20250514
XHS_NANOBOT_API_KEY=your-api-key
```

### 模块级覆盖

```bash
# 可为不同模块指定不同后端
XHS_INTENT_BACKEND=nanobot
XHS_PLANNER_BACKEND=native
XHS_EXECUTOR_BACKEND=nanobot
```

完整配置见 [.env.example](./.env.example)

## 开发指南

```bash
# 运行测试
pytest tests/ -v

# 代码检查
cd webui && npm run lint

# 构建前端
cd webui && npm run build
```

详细开发文档见 [README_DEV.md](./README_DEV.md)

## 文档索引

| 文档 | 说明 |
|------|------|
| [README_DEV.md](./README_DEV.md) | 开发框架说明 |
| [docs/集成计划.md](./docs/集成计划.md) | Agent 后端集成计划 |
| [docs/架构设计.md](./docs/架构设计.md) | 系统架构设计 |

## License

MIT
