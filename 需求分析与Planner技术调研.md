# 需求分析、意图理解与 Planner 技术调研

> 面向项目：[小红书助手](小红书助手.md)——多 Agent 架构（账号战略 / 选题策划 / 内容生成 / 投流 / 内容评估）与 Training-Free 进化。  
> 本文调研「需求分析、意图理解模块」与「Planner 实现方案」的技术选型，**以高准确率为目标**，**国内外模型均可选用**，并覆盖**向 Cursor/Claude Code 级智能与编程能力对齐**的可行路径，与现有 [技术调研.md](技术调研.md) 中的技术栈可衔接。

## 总体结论

- **需求分析、意图理解（高准确率）**：不满足于「够用」的 MVP，采用**四阶段演进**——从「意图+抽槽分离」到「前置意图 RAG 召回」再到「多轮 RAG + 微调」；引入 **OOS（Out-of-Scope）拒识**、**混合路由/不确定性路由**、**微调（LoRA）** 与 **Benchmark 驱动评估**（如 URS、Meeseeks 等），目标意图准确率 94%+、槽位 F1 与任务完成率可追踪。**国内外模型均可**：Qwen/通义、DeepSeek、GLM/智谱、Claude、GPT、Gemini 等按准确率与成本选型，输出与 Planner 约定结构化 JSON。
- **Planner（高准确率）**：以 **LangGraph Plan-and-Execute** 为主，**规划节点使用强推理模型**（如 Claude Opus、GPT-4o、DeepSeek R1、Qwen 72B 等），执行节点可按步骤选用更小模型以控成本；**Verifier 驱动 Replan** 与 **回归测试/离线基准** 保证计划质量可观测、可迭代。复杂任务可扩展 **ADaPT**、**Reason-Plan-ReAct** 等范式。
- **Cursor/Claude Code 级智能与编程能力**：从「只做内容/营销流程」扩展为**具备一定编程与工具执行能力**——通过 **CodeExecutor + 沙箱**（E2B/Vercel Sandbox/Google Agent Engine 等）、**MCP 扩展**（与 Cursor 一致的工具协议）、**Planning → Execution → Verification** 闭环，以及参考 **OpenHands/Aider** 等开源编程 Agent 的编辑/执行/审批流程，使产品能执行脚本、做数据分析、扩展自定义工具，向 Cursor/Claude Code 的「Agent-First、多工具、可执行代码」靠拢。

---

## 环节定义与任务目标（含「询问用户澄清需求」归属）

在 Agent 执行或意图理解分析时**需要询问用户澄清需求**，可能发生在两类环节：**意图理解环节**（主）、**执行环节**（辅）。下表给出各环节的**任务目标**，并标明澄清需求所属环节。

| 环节 | 任务目标 | 询问用户澄清需求是否在本环节 |
| --- | --- | --- |
| **1. 意图理解（需求分析）** | 从用户自然语言中**识别意图类型**、**抽取并补全槽位**（含客户配置、长短期记忆），输出结构化需求（demand_summary、intent_type、slots）；**检测必填槽缺失或歧义**，若缺则生成澄清问句、暂停进入 Planner，待用户补充后重新走意图理解或仅补槽。 | **是（主）**。必填槽缺失或取值歧义时，本环节输出 `needs_clarification=true` 与 `clarification_question`，**不进入 Planner**；多轮中复用已填槽位，仅向用户询问缺项，直至必填齐全再进入下游。 |
| **2. Planner（规划）** | 根据意图输出与账号上下文**生成可执行的多步计划**（steps：agent、input_summary、depends_on、acceptance_criteria），做条件分支（是否投流、是否评估等）；可选支持**用户对任务拆解的修改**（增删改步骤/验收标准），修改后再提交执行。 | **否**。规划阶段不主动向用户「澄清需求」；若产品支持用户编辑计划，那是**用户主动修改**，不是系统发起的澄清。 |
| **3. 执行（多 Agent）** | 按计划**顺序或 DAG 调用各 Agent**（账号战略 / 选题策划 / 内容生成 / 投流 / 内容评估），每步以意图 slots + 上一步产出为输入，完成工具调用与中间结果写入状态；**若某步发现输入不足或无法继续**，可返回「需用户补充」状态。 | **是（辅）**。执行中若某 Agent 发现**信息不足**（如选题策划需要「行业」但 slots 未带、或链接解析失败需用户重填），可向用户**发起执行期澄清**（询问补充信息），待用户回复后继续该步或重试；也可将「用户对生成结果的手动修改」视为一种执行期反馈，不单独算澄清。 |
| **4. Verifier（内容评估与检验）** | 对执行产出（如笔记正文、配图、标题）做**质量、人设一致性、合规、AI 痕迹、投流适配**等校验，输出通过/不通过及可执行修改建议；不通过时驱动 **Replan** 或局部重试，或交由用户决定「按建议改」还是「人工改」。 | **否**。Verifier 不直接「询问用户澄清需求」；不通过时要么自动 Replan，要么将**修改建议呈现给用户**，由用户选择「按建议自动改」或「我手动改」——后者属于用户确认/修改，而非系统发起的澄清问句。 |
| **5. 发布/存档** | 通过 Verifier 后，将最终产物（笔记+配图+标签等）**发布到小红书**或仅存档；可选人工审批开关。 | **否**。不涉及需求澄清。 |
| **6. Training-Free（可选）** | 筛选有价值 session → 奖励评估 → 语义优势提取 → 经验写入向量库，供后续意图/规划检索。 | **否**。不涉及需求澄清。 |

**小结：询问用户澄清需求属于什么环节**

- **主环节：意图理解（需求分析）**  
  当**必填槽位缺失或歧义**时，由意图理解模块返回 `needs_clarification=true` 与 `clarification_question`，**不进入 Planner**；多轮对话中仅向用户询问缺项或歧义项，直至必填齐全再进入 Planner 与执行。这是**需求澄清**的主场景。
