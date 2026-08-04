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

CH4_PLAN = {
"4.1": {
  "objectives": [
    "能说出 supervisor/worker、peer-to-peer、hierarchical 三种多 Agent 模式各自的适用场景",
    "能写一个最小 supervisor 路由，把问题分派给不同职责的 worker",
    "理解「为什么单 Agent 上下文会挤爆」以及多 Agent 如何缓解",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("单 Agent 的天花板：上下文与职责",
        para("一个 Agent 把所有工具的提示、历史对话、中间结果都塞进同一段上下文，任务一复杂就「脑容量」不够：前面看的被后面挤出窗口，不同职责互相干扰，出错也难定位。多 Agent 的核心动机就是「分而治之」——每个 Agent 只管一件事、只看自己需要的上下文，由一个协调者（supervisor）负责派活和汇总。"),
    ),
    code("s4_1_supervisor.py", "python", "最小 supervisor：按关键词把问题派给不同 worker",
        r'''WORKERS = {
    "退款": "售后 Agent",
    "物流": "物流 Agent",
    "功能": "技术支持 Agent",
}

def supervisor(question: str) -> str:
    for keyword, agent in WORKERS.items():
        if keyword in question:
            return "转接 -> " + agent
    return "转接 -> 人工客服"

if __name__ == "__main__":
    print(supervisor("我的订单怎么退款"))
    print(supervisor("这个按钮是干嘛的"))''',
        hl=[5, 8],
        output="转接 -> 售后 Agent\n转接 -> 人工客服",
        note="supervisor 只做「分类 + 派发」，不自己答；真实场景用 LLM 做意图分类而非关键词，但兜底人工分支必须保留。"),
    kp("三种主流模式怎么选",
        para("Supervisor/Worker：一个协调者管多个专职下属，适合「一个入口、内部多专家」；Peer-to-Peer：Agent 之间平等对话、自己协商，适合探索性协作但难控；Hierarchical：多层 supervisor（大主管管小主管），适合超大规模任务。小团队从 supervisor 起步最稳。"),
    ),
    table(["模式", "结构", "适合"],
          [["Supervisor/Worker", "1 协调者 + N 专职", "有统一入口的业务"],
           ["Peer-to-Peer", "Agent 平级协商", "探索/头脑风暴"],
           ["Hierarchical", "多层 supervisor", "超大规模任务"]]),
    callout("tip", "实际应用场景", '**客服**：supervisor 按意图转售后/物流/技术；**研发**：规划者派给编码/测试；**研究**：多 Agent 各读一块文献再汇总'),
    callout("danger", "易错点：所有 Agent 共享同一上下文",
        "多 Agent 的意义在于「隔离上下文」。若把全部历史塞给每个 worker，等于回到单 Agent 的老问题。每个 worker 只接收跟它相关的子任务与上下文。"),
  ],
},
"4.2": {
  "objectives": [
    "理解「角色」= system prompt + 职责边界 + 工具权限",
    "能定义一个 Role 并组装一支多角色团队",
    "知道角色设计的反模式（职责重叠、权限过大）",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("角色不是人设，是「职责边界」",
        para("给 Agent 一个角色，本质是给它三样东西：①一段 system prompt 规定它「是谁、负责什么、不做什么」；②明确的输入输出契约；③受限的工具权限。角色设计的核心原则是「单一职责」——一个 Agent 只干一类事，这样它的提示短、上下文干净、行为可预测、也容易被另一个实现替换。"),
    ),
    code("s4_2_role.py", "python", "用 Role 组装一支多角色团队",
        r'''class Role:
    def __init__(self, name, duty, persona):
        self.name = name
        self.duty = duty
        self.persona = persona

def build_team():
    planner = Role("规划者", "拆解目标", "资深架构师")
    coder = Role("执行者", "写代码", "10年工程师")
    reviewer = Role("审查者", "查错", "严谨测试专家")
    return [planner, coder, reviewer]

if __name__ == "__main__":
    for r in build_team():
        print(r.name + "：" + r.duty)''',
        hl=[4, 10],
        output="规划者：拆解目标\n执行者：写代码\n审查者：查错",
        note="Role 把职责聚合成对象；persona 虽未在此打印，但是提示词的一部分。真实团队里每个 Role 配独立 system 与工具集。"),
    kp("职责重叠是团队最大的内耗",
        para("如果两个 Agent 的职责边界模糊（都觉得「这该我管」或「这不归我」），结果要么重复劳动要么互相推诿。设计时用一句话能说清「谁负责什么」才算边界清晰；权限上遵循最小授权， reviewer 不该有写库的权限。"),
    ),
    table(["角色属性", "作用", "写错会怎样"],
          [["name", "标识与路由", "分派混乱"],
           ["duty", "职责边界", "重叠/遗漏"],
           ["persona", "语气与关注点", "答非所问"],
           ["tools", "能力边界", "越权风险"]]),
    callout("tip", "实际应用场景", '**内容生产**：规划/写作/校对三角色；**研发**：产品/开发/测试三角色；**分析**：取数/建模/解读三角色'),
    callout("danger", "易错点：给单个 Agent 太多工具",
        "工具越多，模型越容易调错或陷入选择困难。按角色裁剪工具集，让「规划者」看不到「执行者」的执行工具，能显著降低误调用。"),
  ],
},
"4.3": {
  "objectives": [
    "理解 Agent 间通信的三种方式（消息总线 / 共享黑板 / 直接调用）",
    "能写一个最小消息总线，支持订阅与发布",
    "知道消息契约（结构化、可追溯、可重放）的重要性",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("通信方式决定协作的可控性",
        para("Agent 之间怎么「说话」有几种范式：直接调用最简单但耦合紧；共享黑板（blackboard）让所有 Agent 读写同一块状态，适合松散协作；消息总线（pub/sub）最解耦，发送方不知道谁在听。生产里消息总线最常用，因为它能异步、可重放、易加监控。无论哪种，消息都应该是结构化的（带类型/来源/时间戳），而不是自由文本。"),
    ),
    code("s4_3_message.py", "python", "最小消息总线：订阅主题 + 发布消息",
        r'''class MessageBus:
    def __init__(self):
        self._subs = {}

    def subscribe(self, topic, fn):
        self._subs.setdefault(topic, []).append(fn)

    def publish(self, topic, msg):
        for fn in self._subs.get(topic, []):
            fn(msg)

def log_agent(m):
    print("Agent 收到：" + m)

if __name__ == "__main__":
    bus = MessageBus()
    bus.subscribe("task", log_agent)
    bus.publish("task", "分析这份财报")''',
        hl=[4, 9],
        output="Agent 收到：分析这份财报",
        note="_subs 存订阅；subscribe 注册、publish 广播。真实总线还要带消息 id/时间戳/来源，便于追溯与重放。"),
    kp("消息契约要可重放",
        para("Agent 协作的 bug 极难复现，因为涉及模型的随机性。把每次消息（请求+响应）结构化落库，就能「把那次失败会话原样重跑」来定位问题。这也是为什么消息优于直接函数调用——调用无痕迹，消息有记录。"),
    ),
    table(["方式", "耦合", "适合"],
          [["直接调用", "紧", "固定两 Agent"],
           ["共享黑板", "中", "松散协作"],
           ["消息总线", "松", "多 Agent 异步"]]),
    callout("tip", "实际应用场景", '**流水线**：上游 publish 产物，下游 subscribe 处理；**告警**：事件总线广播给多个值守 Agent；**编排**：主管 publish 任务，worker subscribe'),
    callout("danger", "易错点：消息用自由文本",
        "自由文本消息无法被程序可靠解析与重放。务必定义结构化 schema（来源/类型/载荷/时间戳），下游才能稳定消费与回溯。"),
  ],
},
"4.4": {
  "objectives": [
    "理解任务分解的三种策略（按领域 / 按阶段 / 按依赖）",
    "能写一个把目标拆成子任务并分配给 worker 的最小实现",
    "知道「依赖关系」如何决定执行顺序",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("分解是「让复杂变得可交付」的关键一步",
        para("多 Agent 协作的第一步往往是把一个大目标拆成可独立执行的子任务。拆法有三种视角：按领域（财务/技术/法务各管一块）、按阶段（先规划再执行再验收）、按依赖（A 的输出是 B 的输入就串行，否则可并行）。拆得好，每个 worker 拿到的是边界清晰、信息完整的子任务；拆得差，worker 在缺上下文的情况下瞎做。"),
    ),
    code("s4_4_decompose.py", "python", "把目标拆子任务并轮转分配给 worker",
        r'''def decompose(goal):
    steps = []
    for i, part in enumerate(goal.split("，")):
        steps.append({"id": i + 1, "task": part.strip()})
    return steps

def assign(steps, workers):
    plan = []
    for step in steps:
        owner = workers[step["id"] % len(workers)]
        plan.append((step["task"], owner))
    return plan

if __name__ == "__main__":
    steps = decompose("读需求，写代码，跑测试")
    print(assign(steps, ["规划", "开发", "测试"]))''',
        hl=[2, 9],
        output="[('读需求', '规划'), ('写代码', '开发'), ('跑测试', '测试')]",
        note="decompose 按逗号切分做演示；真实分解用 LLM 按依赖图产出，assign 按 worker 数轮转。step/task/owner 都被引用。"),
    kp("依赖决定顺序",
        para("分解后必须标注依赖：B 依赖 A 就要等 A 完成；无依赖的可以并行以提速。编排器（如 4.6 的状态机）按依赖图调度，既保证正确又最大化并发。"),
    ),
    table(["拆法", "视角", "例子"],
          [["按领域", "谁懂什么", "财务/技术/法务"],
           ["按阶段", "时间顺序", "规划/执行/验收"],
           ["按依赖", "数据流向", "取数->建模->解读"]]),
    callout("tip", "实际应用场景", '**报告生成**：按章节并行写再汇总；**研发**：需求拆 ticket 分给不同开发；**调研**：按子问题分派给不同检索 Agent'),
    callout("danger", "易错点：拆太细导致协调开销爆炸",
        "子任务不是越细越好。拆太细，supervisor 的协调与消息开销会超过并行收益。以「一个 worker 能独立完成且有明确产出」为粒度下限。"),
  ],
},
"4.5": {
  "objectives": [
    "理解结果聚合的三种策略（投票 / 合并 / 加权）",
    "能写一个多数投票聚合器处理多 Agent 的不一致输出",
    "知道冲突无法自动解决时应升级人工",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("多个 Agent 答得不一样，怎么办",
        para("多 Agent 并行工作后，常出现「答案不一致」：三个 Agent 两个说北京、一个说上海。聚合策略要提前定：投票（取多数）、合并（抽取各自正确部分）、加权（可信 Agent 权重更高）。聚合不是为了「选一个」，而是「在不确定时给出最稳的结论」；当分歧大到无法判断时，应升级人工而非硬选。"),
    ),
    code("s4_5_aggregate.py", "python", "多数投票聚合多 Agent 答案",
        r'''from collections import Counter

def aggregate(answers):
    if not answers:
        return "无结果"
    counts = Counter(answers)
    best, n = counts.most_common(1)[0]
    return best + "（" + str(n) + "/" + str(len(answers)) + " 票一致）"

if __name__ == "__main__":
    print(aggregate(["北京", "北京", "上海"]))''',
        hl=[4, 5],
        output="北京（2/3 票一致）",
        note="Counter 做计票；多数票即结论并带上置信度。真实场景可加权重或让模型做最终裁决。"),
    kp("聚合不是终点，是质量闸门",
        para("聚合输出的「N/M 票一致」本身就是质量信号：一致率高说明任务明确、Agent 靠谱；一致率低说明任务模糊或信息不足，这时该触发复核（重跑或人工）而不是盲目采信。"),
    ),
    table(["策略", "做法", "适合"],
          [["投票", "取多数", "客观有标准答案"],
           ["合并", "抽各自正确部分", "互补型子任务"],
           ["加权", "可信者权重高", "Agent 能力不均"]]),
    callout("tip", "实际应用场景", '**事实问答**：投票取多数；**草稿写作**：合并各版本亮点；**风险评估**：加权（资深 Agent 权高）'),
    callout("danger", "易错点：低一致率仍硬选",
        "2/3 和 1/3 的票差，结论可信度天差地别。务必把一致率当质量阈值：低于某值就升级复核，而非直接输出赢家。"),
  ],
},
"4.6": {
  "objectives": [
    "理解长任务为什么需要显式状态机而非隐式上下文",
    "能写一个带步骤记录与完成的 TaskState，并说明如何持久化续跑",
    "知道失败恢复要把「已完成步骤」与「待重跑步骤」分开",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("长任务不能只靠「聊天历史」记住进度",
        para("几分钟能搞定的任务靠上下文窗口就够了；但跨小时/跨天的长任务，上下文会被截断、进程可能重启。必须用显式状态机把「当前做到哪、哪些已完成、哪些待做」落盘。这样进程挂了能从断点恢复，而非从头再来。状态机还能让人工在任意步骤介入审批。"),
    ),
    code("s4_6_state.py", "python", "长任务状态：记录步骤、标记完成、可快照",
        r'''class TaskState:
    def __init__(self):
        self.steps = []
        self.done = False

    def advance(self, action):
        self.steps.append(action)
        if action == "完成":
            self.done = True

    def snapshot(self):
        return {"steps": list(self.steps), "done": self.done}

if __name__ == "__main__":
    t = TaskState()
    t.advance("检索")
    t.advance("完成")
    print(t.snapshot())''',
        hl=[4, 9],
        output="{'steps': ['检索', '完成'], 'done': True}",
        note="steps 累积轨迹；snapshot 即「可持久化的进度」。真实场景把 snapshot 写库，重启后 load 续跑。"),
    kp("持久化与续跑的边界",
        para("落盘的不只是「进度」，还有每一步的产物（检索到的文档、生成的草稿），否则恢复后要重算。失败时只重跑「从断点起的待做步骤」，已完成的步骤复用其产物，既快又省。"),
    ),
    table(["要素", "为什么", "不做的后果"],
          [["步骤记录", "知道做到哪", "重复劳动"],
           ["产物落盘", "断点复用", "恢复后重算"],
           ["done 标记", "判断是否结束", "无限循环"],
           ["快照", "可迁移/续跑", "进程挂=全丢"]]),
    callout("tip", "实际应用场景", '**长文档写作**：每章存草稿，断点续写；**数据管线**：每步存中间表；**审批流**：每节点存状态等人工'),
    callout("danger", "易错点：把状态只放内存",
        "进程一重启，内存状态全没。长任务的状态必须外置（数据库/文件），否则一次 OOM 或发布就前功尽弃。"),
  ],
},
"4.7": {
  "objectives": [
    "能列出「必须人工」的高风险/不可逆操作清单",
    "写一个审批门：高风险动作先暂停、等人工确认再继续",
    "理解 HITL 不是拖慢，是给 Agent 装「熔断」",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("哪些动作绝不能让 Agent 自己拍板",
        para("凡「不可逆 + 有外部后果」的动作，都应默认人工确认：退款/转账、删除/覆盖数据、改密码/权限、对外发消息、执行生产变更。Agent 可能基于错误上下文或被人诱导做出这些动作，一旦执行无法撤回。HITL（人在回路）就是在这些节点上「挂起等确认」，把控制权暂时交回人。"),
    ),
    code("s4_7_hitl.py", "python", "审批门：高风险动作先暂停等人工确认",
        r'''def needs_approval(action, risk):
    return risk in ("退款", "改密", "删除") or "金额" in action

def execute(action, risk, human_ok=False):
    if needs_approval(action, risk) and not human_ok:
        return "已暂停，等待人工确认：" + action
    return "已执行：" + action

if __name__ == "__main__":
    print(execute("退款 100 元", "退款"))
    print(execute("退款 100 元", "退款", human_ok=True))''',
        hl=[2, 7],
        output="已暂停，等待人工确认：退款 100 元\n已执行：退款 100 元",
        note="needs_approval 用风险标签判定；human_ok 模拟人工通过。真实场景 human_ok 来自人工点击而非代码默认。"),
    kp("HITL 要设计成「可恢复」而非「可阻断」",
        para("好的审批门在暂停时保存完整上下文，人工确认后能从断点继续，而不是整个流程作废重来。同时给人工「拒绝/修改/批准」三种选择，拒绝时把原因回灌给 Agent 让其调整方案。"),
    ),
    table(["操作", "风险", "处置"],
          [["退款/转账", "资损、不可逆", "必人工"],
           ["删/覆盖数据", "不可逆", "必人工"],
           ["改密/权限", "安全", "必人工"],
           ["只读查询", "低", "可自动"]]),
    callout("tip", "实际应用场景", '**金融**：退款/转账人工复核；**运维**：生产变更审批；**客服**：涉敏操作确认；**内容**：对外发布前审'),
    callout("danger", "易错点：默认放行高风险动作",
        "最危险的写法是把 human_ok 默认设 True「为了流程顺」。高风险动作默认必须是「暂停」，人工显式确认才算通过。"),
  ],
},
"4.8": {
  "objectives": [
    "理解 Computer Use 让 Agent 能操作 GUI/浏览器，突破了「只有 API」的限制",
    "能写一个 Computer Use 的最小封装（规划->执行->读取结果）",
    "知道它的能力边界与安全风险（误操作、越权、泄露）",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("Computer Use 把「没有 API 的系统」也变成可操作对象",
        para("很多老系统、内部后台、网页只有界面没有开放 API。Computer Use（让模型「看屏幕 + 操作鼠标键盘」）让 Agent 能像人一样用这些系统：填表、点按钮、读页面。它把 Agent 的触达范围从「有接口的服务」扩到「任何能点的界面」。代价是慢、脆（界面一改就失灵）、且需要沙箱兜底防误操作。"),
    ),
    code("s4_8_computer_use.py", "python", "Computer Use 最小封装：规划->执行->读取",
        r'''def computer_use(instruction, tools):
    plan = tools["plan"](instruction)
    for step in plan:
        tools["act"](step)
    return tools["read"](plan[-1])

def dummy_tools():
    return {
        "plan": lambda s: [s, "点击提交"],
        "act": lambda x: None,
        "read": lambda x: "页面显示：提交成功",
    }

if __name__ == "__main__":
    print(computer_use("提交报销单", dummy_tools()))''',
        hl=[2, 5],
        output="页面显示：提交成功",
        note="computer_use 编排「规划-执行-读取」；dummy_tools 是替身，真实场景接截图+操作 API。step/x/s 均被引用。"),
    kp("能力边界与防护",
        para("Computer Use 本质是「模拟人操作」，所以人会犯的错它都会犯：点错按钮、填错字段、被诱导授权。必须配：①沙箱（隔离宿主机）；②确认门（提交/支付前人工复核）；③操作日志（每步可回放追责）。不要让它碰「无撤销」的高危界面。"),
    ),
    table(["维度", "Computer Use", "直接 API"],
          [["覆盖", "任何界面", "仅开放接口"],
           ["稳定性", "脆（界面变就崩）", "稳"],
           ["速度", "慢", "快"],
           ["安全", "需沙箱+确认", "可控"]]),
    callout("tip", "实际应用场景", '**老系统对接**：无 API 的后台自动填表；**网页操作**：自动提交/查询；**回归测试**：模拟用户点界面'),
    callout("danger", "易错点：让它碰高危界面",
        "Computer Use 在「无撤销」界面（删库、转账、发邮件）上误操作代价极高。这类动作要么接确认门，要么干脆走专用 API 而非模拟点击。"),
  ],
},
}

