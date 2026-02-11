# 小红书助手 · 开发框架说明

本目录为基于 [需求分析与Planner技术调研.md](需求分析与Planner技术调研.md) 与 [意图识别与Planner示例.md](意图识别与Planner示例.md) 实现的**可运行代码骨架**，对应计划「开发框架设计与构建」。

## 数据流

```
用户请求 → 意图理解 → [needs_clarification?] → 可执行性检查 → [can_fulfill?] → Planner → 多 Executor → Verifier → 发布/存档
```

## 项目结构

- **src/xhs_assistant/**：主包
  - **intent/**：意图理解（IntentOutput、Slots、IntentService 占位）
  - **fulfillability/**：可执行性检查（FulfillabilityResult、FulfillabilityService 占位）
  - **planner/**：LangGraph Plan-and-Execute（Plan、Step、build_workflow）
  - **agents/**：五类 Agent 占位 + registry（账号战略、选题策划、内容生成、投流、内容评估与检验）
  - **verifier/**：VerifierService 占位
  - **shared/**：WorkspaceState、Config
- **api/main.py**：FastAPI 入口（POST /intent、/fulfillability、/planner/run）
- **tests/**：test_intent_schema、test_planner_graph

## 环境要求

- Python **>= 3.10**

## 安装与运行

在项目根目录执行：

```bash
# 安装依赖（含可选 dev）
pip install -e ".[dev]"

# 或仅安装运行时依赖
pip install -e .
```

### 验证导入与图编译

在已安装包的前提下（需 Python >= 3.10）：

```bash
python -c "from xhs_assistant.intent.service import IntentService; from xhs_assistant.planner.graph import build_workflow; w = build_workflow(); print('OK')"
```

若未安装包，可从项目根目录设置 `PYTHONPATH=src` 后执行上述命令或 `pytest`（需已安装依赖）。

### 运行测试

```bash
pytest tests/ -v
```

### 启动 API

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 5173
```

- `POST /intent`：请求体 `{"user_input": "帮我起个美妆账号", "account_context": {}}`
- `POST /fulfillability`：请求体 `{"intent_output": {...}, "account_context": {}}`
- `POST /planner/run`：请求体 `{"intent_output": {...}, "account_context": {}, "past_steps": []}`，基于 IntentOutput 执行 Planner + 占位执行

## 后续扩展

- 意图/Planner/Verifier 接入真实 LLM
- RAG/经验库（Chroma/Qdrant）
- Xhs*Service 与平台适配
- Training-Free 筛选与经验写入
- MCP / CodeExecutor 与沙箱

构建阶段不依赖真实 LLM API Key；配置见 `xhs_assistant.shared.config.Config`。
