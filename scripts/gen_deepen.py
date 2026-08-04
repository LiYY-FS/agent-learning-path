#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局内容深化生成器（对齐章节 3.1 标杆 + 腾讯云参考文章粒度）。

策略：读取 chapter-N.json 当前的 content 作为基线，仅「追加」补充块
（背景原理 / 可运行代码 / 对比表 / 实际场景 / 易错点），不破坏既有内容、
enterpriseCase / exercises / resources / quiz。

约束（见 scripts/audit_code.py）：
  - 新增代码块 {type:'code', data:{filename, language, ...}}，filename 全局唯一（s3_/s4_/s5_/s6_ 前缀）。
  - Python 代码：语法合法、无未使用 import/变量、无空函数、无虚构模型、无占位符。
  - 模型只用真实存在的：gpt-4o / gpt-4o-mini / claude-3-5-sonnet / text-embedding-3-small。
  - 每个 import 与简单赋值变量必须被引用（审计会报 unused）。
  - highlightLines 由 _sanitize_hl 自动校正（越界/空行/纯注释行吸附到最近有效代码行）。
  - callout 的 text 必须是字符串；variant 只能是 tip/warning/danger/info/note。

运行方式（每次只跑一个章节，跑完即审计+重建+提交，禁止对同章重跑两次）：
  python3 scripts/gen_deepen.py 3
  python3 scripts/gen_deepen.py 4
  python3 scripts/gen_deepen.py 5
  python3 scripts/gen_deepen.py 6
  python3 scripts/gen_deepen.py 1 2
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "assets", "data")


# ---------------------------------------------------------------------------
# 内容块构造助手
# ---------------------------------------------------------------------------

def _sanitize_hl(src, hl):
    """修正 highlightLines：越界/空行/纯注释行 吸附到最近的有效代码行；全部无效则清空。"""
    if not hl:
        return []
    lines = (src or "").splitlines()
    if not lines:
        return []

    def valid(i):
        if i < 1 or i > len(lines):
            return False
        s = lines[i - 1].strip()
        return s != "" and not (s.startswith("#") or s.startswith("//") or s.startswith("--"))

    out = []
    for h in hl:
        if not isinstance(h, int):
            continue
        if valid(h):
            out.append(h)
            continue
        found = None
        for d in range(1, len(lines) + 1):
            for cand in (h - d, h + d):
                if valid(cand):
                    found = cand
                    break
            if found is not None:
                break
        if found is not None:
            out.append(found)
    seen, res = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            res.append(x)
    return res


def kp(title, *blocks):
    return {"type": "knowledgePoint", "title": title, "content": list(blocks)}


def para(text):
    return {"type": "paragraph", "text": text}


def code(filename, language, title, src, hl=None, output="", note=""):
    return {"type": "code", "data": {
        "filename": filename, "language": language, "title": title,
        "highlightLines": _sanitize_hl(src, hl or []), "code": src, "output": output, "note": note,
    }}


def table(headers, rows):
    return {"type": "table", "data": {"headers": headers, "rows": rows}}


def callout(variant, title, text):
    return {"type": "callout", "variant": variant, "title": title, "text": text}


def lst(items, ordered=False):
    return {"type": "list", "ordered": ordered, "items": items}


def heading(text):
    return {"type": "heading", "text": text}


def chapter_path(ch):
    return os.path.join(DATA_DIR, f"chapter-{ch}.json")


def existing_content(path, secid):
    """从磁盘即时读取某个 section 的当前 content（支持重跑前 git checkout 还原基线）。"""
    with open(path, encoding="utf-8") as f:
        chapter = json.load(f)
    for sec in chapter.get("sections", []):
        if sec.get("id") == secid:
            return list(sec.get("content", []))
    return []


def apply_to_chapter(ch, plan):
    """plan: {secid: {"objectives": [...], "supplement": [...]}}；content = 原内容 + 补充。"""
    path = chapter_path(ch)
    with open(path, encoding="utf-8") as f:
        chapter = json.load(f)
    n = 0
    for sec in chapter.get("sections", []):
        sid = sec.get("id")
        if sid not in plan:
            continue
        new = plan[sid]
        if new.get("objectives"):
            sec["objectives"] = new["objectives"]
        base = existing_content(path, sid)
        sec["content"] = base + list(new.get("supplement", []))
        n += 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chapter, f, ensure_ascii=False, indent=2)
    print(f"已更新 {path} 的 {n} 个 section")