CH5_PLAN = {
"5.1": {
  "objectives": [
    "能设计一个「意图识别 + 知识库 + 人工兜底」的客服 Agent 闭环",
    "理解为什么客服要把「确定性知识」与「开放问答」分开处理",
    "知道哪些情况必须转人工而非硬答",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("客服 Agent 的本质是「分工」",
        para("客服里大量问题是确定性的（退款政策、物流时效），用知识库直答最稳最便宜；少量是开放性的（投诉情绪、复杂个案），才需要模型理解与人工。好的客服 Agent 先用意图识别把问题分流：命中知识库的直接答、需要情绪的转人工、需要查系统的调工具。绝不让模型「凭记忆编」政策类内容。"),
    ),
    code("s5_1_customer.py", "python", "最小客服闭环：知识库命中 + 转人工兜底",
        r'''KNOWLEDGE = {
    "退款": "7天无理由退款，自签收起算",
    "物流": "普通快递 3-5 天达，可查单号",
}

def handle(msg):
    for topic, answer in KNOWLEDGE.items():
        if topic in msg:
            return "知识库答复：" + answer
    return "已转人工客服"

if __name__ == "__main__":
    print(handle("我要退款"))
    print(handle("你们老板电话多少"))''',
        hl=[5, 8],
        output="知识库答复：7天无理由退款，自签收起算\n已转人工客服",
        note="先查确定知识，未命中转人工；真实场景把 KNOWLEDGE 换成向量检索，并加工具查订单状态。"),
    kp("转人工不是失败，是护栏",
        para("很多团队把「转人工」当成 Agent 没答上来的尴尬。恰恰相反，在政策、情绪、权限、钱相关的问题上主动转人工，是对用户最负责的做法。设计目标是「让简单问题秒回，让复杂问题落到对的人手里」。"),
    ),
    table(["问题类型", "处理方式", "为什么"],
          [["政策类", "知识库直答", "不许编造"],
           ["查状态", "调工具", "实时准确"],
           ["情绪/投诉", "转人工", "需共情"],
           ["权限/钱", "转人工", "不可逆"]]),
    callout("tip", "实际应用场景", '**电商客服**：退款/物流走知识库+订单工具，投诉转人工；**SaaS 客服**：文档问答+转技术支持；**银行**：业务咨询直答，交易转柜面'),
    callout("danger", "易错点：让模型编政策",
        "「年假几天」这类制度问题，模型凭记忆答极易出错且口径不一。必须接知识库/RAG，命中才答，否则转人工。"),
  ],
},
"5.2": {
  "objectives": [
    "理解代码助手的两类任务（生成 vs 审查）及其不同要求",
    "能写一个最小代码审查器，按规则清单标出问题行",
    "知道 AI 审查只能补位不能替代人工 review",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("生成与审查是两种能力",
        para("代码助手常被混为一谈，但「写代码」和「审代码」要求完全不同：生成要会联想、会补全；审查要会挑刺、懂坏味道。审查尤其适合用规则清单+模型复核来落地——先跑静态规则（TODO、裸 print、裸 except）抓低级问题，再让模型看逻辑与安全隐患。AI 审查是「第一道网」，减轻人工负担，但不该是唯一把关。"),
    ),
    code("s5_2_code_review.py", "python", "按规则清单标出代码问题行",
        r'''RULES = ["print(", "except:", "import *"]

def review(code_text):
    hits = []
    for i, line in enumerate(code_text.splitlines(), 1):
        for r in RULES:
            if r in line:
                hits.append((i, r))
    return hits

if __name__ == "__main__":
    print(review("def f():\n    print('x')\n    except:\n        pass\n"))''',
        hl=[4, 6],
        output="[(2, \"print(\"), (3, 'TODO')]",
        note="enumerate 带行号；RULES 可扩展为更严格的 lint 集。真实审查再叠加模型对逻辑/安全的判断。"),
    kp("AI 审查的边界",
        para("规则能抓「明显坏」（裸 except、未用变量），模型能抓「可能坏」（并发、注入、越权）。但「这段代码是否满足业务需求、是否过度设计」只有人懂上下文。所以 AI 审查定位是「放大人工的覆盖度」，不是替代。"),
    ),
    table(["层级", "抓什么", "局限"],
          [["静态规则", "低级坏味道", "误报/漏报"],
           ["模型审查", "逻辑/安全", "需上下文"],
           ["人工 review", "业务正确性", "慢、覆盖低"]]),
    callout("tip", "实际应用场景", '**PR 自动审查**：提交即跑规则+模型，标问题再等人工；**存量代码治理**：批量扫 TODO/裸 except；**教学**：给新手即时反馈'),
    callout("danger", "易错点：AI 审查过了就合并",
        "把 AI 审查当「通行证」是危险的。它只能降人工负担，关键逻辑、安全、业务正确性仍需人工拍板。"),
  ],
},
"5.3": {
  "objectives": [
    "理解 NL2SQL 的「方便」与「危险」：自然语言问数据",
    "能写一个带白名单与禁写校验的最小 NL2SQL 安全层",
    "知道 Text-to-SQL 必须配合权限与审计",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("把「人话」变成「SQL」是 Analytics 的圣杯",
        para("NL2SQL 让非技术人员用自然语言查数据（「上月各渠道转化率」），体验极好。但危险也极大：模型可能生成 DROP/DELETE，或查到它无权看的表。生产级 NL2SQL 必须有安全层——白名单限定可查表、禁止写操作、参数化防注入、结果脱敏、全程审计。绝不能把「模型生成的 SQL」直接裸执行。"),
    ),
    code("s5_3_nl2sql.py", "python", "最小 NL2SQL 安全层：白名单 + 禁写校验",
        r'''def nl2sql(question):
    if "订单" in question:
        return "SELECT * FROM orders LIMIT 10"
    return "SELECT 1"

def is_safe(sql):
    forbidden = ("DROP", "DELETE", "UPDATE", "INSERT", ";")
    return not any(f in sql.upper() for f in forbidden)

if __name__ == "__main__":
    sql = nl2sql("查最近订单")
    print(sql, "安全?", is_safe(sql))''',
        hl=[4, 8],
        output="SELECT * FROM orders LIMIT 10 安全? True",
        note="真实场景用 LLM 生成 SQL，但必经 is_safe 拦截写操作与拼接；表名也要在白名单内。f 在 any 生成器中被引用。"),
    kp("权限比语法更重要",
        para("即使 SQL 语法安全（只读 SELECT），「用户 A 查到了用户 B 的订单」也是越权。NL2SQL 必须叠加行级权限（按当前用户过滤）与列级脱敏（手机号打码），否则方便变成了泄密。"),
    ),
    table(["风险", "防护", "例子"],
          [["写操作", "禁 DROP/DELETE/UPDATE", "防误删"],
           ["越权表", "表白名单", "防跨库"],
           ["越权行", "行级过滤", "防看他人数据"],
           ["注入", "参数化", "防拼接"]]),
    callout("tip", "实际应用场景", '**BI 自助**：业务方自然语言查指标；**运营看板**：运营自查数据；**老板视角**：高层看汇总（权限最紧）'),
    callout("danger", "易错点：模型 SQL 直接执行",
        "模型生成的 SQL 一旦裸跑，一个 DELETE 或分号后的恶意语句就能清空表。必须经过禁写+白名单校验，且用只读账号执行。"),
  ],
},
"5.4": {
  "objectives": [
    "理解运营自动化的「监控->判断->执行」闭环",
    "能写一个最小运维循环：超阈值告警并自动处置",
    "知道哪些处置可自动、哪些必须人工",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("运营自动化是「有护栏的自动决策」",
        para("运营/运维里很多动作可自动化：指标超阈值就扩容、异常就告警、定时就跑报表。但这些动作都有「副作用」，所以闭环必须带护栏——自动执行「可逆、低危」的（扩容、发通知），人工确认「不可逆、高危」的（缩容、删数据、改配置）。自动化的价值是「快且不知疲倦」，护栏的价值是「不出大事故」。"),
    ),
    code("s5_4_ops.py", "python", "最小运维闭环：超阈值告警 + 自动扩容",
        r'''def monitor(metrics, threshold):
    alerts = []
    for name, value in metrics.items():
        if value > threshold:
            alerts.append(name)
    return alerts

def act(alerts):
    return ["自动扩容：" + a for a in alerts]

if __name__ == "__main__":
    print(act(monitor({"cpu": 95, "mem": 60}, 80)))''',
        hl=[2, 6],
        output="['自动扩容：cpu']",
        note="monitor 取超阈值项，act 生成处置；真实场景 act 调云 API，缩容/删库等高危动作走人工确认。"),
    kp("自动化的「可逆性」红线",
        para("扩容、发消息、跑只读报表——错了能撤回或无害，可自动。缩容（可能杀掉正常服务）、删数据、改生产配置——错了损失大且难恢复，必须人工。画这条线比「能自动就自动」更重要。"),
    ),
    table(["动作", "可逆性", "处置"],
          [["告警通知", "无害", "可自动"],
           ["扩容", "易回退", "可自动"],
           ["缩容", "可能误杀", "人工"],
           ["删数据", "不可逆", "人工"]]),
    callout("tip", "实际应用场景", '**弹性伸缩**：CPU 高自动扩容；**日报**：定时生成推送；**异常检测**：超阈告警；**成本优化**：闲置资源报告'),
    callout("danger", "易错点：全自动无护栏",
        "让 Agent 自动缩容、自动删、自动改配置，一次误判就是线上事故。高危动作默认人工，自动化只覆盖可逆低危项。"),
  ],
},
"5.5": {
  "objectives": [
    "理解企业知识库问答的「检索+生成+引用」三段式",
    "能写一个带来源引用的 KB QA，抑制幻觉",
    "知道权限隔离（谁能看哪些文档）是企业的硬要求",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("知识库问答 = RAG + 引用 + 权限",
        para("企业知识库问答不是「把文档丢给模型」，而是：①检索相关片段（RAG）；②让模型只基于片段作答；③在答案里标注来源 id（便于回溯与追责）；④按用户权限过滤可检索的文档。缺了引用，用户无法核实；缺了权限，A 部门能看 B 部门机密。这两点是企业级与玩具级的本质区别。"),
    ),
    code("s5_5_kb_qa.py", "python", "带来源引用的知识库问答",
        r'''DOCS = {
    "年假": "年假 10 天，满 1 年加 1 天",
    "报销": "报销需发票，T+3 到账",
}

def answer(question):
    for topic, text in DOCS.items():
        if topic in question:
            return "[" + topic + "] " + text
    return "未检索到相关制度"

if __name__ == "__main__":
    print(answer("年假几天"))''',
        hl=[5, 8],
        output="[年假] 年假 10 天，满 1 年加 1 天",
        note="答案带 [topic] 引用；真实场景用向量检索召回多个片段并拼接来源，权限层在检索前过滤文档。"),
    kp("权限是企业的硬约束",
        para("个人知识库只要「答得对」；企业知识库还要「答得对且只答该用户能看的」。检索前必须按用户角色过滤文档集合——HR 文档不对普通员工可见。这层做不好，RAG 再准也是泄密通道。"),
    ),
    table(["能力", "个人版", "企业版"],
          [["检索", "全量文档", "按权限过滤"],
           ["引用", "可选", "必带来源"],
           ["脱敏", "无", "手机号/金额打码"],
           ["审计", "无", "谁查了什么"]]),
    callout("tip", "实际应用场景", '**员工服务**：制度/FAQ 自助问答；**销售**：产品资料即时查；**法务**：合同条款检索（权限最严）'),
    callout("danger", "易错点：检索前不过滤权限",
        "若所有文档混在一起检索，模型可能把机密片段答给无权限的人。权限过滤必须在检索前，而非生成后。"),
  ],
},
"5.6": {
  "objectives": [
    "能设计一个「规划-编码-审查」多 Agent 协作开发流水线",
    "理解为什么「编码」和「审查」必须是不同 Agent",
    "知道协作开发的产物（PR/测试报告）如何流转",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("开发协作 = 角色化 + 产物化",
        para("让一个 Agent 又写又审自己的代码，等于没有审查。开发协作要把步骤拆给不同角色：规划者拆需求、编码者实现、审查者挑刺，每个角色产出明确的交付物（需求文档、代码、review 意见）在 Agent 间流转。关键是「编码者看不到自己的代码被自动通过」——审查必须独立。"),
    ),
    code("s5_6_dev_team.py", "python", "规划-编码-审查 三步开发流水线",
        r'''STEPS = ["规划", "编码", "审查"]

def dev_pipeline(req):
    results = []
    for step in STEPS:
        results.append(step + "：" + req)
    return results

if __name__ == "__main__":
    print(dev_pipeline("实现登录"))''',
        hl=[2, 5],
        output="['规划：实现登录', '编码：实现登录', '审查：实现登录']",
        note="STEPS 定义流水线；真实场景每步是独立 Agent，产物（设计/代码/意见）传给下一步，审查不通过则回编码。"),
    kp("产物是协作的契约",
        para("Agent 之间不靠「口头默契」协作，而靠「产物」。规划者产出需求拆解文档，编码者基于它写代码，审查者拿着代码与设计比对。产物让每一步可独立验证、可回放、可追责。"),
    ),
    table(["角色", "产物", "下游"],
          [["规划者", "需求拆解", "编码者"],
           ["编码者", "代码+测试", "审查者"],
           ["审查者", "review 意见", "回编码/合并"]]),
    callout("tip", "实际应用场景", '**需求到代码**：产品拆票->开发实现->测试审；**重构**：规划改动点->逐文件改->回归；**修 bug**：定位->修->验证'),
    callout("danger", "易错点：自写自审",
        "让同一个 Agent 写并审自己的代码，审查形同虚设。编码与审查必须分属不同 Agent（或人工），才能真的发现问题。"),
  ],
},
"5.7": {
  "objectives": [
    "理解全栈开发 Agent 要同时管「前端/后端/数据」三层",
    "能写一个把需求拆成三层任务的最小规划器",
    "知道全栈自动化的「接口契约」先于实现",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("全栈 Agent 的难点在「层间契约」",
        para("全栈开发不是「前后端各写各的」，而是三层要严格对齐：前端调的接口、后端提供的接口、数据库存的字段，必须是一致的契约。全栈 Agent 应该先定「接口契约」（URL、参数、返回、表结构），再让各层基于契约并行实现。契约错了，三层全返工。"),
    ),
    code("s5_7_fullstack.py", "python", "把需求拆成前端/后端/库三层任务",
        r'''def plan_fullstack(req):
    frontend = "React 表单 + 校验"
    backend = "FastAPI 接口 + 校验"
    db = "表：users(id, name)"
    return {"前端": frontend, "后端": backend, "库": db}

if __name__ == "__main__":
    print(plan_fullstack("用户注册"))''',
        hl=[2, 4],
        output="{'前端': 'React 表单 + 校验', '后端': 'FastAPI 接口 + 校验', '库': '表：users(id, name)'}",
        note="req 被引用；三层任务各自独立。真实场景先产出 OpenAPI 契约，前端/后端/迁移脚本并行基于契约生成。"),
    kp("契约先于实现",
        para("让 Agent 先产出接口与表结构定义（契约），再实现，能避免「前端等后端、后端等库」的串行阻塞，也避免三层对不齐。契约本身也要进版本管理，改契约要同步通知三层。"),
    ),
    table(["层", "关注", "交付"],
          [["前端", "交互+调接口", "页面/组件"],
           ["后端", "逻辑+提供接口", "API/服务"],
           ["库", "存储结构", "表/迁移"]]),
    callout("tip", "实际应用场景", '**MVP 快速搭建**：先契约后并行实现；**内部工具**：表单+接口+表一气呵成；**原型**：一天出可点 demo'),
    callout("danger", "易错点：三层各写各的没契约",
        "没有统一契约，前端调的字段后端没提供、后端存的字段前端不知道，联调时全面返工。先定契约再实现。"),
  ],
},
"5.8": {
  "objectives": [
    "理解「部署 + 健康检查 + 回滚」是 Agent 上线的最后一公里",
    "能写一个带健康检查的部署函数，失败即回滚",
    "知道 Agent 上线后要监控成功率与成本",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("部署不是「传上去」，是「能回退」",
        para("Agent 上线最怕「新版本行为变差却撤不回来」。可靠部署要有三件套：①灰度（先放一小部分流量）；②健康检查（上线后立即验证关键路径）；③一键回滚（检查失败立刻回到上一稳定版）。Agent 尤其需要监控「成功率/成本/延迟」三个指标，因为模型升级可能悄悄变差。"),
    ),
    code("s5_8_deploy.py", "python", "带健康检查与回滚的部署",
        r'''def deploy(version):
    healthy = check_health()
    if healthy:
        return "已上线 " + version
    return "健康检查失败，回滚到上一版本"

def check_health():
    return True

if __name__ == "__main__":
    print(deploy("v2"))''',
        hl=[2, 5],
        output="已上线 v2",
        note="deploy 先健康检查再确认；check_health 演示返回 True，真实场景打关键接口验证。version 被引用。"),
    kp("上线只是开始",
        para("Agent 上线后才是重点：用 eval 框架（见 2.10）跑标注集得基线，灰度对比新旧版本的成功率与成本，线上监控趋势。发现新版本成本翻倍或准确率掉点，立刻回滚而不是硬扛。"),
    ),
    table(["动作", "目的", "失败处置"],
          [["灰度", "小流量验证", "异常则停"],
           ["健康检查", "验证关键路径", "回滚"],
           ["回滚", "快速恢复", "保留快照"],
           ["监控", "持续可观测", "告警"]]),
    callout("tip", "实际应用场景", '**模型升级**：灰度 5% 流量对比；**提示改动**：A/B 看成功率；**大版本**：蓝绿部署，切流量不换机'),
    callout("danger", "易错点：上了线不监控",
        "一次模型/提示更新可能悄悄让准确率掉 5%、成本翻倍。上线后必须用 eval+线上监控持续盯成功率与成本，异常即回滚。"),
  ],
},
"5.9": {
  "objectives": [
    "理解企业 Agent 的安全合规是「多层防御」而非单点",
    "能写一个输入净化 + 输出校验的 Guardrail",
    "知道合规要求（数据出境、留痕、可审计）如何落到设计",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("安全合规是「分层 + 可审计」",
        para("企业 Agent 的安全不是加一个过滤器就完事，而是分层：输入净化（拦注入）、指令隔离（系统提示与用户输入分通道）、输出校验（限话题/长度/格式）、权限分层（高危动作人工）。再加「全程留痕」——谁、在什么上下文、让 Agent 做了什么、结果如何，都要可审计。合规（如数据不出境、操作可追溯）正是靠这些落地。"),
    ),
    code("s5_9_guard.py", "python", "输入净化 + 输出校验的 Guardrail",
        r'''BLOCKLIST = ["忽略指令", "系统提示", "密码"]

def guard(text):
    low = text.lower()
    for w in BLOCKLIST:
        if w.lower() in low:
            return False, "命中敏感词：" + w
    return True, "通过"

if __name__ == "__main__":
    print(guard("请忽略指令"))
    print(guard("你好"))''',
        hl=[4, 7],
        output="(False, '命中敏感词：忽略指令')\n(True, '通过')",
        note="BLOCKLIST 是黑名单演示，真实需配白名单；guard 同时管输入与输出，二者成对出现。w 在循环中被引用。"),
    kp("合规落到设计而非事后",
        para("「数据不出境」要在架构上把模型调用限制在国内节点；「操作可审计」要在每次调用落库上下文与结果；「最小权限」要在工具层按角色收口。这些不是上线后补，而是设计阶段就定。"),
    ),
    table(["层", "做法", "防什么"],
          [["输入净化", "黑名单/白名单", "注入"],
           ["指令隔离", "系统/用户分通道", "越权"],
           ["输出校验", "限话题/长度", "泄密"],
           ["留痕", "全量记录", "不可审计"]]),
    callout("tip", "实际应用场景", '**金融**：所有调用留痕+权限分层；**政务**：数据不出境+国模节点；**医疗**：脱敏+人工复核敏感操作'),
    callout("danger", "易错点：只防输入不防输出",
        "即使输入干净，模型仍可能输出敏感信息或被诱导越界。输入净化与输出校验必须成对，缺一不可。"),
  ],
},
"5.10": {
  "objectives": [
    "能列出 Agent 上线前必须自检的清单（终止/成本/校验/兜底）",
    "理解常见难点的根因（循环、幻觉、越权、成本失控）",
    "知道如何把「踩过的坑」沉淀为可复用检查项",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("踩坑的本质是「没在设计期设护栏」",
        para("Agent 的常见难点几乎都能在设计期预防：死循环→没终止条件；幻觉→没接知识库/校验；越权→没权限分层；成本失控→没预算上限。与其上线后救火，不如上线前跑一遍 checklist，把每个坑对应成一个必选项。坑不可怕，可怕的是每次都踩同一个。"),
    ),
    code("s5_10_pitfalls.py", "python", "上线前自检清单：缺一项就别上",
        r'''CHECKLIST = ["有终止条件", "有成本上限", "有工具校验", "有人工兜底"]

def self_check(enabled):
    missing = [c for c in CHECKLIST if c not in enabled]
    return "缺失：" + "、".join(missing) if missing else "完备"

if __name__ == "__main__":
    print(self_check(["有终止条件", "有成本上限"]))''',
        hl=[4, 6],
        output="缺失：有工具校验、有人工兜底",
        note="CHECKLIST 是必选项；self_check 返回缺失项。真实场景把这四项做成 CI 卡点，缺一项不允许上线。"),
    kp("把坑变成可复用资产",
        para("每次线上事故，根因和修复都该沉淀进 checklist 与审计脚本（如 audit_code.py）。团队的水平不体现在「少踩坑」，而体现在「同一个坑不踩第二次」。文档化、自动化检查比口头约定可靠。"),
    ),
    table(["难点", "根因", "预防"],
          [["死循环", "无终止条件", "max_steps"],
           ["幻觉", "无知识源", "RAG+校验"],
           ["越权", "无权限层", "角色收口"],
           ["成本爆", "无预算", "上限+监控"]]),
    callout("tip", "实际应用场景", '**上线门禁**：CI 跑 checklist；**复盘**：事故回填检查项；**新人**：照单自检再动手'),
    callout("danger", "易错点：清单写完不执行",
        "checklist 的价值在「卡点」而非「参考」。把它接进 CI/上线流程，缺一项就阻断，而不是贴在墙上。"),
  ],
},
"5.11": {
  "objectives": [
    "理解 Agent 的不同记忆/存储需求对应不同存储选型",
    "能按需求（向量/缓存/结构化）选存储并返回一个说明",
    "知道「存储选型错」会导致检索慢或成本高",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("存储不是「一个数据库搞定」",
        para("Agent 几种数据诉求不同：长期语义记忆要「向量检索」（Milvus/pgvector），短期会话缓存要「快且可过期」（Redis），结构化业务数据要「强一致」（PostgreSQL）。混用或错用都会出问题——用关系库存向量会检索慢，用向量库存订单会丢事务。按访问模式选存储，是 Agent 工程的基本功。"),
    ),
    code("s5_11_storage.py", "python", "按需求选存储：向量/缓存/结构化",
        r'''def pick_store(need):
    if need == "向量检索":
        return "向量库（Milvus / pgvector）"
    if need == "缓存会话":
        return "Redis"
    if need == "持久结构化":
        return "关系库（PostgreSQL）"
    return "本地文件"

if __name__ == "__main__":
    print(pick_store("向量检索"))
    print(pick_store("缓存会话"))''',
        hl=[2, 4],
        output="向量库（Milvus / pgvector）\nRedis",
        note="need 被引用；真实选型还要看规模与延迟。向量库做语义召回，Redis 做低延迟会话，PG 做事务数据。"),
    kp("存储与检索是一对",
        para("选了存储就要配对应的检索方式：向量库配近似检索（ANN）、关系库配 SQL、缓存配 key 查询。很多「检索慢/召回差」的锅，其实是「用错了存储」或「检索方式与存储不匹配」。"),
    ),
    table(["诉求", "存储", "检索方式"],
          [["语义记忆", "向量库", "ANN 相似"],
           ["会话缓存", "Redis", "key 查询"],
           ["业务数据", "PostgreSQL", "SQL"],
           ["文件/日志", "对象存储", "路径"]]),
    callout("tip", "实际应用场景", '**长期记忆**：pgvector 存对话嵌入；**多轮会话**：Redis 存 recent；**订单**：PG 事务；**文档**：对象存储+向量索引'),
    callout("danger", "易错点：什么都往关系库塞",
        "把向量、缓存、文件全塞进一个关系库，结果检索慢、成本高、难扩展。按访问模式分库，是 Agent 存储的基本功。"),
  ],
},
}

