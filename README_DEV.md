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
- **webui/**：Vite + React + TS + Tailwind 的 Web 界面（Manus 风格首页 / 会话页 / 用户信息管理 / 登录注册 / 图片上传预览）
- **data/**：本地 SQLite 数据库等运行时数据（如 `auth.db`），该目录已在 `.gitignore` 中忽略

## 环境要求

- Python **>= 3.10**
- 依赖（见 `pyproject.toml` / `requirements.txt`）：
  - FastAPI / Uvicorn
  - **python-multipart**：处理 `multipart/form-data` 上传（如 `/upload/image`）

## 安装与运行

在项目根目录执行：

```bash
# 安装依赖（含可选 dev，已包含 python-multipart）
pip install -e ".[dev]"

# 或仅安装运行时依赖（同样会安装 python-multipart）
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

### 启动 WebUI 与一键脚本

#### 手动启动

```bash
# 后端（5173）
uvicorn api.main:app --reload --host 0.0.0.0 --port 5173

# 前端（8000）
cd webui
npm install       # 首次
npm run dev
```

- Web 界面地址：`http://localhost:8000`
- API / 文档：`http://localhost:5173`、`http://localhost:5173/docs`

#### 一键启动前后端

项目根目录提供 `start_all.sh`：

```bash
cd /Users/huangzhibiao/Codes/marketinghelper
./start_all.sh
```

脚本会：

- 启动后端：`uvicorn api.main:app --reload --host 0.0.0.0 --port 5173`
- 启动前端：在 `webui` 下执行 `npm run dev`（端口 8000）
- 按 `Ctrl+C` 时同时停止前后端

---

## WebUI 与图片上传行为说明

### 登录与注册（基于本地 SQLite）

- SQLite 文件：`data/auth.db`（已在 `.gitignore` 中忽略）
- 表结构（见 `api/auth_db.py`）：
  - `users(id, username, password_hash, created_at)`
  - `sessions(token, user_id, created_at)`
- 密码哈希使用 PBKDF2-HMAC-SHA256 + 随机盐，存储格式：`salt_hex:hash_hex`。
- 主要接口：
  - `POST /auth/register`：注册
  - `POST /auth/login`：登录，返回 `{ ok, token, username }`
  - `POST /auth/logout`：登出
  - `GET /auth/me`：基于 `Authorization: Bearer <token>` 获取当前用户

### 图片上传与存储（当前实现）

> 当前版本仅在 **前端浏览器内做本地预览**，**不会将图片上传到后端或磁盘**。

- 入口：首页主输入区左下角的上传图标按钮。
- 按钮行为：
  - 触发隐藏的 `<input type="file" multiple accept="image/*">`
  - 支持一次多选或多次选择图片。
- 预览逻辑（`webui/src/components/home/CentralInput.tsx`）：
  - 使用 `FileReader.readAsDataURL` 读取每个图片文件，生成 `data:image/...;base64,...` 的 Data URL。
  - React state：`images: { file: File; url: string }[]`，仅存于前端内存。
  - 输入框上方展示多张缩略图（圆角、可多行换行），每张右上角有 `×` 按钮可单独移除。
- 提交行为：
  - `onSubmit` 目前只发送文本内容给后端（如 `POST /intent`），**不会携带图片数据**。
  - 图片不会写入 `account_context` 或 SQLite，只用于当前会话的本地 UI 体验。

### 后续若要持久化图片的推荐方案（尚未实现）

若后续需要把用户上传的图片真正存到后端，可按以下约定扩展：

1. 新增上传 API：

   - `POST /upload/image`，`Content-Type: multipart/form-data`
   - 字段名：`file`，可选携带 `user_id` 或通过 token 解析用户。

2. 本地存储路径与命名规范：

   - 根目录：`data/uploads/`
   - 日期分层：

     ```text
     data/uploads/{yyyy}/{mm}/{dd}/
     ```

   - 文件名：使用 UUID + 原始扩展名，例如：

     ```text
     data/uploads/2026/02/11/d3f4b1a8-9c2e-4f7a-89ab-1234567890ab.png
     ```

3. 元数据表（可选）：

   - 表 `uploaded_images`（示例）：
     - `id`：主键
     - `user_id`：上传者
     - `path`：相对路径（如 `2026/02/11/d3f4b1a8-9c2e-4f7a-89ab-1234567890ab.png`）
     - `original_name`：原始文件名
     - `content_type`：MIME 类型
     - `size_bytes`：大小
     - `created_at`：上传时间

4. WebUI 对接方式：

   - 先调用上传接口获取图片 `id` 或完整 URL，再在主输入的文本中引用该 id/URL。
   - 文本请求（`/intent` 等）只携带图片引用，不直接传文件本体。

---

## 后续扩展

- 意图/Planner/Verifier 接入真实 LLM
- RAG/经验库（Chroma/Qdrant）
- Xhs*Service 与平台适配
- Training-Free 筛选与经验写入
- MCP / CodeExecutor 与沙箱

构建阶段不依赖真实 LLM API Key；配置见 `xhs_assistant.shared.config.Config`。
