# AI Agent 开发学习路线

> 最后更新：2026 年 7 月 · 已同步最新模型（GPT-5 / Claude Opus 4.8 / Gemini 3.5 / Llama 4）与框架生态（MCP 归 Linux 基金会治理并进入 Stable、Agentic 编码平台成熟）。

**🌐 在线访问：https://18232751914.github.io/agent-learning-path/**

一个系统化、可交互的 AI Agent 开发学习路线网站。覆盖从基础概念到前沿趋势的完整知识体系，融入企业级实战案例与可运行代码示例。

### 这个项目是什么

随着大语言模型（LLM）能力突破，**AI Agent（智能体）** 已成为把 AI 落地到真实业务的关键形态——它能自主规划、调用工具、读写文件、串联多步流程。但市面上资料往往零散、过时，且停留在 2025 年之前的旧生态。

本项目把「学 Agent 开发」整理成一条**循序渐进的路线**：从「什么是 Agent」讲起，到 LLM 原理、Prompt、ReAct、Tool Calling、RAG、记忆，再到 LangChain / LangGraph / MCP 等框架实战、多 Agent 系统设计与编排，最后展望 Agent OS、具身智能、AGI 等前沿方向。内容已全部同步至 **2026 年 7 月** 的真实生态（GPT-5 / Claude Opus 4.8 / Gemini 3.5 / Llama 4、MCP 归 Linux 基金会治理、Agentic 编码平台成熟）。

它不是一份文档，而是一个**可交互的网页应用**：每个知识点都配有可视化图表、可复制的运行代码、企业级真实案例，以及即时测验，帮助边学边练。

### 谁适合用

- 想系统入门 AI Agent 开发的工程师、学生、技术爱好者
- 已会写 LLM 调用，但想搞懂 RAG / 多 Agent / 框架选型的开发者
- 需要把 Agent 落地到客服、代码审查、数据分析等业务的团队

### 特性

- **6 大章节 51 小节** 完整知识体系
- **极客科技风** 深色主题（霓虹紫/青色点缀）
- **代码高亮** + 一键复制 + 预期输出
- **Mermaid 流程图** + 架构图可视化
- **进度追踪** localStorage 本地存储
- **测验系统** 59 道题 + 章节综合测验
- **企业级案例** 每小节含真实场景案例
- **响应式设计** 支持手机/平板/桌面
- **零依赖** 纯静态 HTML/CSS/JS

## 章节结构

1. **基础概念入门** - Agent 定义、LLM 原理、Prompt 基础
2. **核心原理深入** - ReAct、Tool Calling、RAG、记忆管理、评估
3. **框架与工具实战** - LangChain、LangGraph、MCP、可观测性
4. **多 Agent 系统设计** - 架构模式、协作、长任务编排、HITL
5. **行业应用与最佳实践** - 客服、代码审查、数据分析、部署、安全
6. **前沿趋势展望** - Agent OS、具身智能、AGI、多模态

## 如何启动

本项目是**纯静态网站**（零依赖、零构建），不需要安装 npm 包或编译。只需一个能托管静态文件的本地服务器即可。

### 方式一：Python 内置服务器（最简单，推荐）

```bash
# 1. 进入项目目录
cd /Users/ebond/Workbuddy/agent

# 2. 启动本地服务器（8080 为端口号，可自定义）
python3 -m http.server 8080

# 3. 浏览器打开
#    http://localhost:8080
```

> 说明：项目使用 **Hash 路由**（`#/chapter-1` 这类地址），因此用任意静态服务器托管都能正常工作，不会因路径刷新而 404。

### 方式二：Node.js 服务器

```bash
# 需要本地装有 Node.js
cd /Users/ebond/Workbuddy/agent
npx serve .
# 或
npx http-server -p 8080
# 启动后终端会打印访问地址，默认多为 http://localhost:3000 或 http://localhost:8080
```

### 方式三：VS Code Live Server

1. 用 VS Code 打开项目文件夹
2. 安装扩展 **Live Server**
3. 右键 `index.html` → **Open with Live Server**
4. 浏览器自动打开预览地址（默认 `http://localhost:5500`）

### 方式四：直接双击打开（零环境，推荐给初学者）