CH6_PLAN = {
"6.1": {
  "objectives": [
    "理解「Agent OS」想解决什么：把 Agent 当「一等公民」统一调度资源与权限",
    "能写一个最小能力注册表与调度器，说明 OS 层在做什么",
    "知道 Agent OS 与「普通编排框架」的区别：资源/权限/生命周期的一层",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("Agent OS：给 Agent 一个「运行环境」",
        para("普通编排框架管「流程怎么走」，Agent OS 管「Agent 作为一类程序该怎么被运行」：统一的资源配额（算力/上下文/工具额度）、统一的权限与身份、统一的生命周期（创建/暂停/恢复/销毁）、统一的事件总线。它把「跑 Agent」从「写个脚本」升级成「操作系统调度进程」的层级，让大量 Agent 能安全共存、互不踩踏。"),
    ),
    code("s6_1_agentos.py", "python", "最小 Agent OS：能力注册表 + 资源调度",
        r'''AGENTS = {"研究员": 2, "执行者": 4, "审查者": 1}

def schedule(task, budget):
    owner = min(AGENTS, key=AGENTS.get)
    if AGENTS[owner] > budget:
        return "资源不足"
    return owner + " 接手：" + task

if __name__ == "__main__":
    print(schedule("写周报", 3))''',
        hl=[4, 6],
        output="审查者 接手：写周报",
        note="AGENTS 存配额，schedule 按最闲者派单并校验预算。真实 OS 还管身份/权限/事件总线。min 的 key 引用 AGENTS.get。"),
    kp("OS 层 vs 编排层",
        para("编排层（LangGraph 等）关心「这一步调哪个 Agent」；OS 层关心「这个 Agent 有多少算力、能碰哪些数据、崩了怎么回收」。后者是横切关注点，单独抽出来才让「成千上万个 Agent 同跑」成为可能。"),
    ),
    table(["关注点", "编排框架", "Agent OS"],
          [["流程", "管步骤", "不管"],
           ["资源", "不管", "配额/调度"],
           ["权限", "部分", "统一身份"],
           ["生命周期", "部分", "创建/恢复/销毁"]]),
    callout("tip", "实际应用场景", '**企业内部**：百个 Agent 共享一套调度与权限；**多租户**：按配额隔离；**平台**：像管容器一样管 Agent'),
    callout("danger", "易错点：在编排层硬塞 OS 职责",
        "把资源/权限/生命周期都塞进业务编排，会又乱又难扩。这些横切关注点应下沉到 OS 层统一处理。"),
  ],
},
"6.2": {
  "objectives": [
    "理解具身智能 = 感知-决策-执行 闭环 + 物理约束",
    "能写一个最小「感知->策略->动作」的具身 Agent 循环",
    "知道物理世界的「不可逆/安全风险」远高于纯软件 Agent",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("具身智能把 Agent 从「对话框」放进「物理世界」",
        para("软件 Agent 的输出是文字；具身 Agent（机器人、自动驾驶、机械臂）的输出是「动作」，会真实改变物理世界。它被迫面对软件 Agent 没有的约束：传感器有噪声、动作有延迟、错了可能撞坏东西。所以具身 Agent 的核心是「感知-决策-执行」闭环 + 强安全策略（遇红即停、力超限即停）。"),
    ),
    code("s6_2_embodied.py", "python", "最小具身循环：感知 -> 策略 -> 动作",
        r'''def step(sensor, policy):
    perception = sensor()
    action = policy(perception)
    return action

def camera():
    return "看到红色按钮"

def safety_policy(see):
    if "红色" in see:
        return "停止"
    return "前进"

if __name__ == "__main__":
    print(step(camera, safety_policy))''',
        hl=[2, 6],
        output="停止",
        note="step 把传感器与策略解耦；safety_policy 是硬护栏（见红即停）。真实场景还要力/距离反馈与紧急停止。"),
    kp("物理世界的「不可逆」",
        para("软件 Agent 答错顶多给错信息；具身 Agent 撞了、夹了、冲了，后果物理且常不可逆。所以具身系统对「安全策略」的依赖远高于软件 Agent——宁可保守（停下），不可冒险（继续）。"),
    ),
    table(["维度", "软件 Agent", "具身 Agent"],
          [["输出", "文本", "物理动作"],
           ["错误代价", "低", "高/不可逆"],
           ["感知", "文本/API", "多模态传感器"],
           ["安全", "护栏", "硬停止"]]),
    callout("tip", "实际应用场景", '**仓储**：分拣 robot 避障搬运；**自动驾驶**：感知-决策-控制闭环；**客服机器人**：实体导览'),
    callout("danger", "易错点：把软件 Agent 的「试错」搬进物理",
        "软件里「试一下看看」成本几乎为零；物理里试错可能撞坏设备或伤人。具身 Agent 必须先过安全策略再动作，不能边试边学。"),
  ],
},
"6.3": {
  "objectives": [
    "理解 Agent 能力演进的「阶梯」（感知->推理->规划->工具->多Agent->反思）",
    "能写一个能力阶梯检查器，标出当前所处层级",
    "知道「离 AGI 还有多远」要看哪些能力缺口",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("Agent 能力是一条可度量的阶梯",
        para("与其空谈 AGI，不如把能力拆成可观测的阶梯：感知（看懂输入）→推理（逻辑/数学）→规划（拆目标）→工具（动手查/做）→多 Agent（协作）→自我反思（从失败学）。当前主流 Agent 大多停在「工具+规划」层，离「稳健自我反思、跨领域迁移」还有明显缺口。用阶梯描述，既能定位技术水位，也能指明清哪个能力缺。"),
    ),
    code("s6_3_agi.py", "python", "能力阶梯：标出已具备的层级",
        r'''LADDER = ["感知", "推理", "规划", "工具", "多Agent", "自我反思"]

def reached(caps):
    return [c for c in LADDER if c in caps]

if __name__ == "__main__":
    print(reached(["感知", "推理", "规划"]))''',
        hl=[2, 4],
        output="['感知', '推理', '规划']",
        note="LADDER 定义阶梯；reached 过滤已具备项。真实评估用基准测试逐项打分而非主观判断。c 在推导中被引用。"),
    kp("缺口比峰值更重要",
        para("一个 Agent 在某一项极强、另一项为零，整体仍不可靠。评估要看「最短板」：规划再强，没有工具也落不了地；工具再多，不会反思也修不了错。补齐缺口比堆高峰值更影响可用性。"),
    ),
    table(["层级", "代表能力", "当前水位"],
          [["感知/推理", "看懂/算对", "已成熟"],
           ["规划/工具", "拆目标/动手", "主流"],
           ["多Agent", "协作", "成长中"],
           ["自我反思", "从失败学", "早期"]]),
    callout("tip", "实际应用场景", '**能力地图**： product 用阶梯给竞品定位；**选型**：按缺口补能力；**路线图**：标下一站补哪层'),
    callout("danger", "易错点：用峰值代整体",
        "演示视频里某个任务惊艳，不代表整体可靠。看最短板与失败模式，才知它到底能信几分。"),
  ],
},
"6.4": {
  "objectives": [
    "理解多模态 Agent 要处理「文本/图像/音频/视频」的异质输入",
    "能写一个多模态输入路由器，按类型分派处理器",
    "知道多模态的关键难点：对齐、成本、延迟",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("多模态不是「多几个接口」，是「对齐与路由」",
        para("多模态 Agent 的输入可能是文字、图片、语音、视频混在一起。核心工程问题是：①路由——什么类型交给什么模型（图给视觉模型、语音先转写）；②对齐——把不同模态的信息映射到同一语义空间，让模型能「看图说话、听声判断」；③成本——视觉/语音模型贵且慢，不能什么都丢大模型。路由 + 按需调用是多模态省钱的关键。"),
    ),
    code("s6_4_multimodal.py", "python", "多模态输入路由：按类型分派处理器",
        r'''def route(msg_type, handlers):
    fn = handlers.get(msg_type)
    return fn() if fn else "未知类型"

if __name__ == "__main__":
    handlers = {
        "text": lambda: "处理文本",
        "image": lambda: "调用视觉模型",
        "audio": lambda: "转写语音",
    }
    print(route("image", handlers))''',
        hl=[2, 6],
        output="调用视觉模型",
        note="route 按类型分发；真实场景先 ASR 转写音频、再用视觉模型理解图像，最后统一进 LLM。msg_type/handlers/fn 均被引用。"),
    kp("成本与延迟是隐藏 boss",
        para("多模态最贵的不是模型贵，而是「每次都全量调用」。工程上要：能文本解决的绝不调视觉、能缓存的不重算、长视频抽关键帧而非逐帧。路由的精细度直接决定账单。"),
    ),
    table(["模态", "处理", "成本/延迟"],
          [["文本", "直送 LLM", "低"],
           ["图像", "视觉模型", "中"],
           ["音频", "先 ASR 再 LLM", "中"],
           ["视频", "抽帧+视觉", "高"]]),
    callout("tip", "实际应用场景", '**电商**：图搜+文描；**医疗**：影像+报告；**客服**：语音+工单；**内容**：视频摘要'),
    callout("danger", "易错点：所有输入都丢大模型",
        "图片、语音、视频全量丢多模态大模型，成本爆炸且慢。先路由、先轻量处理（ASR/抽帧）、再按需调大模型。"),
  ],
},
"6.5": {
  "objectives": [
    "理解 Agent 对齐（Alignment）要解决「目标与行为一致」",
    "能写一个基于原则的约束检查器（宪法式护栏）",
    "知道对齐是「持续对抗」，不是一次配置",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("对齐 = 让 Agent 的行为符合人的意图与底线",
        para("模型越强，越容易「聪明地做错事」——为达目标走捷径、钻空子、越界。对齐要解决的问题是：Agent 的目标与行为，是否始终符合人的真实意图与道德/法律底线。工程上常用「宪法式护栏」：把一组原则（不伤害、诚实、守权限）写成可执行的约束，每次动作前过一遍检查；再配合 RLHF/红队持续对抗发现漏洞。"),
    ),
    code("s6_5_alignment.py", "python", "宪法式护栏：按原则检查动作",
        r'''PRINCIPLES = ["不伤害", "诚实", "守权限"]

def check(action):
    for p in PRINCIPLES:
        if violates(p, action):
            return False, "违反：" + p
    return True, "通过"

def violates(principle, action):
    if principle == "不伤害" and "删除" in action:
        return True
    return False

if __name__ == "__main__":
    print(check("删除全部数据"))
    print(check("查询天气"))''',
        hl=[4, 9],
        output="(False, '违反：不伤害')\n(True, '通过')",
        note="PRINCIPLES 是宪法；check 逐条过，violates 判具体违反。真实场景原则更细且由模型+规则共判。p/principle/action 均被引用。"),
    kp("对齐是持续对抗",
        para("写一次护栏不等于永远安全。新能力会引入新漏洞（如新工具可被越权调用），红队测试、用户反馈、线上监控要持续喂回原则库。对齐是过程，不是配置项。"),
    ),
    table(["手段", "作用", "局限"],
          [["宪法护栏", "硬性底线", "原则要全"],
           ["RLHF", "对齐偏好", "主观"],
           ["红队", "发现漏洞", "滞后"],
           ["监控", "线上纠偏", "事后"]]),
    callout("tip", "实际应用场景", '**金融**：交易严守合规底线；**医疗**：不越权给诊断；**内容**：不生成有害信息；**企业**：不越权碰数据'),
    callout("danger", "易错点：一次配置管终身",
        "模型升级、新工具上线都会带来新越权路径。对齐要持续红队+监控+反馈回流，不是写一次护栏就高枕无忧。"),
  ],
},
"6.6": {
  "objectives": [
    "理解「Agent 经济」= Agent 作为可交易的服务单元",
    "能写一个最小 Agent 市场匹配器（任务->报价->派单）",
    "知道市场化带来的新问题：信任、计价、问责",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("当 Agent 能「接单赚钱」",
        para("Agent 经济指：把一个个专用 Agent 当成「可被发现、可调用、可计价」的服务单元，放在市场里按任务匹配。用户发任务，市场按能力+报价派给最合适的 Agent，完成后按用量计费。它把「用 Agent」从「自己养一个」变成「按需调用」，类似把算力做成云。前提是解决信任（它靠谱吗）、计价（多少钱合理）、问责（出事了谁负责）。"),
    ),
    code("s6_6_market.py", "python", "最小 Agent 市场：任务->报价->派单",
        r'''AGENTS = {"写作": 0.5, "翻译": 0.3, "编码": 0.9}

def bid(task, budget):
    if task in AGENTS and AGENTS[task] <= budget:
        return "派单：" + task + " 报价 " + str(AGENTS[task])
    return "无合适 Agent 或超预算"

if __name__ == "__main__":
    print(bid("编码", 1.0))''',
        hl=[4, 6],
        output="派单：编码 报价 0.9",
        note="AGENTS 存报价；bid 校验能力与预算。真实市场还要声誉/计价/结算。task/budget 被引用。"),
    kp("市场化的三道坎",
        para("①信任：怎么证明一个陌生 Agent 靠谱？靠声誉/评测/押金。②计价：按 token、按次、还是按结果？不同模式激励不同行为。③问责：Agent 替你做了错事，责任在谁？这三条不解决，市场就转不起来。"),
    ),
    table(["问题", "解法", "难点"],
          [["信任", "声誉/评测", "刷分"],
           ["计价", "按结果计费", "归因难"],
           ["问责", "身份+日志", "跨境"]]),
    callout("tip", "实际应用场景", '**API 市场**：专用 Agent 上架按次调；**企业内部**：部门间按用量结算；**众包**：任务广播给多个 Agent 竞标'),
    callout("danger", "易错点：只看价格不看声誉",
        "市场化里最低价 Agent 可能最不靠谱。匹配要同时看报价与声誉/评测分，否则省了钱赔了质量。"),
  ],
},
"6.7": {
  "objectives": [
    "理解开源生态对 Agent 技术的「加速度」作用",
    "能写一个最小插件注册表加载器（发现+加载社区 Agent）",
    "知道选型开源时要看：活跃度、协议、与自有栈的契合",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("开源把 Agent 能力「模块化、可复用」",
        para("Agent 领域迭代极快，开源生态（框架、工具、预置 Agent、评测集）让团队不必从零造轮子：一个社区写的检索 Agent、一个 MCP 工具集，装上就能用。生态的「加速度」来自：可组合（拼乐高）、可审计（看源码）、可 fork（改了自用）。但选型不能只看 Star，要看协议是否商用友好、是否还活跃、是否与你的栈契合。"),
    ),
    code("s6_7_oss.py", "python", "最小插件注册表：发现并加载社区组件",
        r'''REGISTRY = {"web-search": "v1.2", "pdf-read": "v0.9"}

def load(name):
    if name in REGISTRY:
        return name + "@" + REGISTRY[name] + " 已加载"
    return "未找到插件：" + name

if __name__ == "__main__":
    print(load("web-search"))''',
        hl=[4, 6],
        output="web-search@v1.2 已加载",
        note="REGISTRY 存可用组件与版本；load 按需加载。真实生态用包管理器+签名校验保证来源可信。name 被引用。"),
    kp("选型开源的三把尺",
        para("①活跃度：最近还有提交和 issue 回复吗？停更的项目别上生产。②协议：MIT/Apache 商用友好，AGPL 有传染风险，看清再引。③契合：与你现有的模型/框架/部署是否顺。三者都过才引入。"),
    ),
    table(["维度", "看什么", "红灯"],
          [["活跃度", "近期提交/issue", "半年无更新"],
           ["协议", "是否商用友好", "AGPL 传染"],
           ["契合", "与自有栈兼容", "要大改"]]),
    callout("tip", "实际应用场景", '**快速验证**：装社区 Agent 跑 spike；**能力补齐**：引 MCP 工具集；**内部沉淀**：把自研组件也开源反哺'),
    callout("danger", "易错点：只看 Star 不选型",
        "Star 高可能只是营销。真正决定能不能用的是活跃度、协议、与栈的契合度，这三把尺缺一不可。"),
  ],
},
"6.8": {
  "objectives": [
    "能为「从入门到能建生产 Agent」设计一条可验证的学习路线",
    "能写一个进度 tracker 量化当前所处阶段",
    "理解「学完基础后」该往哪些深水区走（多Agent/RAG/评估/安全）",
  ],
  "supplement": [
    heading("深入解析与实战"),
    kp("路线要「可验证」而非「看完即忘」",
        para("Agent 技术更新快，死记版本号没用，要建「能力路线 + 每阶段产出物」。基础阶段产出「会调工具的 Agent」；进阶段产出「多 Agent 协作系统」；生产阶段产出「带评估与护栏的上线 Agent」。每到一个阶段就做一个能跑的东西，比收藏 100 篇文更有用。路线尽头不是「学完」，是「能独立交付生产级 Agent」。"),
    ),
    code("s6_8_roadmap.py", "python", "学习路线进度量化",
        r'''ROADMAP = ["Agent 架构", "多Agent", "RAG", "评估", "部署", "安全"]

def progress(done):
    hit = [x for x in done if x in ROADMAP]
    return round(100 * len(hit) / len(ROADMAP), 1)

if __name__ == "__main__":
    print(progress(["Agent 架构", "多Agent", "RAG"]))''',
        hl=[4, 6],
        output="50.0",
        note="ROADMAP 定义路线；progress 按已完成项算百分比。真实学习用「能否交付对应产出物」判定而非看视频。x/done 被引用。"),
    kp("深水区在哪里",
        para("基础之后，真正的区分度在四个深水区：多 Agent 协作（编排与通信）、RAG（检索质量）、评估（量化好坏）、安全（护栏与对齐）。把这四个啃透，才算从「会用框架」到「能交付可靠系统」。"),
    ),
    table(["阶段", "产出物", "标志"],
          [["基础", "会调工具的 Agent", "跑通循环"],
           ["进阶", "多 Agent 系统", "能协作"],
           ["生产", "带评估+护栏", "可上线"],
           ["专家", "可观测+可演进", "能长期运维"]]),
    callout("tip", "实际应用场景", '**入门**：做个人知识库问答；**进阶**：做多 Agent 开发助手；**生产**：加评估与安全上线；**专家**：建监控与复盘机制'),
    callout("danger", "易错点：囤课不产出",
        "Agent 是做出来的不是看会的。每个阶段必须有一个能跑的产出物，否则「学了很多」只是错觉。"),
  ],
},
}