- **辅环节：执行（多 Agent）**  
  当某 Agent **执行中发现输入不足或无法继续**（如缺关键参数、链接解析失败、上下文缺失）时，可向用户**发起执行期澄清**（如「请补充行业」或「请重新提供链接」），待用户回复后继续该步或重试。这是**执行期补充信息**，与意图阶段的「缺槽澄清」区分开，便于日志与产品设计（如：意图澄清 vs 执行中追问）。

---

## 链接索引

> 说明：为方便在 Preview 中直接点击跳转，这里把文档中提到的**开源框架/组件**、**云厂商/闭源能力**与**论文/博客**入口统一汇总。

### 需求分析 / 意图理解相关

- **腾讯元器（工作流 LLM 意图识别节点）**：[腾讯元器 - 工作流 LLM 意图识别节点](https://yuanqi.tencent.com/guide/workflow-llm-intent-recognition-node)
- **阿里云 PAI（基于 LLM 的意图识别解决方案）**：[阿里云 PAI - 基于LLM的意图识别解决方案](https://help.aliyun.com/zh/pai/use-cases/llm-based-intent-recognition-solution)
- **Chatopera（意图与槽位文档）**：[Chatopera - 意图识别](https://docs.chatopera.com/products/chatbot-platform/explanations/intent.html)
- **IntelliQ（LLM 意图识别 + Slot + 多轮问答 / NL2API）**：[`answerlink/IntelliQ`](https://github.com/answerlink/IntelliQ)
- **llm_intend（大模型意图识别）**：[`yanyg123/llm_intend`](https://github.com/yanyg123/llm_intend)

### Planner / 规划范式相关

- **LangGraph Plan-and-Execute 官方教程**：[LangGraph - Plan-and-Execute](https://langchain-ai.github.io/langgraph/tutorials/plan-and-execute/plan-and-execute/)
- **LangGraph 与 AutoGen 集成**：[LangGraph - Integrate with AutoGen, CrewAI](https://langchain-ai.github.io/langgraph/how-tos/autogen-integration-functional/)
- **LangGraph 官方示例（plan-and-execute）**：[`langchain-ai/langgraph` examples](https://github.com/langchain-ai/langgraph/blob/main/examples/plan-and-execute/plan-and-execute.ipynb)
- **Plan-and-Execute-Agent（社区实现）**：[`saurav-dhait/Plan-and-Execute-Agent`](https://github.com/saurav-dhait/Plan-and-Execute-Agent)
- **LangChain 博客 - Planning Agents**：[Plan-and-Execute Agents](https://blog.langchain.com/planning-agents)
- **Plan-and-Solve 论文**：[arXiv:2305.04091](https://arxiv.org/abs/2305.04091)
- **ReAct 论文**：[arXiv:2210.03629](https://arxiv.org/abs/2210.03629)
- **ADaPT（As-Needed Decomposition and Planning）**：项目页 [Allen AI ADaPT](https://allenai.github.io/adaptllm/)；ACL Anthology [2024.findings-naacl.264](https://aclanthology.org/2024.findings-naacl.264)；arXiv [2311.05772](https://arxiv.org/abs/2311.05772)；GitHub [archiki/ADaPT](https://github.com/archiki/ADaPT)
- **Reason-Plan-ReAct（RP-ReAct）论文**：[arXiv:2512.03560](https://arxiv.org/html/2512.03560)
- **Modular ReAct（规划与工具选择分离）**：[Separation of planning concerns in ReAct-style LLM agents](http://krasserm.github.io/2024/03/06/modular-agent/)
- **Baby-AGI**：[`yoheinakajima/babyagi`](https://github.com/yoheinakajima/babyagi)

### 高准确率意图/规划与评估

- **URS（User-Centric Multi-Intent Benchmark）**：[ACL Anthology 2024.emnlp-main.210](https://aclanthology.org/2024.emnlp-main.210)（多意图评估、GPT-4-as-Judge 与人类偏好相关性 0.95）
- **Meeseeks（多轮指令遵循评估）**：[arXiv:2504.21625](https://arxiv.org/html/2504.21625v1)（意图识别、内容验证、输出结构验证）
- **Intent Detection in the Age of LLMs**：[ACL Anthology 2024.emnlp-industry.114](https://aclanthology.org/2024.emnlp-industry.114)（混合路由、不确定性路由、OOS 检测）
- **AI 智能体意图识别优化进阶**：[51CTO 意图识别进阶](https://www.51cto.com/aigc/7562.html)、[腾讯新闻 意图识别提升](https://news.qq.com/rain/a/20250805A020W500)（四阶段演进、意图 RAG、多轮 RAG、微调效果）

### Cursor / Claude Code 级智能与编程能力

- **Cursor 官方文档**：[Agent Overview](https://docs.cursor.com/agent/overview)、[Planning](https://docs.cursor.com/agent/planning)、[MCP](https://docs.cursor.com/context/model-context-protocol)、[Third-Party Hooks](https://cursor.com/docs/agent/third-party-hooks)
- **Cursor 2.0 Agent-First 架构**：[Cursor 2.0 Agent-First Guide](https://www.digitalapplied.com/blog/cursor-2.0-agent-first-architecture-guide)（并行 Agent、Git worktree、工具调用）
- **OpenHands（开源编程 Agent）**：[`OpenHands/software-agent-sdk`](https://github.com/OpenHands/software-agent-sdk)、[OpenHands Docs](https://docs.openhands.dev/sdk/getting-started)（Build/Plan Agent、Bash/文件/浏览器工具）
- **Aider（AI Pair Programmer）**：[aider.chat](https://aider.chat/)、[Aider Docs](https://aider.chat/docs/)（Git 集成、多格式编辑、多 LLM 支持）
- **代码执行沙箱**：[E2B](https://www.e2b.dev/)（[Docs](https://e2b.dev/docs)、[Connect LLMs](https://e2b.dev/docs/quickstart/connect-llms)）；Google Agent Engine [Code Execution](https://docs.cloud.google.com/agent-builder/agent-engine/code-execution/overview)；[Vercel Sandbox](https://vercel.com/docs/vercel-sandbox)；[Codegen Sandboxes](https://docs.codegen.com/sandboxes/overview)；[Vercel 安全执行 AI 生成代码](https://vercel.com/guides/running-ai-generated-code-sandbox)

### 与《技术调研.md》重叠（可交叉引用）

- **LangGraph**：[`langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph)
- **LangChain**：[`langchain-ai/langchain`](https://github.com/langchain-ai/langchain)
- **AutoGen**：[`microsoft/autogen`](https://github.com/microsoft/autogen)
- **DSPy**：[`stanfordnlp/dspy`](https://github.com/stanfordnlp/dspy)

---

## 一、需求分析、意图理解模块

### 1.1 定位与目标

在本项目中，该模块位于整体数据流最上游：

- **输入**：用户自然语言请求（如「帮我起个美妆账号，先做种草，一周 3 更」）。
- **输出**：结构化需求/意图，供 **Planner** 与下游 Agent 使用；必要时发起多轮澄清并做槽位填充。

目标可归纳为：

1. **意图识别**：判定请求所属类型（如：账号战略制定、选题策划、单篇内容生成、投流策略、评估与检验、混合/多步任务等），与 [小红书助手.md](小红书助手.md) 中的五类 Agent 能力对齐。
2. **参数抽取**：从文本中抽取关键参数——账号阶段（起号/冷启动/放量/变现）、目标（涨粉/种草/转化）、资源约束（更新频率、预算）、内容类型、行业、人设要点等；部分为枚举，部分为自由文本或实体。
3. **多轮澄清与槽位填充**：当必填槽位缺失或歧义时，生成澄清问句并接收用户补充，直至可交付 Planner 的最小信息集齐。
4. **可扩展**：新意图/新槽位的扩展方式清晰（配置驱动或数据驱动），并与 MCP/工具描述衔接，便于后续与技能治理统一。

### 1.2 技术方案对比

#### 1.2.1 基于 LLM 的意图识别

| 方案 | 说明 | 优点 | 缺点 | 适用场景 |
| --- | --- | --- | --- | --- |
| **零样本 / 少样本 + 结构化输出** | 用 LLM 直接输出 JSON（意图类型 + 槽位键值），Schema 固定 | 无需标注即可上线；易与 LangChain 等集成 | 复杂/长尾意图准确率依赖 prompt 与模型能力 | MVP、意图数量有限且可枚举 |
| **微调** | 用 instruction-output 对微调 Qwen 等模型（如阿里 PAI 方案） | 领域意图与表述更稳定；可压参数量 | 需要每类 50–100+ 条标注；迭代成本高 | 意图类别多、表述多样、对准确率要求高 |
| **云厂商工作流节点** | 腾讯元器、阿里 PAI 等提供「意图识别」节点，拖拽配置 | 免运维、快速对接 | 与自建栈解耦弱；定制与扩展受平台限制 | 快速验证或已有云厂商统一底座 |

- **数据准备（参考阿里 PAI）**：单意图每类建议 50–100 条、多意图/多轮建议为单意图的 20% 以上；JSON 含 `instruction`（用户输入）与 `output`（意图及参数）。详见 [阿里云 PAI 意图识别](https://help.aliyun.com/zh/pai/use-cases/llm-based-intent-recognition-solution)。
- **与 Chatopera 等产品的异同**：Chatopera 将「意图 + 槽位 + 词典」作为对话机器人标配；本模块侧重「需求分析 → Planner 输入」的接口形态，槽位设计需与小红书助手的业务枚举（账号阶段、目标、内容类型等）对齐。

#### 1.2.2 槽位 / 实体抽取

| 方式 | 说明 | 优点 | 缺点 |
| --- | --- | --- | --- |
| **LLM 一次性抽取** | 在意图识别的同一结构化输出中包含所有槽位 | 实现简单；与意图联合推理，上下文一致 | 长文本或槽位多时可能遗漏/幻觉 |
| **序列标注（NER/槽位标注）** | 传统 NLU 管道：分词 + 序列标注模型 | 对专有名词、时间、枚举值稳定 | 需标注数据；与 LLM 意图模块两套管道，维护成本高 |
| **分步：先意图后槽位** | 先识别意图，再按意图的 Slot Schema 调用 LLM 或规则 | 每意图的槽位可定制、可扩展 | 多一次调用；需维护意图→槽位 Schema 映射 |

**建议**：MVP 以 **LLM 单次结构化输出（意图 + 槽位）** 为主；枚举类（账号阶段、目标、内容类型）可选用**封闭枚举**或**模型自动枚举**（见下）；专有名词与时间若要求高，可后续加 NER 或规则后处理。

#### 1.2.2.1 封闭枚举 vs 模型自动枚举

| 方式 | 说明 | 优点 | 缺点 | 适用 |
| --- | --- | --- | --- | --- |
| **封闭枚举** | 槽位取值来自预定义列表（如行业=美妆|工装|母婴|…，阶段=起号|冷启动|放量|变现）；LLM 仅从列表中选或填默认值。 | 稳定、可校验、下游强类型；产品/运营可配；易做 Benchmark。 | 新行业/新表述出现需人工维护列表；长尾表述可能被错误映射或拒识。 | 枚举空间相对稳定、对一致性要求高的场景。 |
| **模型自动枚举** | 由模型根据用户输入**自动产出或扩展**枚举取值：例如模型输出「行业=工装」「品牌=全包圆装修」，不限定在预定义列表内；或先由模型生成候选取值，再归一化到规范词。 | 无需预列全量枚举；可覆盖长尾行业、新品类、用户自造表述；扩展成本低。 | 同一语义可能被抽成不同字符串（如「工装」vs「工装装修」）；下游需做归一化或容忍多写法；Benchmark 需定义等价类。 | 枚举空间开放、行业/品类会持续扩展的场景。 |
| **混合（推荐）** | **核心槽位封闭 + 开放槽位模型自动枚举**：如账号阶段、目标（涨粉/种草/转化）用封闭枚举；行业、品牌、内容类型等用模型自动枚举，并对高频结果做**归一化表**或**事后写入枚举候选**（经审核后加入封闭列表）。或：**种子封闭 + 模型建议扩展**——初始给少量封闭值，模型可建议新值，新值经规则/人工确认后加入列表或仅当次使用。 | 平衡稳定性与扩展性；核心流程可控，长尾可覆盖；可逐步把「模型常输出的值」沉淀为封闭项。 | 需设计归一化策略与候选审核流程（若写入枚举库）。 | 多数业务：阶段/目标等少量封闭，行业/品牌/特色等开放或半开放。 |

**模型自动枚举的实现方式**：

- **方式 A（自由抽取 + 后归一化）**：LLM 直接输出槽位值（如 `industry: "工装"`），不传枚举列表；下游用**归一化表**（同义词→规范词）或**小模型/规则**将「工装装修」「工装」等映射到统一规范词，便于 Planner 与 Agent 消费。
- **方式 B（约束生成 + 允许 other）**：Schema 中该槽位类型为 `enum | other`；LLM 优先从给定枚举选，若都不匹配则填 `other` 并在另一字段输出原始表述（如 `industry_raw: "全屋整装"`），下游按 `industry_raw` 或二次分类处理。
- **方式 C（模型先提议，再映射）**：先让 LLM 输出「用户表述对应的槽位值」及「建议的规范词」；系统将「建议规范词」与现有枚举比对，若存在则用现有值，若不存在则暂存为当次会话的开放值，并可选地写入「待审核枚举候选」供运营后续加入封闭列表。

若采用**模型自动枚举**，建议对开放槽位做**长度与格式校验**、**敏感词过滤**，并对高频抽取结果做**统计与沉淀**，逐步形成规范词表或封闭子集，以兼顾扩展性与一致性。

#### 1.2.3 高准确率路径（四阶段演进与 OOS/混合路由）

在**要求非常高的准确率**时，不满足于单节点 LLM 即兴输出，建议按业界实践采用**四阶段演进**（参见 [51CTO 意图识别进阶](https://www.51cto.com/aigc/7562.html)、[腾讯新闻 意图识别提升](https://news.qq.com/rain/a/20250805A020W500)）：

| 阶段 | 方案 | 要点 | 准确率/延迟 | 适用 |
| --- | --- | --- | --- | --- |
| **A 初级** | 单节点 + 提示词工程 | 意图+槽位一体、Few-Shot+CoT、结构化输出 | 意图多时提示膨胀（如 13 意图超 11000 字符），准确率受限 | 意图 ≤5 的简单场景 |
| **B 中级** | 意图与抽槽节点分离 | 意图节点 ~1500 字 prompt，每抽槽节点 ~2500 字 | 逻辑清晰、易维护；调用次数增加，总耗时约 5s | 意图 5–15、对延迟不敏感 |
| **C 进阶** | 前置意图 RAG 召回 | 构建「意图泛化知识库」，检索增强意图识别，覆盖方言/口语 | 准确率可提升至 **94.8%+**，Bad Case 可定向修复 | 单轮、大量特异表达的垂类 |
| **D 高阶** | 合并节点 + 多轮 RAG | Case 库管理「历史提问+最新提问+思考过程」，多轮会话组装与召回 | 兼顾多轮与效率 | 需结合历史判断意图的复杂多轮 |

- **OOS（Out-of-Scope）拒识**：明确定义意图边界与槽位约束，对不属于预定义意图的输入返回「拒识」或转人工，避免错误识别进入下游；可结合**两步法**（先 OOS 检测再意图分类）与**负样本增强**提升 OOS 准确率（参见 [ACL 2024 Intent Detection in the Age of LLMs](https://aclanthology.org/2024.emnlp-industry.114)）。
- **混合路由 / 不确定性路由**：当 LLM 置信度低时，走「小模型+规则」或「二次大模型校验」；**不确定性路由**可将延迟压到接近原生 LLM 的 50%，同时准确率与原生 LLM 差距控制在 2% 以内（同上 ACL 文献）。
- **微调（LoRA）**：在通义等国内模型上，参数高效微调可使**意图识别准确率提升约 14.3%**、QPS 从 12.3 提升至 86.7、延迟降低约 74%（参见 [阿里云 通义智能客服实战](https://developer.aliyun.com/article/1668018)）。国内外模型均可采用：Qwen/通义、DeepSeek、GLM/智谱、Claude、GPT、Gemini 等按效果与成本选型。
- **Benchmark 与评估**：采用**多意图/多轮 Benchmark** 驱动迭代，例如 **URS**（User-Centric Multi-Intent，与人类偏好相关性 0.95）、**Meeseeks**（多轮指令遵循、意图识别+内容验证+输出结构验证）；指标除意图 Accuracy、槽位 F1 外，增加**任务完成率（E2E）**与**拒识率/误入率**。

#### 1.2.4 多轮对话与澄清

- **何时发起澄清**：必填槽位缺失或取值歧义（如「做点内容」未区分是选题还是成稿）时，返回「需澄清」状态及建议问法。
- **Slot 填充策略**：可参考 IntelliQ 等——意图识别 + 参数抽取 + Slot 填充 + NL2API/Function Call；多轮上下文需传入历史槽位与上一轮系统回复。
- **与 Function Call / MCP 的衔接**：意图输出可包含「建议调用的工具/Agent」字段，供 Planner 或路由使用；工具描述与 MCP 统一后，便于扩展为新技能。

#### 1.2.5 可扩展性

- **配置驱动**：意图与槽位用 YAML/JSON 声明（枚举值、必填/可选、类型），LLM 仅做填空与分类；新增意图时改配置即可，适合意图集合相对稳定。
- **数据驱动**：新增意图/槽位时补充标注数据并微调或 few-shot；适合表述多样、持续扩展的场景。
- **与 MCP 的衔接**：可将「意图 → 推荐工具集」做成映射表或由 LLM 从 MCP 工具描述中检索，便于与 [技术调研.md](技术调研.md) 第七章 Skills/Tools 治理一致。

#### 1.2.6 槽位补全方案 vs 非槽位补全方案对比

| 维度 | 槽位补全方案 | 非槽位补全方案 |
| --- | --- | --- |
| **定义** | 显式定义 Slot Schema（槽位名、类型、必填/可选、枚举值、默认值）；从用户输入 + 账号上下文/长短期记忆中**抽取并补全**槽位；缺必填时发起澄清或从记忆/配置中补全。 | 不依赖显式槽位抽象：仅做意图分类（或意图+自由键值）；或 LLM 一次性输出「意图 + 任意结构化键值」；或意图+原始需求摘要直接交给 Planner，由下游 Agent 自行解析。 |
| **输入来源** | 用户当前句 + 客户配置（模式1 语言/模式2 链接）+ 用户记忆（标签、背景、最近交互、数据表现、运营等级等）。 | 通常仅用户当前句（+ 可选简短对话历史）；少数方案会把「上下文」拼进 prompt 由 LLM 自由发挥。 |
| **输出形态** | 结构化 `slots` 对象：键与 Schema 一致，值来自抽取或补全（记忆/默认/链接解析）；必填槽齐全或标 `needs_clarification`。 | 意图类型 + 自由格式的 `demand_summary` 或键值；无「必填/缺槽」的显式校验与补全。 |
| **多轮与澄清** | 必填槽缺失时明确触发澄清问句；多轮中可复用已填槽位，仅补缺项；支持「用户对任务拆解/槽位」的修改。 | 多轮依赖 LLM 对历史的理解；无显式缺槽检测，澄清多为模型自由生成，易遗漏或重复问。 |
| **准确率与可控性** | 高：槽位边界清晰，可做 OOS、枚举校验、记忆补全、RAG 召回补槽；易上 Benchmark（槽位 F1、任务完成率）。 | 依赖模型即兴表现；同一句话不同运行可能抽出不同键值；难做稳定回归与 Bad Case 定向修复。 |
| **可维护性与扩展** | 新增/修改意图时改 Schema 与配置即可；槽位与业务枚举（行业、阶段、目标等）强绑定，产品与运营可读可配。 | 新增意图或参数时多靠改 prompt 或加 few-shot；键值语义不统一，下游若强依赖字段名易碎。 |
| **延迟与成本** | 若「意图 + 抽槽」分离或加 RAG/记忆检索，调用次数与耗时增加；可做混合路由（高置信走单节点，低置信走补全链路）控成本。 | 单次 LLM 调用即可产出，延迟与成本低；但为补全信息可能需下游多轮或重复调用。 |
| **适用场景** | 高准确率、多轮对话、需记忆/配置补全、需用户修改任务拆解、与 Planner 强约定接口（如固定 slots 字段）的产品。 | 快速 MVP、意图与参数简单、对槽位粒度无要求、可接受「意图+摘要」由 Planner 自由解析的场景。 |

**小结**：

- **槽位补全**：适合「需求分析 → Planner」接口需稳定、多轮澄清与记忆补全、高准确率与可维护性的场景（如 [意图识别与Planner示例.md](意图识别与Planner示例.md) 示例一中的客户配置 + 长短期记忆 + 用户可修改任务拆解）；实现成本与调用链略高，可结合四阶段演进与混合路由压成本。
- **非槽位补全**：适合快速验证、意图简单、不强调缺槽检测与记忆补全的场景；若后续要提升准确率或接多轮/记忆，再引入槽位 Schema 与补全逻辑即可。

### 1.3 推荐实现与落地（含高准确率）

- **开源/自建**：**LangChain 结构化输出**（Pydantic/JSON Schema）实现意图+槽位一体输出；提示词优化可用 **DSPy**。**高准确率路线**：采用「意图与抽槽分离」+「前置意图 RAG」+ 可选「微调（LoRA）」；OOS 拒识与混合/不确定性路由作为标配。
- **模型选型（国内外均可）**：意图与抽槽可选用 **Qwen/通义、DeepSeek、GLM/智谱、Claude、GPT-4o、Gemini** 等；按自有 Benchmark（意图 Accuracy、槽位 F1、OOS 准确率、延迟）做 A/B 选型，不绑定单一厂商。
- **与现有技术栈衔接**：
  - 意图输出与 **Planner 输入** 约定：`demand_summary`、`intent_type`、`slots`、`needs_clarification`、`clarification_question`；Planner 仅在有 `demand_summary` 且未标 `needs_clarification` 时生成计划。
  - 与 **RAG/经验库** 联动：意图泛化知识库 + 历史相似需求检索，对应 [技术调研.md](技术调研.md) 第三章 RAG、第十章 Training-Free。
- **数据与评估（高准确率标配）**：
  - 标注数据：单意图每类 50–100 条起；多意图/多轮建议 ≥ 单意图的 20%；OOS 与边界 Case 单独标注。
  - 评估指标：意图准确率（Accuracy）、槽位 F1、**OOS 准确率/误入率**、任务完成率（E2E）；采用 URS/Meeseeks 或自建 Benchmark 做回归。

### 1.4 小结表：需求分析 / 意图理解

| 维度 | 推荐选型 | 需要自建/补充 |
| --- | --- | --- |
| 意图识别 | LLM 结构化输出（LangChain）；高准确率：意图与抽槽分离 + 意图 RAG + 微调 | 意图与槽位 Schema、枚举值列表；意图泛化知识库 |
| 槽位抽取 | 与意图同步或分节点；枚举用封闭列表 | 专有名词/时间等高精度时的 NER 或规则 |
| 高准确率 | 四阶段演进、OOS 拒识、混合/不确定性路由、LoRA 微调、URS/Meeseeks 等 Benchmark | 标注数据（含 OOS）、回归测试、多模型 A/B |
| 多轮澄清 | 必填槽位检测 + 澄清问句生成；高阶多轮 RAG | 多轮状态管理与对话策略 |
| 模型 | 国内外均可：Qwen/DeepSeek/GLM/Claude/GPT/Gemini 等，按准确率与成本选型 | 自有 Benchmark、A/B 与回归 |
| 可扩展 | 配置驱动意图/Slot Schema；与 MCP 工具描述对接 | 意图↔Agent/工具映射表、版本化配置 |

---

## 二、Planner 实现方案

### 2.1 定位与目标

在 [小红书助手.md](小红书助手.md) 与 [技术调研.md](技术调研.md) 第六章数据流中，Planner 的角色为：

- **输入**：需求分析/意图理解模块输出的结构化需求（需求摘要、意图类型、关键参数）+ 账号上下文（人设、阶段、历史摘要等）。
- **输出**：可执行的多步计划，对应「账号战略 → 选题策划 → 内容生成 → 内容评估与检验 → 投流」及分支（如仅选题、仅成稿等）；每步包含步骤 ID、负责 Agent、输入摘要、依赖、验收条件，便于状态机驱动与 Verifier 判断通过/Replan。
- **行为**：支持 **Verifier 驱动的 Replan**（某步不通过时回到 Planner 重规划或局部调整）；支持条件分支（如无需投流则跳过投流步骤）。

### 2.2 规划范式对比

| 范式 | 核心思想 | 优点 | 缺点 | 与本项目的匹配度 |
| --- | --- | --- | --- | --- |
| **Plan-and-Execute** | 先生成完整多步计划，再逐步执行；每步后可选择 Replan | 显式长期规划、轨迹可持久化、可用大模型规划+小模型执行 | 计划一次性固定，执行期变化需依赖 Replan | 高：与「五 Agent 顺序/分支」天然契合 |
| **ReAct** | 边推理边行动，每步决定 Thought/Action/Observation | 灵活、适应动态环境 | 长期规划弱、步数多时成本高、难以做「整链回放」 | 中：适合单 Agent 内工具调用，不适合顶层多 Agent 编排 |
| **ADaPT（按需分解）** | 先尝试执行；仅当执行失败时再对子任务做递归分解与规划 | 自适应任务复杂度与执行器能力；在 ALFWorld/WebShop 等显著优于 ReAct 与固定 Plan-and-Execute | 实现与调参更复杂 | 高（扩展）：任务不确定性强时可引入 |
| **Reason-Plan-ReAct（RP-ReAct）** | Reasoner-Planner 与 Proxy-Executor 分离；战略规划与执行解耦 | 适合企业级多工具、多数据源协同 | 架构更重 | 高（扩展）：与「Planner + 多 Executor」一致 |
| **Modular Planning** | 规划只负责「步骤描述 + 工具选择」，具体 function calling 交给专门模块 | 可用较小模型做规划，降低成本 | 需维护工具/步骤接口 | 中：可与现有 Planner 节点内「工具选择」结合 |

- 与 [技术调研.md](技术调研.md) 第九章「推理」一致：Plan-and-Execute 适合多步、多角色交接；ReAct 适合工具密集型单 Agent；Verifier 驱动的 Replan 对应「反思/Critic」。
- **推荐**：以 **Plan-and-Execute** 为主范式，用 **LangGraph** 实现「Plan → Execute → Replan」回路；复杂或高失败率场景再考虑 ADaPT 式按需分解或 RP-ReAct 式双角色。

### 2.3 开源实现选型

| 框架/项目 | 规划粒度 | 状态/回放 | Replan 支持 | 与「五 Agent + Verifier」的匹配度 | 说明 |
| --- | --- | --- | --- | --- | --- |
| **LangGraph** | 节点=规划/执行/Replan；子图可封装多 Agent | 强（原生 store/persistence、time travel） | 强（条件边 replan→agent 或 END） | 高 | 官方 [Plan-and-Execute 教程](https://langchain-ai.github.io/langgraph/tutorials/plan-and-execute/plan-and-execute/)：plan_step → execute_step → replan_step → 条件边；适合做「规划层」 |
| **AutoGen** | GraphFlow/DAG、GroupChat 中 Planner 角色 | 中（依赖日志与自定义存储） | 中（需在流程里显式写 Replan 逻辑） | 高 | 适合多 Agent 协作与工具调用；与 LangGraph 集成时可在 LangGraph 节点内调用 AutoGen Agent（见 [集成文档](https://langchain-ai.github.io/langgraph/how-tos/autogen-integration-functional/)） |
| **CrewAI** | 角色+任务列表，偏「任务分配」 | 中 | 中（多靠业务代码） | 中 | Demo/MVP 友好；复杂 Replan 与状态回放不如 LangGraph |
| **Plan-and-Execute-Agent（社区）** | 与 LangGraph 思路类似 | 取决于实现 | 通常支持 | 中 | 可作参考实现，生产建议以 LangGraph 为主 |

- **LangGraph 实现要点**（摘自官方教程）：
  - 状态：`input`、`plan`（步骤列表）、`past_steps`、`response`。
  - 节点：`planner`（生成 plan）、`agent`（执行当前步骤，可调用 ReAct 子图或 AutoGen）、`replan`（根据 past_steps 决定继续执行或返回 response）。
  - 条件边：`replan` → 若已有最终 `response` 则 END，否则回到 `agent`。
  - 可选：每步用更小模型执行，仅规划用大模型，以降低成本。
- **与 Verifier 的衔接**：执行节点可调用「内容评估与检验 Agent」；若 Verifier 返回不通过，将「不通过原因」写回状态并路由到 `replan`，由 Planner 更新 plan（如增加修改步骤或重试某 Agent）。

### 2.4 落地建议（贴小红书助手，含高准确率与模型选型）

- **Planner 输入**：
  - 意图理解模块输出的 `demand_summary`、`intent_type`、`slots`。
  - 账号上下文：人设、账号阶段、历史内容摘要、目标（涨粉/种草/转化）等（来自用户信息管理或 Memory）。
- **Planner 输出（结构化 Plan）**：
  - 建议 Schema：`steps[]`，每步含 `step_id`、`agent`、`input_summary`、`depends_on`、`acceptance_criteria`；便于 LangGraph 状态机驱动与 Training-Free 的 session 筛选/回放。
- **高准确率规划（强推理模型 + 国内外均可）**：
  - **规划节点**：使用**强推理/长链推理**模型以提升计划质量，例如 **Claude Opus/Sonnet、GPT-4o、DeepSeek R1、Qwen 72B、GLM-4** 等；按自有「计划合理性/可执行性/与 Verifier 通过率」等指标做 A/B，不绑定单一厂商。
  - **执行节点**：可按步骤选用更小/更快模型（如 Qwen 14B、DeepSeek Coder、GPT-4o-mini）以控成本与延迟。
  - **Verifier 驱动 Replan + 回归**：Verifier 不通过时回到 Planner 重规划或局部调整；对典型需求建立**离线计划基准**与**回归测试**，保证迭代不退化。
- **与 Training-Free 的衔接**：高价值 session 的「计划 → 执行结果 → 评分」写入经验库；后续规划时检索「相似需求下的成功计划」作为 few-shot 或约束。
- **可扩展方向**：
  - **ADaPT**：某步反复失败时对该步做按需子分解。
  - **Reason-Plan-ReAct**：Reasoner-Planner + 多 Proxy-Executor，适合多数据源/多工具协同。

### 2.5 小结表：Planner

| 维度 | 推荐选型 | 需要自建/补充 |
| --- | --- | --- |
| 规划范式 | Plan-and-Execute（主）；Replan 由 Verifier 驱动 | 计划 Schema、验收条件与 Verifier 的接口约定 |
| 运行时 | LangGraph（状态机 + 持久化 + 条件边） | plan/replan/execute 节点实现；与 AutoGen 的节点内集成 |
| 计划表达 | 结构化 JSON（步骤 ID、Agent、输入摘要、依赖、验收条件） | 与各 Executor、Verifier 的输入输出对齐 |
| 高准确率 | 规划节点用强推理模型；执行节点可用较小模型；Verifier + 回归测试 | 典型需求离线基准、计划合理性/Verifier 通过率指标 |
| 模型 | 国内外均可：Claude/GPT/DeepSeek/Qwen/GLM 等，规划与执行分层选型 | 自有 Benchmark、A/B 与回归 |
| 扩展 | ADaPT/RP-ReAct 作进阶选项 | 按需分解的触发条件与子图设计 |

---

## 三、高准确率与模型选型（国内外模型均可）

- **意图/需求分析**：目标**意图准确率 94%+**、槽位 F1 与 E2E 任务完成率可追踪。实现路径见本文 1.2.3（四阶段演进、OOS、混合路由、微调、Benchmark）。**模型**：Qwen/通义、DeepSeek、GLM/智谱、Baichuan、Kimi（国内）；Claude、GPT-4o、Gemini、Llama（国外）。按自有 Benchmark 与成本选型，可混合（如意图用 Claude、抽槽用 Qwen 以控成本）。
- **Planner**：目标**计划可执行性与 Verifier 通过率**可观测、可回归。规划节点用强推理模型（Claude Opus、GPT-4o、DeepSeek R1、Qwen 72B、GLM-4 等）；执行节点可用较小模型。**模型**：同上，国内外均可；建议规划与执行分层选型（大模型规划、小模型执行）。
- **评估与回归**：意图侧用 URS/Meeseeks 或自建多轮 Benchmark；规划侧用「典型需求 → 计划合理性 + Verifier 通过率」做离线基准；每次迭代跑回归，防止准确率退化。

---

## 四、Cursor / Claude Code 级智能与编程能力

产品若要对齐 **Cursor、Claude Code** 的智能水平并具备**一定编程能力**，需在现有「需求分析 → Planner → 多 Executor → Verifier」之上增加：**Agent-First 设计**、**多工具与代码执行**、**Planning → Execution → Verification** 闭环、以及**可扩展的 MCP/代码沙箱**。本节给出可行路径与选型，不改变小红书助手主流程，而是**可选的扩展维度**。

### 4.1 Cursor / Claude Code 能力拆解（对齐目标）

| 能力维度 | Cursor / Claude Code 典型表现 | 本产品可对齐的形态 |
| --- | --- | --- |
| **Agent-First** | 以 Agent 为中心，多步自主规划与执行，而非单次问答 | 已有 Planner → 多 Executor → Verifier；可加强「自主拆解与工具选择」 |
| **多工具** | Terminal、Browser、Review、MCP、Git 等；工具调用前可审批 | 引入 MCP 统一工具协议；高风险工具（代码执行、写文件）需审批或沙箱 |
| **Planning → Execution → Verification** | 先规划再执行，执行结果可验证并触发 Replan | 已有；可加强 Verifier 对「代码/脚本结果」的校验 |
| **代码编辑与执行** | 编辑文件、执行命令、运行脚本；在沙箱或隔离环境中 | 新增 **CodeExecutor** + **沙箱**（见下）；用于数据分析、自动化脚本、报表生成等 |
| **长上下文与代码库理解** | 大 context、语义检索、多文件推理 | 与现有 RAG/经验库、Semantic Search 一致；可扩展「项目/代码库」为资源 |
| **并行与隔离** | 多 Agent 并行、Git worktree 隔离（Cursor 2.0） | LangGraph 子图 + 任务级隔离；重度可考虑 worktree 级隔离 |

参考：[Cursor 文档](https://docs.cursor.com/agent/overview)、[Cursor 2.0 Agent-First](https://www.digitalapplied.com/blog/cursor-2.0-agent-first-architecture-guide)、[Cursor MCP](https://docs.cursor.com/context/model-context-protocol)。

### 4.2 编程能力的实现路径（CodeExecutor + 沙箱 + MCP）

- **CodeExecutor（代码执行器）**：Agent 可生成并执行代码（Python/Node 等），用于**数据分析、简单脚本、报表生成、内容处理**等。必须**沙箱化**，禁止直接访问生产库与敏感资源。
- **沙箱选型（国内外均可）**：
  - **E2B**：云函数式沙箱，按执行时长计费，支持多语言。
  - **Vercel Sandbox**：[Vercel Sandbox](https://vercel.com/docs/vercel-sandbox) 用于安全执行 AI 生成代码，远程隔离、短生命周期。
  - **Google Agent Engine Code Execution**：[Code Execution](https://docs.cloud.google.com/agent-builder/agent-engine/code-execution/overview)，支持多 Agent 框架与任意生成模型，沙箱可持久状态（如 14 天）。
  - **自建**：Docker 容器或 K8s Job 短生命周期执行，资源与网络隔离。
- **MCP（Model Context Protocol）**：与 Cursor 一致，将「工具/资源/提示词」标准化为 MCP server；本产品可将 Xhs*Service、EvalService、**CodeExecutor**、数据拉取脚本等封装为 MCP tools，供 Planner 与 Executor 调用，并做权限与审批（见 [技术调研.md](技术调研.md) 第七章）。
- **审批与安全**：对「执行命令/写文件/访问网络」等高风险操作，采用**人工审批**或**策略白名单**；代码执行仅限沙箱内，禁止挂载生产卷与敏感环境变量。

### 4.3 开源编程 Agent 参考（OpenHands、Aider）

- **OpenHands**：[`OpenHands/software-agent-sdk`](https://github.com/OpenHands/software-agent-sdk)、[Docs](https://docs.openhands.dev/sdk/getting-started)。提供 **Build Agent**（完整工具：Bash、文件、浏览器等）与 **Plan Agent**（仅分析不写代码）；支持多 LLM、自定义工具、安全策略。可借鉴：Agent 与工具边界、执行与审批流程、多步骤任务编排。
- **Aider**：[aider.chat](https://aider.chat/)、[Docs](https://aider.chat/docs/)。终端内 AI 结对编程，**Git 集成**、多编辑格式、多 LLM（Claude、DeepSeek R1、GPT-4o 等）。可借鉴：编辑格式（whole/diff/udiff）、与 Git 的集成方式、多文件重构与 Lint/Test 驱动修复。
- 本产品**不必须**全盘复用 OpenHands/Aider，而是将「可执行代码」「可编辑文件」「可运行命令」作为**可选能力**接入现有 Planner-Executor 体系：例如「选题策划」需要跑数据脚本时调用 CodeExecutor；「内容评估」需要批量改稿时走带审批的编辑工具。

### 4.4 与小红书助手场景的结合

- **已有能力**：账号战略、选题、内容生成、投流、评估——均为「业务 Agent + 工具调用」，无需代码即可运行。
- **编程能力的可选用途**：
  - **数据分析与报表**：执行用户或系统发起的「拉取某段时间笔记数据并出图/出表」等脚本。
  - **自动化与扩展**：用户自定义「定时拉竞品、写摘要」等流程，由 Agent 生成脚本并在沙箱中执行。
  - **内容/素材处理**：批量重写、格式转换、简单图像处理等，由 Agent 生成代码并在沙箱中执行。
- **落地顺序建议**：先巩固「需求分析 + Planner + 五 Agent + Verifier」与**高准确率**；再引入 **MCP 化工具**与**只读/低风险 CodeExecutor**（如只读数据分析）；最后再开放「写文件/网络请求」等并配审批与沙箱。

---

## 五、与《技术调研.md》的交叉引用

- **需求分析/意图理解**：输出供 Planner 使用，并与 **RAG/经验库**（技术调研第三章、第七章）、**MCP/Tools**（第七章）衔接；数据与评估可复用 **LangChain Evaluators**（第九章）。
- **Planner**：位于 **多 Agent 编排**（技术调研第一章、第八章）的「Leader」位置；**工作流与状态** 由 LangGraph 承担（第一章、第六章）；**推理范式** 对应第九章；**Training-Free** 对应第十章；**端到端数据流** 见第六章。
- **编程能力与沙箱**：与 [技术调研.md](技术调研.md) 第七章 Skills/Tools、MCP 一致；CodeExecutor 与沙箱为新增能力，不替代现有业务 Agent。
- 建议在 [技术调研.md](技术调研.md) 的总体结论或第六章数据流处增加对本文的索引：「需求分析与意图理解、Planner、高准确率与模型选型、Cursor/编程能力见《需求分析与Planner技术调研》。」

---

## 六、最小数据流（含需求分析与 Planner）

```text
用户自然语言请求
        │
        ▼
需求分析 / 意图理解模块
        │  输出：demand_summary, intent_type, slots[, needs_clarification]
        │  若 needs_clarification → 多轮澄清 → 再进入下游
        ▼
Planner（LangGraph plan 节点）
        │  输入：结构化需求 + 账号上下文
        │  产出：steps[]（step_id, agent, input_summary, depends_on, acceptance_criteria）
        ▼
多 Executor（账号战略 / 选题策划 / 内容生成 / 投流 / 内容评估）
        │  按 steps 顺序或 DAG 依赖执行；工具调用：Xhs*Service / VectorService / EvalService 等
        ▼
Generator（汇总笔记+配图+标签+评论引导等）
        │
        ▼
Verifier（质量/合规/人设/AI 痕迹/投流适配）
   │            │
   │ replan     │ pass
   ▼            ▼
回到 Planner     发布/存档
        │
        ▼
Training-Free：session → 筛选 → 奖励评估 → 优势提取 → 写入经验库（供意图/规划检索）
```

以上内容可直接用于选型与架构设计；若与现有 [技术调研.md](技术调研.md) 合并为同一文档的续章，可将本文「一」至「六」分别对应第十三章（需求分析与意图理解）、第十四章（Planner）、第十五章（高准确率与模型选型）、第十六章（Cursor/编程能力）、交叉引用与数据流，并统一链接索引。