无需任何服务器或联网，直接**双击 `index.html`** 用浏览器打开即可（`file://` 协议）。

> 项目已将所有教学内容内联进 `assets/js/data.js`（以 `window.__DATA__` 变量提供），因此**不依赖 `fetch()` 加载 JSON**，可完全离线、双击运行。代码高亮（highlight.js）与流程图（Mermaid）依赖 CDN，离线时仅图表降级，文字内容不受影响。

### 启动后看不到内容？排查清单

- **端口被占用**：换一个端口，例如 `python3 -m http.server 9000`，再访问 `http://localhost:9000`。
- **页面空白 / 内容不加载**：本项目已内联全部数据，**支持直接双击 `index.html`（`file://`）打开，也支持任意 HTTP 服务器**。若仍空白，请确认 `assets/js/data.js` 与 `index.html` 在同一目录层级未被误删；必要时改用方式一/二的本地服务器排查。
- **图表（Mermaid）不显示**：Mermaid 与代码高亮依赖 CDN，首次打开需联网；离线环境会看到降级样式，但文字内容不受影响。
- **端口占用快速查杀**（macOS）：`lsof -i :8080` 找到 PID 后 `kill <PID>`。

### 自定义与二次开发

- **改内容**：所有教学内容在 `assets/data/*.json`，按需编辑后刷新浏览器即可生效（无需重建）。
- **改样式**：主题配色集中在 `assets/css/variables.css`（CSS 变量）。
- **部署上线**：把整个项目目录（含 `index.html` 与 `assets/`）上传到任意静态托管即可（GitHub Pages / Vercel / Nginx / 对象存储均可）。

## 项目结构

```
agent/
├── index.html              # 单页应用入口
├── assets/
│   ├── css/                # 6 个 CSS 文件
│   │   ├── variables.css   # CSS 变量（配色/字体/间距）
│   │   ├── base.css        # 基础样式
│   │   ├── layout.css      # 布局（侧边栏/内容区/响应式）
│   │   ├── components.css  # 组件（卡片/代码块/测验）
│   │   ├── syntax.css      # 语法高亮
│   │   └── animations.css  # 动画
│   ├── js/                 # 8 个 JS 模块
│   │   ├── app.js          # 应用入口
│   │   ├── router.js       # Hash 路由
│   │   ├── renderer.js     # 内容渲染引擎
│   │   ├── progress.js     # 进度追踪
│   │   ├── quiz.js         # 测验系统
│   │   ├── codeblock.js    # 代码块组件
│   │   ├── mermaid-init.js # Mermaid 初始化
│   │   └── utils.js        # 工具函数
│   └── data/               # 10 个 JSON 数据文件
│       ├── chapters.json   # 章节元数据
│       ├── chapter-1.json  # 第 1-6 章内容
│       ├── ...
│       ├── quizzes.json    # 测验题库
│       ├── glossary.json   # 术语速查表
│       └── appendix.json   # 附录
└── README.md
```

## 技术栈

- **HTML/CSS/JS** - 零构建、零依赖
- **highlight.js** (CDN) - 代码语法高亮
- **Mermaid.js** (CDN) - 流程图/架构图
- **Google Fonts** - Inter / JetBrains Mono / Noto Sans SC
- **localStorage** - 进度追踪存储

## 学习路线

| 章节 | 时长 | 难度 | 核心内容 |
|------|------|------|----------|
| 第 1 章 基础概念 | 8h | ★☆☆ | Agent 定义、LLM 原理、Prompt |
| 第 2 章 核心原理 | 20h | ★★★ | ReAct、RAG、Tool Calling |
| 第 3 章 框架实战 | 18h | ★★★ | LangChain、LangGraph、MCP |
| 第 4 章 多 Agent | 15h | ★★★★ | 架构模式、协作、HITL |
| 第 5 章 行业应用 | 25h | ★★★★ | 企业项目、部署、安全 |
| 第 6 章 前沿趋势 | 10h | ★★☆ | Agent OS、AGI、多模态 |

## 链接

- 🌐 **在线访问**：https://18232751914.github.io/agent-learning-path/
- 💻 **GitHub 仓库**：https://github.com/18232751914/agent-learning-path
- ⭐ 欢迎 Star / Fork / Issue 反馈

## License

MIT
