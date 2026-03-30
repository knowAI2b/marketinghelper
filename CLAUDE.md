# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

小红书助手 (XHS Assistant) - A marketing assistant for Xiaohongshu (小红书) platform that uses LangGraph for multi-agent orchestration.

**Core Data Flow:**
```
用户请求 → 意图理解 → [needs_clarification?] → 可执行性检查 → [can_fulfill?] → Planner → 多 Agent 执行 → Verifier → 发布/存档
```

## Commands

### Backend (Python/FastAPI)
```bash
# Install dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run single test file
pytest tests/test_file.py -v

# Verify imports and graph compilation
python -c "from xhs_assistant.intent.service import IntentService; from xhs_assistant.planner.graph import build_workflow; w = build_workflow(); print('OK')"

# Start API server (port 5173)
uvicorn api.main:app --reload --host 0.0.0.0 --port 5173
```

### Frontend (React/Vite)
```bash
cd webui
npm install
npm run dev      # Development server on port 8000
npm run build    # Production build
npm run lint     # ESLint
```

### One-command startup
```bash
./start_all.sh   # Starts both backend (5173) and frontend (8000)
./start_dev.sh   # Alternative dev startup script
```

## Architecture

### Backend (`src/xhs_assistant/`)
- **intent/**: Intent understanding (IntentOutput schema, IntentService)
- **fulfillability/**: Feasibility checking (FulfillabilityResult, FulfillabilityService)
- **planner/**: LangGraph Plan-and-Execute workflow (graph.py, Plan/Step schemas)
- **agents/**: Five agent implementations with registry pattern
  - 账号战略 (Account Strategy)
  - 选题策划 (Topic Planning)
  - 内容生成 (Content Generation)
  - 投流 (Ads Planning)
  - 内容评估与检验 (Content Evaluation)
- **verifier/**: Verification service
- **shared/**: WorkspaceState, Config

### Backend Abstraction Layer (`backends/`)
The system uses an abstract `AgentBackend` base class to support multiple execution backends:
- **native**: Pure local implementation using LangGraph (for offline/testing)
- **nanobot**: LiteLLM-based implementation (recommended for production)
- **nanoclaw**: Reserved for future extension

Backend selection is configured via environment variables with module-level overrides:
```bash
XHS_AGENT_BACKEND_TYPE=nanobot           # Default backend
XHS_INTENT_BACKEND=nanobot               # Override for intent module
XHS_PLANNER_BACKEND=native               # Override for planner module
XHS_EXECUTOR_BACKEND=nanobot             # Override for executor module
```

### API (`api/`)
- `main.py`: FastAPI endpoints
  - `POST /intent`: Intent understanding
  - `POST /fulfillability`: Feasibility check
  - `POST /planner/run`: Execute planner workflow
  - `POST /auth/register`, `/auth/login`, `/auth/logout`, `/auth/me`: Authentication
  - `POST /upload/image`: Image upload
  - `GET /backend/info`, `/backend/status`, `/backend/agents`: Backend management
- `auth_db.py`: SQLite-based auth (users, sessions, uploaded_images)

### Frontend (`webui/src/`)
- React 19 + TypeScript + Tailwind CSS 4 + Vite 7
- `components/`: account, auth, home, layout, session, ui, xhs
- `contexts/`: Auth context
- `stores/`: State management
- `types/`: TypeScript types

## LangGraph Workflow

The planner uses a Plan-and-Execute pattern:
```
START → plan_node → execute_node → replan_node → [conditional: execute or END]
```

- `plan_node`: Generates Plan from IntentOutput
- `execute_node`: Runs current step via agent registry or external backend
- `replan_node`: Checks if more steps remain

The workflow supports progress callbacks via `run_workflow_with_progress()` for SSE streaming.

## Environment Configuration

Required environment variables (see `.env.example`):
```bash
# API Keys (at least one required)
XHS_NANOBOT_API_KEY=your-api-key        # For nanobot backend
ANTHROPIC_API_KEY=your-key              # Alternative
OPENAI_API_KEY=your-key                 # Alternative

# Model configuration
XHS_NANOBOT_MODEL=anthropic/claude-sonnet-4-20250514

# MCP Server (optional)
XHS_MCP_SERVER_ENABLED=true
XHS_MCP_TRANSPORT=sse
XHS_MCP_SSE_PORT=5174
```

## UI Design Instructions

When designing UI, follow this workflow:
1. **Layout design**: ASCII wireframe, confirm with user
2. **Theme design**: Save CSS variables to `.superdesign/design_iterations/`
3. **Animation design**: Specify transitions and micro-interactions
4. **Generate HTML**: Single file in `.superdesign/design_iterations/`

Use Tailwind CSS via CDN (`<script src="https://cdn.tailwindcss.com"></script>`), Flowbite for components, Lucide icons. Avoid indigo/blue colors unless specified. Use Google Fonts (Inter, DM Sans, Geist Mono, etc.).

## Key Files

- `pyproject.toml`: Python package config (langgraph, langchain, fastapi, uvicorn)
- `webui/package.json`: Frontend dependencies (react, react-router-dom, lucide-react, tailwindcss)
- `start_all.sh`: One-command dev startup
- `README_DEV.md`: Detailed development documentation (in Chinese)