# AI Agent 开发学习路线

> 最后更新：2026-09-22 · 已同步截至 2026 年 9 月的 Agent 开发主线：工程地基、模型路由、SDK、MCP、低代码/Agent 平台、评测、观测、可靠性与就业冲刺项目。具体模型名称、治理状态和 SDK API 以官方文档为准。

**🌐 在线学习地址：https://LiYY-FS.github.io/agent-learning-path/**

一个系统化、可交互的 AI Agent 开发学习路线网站。覆盖从基础概念到前沿趋势的完整知识体系，融入企业级实战案例与可运行代码示例。

### 这个项目是什么

随着大语言模型（LLM）能力突破，**AI Agent（智能体）** 已成为把 AI 落地到真实业务的关键形态——它能自主规划、调用工具、读写文件、串联多步流程。但市面上资料往往零散、滞后，且仍停留在 2025 年及之前的旧生态。

本项目把「学 Agent 开发」整理成一条**循序渐进的路线**：从「什么是 Agent」讲起，到 LLM 原理、Prompt、ReAct、Tool Calling、RAG、记忆，再到 LangChain / LangGraph / MCP 等框架实战、多 Agent 系统设计与编排，最后展望 Agent OS、具身智能、AGI 等前沿方向。内容已同步至 **2026-09-22** 的主流实践：工程地基、模型路由、OpenAI Agents SDK、LlamaIndex、MCP、Agent Skill、Computer Use、代码沙箱、低代码/Agent 平台、评测/观测与本地化运行能力。

它不是一份文档，而是一个**可交互的网页应用**：每个知识点都配有可视化图表、可复制的运行代码、企业级真实案例，以及即时测验，帮助边学边练。

### 谁适合用

- 想系统入门 AI Agent 开发的工程师、学生、技术爱好者
- 已会写 LLM 调用，但想搞懂 RAG / 多 Agent / 框架选型的开发者
- 需要把 Agent 落地到客服、代码审查、数据分析等业务的团队

### 特性

- **6 大章节 65 小节** 完整知识体系
- **极客科技风** 深色主题（霓虹紫/青色点缀）
- **代码高亮** + 一键复制 + 预期输出
- **Mermaid 流程图** + 架构图可视化
- **进度追踪** localStorage 本地存储
- **测验系统** 195 道题 + 6 套章节综合测验
- **企业级案例** 每小节含真实场景案例
- **本地化示例** 向量与工具演示优先使用本地 Ollama / 无 Key 方案
- **响应式设计** 支持手机/平板/桌面
- **零构建门槛** 纯静态 HTML/CSS/JS，CI 自动构建数据与缓存破坏

## 2026-09-22 更新说明

- 完成五视角内容审计整合：工程地基、LLM/Agent 底层机制、框架与生态、评测/观测/可靠性、安全/隐私/前沿方向均已补齐到章节体系。
- 新增第 5 章 **5.12 工程地基、基础设施与部署拓扑**，覆盖 Python 异步、Pydantic、Docker、CI/CD、Postgres、Redis、队列、Temporal、幂等、背压、断点续跑与部署拓扑。
- 新增第 5 章 **5.13 评测、观测与可靠性工程**，覆盖 LLM-as-judge、人工标注、promptfoo、DeepEval、RAGAS、LangSmith/Langfuse/OpenTelemetry、Arize Phoenix、Helicone、重试退避、超时、断路器与检查点。
- 新增第 6 章 **6.10 2026-09-22 前沿方向与学习资源整合**，覆盖 KV Cache、Token/上下文、采样解码、结构化输出、微调、Graph-of-Thoughts、NeMo Guardrails、GDPR、细分 Agent 方向、Prompt Injection、工具沙箱、MCP 供应链、产品 ROI 与学习资源。
- 修正内容统计：当前为 **6 章 65 小节**、**195 道单元测验**、**6 套章节综合测验**。

## 2026-09-21 更新说明

- 完成当时全站日期与元信息同步：README、章节元数据、站点版本展示均已更新到 **2026-09-21**。
- 修正当时内容统计：当时为 **6 章 62 小节**、**195 道单元测验**、**6 套章节综合测验**；当前统计见上方 2026-09-22 更新说明。
- 保持系统最新特性：新增/强调 OpenAI Agents SDK、LlamaIndex、Agent Skill、Computer Use、代码沙箱、低代码/Agent 平台与本地化运行能力，避免课程继续停留在旧生态。
- 求职/作品集入口见：`http://127.0.0.1:8000/#/chapter/ch6/section/6.9`。
- 通过代码静态审计：`scripts/audit_code.py` 输出 **0 条问题**；章节 quiz id 与题库定义一致。

## 章节结构

1. **基础概念入门** - Agent 定义、LLM 原理、Prompt 基础
2. **核心原理深入** - ReAct、Tool Calling、RAG、记忆管理、评估
3. **框架与工具实战** - LangChain、LangGraph、OpenAI Agents SDK、LlamaIndex、MCP、Agent Skill、低代码/Agent 平台、可观测性
4. **多 Agent 系统设计** - 架构模式、协作、长任务编排、HITL
5. **行业应用与最佳实践** - 客服、代码审查、数据分析、部署、安全、工程基础设施、评测与可靠性
6. **前沿趋势展望** - Agent OS、具身智能、AGI、多模态、Agent 安全、社区生态、就业冲刺包与前沿资源整合

> 说明：学习时长按“阅读 + 动手项目 + 测验 + 扩展资源”估算，不是只读文档的时间。

## 学习路线

| 章节 | 时长 | 难度 | 核心内容 |
|------|------|------|----------|
| 第 1 章 基础概念 | 8h | ★☆☆ | Agent 定义、LLM 原理、Prompt |
| 第 2 章 核心原理 | 20h | ★★★ | ReAct、RAG、Tool Calling |
| 第 3 章 框架实战 | 18h | ★★★ | LangChain、LangGraph、Agents SDK、LlamaIndex、MCP、Agent Skill |
| 第 4 章 多 Agent | 15h | ★★★★ | 架构模式、协作、HITL |
| 第 5 章 行业应用 | 28h | ★★★★ | 企业项目、部署、安全、工程底座、评测可靠性 |
| 第 6 章 前沿趋势 | 16h | ★★☆ | Agent OS、AGI、多模态、安全、社区生态、就业冲刺包、前沿整合 |

## 链接

- 🌐 **在线学习地址**：https://LiYY-FS.github.io/agent-learning-path/
- 💻 **GitHub 仓库**：https://github.com/LiYY-FS/agent-learning-path
- ⭐ 欢迎 Star / Fork / Issue 反馈

## License

MIT