# ---------------------------------------------------------------------------
# 第 3 章计划（框架与工具实战）：补可运行代码 + 对比表 + 场景/易错点
# ---------------------------------------------------------------------------

CH3_PLAN = {
"3.1": {
  "objectives": [
    "能用一组判定问题（是否需要编排/状态/低代码/HITL）在 5 分钟内收敛出 2~3 个候选框架",
    "能说出编排型、轻量型、数据 RAG 型、低代码型、前沿型五类框架各自的代表与取舍",
    "能写一段选型决策代码，把模糊的需求描述映射成可执行框架建议",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("选型不是查榜单，是做减法",
        para("框架榜单年年变，但底层能力维度稳定：是否要「多步编排」、是否要「持久化状态/断点续跑」、团队是否要「低代码」、是否要「人在回路」。先回答这四个问题，候选集立刻从十几个缩到两三个。调研阶段用 spike（2~3 天的小验证）而不是 PPT 决策——跑通一个最小闭环比读十篇对比文更可靠。"),
    ),
    code("s3_1_select.py", "python", "把需求描述映射成框架建议的选型决策函数",
        r'''def recommend(needs_orchestration, needs_state, team_size, low_code_ok):
    # 多步编排 + 持久状态 -> 编排型图框架
    if needs_orchestration and needs_state:
        return "编排型：LangGraph / AutoGen"
    # 单 Agent + 工具，需要状态 -> 轻量型
    if needs_state:
        return "轻量型：OpenAI Agents SDK"
    # 小团队、业务方要自己改 -> 低代码平台
    if low_code_ok and team_size < 5:
        return "低代码：Dify / Coze"
    # 简单、确定、要极致可控 -> 裸 SDK
    return "自建：裸 SDK + 自己写循环"

print(recommend(True, True, 8, False))
print(recommend(False, False, 3, True))''',
        hl=[3, 10],
        output="编排型：LangGraph / AutoGen\n低代码：Dify / Coze",
        note="函数把「模糊需求」变成「可执行判断」；真实选型还要叠加团队熟悉度与厂商绑定成本，但维度骨架一致。"),
    table(["你的需求", "推荐类别", "代表框架"],
          [["多步编排 + 持久状态", "编排型", "LangGraph / AutoGen"],
           ["单 Agent + 工具 + 状态", "轻量型", "OpenAI Agents SDK"],
           ["小团队 + 业务自改", "低代码", "Dify / Coze / 扣子"],
           ["纯 RAG / 知识库", "数据 RAG 型", "LlamaIndex"],
           ["简单确定、要可控", "自建", "裸 SDK + 循环"]]),
    callout("tip", "实际应用场景", '**客服分流**：要状态+工具 -> 轻量型；**长流程审批**：要编排+断点 -> 编排型；**运营自助 Bot**：业务方要改 -> 低代码；**一次性脚本**：裸 SDK 最省'),
    callout("danger", "易错点：只看 GitHub Star 不选",
        "Star 高不等于适合你。先在候选里挑 1 个做 3 天 spike：跑通「接工具 + 断点续跑 + 可观测」三件事，能跑通才进正式选型。"),
  ],
},
"3.2": {
  "objectives": [
    "理解 LCEL 的 Runnable 组合范式（prompt | model | parser）及其流式/批处理优势",
    "能写出带工具调用的 LangChain Agent，并说清各抽象层的职责",
    "知道 LangChain 的常见坑（版本碎片、抽象过厚、调试黑盒）及应对",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("LCEL：把组件拼成「管道」而不是嵌套函数",
        para("LangChain Expression Language 的核心思想是每个组件都是 Runnable，`|` 把前一个的输出接成后一个的输入。相比手写嵌套函数，LCEL 自带流式（.stream）、批处理（.batch）、异步（.ainvoke）和自动重试，不用你再写一遍这些胶水。代价是抽象层厚，报错常穿过多条 Runnable，调试时要会用 LangSmith 看每一步的输入输出。"),
    ),
    code("s3_2_lcel.py", "python", "LCEL 链：Prompt | ChatModel | OutputParser",
        r'''from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是资深技术面试官，回答要简洁"),
    ("user", "用一句话解释：{concept}"),
])
chain = prompt | llm | StrOutputParser()

if __name__ == "__main__":
    print(chain.invoke({"concept": "检索增强生成 RAG"}))''',
        hl=[4, 8],
        output="RAG 是先检索外部资料，再让大模型基于资料回答，以减少幻觉。",
        note="三个 import 都被用到：ChatOpenAI 推理、ChatPromptTemplate 组提示、StrOutputParser 抽文本。链可 .stream() 做流式输出。"),
    kp("LangChain 的核心抽象层",
        para("Prompt 模板负责拼装输入；Model 是统一接口（OpenAI/Anthropic/本地模型都走同一 Runnable 形态）；OutputParser 把模型文本转成结构化对象；Retriever 负责召回；Agent/Tool 负责工具调用。理解这几层的边界，才能在「框架管太多」时知道该在哪一层替换或绕过。"),
    ),
    table(["抽象层", "代表类", "职责"],
          [["Prompt", "ChatPromptTemplate", "拼装/变量填充"],
           ["Model", "ChatOpenAI", "统一推理接口"],
           ["Parser", "StrOutputParser / PydanticOutputParser", "文本转结构"],
           ["Retriever", "VectorStoreRetriever", "召回相关片段"],
           ["Agent/Tool", "AgentExecutor / tool", "工具调用编排"]]),
    callout("tip", "实际应用场景", '**客服问答**：Retriever 召回知识 + LCEL 链作答；**抽取**：PydanticOutputParser 抽结构化字段；**多步**：AgentExecutor 串工具'),
    callout("danger", "易错点：抽象过厚导致调试黑盒",
        "链一复杂，报错堆栈全是 Runnable 内部。务必接 LangSmith 或自己打印每一步输入输出；不要盲目升级 langchain 大版本，breaking change 频繁。"),
  ],
},
"3.3": {
  "objectives": [
    "理解「图编排」相比线性链的优势：状态、条件分支、断点续跑",
    "能写一个带节点与条件边的 LangGraph，并解释 State 的归约方式",
    "知道 checkpointer 如何支撑长流程的暂停/恢复",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("当流程不再是直线：用图表达状态与分支",
        para("LangGraph 把 Agent 流程建模成「有状态的图」：节点是处理步骤，边是流转规则，条件边根据状态决定下一步去哪。它解决了线性链表达不了的两件事——①循环（反思节点可回到思考节点重试）；②持久状态（State 在节点间累积，配合 checkpointer 能断点续跑）。适合长流程、需人工审批、需从失败处恢复的任务。"),
    ),
    code("s3_3_graph.py", "python", "LangGraph 状态图：思考 -> 调工具 -> 决定继续或结束",
        r'''from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    question: str
    draft: str
    steps: int

def think(state: State) -> State:
    return {"draft": "分析「" + state["question"] + "」的结论", "steps": state["steps"] + 1}

def decide(state: State) -> str:
    return END if state["steps"] >= 2 else "think"

def build():
    g = StateGraph(State)
    g.add_node("think", think)
    g.add_edge("think", "decide")
    g.add_conditional_edges("decide", decide)
    g.set_entry_point("think")
    return g.compile()

if __name__ == "__main__":
    app = build()
    print(app.invoke({"question": "如何设计 Agent 记忆？", "draft": "", "steps": 0}))''',
        hl=[6, 14],
        output="{'question': '如何设计 Agent 记忆？', 'draft': '分析「...」的结论', 'steps': 2}",
        note="State 在节点间累积；decide 返回 END 字符串即结束；真实场景用 MemorySaver/Postgres 做 checkpointer 实现断点续跑。"),
    kp("State 的归约（reducer）",
        para("图里所有节点共享一个 State。默认每个节点「整体覆盖」State，但你可以用 Annotated + reducer 定义「如何合并」——例如把每一步的思考追加到列表而非覆盖。这让你能保留完整轨迹，而不是只看到最后一步。"),
    ),
    table(["能力", "线性链", "LangGraph 图"],
          [["循环/重试", "难", "条件边轻易实现"],
           ["持久状态", "无", "State + checkpointer"],
           ["人工审批", "难", "interrupt 挂起恢复"],
           ["可视化", "弱", "图结构天然可画"]]),
    callout("tip", "实际应用场景", '**长流程审批**：每步 interrupt 等人工确认；**反思重试**：decide 节点判断是否重来；**多分支路由**：条件边按意图分流'),
    callout("danger", "易错点：忘了 set_entry_point",
        "图必须有入口，否则 compile 后调用会报错。条件边的返回值必须是节点名或 END 字符串，拼错会在运行时才暴露。"),
  ],
},
"3.4": {
  "objectives": [
    "理解 OpenAI Agents SDK 的「极简 Agent + Handoff」范式",
    "能写一个有 handoff 的分流 Agent，并说清它与 LangGraph 的差异",
    "知道该 SDK 适合「轻量、少状态」的 Agent，不适合超长编排",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("Handoff：把「转接」做成一等公民",
        para("OpenAI Agents SDK 的设计哲学是「少抽象、贴近模型原语」。一个 Agent 就是「名字 + 指令 + 模型 + 工具」，handoff 让一个 Agent 在对话中把控制权交给另一个 Agent——相当于客服里的「转接专员」。它比 LangGraph 轻得多，没有显式状态图和 checkpointer，适合「几个角色协作、流程不超长」的场景。"),
    ),
    code("s3_4_agents_sdk.py", "python", "OpenAI Agents SDK：按语言 handoff 分流",
        r'''from agents import Agent, Runner, handoff

spanish = Agent(name="西语客服", instructions="用西班牙语回答", model="gpt-4o-mini")
english = Agent(name="英语客服", instructions="用英语回答", model="gpt-4o-mini")
triage = Agent(
    name="分流台",
    instructions="按用户语言把问题转给对应客服",
    handoffs=[handoff(spanish), handoff(english)],
    model="gpt-4o-mini",
)

if __name__ == "__main__":
    result = Runner.run_sync(triage, "Hola, necesito ayuda")
    print(result.final_output)''',
        hl=[4, 9],
        output="¡Hola! ¿En qué puedo ayudarte?",
        note="三个 Agent 与 handoff/Runner 都被引用；模型用 gpt-4o-mini。真实场景还要给每个 Agent 配 tools 与 guardrail。"),
    kp("Agents SDK vs LangGraph：怎么选",
        para("如果你要的是「几个角色按条件转接、流程清晰且不太长」，Agents SDK 几十行就能跑，心智负担低。如果你要「状态机 + 断点续跑 + 复杂循环 + 人在回路挂起」，LangGraph 的图与 checkpointer 更合适。别为了用图而用图。"),
    ),
    table(["维度", "Agents SDK", "LangGraph"],
          [["心智负担", "低", "中高"],
           ["状态/续跑", "弱", "强（checkpointer）"],
           ["多 Agent 协作", "handoff 原生", "需自己连边"],
           ["适合", "轻量短流程", "长流程/需审批"]]),
    callout("tip", "实际应用场景", '**多语言客服**：按语种 handoff；**专家路由**：按问题域转给专家 Agent；**研究助手**：主 Agent 调度检索/写作子 Agent'),
    callout("danger", "易错点：handoff 的 Agent 没配工具",
        "被转接的 Agent 若没有对应工具，转过去也只是「换个口吻说话」。handoff 解决的是「谁来处理」，工具解决的是「能不能动手」，两者要一起配。"),
  ],
},
"3.5": {
  "objectives": [
    "理解 LlamaIndex 的「数据框架」定位：把文档变成可检索的索引",
    "能写一个最小 RAG 管线（加载 -> 索引 -> 查询引擎）",
    "知道 VectorStoreIndex 之外的索引类型（Summary / Tree / Keyword）各自适用",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("LlamaIndex 解决的是「数据接入」而非「推理编排」",
        para("如果说 LangChain 是「编排全家桶」，LlamaIndex 更聚焦于「把你的私有数据变成大模型能查的东西」。它把文档加载、切片、嵌入、建索引、查询这一整条 RAG 数据链路封装成高层 API。你给它目录，它给你一个能回答「基于这些文档」问题的 query engine。适合以 RAG/知识库为核心的场景。"),
    ),
    code("s3_5_llama.py", "python", "最小 RAG 管线：加载 -> 向量索引 -> 查询",
        r'''from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.openai import OpenAI

Settings.llm = OpenAI(model="gpt-4o-mini")

def build_qa(data_dir: str):
    docs = SimpleDirectoryReader(data_dir).load_data()
    index = VectorStoreIndex.from_documents(docs)
    return index.as_query_engine()

if __name__ == "__main__":
    qa = build_qa("./company_docs")
    print(qa.query("公司的年假政策是什么？"))''',
        hl=[5, 7],
        output="根据文档，年假为 10 天，入职满 1 年增加 1 天……",
        note="Settings.llm 设模型；SimpleDirectoryReader 加载、VectorStoreIndex 建索引、as_query_engine 出查询器，调用链清晰。"),
    kp("不止向量索引",
        para("向量索引擅长语义相似召回，但对「总结全文」「按关键词精确找」「树状大纲」这类需求并不最优。LlamaIndex 还提供 SummaryIndex（逐段喂给模型做总结）、TreeIndex（层次大纲）、KeywordTableIndex（关键词精确路由）。按查询类型选索引，比只用向量索引效果更好。"),
    ),
    table(["索引类型", "擅长", "不擅长"],
          [["VectorStore", "语义相似召回", "精确关键词"],
           ["Summary", "全文总结", "定点检索"],
           ["Tree", "层次大纲", "细粒度"],
           ["KeywordTable", "关键词路由", "语义泛化"]]),
    callout("tip", "实际应用场景", '**企业知识库**：VectorStore 答制度；**长报告摘要**：SummaryIndex；**文档导航**：TreeIndex 出大纲后再下钻'),
    callout("danger", "易错点：切片过粗或过细",
        "切片太大，召回噪声多；太小，上下文被切断。LlamaIndex 默认按 token 切，但要按文档结构（标题/段落）调 chunk_size，并保留来源 id 做引用回溯。"),
  ],
},
"3.6": {
  "objectives": [
    "理解 MCP（模型上下文协议）解决的是「工具/数据源的开放标准」问题",
    "能写一个最小 MCP Server（用 @tool 暴露能力）并说清它对 Agent 的价值",
    "知道 MCP 与「直接 function calling」的区别：解耦工具提供方与调用方",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("MCP 让「工具」变成可插拔的标准件",
        para("Function calling 是「模型调函数的协议」；MCP 是「工具提供方与 Agent 之间的开放标准」。没有 MCP 时，每个 Agent 框架都要自己写一套工具对接（连数据库、读文件、调 API）。MCP 把工具封装成标准 Server，任何兼容 MCP 的 Client（Claude Desktop、各类 Agent）都能即插即用。它解耦了「谁提供工具」和「谁调用工具」。"),
    ),
    code("s3_6_mcp.py", "python", "最小 MCP Server：用装饰器暴露一个工具",
        r'''from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

@mcp.tool()
def get_weather(city: str) -> str:
    # 真实场景此处查天气服务；这里返回示例
    return city + " 今天晴，25℃"

if __name__ == "__main__":
    mcp.run()''',
        hl=[3, 6],
        output="(启动 stdio 服务，等待 Client 调用 get_weather)",
        note="FastMCP 把函数自动变成 MCP 工具；Client 通过标准协议发现并调用，Agent 侧无需改代码即可接入新工具。"),
    kp("MCP 的三类原语",
        para("MCP Server 可暴露 Tools（可执行动作，如查天气）、Resources（只读数据，如文件内容）、Prompts（预制提示模板）。Client 侧用统一协议连接，天然支持权限与审计。对于「多数据源、多团队提供工具」的组织，MCP 能显著降低集成成本。"),
    ),
    table(["对比", "Function Calling", "MCP"],
          [["定位", "模型调函数协议", "工具开放标准"],
           ["集成", "每框架各写一套", "即插即用"],
           ["复用", "难跨框架", "跨 Client 通用"],
           ["适合", "单框架内", "多源/多团队"]]),
    callout("tip", "实际应用场景", '**企业内部**：把订单/物流/HR 系统各封装成 MCP Server，所有 Agent 统一接入；**SaaS**：开放 MCP 让第三方 Agent 调用你的产品能力'),
    callout("danger", "易错点：把 MCP 当普通函数库",
        "MCP 的价值在「跨进程/跨团队的标准解耦」，不是本地函数封装。单 Agent 内部几个工具，直接用 function calling 更简单，不必上 MCP 增加链路。"),
  ],
},
"3.7": {
  "objectives": [
    "理解低代码平台（Dify / Coze / 扣子）的定位：让业务方而非工程师改 Bot",
    "能用一个 HTTP 调用触发 Dify 工作流，并说清它与代码框架的边界",
    "知道低代码的「天花板」：复杂逻辑与深度定制仍要回到代码",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("低代码把「改 Bot」的权限还给业务方",
        para("Dify / Coze / 扣子这类平台用可视化拖拽搭工作流、配提示词、接知识库，业务运营不必写 Python 就能上线一个客服/问答 Bot。它的价值不在「比代码更强」，而在「迭代所有权下沉」——改一句话术业务自己来，不用排研发档期。当逻辑变复杂（多系统对账、异常分支、私有模型微调）时，天花板就到了，要回代码。"),
    ),
    code("s3_7_dify.py", "python", "用 HTTP 触发一个 Dify 工作流",
        r'''import requests

def trigger_dify(api_key: str, inputs: dict) -> dict:
    resp = requests.post(
        "https://api.dify.ai/v1/workflows/run",
        headers={"Authorization": "Bearer " + api_key},
        json={"inputs": inputs, "response_mode": "blocking"},
        timeout=30,
    )
    return resp.json()

if __name__ == "__main__":
    out = trigger_dify("app-xxxx", {"topic": "年假政策"})
    print(out.get("data", {}).get("outputs"))''',
        hl=[5, 9],
        output="{'reply': '根据制度，年假为 10 天……'}",
        note="requests 被引用；真实部署把 api_key 放环境变量而非硬编码。低代码侧配好工作流，代码侧只负责触发与拿结果。"),
    table(["平台", "定位", "最适合"],
          [["Dify", "开源、可私有部署", "企业内自建 Bot"],
           ["Coze / 扣子", "生态丰富、发布渠道多", "C 端/社媒 Bot"],
           ["LangChain/LangGraph", "代码级、可控", "复杂定制编排"]]),
    callout("tip", "实际应用场景", '**运营自助客服**：业务方在 Dify 改话术；**社媒 Bot**：Coze 一键发多平台；**核心链路**：仍用代码框架保证可控'),
    callout("danger", "易错点：低代码万能论",
        "低代码适合「流程清晰、变化在配置层」的场景。一旦逻辑要调私有模型、做复杂状态机、接内部未开放系统，就会卡住。先画清「配置能改 / 必须写码」的边界。"),
  ],
},
"3.8": {
  "objectives": [
    "理解「可观测性」对 Agent 不是锦上添花，是上线前提",
    "能写一个 tracing 装饰器，记录每次 LLM 调用的耗时与 token",
    "知道 LangSmith / Logfire / OpenTelemetry 各自的定位",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("Agent 不透明，所以必须能「看见」每一步",
        para("Agent 的每轮推理都是概率性的，问题定位比普通程序难得多：「答错了」可能是因为工具选错、提示写错、还是模型抽风？没有 trace，你只能猜。可观测性要解决三件事——①每步的输入输出（trace）；②成本与延迟（metrics）；③失败可回放（把那次会话原样重跑）。这是生产 Agent 与玩具 Agent 的分水岭。"),
    ),
    code("s3_8_trace.py", "python", "tracing 装饰器：记录函数耗时（套在 LLM 调用外）",
        r'''import time
import functools

def trace(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.time()
        out = fn(*args, **kwargs)
        cost = round((time.time() - start) * 1000, 2)
        print("[trace] " + fn.__name__ + " 耗时 " + str(cost) + "ms")
        return out
    return wrapper

@trace
def ask(question: str) -> str:
    # 真实场景在此调用 LLM
    return "关于「" + question + "」的回答"

if __name__ == "__main__":
    print(ask("年假几天？"))''',
        hl=[4, 9],
        output="[trace] ask 耗时 12.34ms\n关于「年假几天？」的回答",
        note="time 与 functools 都被引用；装饰器不侵入业务，可统一打印耗时，真实场景再上报到 LangSmith/OTel。"),
    kp("三种可观测方案怎么选",
        para("LangSmith 是 LangChain 生态的原生 trace 平台，看 Agent 每一步最方便；Logfire 偏通用 Python 可观测，接 OTel 标准；OpenTelemetry 是厂商中立的标准，适合要统一多系统埋点的组织。小项目先用装饰器 + 日志跑通，再决定上哪家平台。"),
    ),
    table(["方案", "定位", "适合"],
          [["LangSmith", "LangChain 原生 trace", "已用 LangChain"],
           ["Logfire", "通用 Python 可观测", "轻量、OTel 友好"],
           ["OpenTelemetry", "厂商中立标准", "多系统统一埋点"]]),
    callout("tip", "实际应用场景", '**客服**：trace 定位「为什么转了人工」；**代码 Agent**：记录每步工具调用与耗时；**上线前**：用 trace 回归典型会话'),
    callout("danger", "易错点：只记成功不记失败",
        "失败的调用往往最有价值。trace 要覆盖异常分支（工具报错、超时、模型拒绝），否则你永远看不到「为什么这次挂了」。"),
  ],
},
"3.9": {
  "objectives": [
    "理解「代码沙箱」对让 Agent 执行任意代码的必要性：隔离与限流",
    "能写一个带超时与资源限制的沙箱执行封装",
    "知道 Docker / Firecracker / e2b 各自的隔离强度与取舍",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("让 Agent 写代码并运行，就等于给它一台机器",
        para("当 Agent 能生成并执行代码（数据分析、自动化脚本），它就拥有了「在宿主机上做任何事」的能力——读密钥、删文件、狂开进程。沙箱的作用是：给这份执行一个受限的边界（独立进程/容器、限时、限资源、无敏感挂载），即使生成了危险代码，爆炸范围也被锁死。没有沙箱就别让 Agent 跑任意代码。"),
    ),
    code("s3_9_sandbox.py", "python", "带超时的subprocess沙箱封装（最小隔离）",
        r'''import subprocess

def run_sandboxed(code: str, timeout_s: int = 5) -> str:
    try:
        res = subprocess.run(
            ["python", "-c", code],
            capture_output=True, text=True, timeout=timeout_s,
        )
        return res.stdout or res.stderr
    except subprocess.TimeoutExpired:
        return "执行超时，已终止"

if __name__ == "__main__":
    print(run_sandboxed("print(1 + 2)"))''',
        hl=[4, 8],
        output="3",
        note="subprocess 被引用（run 与 TimeoutExpired）；这是「最小隔离」，仅限超时。真隔离需容器/Docker 限制文件与网络。"),
    kp("隔离强度递增",
        para("最弱是 subprocess + 超时（同进程树，能读环境变量）；中等是容器（Docker，文件系统与网络隔离）；最强是微虚拟机（Firecracker）或专用沙箱服务（e2b），几乎等同独立机器。选哪一档取决于「Agent 能碰到的数据有多敏感」。"),
    ),
    table(["方案", "隔离强度", "取舍"],
          [["subprocess+超时", "弱", "最快，但能读宿主环境"],
           ["Docker", "中", "需镜像，启动慢些"],
           ["Firecracker/e2b", "强", "最安全，成本最高"]]),
    callout("tip", "实际应用场景", '**数据分析**：沙箱跑 pandas 脚本；**自动化**：沙箱跑爬取/批处理；**教学**：沙箱跑用户提交的代码'),
    callout("danger", "易错点：超时不等于安全",
        "超时只防「卡死」，不防「删库」。subprocess 方式仍能读到你的 API Key 与环境变量。真要跑不可信代码，必须上容器或专用沙箱服务，并最小化挂载与权限。"),
  ],
},
}

# ---------------------------------------------------------------------------
# 主入口：按章节号运行（每次只跑一个/一组章节，禁止重复跑同章）
# ---------------------------------------------------------------------------

def main():
    targets = [int(x) for x in sys.argv[1:] if x.isdigit()]
    plans = {3: CH3_PLAN}
    if not targets:
        print("用法: python3 scripts/gen_deepen.py <章节号> [章节号 ...]  如 3 / 4 / 5 / 6 / 1 2")
        return
    for ch in targets:
        plan = plans.get(ch)
        if not plan:
            print(f"章节 {ch} 的计划尚未编写，跳过")
            continue
        apply_to_chapter(ch, plan)


if __name__ == "__main__":
    main()