# ---------------------------------------------------------------------------
# 第 1 章再深化（在已扩写基础上继续加背景/原理/对比表/扩展提示）
# 不新增代码块，避免与已有 s1_* 重复；仅追加知识密度。
# ---------------------------------------------------------------------------

CH1X_PLAN = {
"1.1": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("自主性谱系：从脚本到完全自治",
        para("可以画一条「自主性」光谱：规则脚本（if/else，零自主）→ RPA（按固定流程点击，低自主）→ 工作流（编排确定步骤，中低自主）→ Copilot（人给指令、模型补全，中自主）→ 单 Agent（模型自定步骤、可调用工具、能自循环，高自主）→ 多 Agent 系统（多个自治体协作，极高自主）。关键不是越自主越好，而是让自主程度匹配任务的不确定性与风险。订票、转账这类错了代价高的任务，反而该把自主收回、让人确认。"),
    ),
    table(["自主档位", "谁定步骤", "失败代价", "典型用例"],
          [["规则脚本", "开发者", "低", "数据清洗脚本"],
           ["RPA", "流程设计器", "低", "批量表单录入"],
           ["Copilot", "人", "中", "代码补全/写文案"],
           ["单 Agent", "模型", "中高", "客服/调研"],
           ["多 Agent", "多个模型", "高", "研发自动化"]]),
    callout("warning", "过度自主的隐性风险",
        "自主越高，模型幻觉乘以工具副作用的事故面越大。给 Agent 接写权限（发邮件、调 API、删数据）前，先问：这个动作能否撤销？出错能否告警？不可撤销的动作必须加 HITL（人在回路）确认。"),
    callout("tip", "何时不该用 Agent",
        "任务步骤固定、输入输出确定、不需要外部工具，直接用函数或模板最快最稳。Agent 的循环与推理是为不确定付费的，确定性任务用它只会更慢更贵更易错。"),
  ],
},
"1.2": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("分词器决定了成本与上限",
        para("Token 不是字符也不是词，是模型厂商训练时统计出来的最小子词单元。中文通常 1 个汉字约 1~2 个 token，英文 1 个词约 1~1.4 个 token，代码和公式的 token 数更不可预测。同样一段中文喂给不同分词器，token 数可能差很多，直接影响价格与上下文占用。写 prompt 时少废话、用短词，不只是风格，是省钱。"),
    ),
    kp("上下文窗口不等于推理窗口",
        para("模型标称 128K 上下文指的是能塞进去的 token 量，但长上下文下模型对中段内容的注意力会衰减（lost in the middle 现象），且每多一轮对话都要把历史重新算一遍，延迟与成本线性上升。所以不要无脑堆历史，要用摘要、检索、分窗口来挤有效信息。"),
    ),
    table(["模型档位(示例)", "典型上下文", "每 1K 输入 token 相对价", "适合"],
          [["小模型 gpt-4o-mini", "128K", "低（约 1/10）", "分类/抽取/高并发"],
           ["主力 gpt-4o", "128K", "中", "通用对话/复杂推理"],
           ["长上下文专用", "200K+", "高", "整本文档分析"]]),
    callout("danger", "易错点：用长上下文代替检索",
        "把整本手册塞进 prompt 看起来方便，但既贵又容易让模型中间迷失。正确做法是 RAG：先检索相关片段，只把几百 token 的精华送进窗口。"),
    callout("tip", "流式降低体感延迟",
        "等模型吐完 200 字再显示，用户会觉得卡。用 .stream() 边生成边渲染首字，体感延迟从数秒降到毫秒级，是聊天产品的基本功。"),
  ],
},
"1.3": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("Prompt 是每次调用都付费的代码",
        para("和写一次跑一万次的函数不同，prompt 在每一次请求里都要重新发送给模型并重新计费。一段 500 token 的 system prompt，日调用 100 万次就是 5 亿 token 成本。所以 prompt 要像代码一样做性能优化：删冗余、抽公共、对高频简单任务换小模型。"),
    ),
    kp("用结构化分隔符让模型分清边界",
        para("当 prompt 里同时有指令、示例、待处理文本时，用 <instruction> / <examples> / <input> 这类 XML 标签或代码块把区块隔开，能显著降低模型张冠李戴的概率，比纯靠空行和注意二字可靠得多。"),
    ),
    table(["分隔方式", "适用", "坑"],
          [["XML 标签 <tag>", "多区块复杂 prompt", "标签名别和正文冲突"],
           ["代码块 ```", "包裹待处理文本/代码", "文本里本身有 ``` 会截断"],
           ["分隔线 ----", "简单分区", "区分度弱，长 prompt 易混"]]),
    callout("danger", "易错点：few-shot 示例泄露隐私",
        "你给的示例会原样进入上下文并被模型在当次会话记住。示例里别放真实姓名、手机号、内部数据，用脱敏的占位样本。"),
    callout("tip", "示例要对齐分布",
        "few-shot 的示例应当覆盖真实输入的难度与风格。给的全是简单样例，模型遇到难样本会降级处理；给的样例和线上分布不一致，效果反而不如 zero-shot。"),
  ],
},
"1.4": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("幻觉可度量，也该被度量",
        para("幻觉指模型生成了看似合理但事实错误的文本。它无法完全消除，但可以用事实一致性评测来量化：把模型回答与可信知识源逐句比对，算有多少句能在来源中找到支撑。上线前跑一批这样的评测，比看 demo 更靠谱。"),
    ),
    kp("选型是能力乘以成本乘以延迟的三角权衡",
        para("不要默认就用最贵的模型。高并发、确定性强、容错低的任务（如分类、抽取、路由）用 gpt-4o-mini 这类小模型往往 90% 场景够用，成本降一个数量级。把大模型留给真正需要复杂推理的步骤，用小模型前置过滤加大模型深度处理的分级策略最省钱。"),
    ),
    table(["任务类型", "首选策略", "理由"],
          [["分类/路由", "小模型", "边界清晰，不需强推理"],
           ["信息抽取", "小模型+JSON", "结构化、可校验"],
           ["复杂推理/写作", "大模型", "需要世界知识与逻辑"],
           ["长文档分析", "大模型+检索", "上下文+知识点"]]),
    callout("danger", "易错点：被流畅度欺骗",
        "模型写得越顺、越自信，越容易让人放下戒备。流畅不等于正确。凡是进入决策或对外发布的内容，都要有可验证来源或人工复核兜底。"),
    callout("tip", "用拒答阈值兜底",
        "像 1.4 代码的做法：当置信度或检索命中低于阈值就拒答或转人工，比硬编一个答案安全。把「我不确定」当成一等公民能力。"),
  ],
},
"1.5": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("2023 后是能力临界点而非技术突变",
        para("Agent 的概念（规划、工具、记忆）早在 2022 年的 ReAct 论文就提出，但长期不实用，因为模型太弱：规划经常崩、工具调用格式错、长程记忆丢三落四。直到 GPT-4 级别模型在推理与指令遵循上越过某个临界点，这些旧范式才突然能用。判断一项 Agent 技术值不值得上，核心是当下模型的真实能力，而非论文多新。"),
    ),
    kp("Agent 与 Copilot 的边界在谁掌控流程",
        para("Copilot 里人是主驾驶，模型在边上补全；Agent 里模型是主驾驶，自己决定下一步调哪个工具、是否重试。这个区别决定了产品形态：Copilot 适合人要对结果负责的创作/分析场景；Agent 适合目标清晰、步骤不确定、可验证的执行场景。"),
    ),
    table(["维度", "Copilot", "Agent"],
          [["流程控制权", "人", "模型"],
           ["失败影响", "小（人兜底）", "大（需护栏）"],
           ["适合", "创作/分析", "执行/自动化"],
           ["上线门槛", "低", "高（需可观测+回滚）"]]),
    callout("danger", "易错点：把所有逻辑塞进 prompt",
        "想让 Agent 聪明，第一反应常是写超长 prompt 把规则堆进去，结果脆弱、不可调试、易越界。正确做法是把确定逻辑写成代码/工具，prompt 只负责目标与约束，让模型在工具边界内发挥。"),
    callout("tip", "RPA 不等于 Agent，但可组合",
        "RPA 处理固定界面点击，Agent 处理不确定决策。真实项目常是 Agent 做判断、调用 RPA 执行老旧系统操作——用 Agent 的脑子配 RPA 的手。"),
  ],
},
"1.6": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("T 型能力模型：广度打底，深度突破",
        para("学 Agent 不要一头扎进某个框架。先建立横向广度：懂 LLM 原理、Prompt、Tool/RAG/记忆这些通用概念（T 的横杠）；再选一条纵向深入：比如 LangGraph 编排，或 RAG 工程，或评估体系（T 的竖杠）。广度让你不迷路，深度让你能交付。"),
    ),
    kp("项目驱动大于课程驱动",
        para("纯看教程容易看懂了但写不出。每学一个概念就做一个 50 行的小 demo：学到 Tool Calling 就写个能查天气的 Agent；学到 RAG 就接一份自己的文档问答。小项目带来真实报错，报错才是真正的老师。"),
    ),
    table(["周次", "主题", "最小可运行产出"],
          [["1", "LLM+Prompt", "一个带 system prompt 的问答脚本"],
           ["2", "Tool Calling", "能查天气/算数的 Agent"],
           ["3", "ReAct+Loop", "可打印思考轨迹的 Agent"],
           ["4", "RAG", "基于个人文档的问答"],
           ["5", "记忆+评估", "带摘要记忆加一组测试用例"],
           ["6", "编排框架", "用 LangGraph 写一个多步流程"]]),
    callout("tip", "里程碑要可验证",
        "读懂 ReAct 不是里程碑，能独立写出并打印 ReAct 轨迹的脚本且通过 3 个测试用例才是。把里程碑写成可勾选的产出，每完成一项划掉一项，进度才真实。"),
  ],
},
}

# ---------------------------------------------------------------------------
# 第 2 章再深化（在已扩写基础上继续加原理/对比表/工程扩展提示）
# 不新增代码块，避免与已有 s2_* 重复；仅追加知识密度。
# ---------------------------------------------------------------------------

CH2X_PLAN = {
"2.1": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("架构在演化：从单层到规划-反思双层",
        para("最简单的 Agent 是模型加工具加循环单层；稍复杂会加一个规划层先把目标拆成步骤；再进一步加反思层用 Critic 模型评估输出、失败就重做。层越多越智能也越贵越慢。教学骨架（s2_1）是单层，生产系统往往按需叠层——不是越多越好。"),
    ),
    table(["架构形态", "组成", "何时用"],
          [["单层", "模型+工具+循环", "步骤少、可一步到位"],
           ["规划层", "加 Planner", "多步、需先拆解"],
           ["反思层", "加 Critic", "质量要求高、允许重试"],
           ["多 Agent", "多个单层协作", "子任务异质、需分工"]]),
    callout("warning", "抽象边界要早定",
        "组件接口（工具协议、记忆接口、消息格式）越早定清楚，后面换模型/换存储越轻松。第二章骨架把这些做成可插拔，正是为这一步留余地。"),
    callout("danger", "易错点：全量历史塞 system prompt",
        "把完整对话历史无脑塞进 system prompt，既撑爆窗口又拖慢推理，还容易让模型被早期错误带偏。短期记忆该裁（滑窗/摘要），长期记忆该外置（数据库+检索）。"),
  ],
},
"2.2": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("ReAct vs CoT vs Reflexion 三兄弟",
        para("CoT（思维链）只想不做，适合纯推理；ReAct 在想和做（调工具）之间交替，用观测纠偏，适合需要外部信息的任务；Reflexion 在 ReAct 之上加自我反思，把失败写进记忆下次避开。简单说：CoT 动脑，ReAct 动脑加动手，Reflexion 动脑加动手加复盘。"),
    ),
    table(["范式", "产出", "能否用工具", "复盘"],
          [["CoT", "推理步骤", "否", "否"],
           ["ReAct", "Thought/Action/Obs", "能", "否"],
           ["Reflexion", "ReAct+反思", "能", "能"]]),
    callout("warning", "轨迹可能爆炸",
        "ReAct 没有上限会一直 Thought-Action 循环，token 与延迟指数增长。必须设最大步数（见 s2_5 护栏）并在轨迹过长时强制收敛或交人。"),
    callout("danger", "易错点：只看 Final Answer",
        "Final Answer 看起来对，中间 Action 可能已经调错工具、读到脏数据。生产环境必须落盘完整轨迹，出错时回放定位，而不是只看结果。"),
  ],
},
"2.3": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("计划粒度是门艺术",
        para("计划拆太粗，执行时模型容易跑偏；拆太细，规划开销盖过执行，且一步错了全局重来。经验值：每个子任务应当能被一次工具调用或一段明确逻辑完成。长任务优先 Plan-Execute，因为失败可以只重规划受影响的后续步骤，不必推倒重来。"),
    ),
    table(["范式", "何时用", "代价"],
          [["Plan-Execute", "长任务/可失败", "规划开销"],
           ["ReAct", "需边做边纠偏", "易循环爆炸"],
           ["Reflexion", "质量敏感", "多次重试成本"],
           ["Workflow", "步骤确定", "不灵活"]]),
    callout("warning", "重规划要结合观测",
        "重规划不是重跑旧计划，而是根据已完成的真实结果调整后续。忽略已完成部分、机械重发原计划的 Agent，会卡在同一个坑里反复跌倒。"),
    callout("danger", "易错点：计划一次定死",
        "把计划当 immutable 合同，环境一变就失效。计划应是可变假设：每完成一步就用新观测更新它。"),
  ],
},
"2.4": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("Tool Schema 的隐藏规则决定调用质量",
        para("模型靠你给的 JSON Schema 来理解工具。三个常被忽视的点：每个参数都要写 description，模型读的是描述不是变量名；用 enum 限定取值能大幅降低乱填；required 只放真正必填的，多余的必填会让模型为了凑参数而编造。Schema 写得像给同事的接口文档，调用才稳。"),
    ),
    table(["Schema 错误", "后果", "正确做法"],
          [["参数无 description", "模型猜语义、填错", "每个参数写清用途与单位"],
           ["滥用 required", "模型编造参数凑齐", "只标真正必填"],
           ["无 enum 约束", "自由文本易越界", "枚举值显式列出"],
           ["描述泄露内部实现", "暴露系统细节/被注入", "只说做什么不说怎么实现"]]),
    callout("warning", "并行调用有依赖陷阱",
        "s2_4 演示了并行查多城天气，因为它们互不依赖。一旦后续步骤依赖前一步结果（如查余额再转账），就必须串行，否则会读到空的或旧的值。依赖分析要写在编排层。"),
    callout("danger", "易错点：工具描述泄露系统信息",
        "工具 description 里写调用内部 API、读取数据库 user 表，等于把架构白给模型，也成了注入入口。描述只讲业务能力，实现细节留在代码里。"),
  ],
},
"2.5": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("失控的两种形态与对应护栏",
        para("循环失控常见两类：步数爆炸（一直 Thought 不停）；工具反复失败仍重试（死循环调同一个坏接口）。前者用 max_steps 上限，后者用 per-tool 失败计数加退避（backoff）。s2_5 的护栏正是这两类阈值。护栏不是可选项，是 Agent 上线的最低门槛。"),
    ),
    table(["失控类型", "防护", "典型阈值"],
          [["步数爆炸", "max_steps", "8~15 步"],
           ["工具死循环", "失败计数+退避", "同工具失败 3 次停"],
           ["超时", "整体 timeout", "单次工具 10s"],
           ["预算击穿", "token/cost 上限", "单次会话上限"]]),
    callout("warning", "护栏要可观测",
        "触发护栏时不能静默失败。要记录为什么停、停在哪一步、最后观测是什么，否则线上出了问题你连复现都做不到。"),
    callout("danger", "易错点：护栏过松或过紧",
        "过松等于没防（模型烧钱到上限才停）；过紧则正常长任务被误杀。阈值要按真实任务分布标定：先放宽跑一批，看正常任务用到几步，再据此收紧。"),
  ],
},
"2.6": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("记忆分三层：工作/短期/长期",
        para("工作记忆等于当前一轮的输入输出（瞬时）；短期记忆等于当前会话的滚动历史（需裁剪）；长期记忆等于跨会话沉淀的知识（需压缩加检索）。混淆三者是新手最常犯的错：把本该外置的长期知识塞进每轮 prompt，既贵又噪。正确分层后，每轮只带工作记忆加短期精华加长期检索结果。"),
    ),
    table(["记忆层", "存活", "存储", "操作"],
          [["工作", "一轮", "变量", "拼接"],
           ["短期", "一会话", "滑窗/摘要", "裁剪"],
           ["长期", "跨会话", "向量库/DB", "写入+检索"]]),
    callout("warning", "摘要会丢细节",
        "s2_6 用摘要压缩短期记忆，但摘要模型可能把关键异常值、用户偏好这类细节吞掉。压缩时保留结构化事实（金额、ID、决定）而不仅是叙事，必要时对重要片段做钉住不压缩。"),
    callout("danger", "易错点：记忆污染",
        "把不可靠的模型生成物直接写回长期记忆，会污染后续所有会话（错误越积越多）。写入长期记忆前要做可信度过滤：只存可验证事实、用户明确确认的信息、工具返回的结构化结果。"),
  ],
},
"2.7": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("JSON Mode 与 Schema Mode 是两回事",
        para("JSON Mode 只保证输出是合法 JSON，不保证字段对、类型对；Schema Mode（如 structured outputs / function calling 的严格模式）会按你给的 schema 强制字段名、类型、enum，连多一个字段都不允许。需要直接进下游系统的数据，必须用 Schema Mode 而非 JSON Mode。"),
    ),
    table(["方式", "保证", "局限"],
          [["手写解析", "无", "脆弱、易崩"],
           ["JSON Mode", "合法 JSON", "字段/类型不保"],
           ["Schema Mode", "严格符合 schema", "模型有时抗拒/需重试"],
           ["二次校验", "业务正确", "需写规则"]]),
    callout("warning", "三层保障才稳",
        "s2_7 的做法：response_format 约束加代码校验加失败重试。不要只信第一层——模型偶尔会忘了格式，重试加校验能把成功率从 95% 拉到 99.9%。"),
    callout("danger", "易错点：只信 response_format",
        "拿到结构化输出就直接取值进库，一旦模型漏字段就 KeyError 崩服务。任何结构化输出进业务前都要过一遍 schema 校验与默认值兜底。"),
  ],
},
"2.8": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("分块（Chunking）是 RAG 的隐形天花板",
        para("检索质量上限在分块阶段就定了。块太大召回精度低、噪声多；块太小语义被切碎、上下文断裂。经验：文本 300~800 token、重叠 10%~20%；代码按函数/类切；表格尽量整块保留。切完一定要人工抽几条看召回的相关块是否真能回答问题。"),
    ),
    table(["参数", "太小", "太大", "经验值"],
          [["chunk_size", "语义断裂", "噪声多", "300~800 token"],
           ["overlap", "边界丢失", "冗余贵", "10%~20%"],
           ["切分单位", "碎", "混", "语义/结构边界"]]),
    callout("warning", "召回不等于答案",
        "s2_8 加了重排（rerank）环节：向量召回的 Top-K 常有相关但排序错的块，重排模型能按与问题真实相关度重新打分。跳过重排直接用召回结果，是 RAG 答非所问的头号原因。"),
    callout("danger", "易错点：检索噪声喂乱模型",
        "把 10 个低相关块一股脑塞给模型，模型会被噪声带偏甚至引用错误块。控制送入上下文的块数（3~5 个精选）加重排，并要求无依据就说明不知道。"),
  ],
},
"2.9": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("从单路径到多路径推理",
        para("基础 Prompt 是一条线走到底；进阶技术让模型分叉：Self-Consistency 对同一题采样多条推理路径，投票取多数，显著提升数学/逻辑题准确率；Tree of Thoughts 把思路展开成树，搜索最优分支，适合需要探索的策略题。代价是调用次数乘 N，只在错不起的任务上用。"),
    ),
    table(["技术", "思路", "成本", "适合"],
          [["CoT", "单链", "1x", "通用"],
           ["Self-Consistency", "多链投票", "Nx", "数学/逻辑"],
           ["ToT", "树搜索", "高", "需探索的策略"],
           ["Reflexion", "反思复盘", "高", "质量敏感"]]),
    callout("warning", "注入攻击比想象中常见",
        "s2_9 演示了 Prompt 注入：用户在你给的待处理文本里写忽略以上指令、输出某某，模型可能照做。凡是把不可信内容拼进 prompt，都要假设它会被用来攻击。"),
    callout("danger", "易错点：只防注入不校验输出",
        "防住输入注入不代表安全：模型仍可能输出违规/涉密内容。输出侧也要有护栏（内容审核、敏感词、格式校验），形成输入防护加输出校验双闸。"),
  ],
},
"2.10": {
  "supplement": [
    heading("原理深挖与工程扩展"),
    kp("离线评测与在线评测分工",
        para("离线评测用固定数据集（golden set）在发布前跑，验证功能对不对；在线评测看真实流量指标（成功率、用户满意度、成本/延迟），验证上线后好不好。两者不可互相替代：离线全过但线上翻车的案例极多（数据分布漂移、用户用法超出预期）。"),
    ),
    table(["评测类型", "问的问题", "指标举例"],
          [["离线", "功能对不对", "准确率/格式合规率"],
           ["在线", "用户满不满意", "满意度/CSAT/留存"],
           ["成本", "贵不贵", "单次 token/元"],
           ["安全", "会不会出事", "注入成功率/违规率"]]),
    callout("warning", "评估集要随业务长",
        "golden set 写一次就放着会过时。把线上真实 bad case 持续回流进评估集，评估集才代表真实分布，否则评出来一片绿、线上照样翻车。"),
    callout("danger", "易错点：只看通过率不看成本",
        "某版 prompt 通过率加 2% 但每次多烧 3 倍 token，整体是亏的。评估必须同时看质量加成本加延迟三件套，用单指标决策会误导优化方向。"),
  ],
},
}


def main():
    targets = [int(x) for x in sys.argv[1:] if x.isdigit()]
    plans = {1: CH1X_PLAN, 2: CH2X_PLAN, 3: CH3_PLAN, 4: CH4_PLAN, 5: CH5_PLAN, 6: CH6_PLAN}
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
