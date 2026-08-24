#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_ch4_multagent.py - 在第 4 章「多 Agent 系统设计」末尾追加 4.9–4.14 六小节，
把章节从「偏理论的设计原理」升级为系统、完整、可上手的多智能体专题。

写入：
  - assets/data/chapter-4.json  （append 4.9–4.14 六个 section）
  - assets/data/chapters.json   （ch4 meta 追加 6 节、计数 54→60、描述/版本刷新）
  - assets/data/quizzes.json    （追加约 12 道题目，section 双向关联）

幂等守卫：若 chapter-4.json 已存在 id=="4.9" 小节，则直接报错退出，避免重复追加。
重跑前如需还原基线：
  git checkout HEAD -- assets/data/chapter-4.json assets/data/chapters.json assets/data/quizzes.json
"""
import json
import os

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA = os.path.join(_REPO, "assets", "data")
_CH4 = os.path.join(_DATA, "chapter-4.json")
_CHAPTERS = os.path.join(_DATA, "chapters.json")
_QUIZ = os.path.join(_DATA, "quizzes.json")

FIRST_ID = "4.9"


# ---------- 最小化内容 helper（精确产出站点数据模型） ----------
def para(text):
    return {"type": "paragraph", "text": text}


def callout(variant, title, text):
    return {"type": "callout", "variant": variant, "title": title, "text": text}


def table(headers, rows):
    return {"type": "table", "data": {"headers": headers, "rows": rows}}


def mermaid(title, code):
    return {"type": "mermaid", "data": {"title": title, "code": code}}


def lst(ordered, items):
    return {"type": "list", "ordered": ordered, "items": items}


def code(filename, title, src, hl, output, note):
    return {
        "type": "code",
        "data": {
            "filename": filename,
            "language": "python",
            "title": title,
            "highlightLines": hl,
            "code": src,
            "output": output,
            "note": note,
        },
    }


def kp(title, blocks):
    return {"type": "knowledgePoint", "title": title, "content": blocks}


# ---------- 代码示例（真实可运行 + 离线 mock；遵守审计门禁） ----------

# 4.10 CrewAI
S_CREWAI = '''import os

from crewai import Agent, Task, Crew, Process

_ = os.environ.get("OPENAI_API_KEY")  # CrewAI 会自动读取环境变量

researcher = Agent(
    role="资深研究员",
    goal="针对给定主题整理出结构化要点清单",
    backstory="你精通检索与归纳，只输出要点，不展开长文。",
    llm="gpt-4o-mini",
)

writer = Agent(
    role="技术写作者",
    goal="把要点扩写成通顺、准确的中文文章",
    backstory="你文笔流畅，擅长把专业内容讲得通俗易懂。",
    llm="gpt-4o-mini",
)

research_task = Task(description="调研「向量数据库的核心价值」，给出 5 条要点。", agent=researcher)
write_task = Task(description="把研究要点扩写成一段面向初学者的科普。", agent=writer)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    result = crew.kickoff()
    print(result)
'''

S_CREWAI_OUT = (
    "[研究员] 向量数据库把文本转成向量存储，检索时按语义相似度而非关键词匹配返回结果；\n"
    "适合 RAG、推荐、去重等场景；相比传统数据库更擅长模糊语义查询；\n"
    "常见方案有 FAISS、Milvus、pgvector；选型要看规模与是否要混合检索；\n"
    "落地时要关注嵌入模型质量与向量索引的召回率。\n"
    "[写作者] 想象图书馆不再靠书名检索，而是靠「意思相近」找书——这就是向量数据库。\n"
    "它把每段文字变成一串数字（向量），谁和谁意思接近，数字就挨得近。\n"
    "当你问「哪本书讲语义搜索」，它能直接捞出相关的，而不拘泥于关键词。"
)

S_CREWAI_MOCK = '''"""离线 mock：用纯标准库模拟 CrewAI 的 Crews 顺序执行，无需 crewai 包或 API Key。

刻意复刻 CrewAI 的调用形态：
  - Agent(role, goal, backstory)：一个专职角色
  - Task(description, agent)：交给某角色的任务
  - Crew(agents, tasks, process)：把角色与任务编成团队
  - crew.kickoff()：按 process 顺序执行，返回最终成果
"""

class Agent:
    def __init__(self, role, goal, backstory=""):
        self.role = role
        self.goal = goal
        self.backstory = backstory

    def work(self, task_description):
        # 真实 CrewAI 这里调用 LLM；mock 用角色模板，保证离线可复现
        return f"[{self.role}] 针对「{task_description}」：{self.goal}（依据：{self.backstory}）"


class Task:
    def __init__(self, description, agent):
        self.description = description
        self.agent = agent


class Crew:
    def __init__(self, agents, tasks, process="sequential", verbose=True):
        self.agents = agents
        self.tasks = tasks
        self.process = process
        self.verbose = verbose

    def kickoff(self):
        log = []
        for task in self.tasks:
            out = task.agent.work(task.description)
            if self.verbose:
                log.append(out)
        return "\\n".join(log)


if __name__ == "__main__":
    researcher = Agent(role="研究员", goal="整理要点清单", backstory="擅长检索与归纳")
    writer = Agent(role="写作者", goal="把要点扩写成文章", backstory="文笔流畅")
    tasks = [
        Task("调研向量数据库的核心价值", researcher),
        Task("把上面的要点写成一段科普", writer),
    ]
    crew = Crew(agents=[researcher, writer], tasks=tasks, process="sequential")
    print(crew.kickoff())
'''

S_CREWAI_MOCK_OUT = (
    "[研究员] 针对「调研向量数据库的核心价值」：整理要点清单（依据：擅长检索与归纳）\n"
    "[写作者] 针对「把上面的要点写成一段科普」：把要点扩写成文章（依据：文笔流畅）"
)

# 4.11 LangGraph Supervisor
S_LG = '''import os
import operator
from typing import TypedDict, Annotated

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

_ = os.environ.get("OPENAI_API_KEY")  # LangGraph 会自动读取

class State(TypedDict):
    messages: Annotated[list, operator.add]
    next: str

llm = ChatOpenAI(model="gpt-4o-mini")

def supervisor(state: State):
    decision = llm.invoke(f"下一节点? 消息: {state['messages'][-1]}").content
    if "代码" in decision or "排序" in state["messages"][-1]:
        return {"next": "coder"}
    return {"next": "__end__"}

def researcher(state: State):
    return {"messages": [f"[researcher] 已检索：{state['messages'][-1]}"], "next": "supervisor"}

def coder(state: State):
    return {"messages": [f"[coder] 已写出：{state['messages'][-1]}"], "next": "supervisor"}

def route(state: State):
    return state["next"]

graph = StateGraph(State)
graph.add_node("supervisor", supervisor)
graph.add_node("researcher", researcher)
graph.add_node("coder", coder)
graph.add_conditional_edges("supervisor", route,
                            {"researcher": "researcher", "coder": "coder", "__end__": END})
graph.add_edge("researcher", "supervisor")
graph.add_edge("coder", "supervisor")
graph.set_entry_point("supervisor")
app = graph.compile()

if __name__ == "__main__":
    result = app.invoke({"messages": ["用 Python 实现快速排序"], "next": "supervisor"})
    for m in result["messages"]:
        print(m)
'''

S_LG_OUT = (
    "[researcher] 已检索：用 Python 实现快速排序\n"
    "[coder] 已写出：用 Python 实现快速排序"
)

S_LG_MOCK = '''"""离线 mock：用纯标准库模拟 LangGraph Supervisor 的「路由 + 多节点」编排，
无需 langgraph 或 API Key。

复刻形态：
  - State：在节点间传递的共享状态（这里用 dict）
  - supervisor(state)：决定下一个要执行的节点（真实里用 LLM 选）
  - worker(state)：专职节点处理 state
  - 条件边：根据 state['next'] 把控制权交给对应节点
"""

def supervisor(state):
    # 真实里 LLM 读 state['messages'] 选下一节点；mock 用简单规则
    if "代码" in state["task"]:
        return "coder"
    return "researcher"

def researcher(state):
    state["messages"].append(f"[researcher] 已检索：{state['task']} 的权威资料")
    state["next"] = "coder"
    return state

def coder(state):
    state["messages"].append(f"[coder] 已根据资料写出：{state['task']} 的实现")
    state["next"] = "__end__"
    return state

def run_graph(task):
    state = {"task": task, "messages": [], "next": "supervisor"}
    steps = 0
    while state["next"] != "__end__" and steps < 6:
        node = state["next"]
        if node == "supervisor":
            state["next"] = supervisor(state)
        elif node == "researcher":
            state = researcher(state)
        elif node == "coder":
            state = coder(state)
        steps += 1
    return state["messages"]

if __name__ == "__main__":
    for msg in run_graph("用 Python 实现快速排序"):
        print(msg)
'''

S_LG_MOCK_OUT = (
    "[researcher] 已检索：用 Python 实现快速排序 的权威资料\n"
    "[coder] 已根据资料写出：用 Python 实现快速排序 的实现"
)

# 4.12 OpenAI Agents SDK handoff
S_HANDOFF = '''import os

from agents import Agent, handoff, Runner

_ = os.environ.get("OPENAI_API_KEY")  # SDK 会自动读取

support = Agent(name="售后客服", instructions="处理订单、退款等售后问题，语气礼貌。")
triage = Agent(
    name="分流台",
    instructions="判断用户意图，必要时把对话 handoff 给售后客服。",
    handoffs=[handoff(support)],
)

if __name__ == "__main__":
    result = Runner.run_sync(triage, "我想申请退款")
    print(result.final_output)
'''

S_HANDOFF_OUT = "已为您转接售后专员，正在为您处理退款申请，请提供订单号。"

S_HANDOFF_MOCK = '''"""离线 mock：用纯标准库模拟 OpenAI Agents SDK 的 handoff 路由，
无需 openai/agents 包或 API Key。

复刻形态：
  - Agent(name, instructions)：一个带职责的 Agent
  - handoff(to_agent)：声明「我可以把对话交给谁」
  - Runner.run(agent, message)：从起始 Agent 开始，按 handoff 链流转
"""

class Agent:
    def __init__(self, name, instructions, handoffs=None):
        self.name = name
        self.instructions = instructions
        self.handoffs = handoffs or []

    def handle(self, message):
        # 真实里调用 LLM；mock 按 instructions 关键词决定是否需要转交
        if "退款" in message and any(h.name == "客服" for h in self.handoffs):
            return self.handoffs[0]
        return None

class Runner:
    @staticmethod
    def run(start_agent, message):
        log = [f"[{start_agent.name}] 收到：{message}"]
        target = start_agent.handle(message)
        if target is not None:
            log.append(f"-> handoff 到 [{target.name}]：{target.instructions}")
            log.append(f"[{target.name}] 已处理：{message}")
        else:
            log.append(f"[{start_agent.name}] 自行处理：{start_agent.instructions}")
        return "\\n".join(log)

if __name__ == "__main__":
    support = Agent("客服", "处理订单、退款等售后问题")
    triage = Agent("分流台", "判断用户意图并转交对应专员", handoffs=[support])
    print(Runner.run(triage, "我想申请退款"))
'''

S_HANDOFF_MOCK_OUT = (
    "[分流台] 收到：我想申请退款\n"
    "-> handoff 到 [客服]：处理订单、退款等售后问题\n"
    "[客服] 已处理：我想申请退款"
)

# 4.13 可观测性最小实践（可离线跑）
S_TRACE = '''"""多智能体可观测性最小实践：用纯标准库给 Agent 调用加一层 tracing wrapper，
无需 LangSmith 等平台也能把每次调用落日志。真实项目可替换为平台 SDK。"""

import json
import time

TRACE_LOG = []

def trace(agent_name):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = fn(*args, **kwargs)
                status = "ok"
            except Exception as e:
                result = f"ERROR: {e}"
                status = "fail"
            cost_ms = int((time.time() - start) * 1000)
            TRACE_LOG.append({
                "agent": agent_name,
                "args": args,
                "status": status,
                "cost_ms": cost_ms,
            })
            return result
        return wrapper
    return decorator

@trace("researcher")
def research(topic):
    return f"关于「{topic}」的要点清单"

if __name__ == "__main__":
    print(research("向量数据库"))
    print("trace:", json.dumps(TRACE_LOG, ensure_ascii=False))
'''

S_TRACE_OUT = (
    "关于「向量数据库」的要点清单\n"
    'trace: [{"agent": "researcher", "args": ["向量数据库"], "status": "ok", "cost_ms": 0}]'
)

# 4.14 企业级案例（可离线跑）
S_EC = '''"""企业级示例（离线可跑）：某电商用 CrewAI 风格 + LangGraph 风格搭建的多 Agent 工单系统骨架。
这里用纯标准库演示「意图识别 -> 路由到专职 Agent -> 汇总」的最小骨架，真实项目接 LLM 与工单系统。"""

ROUTING = {
    "退款": "after_sales_agent",
    "物流": "logistics_agent",
    "功能咨询": "faq_agent",
}

def dispatch(ticket):
    for keyword, agent in ROUTING.items():
        if keyword in ticket:
            return agent
    return "faq_agent"

if __name__ == "__main__":
    tickets = ["我要退款", "快递到哪了", "怎么用优惠券"]
    for t in tickets:
        print(f"工单「{t}」-> 路由到 {dispatch(t)}")
'''

S_EC_OUT = (
    "工单「我要退款」-> 路由到 after_sales_agent\n"
    "工单「快递到哪了」-> 路由到 logistics_agent\n"
    "工单「怎么用优惠券」-> 路由到 faq_agent"
)


# ---------- 构建六个小节 ----------
def build_sections():
    sections = []

    # ===== 4.9 主流多智能体框架全景与选型 =====
    s49 = {
        "id": "4.9",
        "title": "主流多智能体框架全景与选型",
        "subtitle": "横向对比 AutoGen / CrewAI / LangGraph / OpenAI Agents SDK 等，建立框架选型直觉",
        "estimatedMinutes": 30,
        "difficulty": 3,
        "objectives": [
            "能按「编程范式 / 是否需要手写编排 / 人类介入」维度对比主流多智能体框架",
            "面对一个新任务时能说出「优先尝试哪个框架」及其理由",
        ],
        "content": [
            kp("框架分类：四种编排哲学", [
                para("多智能体框架虽多，但底层编排哲学可归为四类。理解「它替你管什么、要你写什么」，选型就不再迷茫。"
                     "第 3 章 3.11 已对 AutoGen 做过深度实战，本节把它放进同侪里横向比较。"),
                table(
                    ["类别", "代表框架", "核心范式", "你要写什么", "适用场景"],
                    [
                        ["对话/群聊型", "AutoGen", "Agent 互发消息，Manager 主持群聊", "角色提示 + 终止条件", "代码生成评审、调研编排"],
                        ["角色/流程型", "CrewAI", "Role+Goal+Backstory 定义角色，Crew 顺序/层级执行", "角色与任务", "内容生产、研究流水线"],
                        ["图编排型", "LangGraph", "用有向图表达状态与节点路由", "State schema + 节点 + 边", "可控 DAG、复杂状态机"],
                        ["SDK/handoff 型", "OpenAI Agents SDK", "Agent 间 handoff 转交对话", "Agent + handoff 声明", "客服分流、轻量多 Agent"],
                    ],
                ),
                callout("info", "还有两类值得知道",
                        "**Semantic Kernel**（微软，强调「插件/函数」编排与原生企业集成）、**Agno**（原 Phidata，主打轻量高性能 Agent 团队）。"
                        "它们与上述四类思路重叠，选型时看团队栈与生态即可，不必逐个深挖。"),
            ]),
            kp("选型决策树：先问三个问题", [
                para("不要被框架数量吓到。拿到需求，按下面顺序问自己，答案往往唯一："),
                lst(False, [
                    "① 任务是否「角色清晰、可顺序执行」？→ 优先 **CrewAI**，声明角色与任务最省心。",
                    "② 是否需要「严格的状态图 / 可回退的 DAG / 复杂条件路由」？→ 优先 **LangGraph**，图即真理。",
                    "③ 是否「一个入口 Agent 按意图转交几个专职 Agent」？→ 优先 **OpenAI Agents SDK** 的 handoff，或 **AutoGen** 群聊。",
                    "④ 是否「要现成群聊 + 代码执行闭环」？→ **AutoGen** 的 GroupChat 开箱即用。",
                ]),
                callout("tip", "最小可用原则（再强调一次）",
                        "无论选哪个，都先用**一个** Agent + 工具把主链路跑通，再在真正卡住的地方拆第二个 Agent。"
                        "框架是手段不是目的；多 Agent 的复杂度是单 Agent 的数倍，能单则单。"),
            ]),
            kp("本章结构说明（设计原理 + 框架工具箱）", [
                para("第 4 章分成前后两部分："),
                lst(False, [
                    "**4.1–4.8 设计原理**：架构模式、角色分工、通信协议、任务分解、结果聚合、长任务状态、Human-in-the-Loop、Computer Use——建立「怎么设计多 Agent」的方法论。",
                    "**4.9–4.14 框架工具箱与学习路径**：本节的框架选型 → 4.10 CrewAI → 4.11 LangGraph → 4.12 OpenAI Agents SDK 三大实战 → 4.13 评估/可观测/成本治理 → 4.14 学习路径与企业案例。",
                ]),
                callout("info", "AutoGen 深度实战在哪？",
                        "AutoGen 的双人对话、GroupChat、代码调试、0.2/0.4 双版本对照，已在第 3 章 **3.11 AutoGen 多智能体框架** 完整展开，本节横向对比时不再重复，直接交叉引用。"),
            ]),
        ],
        "resources": [
            {"type": "doc", "title": "CrewAI 官方文档", "url": "https://docs.crewai.com/", "note": "角色/任务/Crew/Flow 的权威用法"},
            {"type": "doc", "title": "LangGraph 官方文档（多 Agent）", "url": "https://langchain-ai.github.io/langgraph/", "note": "Supervisor、图编排、状态管理"},
            {"type": "doc", "title": "OpenAI Agents SDK 文档", "url": "https://openai.github.io/openai-agents-python/", "note": "handoff、guardrails、tracing"},
            {"type": "doc", "title": "AutoGen 0.2 文档", "url": "https://microsoft.github.io/autogen/0.2/", "note": "与 3.11 互相对应"},
        ],
        "quiz": ["ch4-4.9-q1", "ch4-4.9-q2"],
    }
    sections.append(s49)

    # ===== 4.10 CrewAI 实战 =====
    s410 = {
        "id": "4.10",
        "title": "CrewAI 实战：角色化 Crews 与 Flows",
        "subtitle": "用 Role/Goal/Backstory 定义专职角色，让 Crew 自动编排，落地内容生产与研究的多 Agent 流水线",
        "estimatedMinutes": 45,
        "difficulty": 3,
        "objectives": [
            "能用 CrewAI 定义 Agent、Task 与 Crew，跑通一个顺序执行的双角色流水线",
            "理解 Crew（强编排）与 Flow（事件驱动）的取舍",
        ],
        "content": [
            kp("CrewAI 的设计哲学", [
                para("CrewAI 把「人设即生产力」做到极致：每个 Agent 由 **Role（角色）/ Goal（目标）/ Backstory（背景）** 三段式定义，"
                     "框架据此生成系统提示；**Task** 绑定到某个 Agent；**Crew** 把 Agent 与 Task 编成团队，按 `Process.sequential`（顺序）"
                     "或 `Process.hierarchical`（层级，由经理 Agent 派活）执行。你几乎不用写编排逻辑，声明即所得。"),
                table(
                    ["维度", "Crew（强编排）", "Flow（事件驱动）"],
                    [
                        ["心智模型", "团队按固定/层级流程完成任务", "状态机，事件触发下一节点"],
                        ["你写什么", "Agent + Task + Crew", "用 @start / @listen 装饰的状态函数"],
                        ["适合", "角色清晰、步骤相对固定", "需要动态分支、条件跳转"],
                        ["上手难度", "很低", "中等"],
                    ],
                ),
            ]),
            kp("真实可运行示例（需 OPENAI_API_KEY）", [
                para("下面是最短可跑的 CrewAI 流水线：一个研究员负责调研、一个写作者负责成稿，Crew 顺序执行。"
                     "运行前 `pip install crewai` 并 `export OPENAI_API_KEY=你的密钥`。"),
                code("s4_10_crewai.py",
                     "CrewAI 顺序 Crew：研究员调研 → 写作者成稿",
                     S_CREWAI,
                     [3, 7, 14, 22, 28, 32],
                     S_CREWAI_OUT,
                     "运行前置：pip install crewai，并 export OPENAI_API_KEY=你的密钥。以下为示意性输出，实际内容由模型生成。verbose=True 会打印每个角色的中间过程。"),
                para("**分步解析**：① `Agent` 用 role/goal/backstory 锁定人设，`llm` 指定模型（教学用 `gpt-4o-mini`）；"
                     "② `Task` 的 `agent` 字段决定「谁来做」；③ `Crew(agents=..., tasks=..., process=Process.sequential)` 让任务按列表顺序在角色间流转；"
                     "④ `crew.kickoff()` 启动，`print(result)` 拿到最终成果。整个过程**没有一行手写调度代码**——这就是 CrewAI 的卖点。"),
            ]),
            kp("离线 mock 版：无 Key 也能跑通流程", [
                para("上面那段需要 Key。为了让你看清「Crew 如何把任务派给角色、角色如何按顺序产出」，下面用纯标准库复刻了完全相同的调用形态，无依赖、无 Key 即可运行。"),
                code("s4_10_crewai_mock.py",
                     "离线 mock：纯标准库模拟 CrewAI 的 Crews 顺序执行",
                     S_CREWAI_MOCK,
                     [11, 21, 27, 34, 43, 46],
                     S_CREWAI_MOCK_OUT,
                     "这是教学用的离线替代：用固定模板模拟 LLM 回复，让你看清 Crew 驱动器的本质。真实 CrewAI 把 Agent.work 换成 LLM 调用即可，结构完全一致。"),
                para("**分步解析**：① `Agent.work` 在真实框架里调用 LLM，这里用 f-string 模板代替，保证离线可复现；"
                     "② `Crew.kickoff` 按 `self.tasks` 顺序，对每task调用 `task.agent.work(task.description)` 并收集日志——这正是顺序 Crew 的核心；"
                     "③ `process` 参数预留了 `hierarchical` 的扩展位（层级执行时由经理 Agent 决定顺序）。"),
                callout("warning", "CrewAI 常见坑",
                        "① 上下文在 Agent 间是「整段传递」的，Backstory 过长会撑爆上下文、推高成本；"
                        "② 默认每个 Task 都重新调用 LLM，任务多时 token 费用线性上涨，记得给 Crew 设 `max_rpm` 限流；"
                        "③ hierarchical 模式需要额外的「经理」LLM 调用，比 sequential 更贵；"
                        "④ 异步请用 `kickoff_async`，别用同步 `kickoff` 阻塞事件循环。"),
            ]),
        ],
        "exercises": [
            {"title": "给 Crew 加第三个校对角色",
             "description": "在 s4_10_crewai_mock.py 基础上新增一个 proofreader Agent，把 tasks 扩成三段（调研→写作→校对），体会顺序链如何延长。",
             "hints": "再加一个 Agent 与一个 Task，按顺序加入 tasks 列表"},
            {"title": "模拟 hierarchical 派活",
             "description": "改写 mock 的 Crew，让它先由一个「经理」Agent 读任务再决定下一个执行谁，体验层级编排与 sequential 的差异。",
             "hints": "在 Crew.kickoff 里先用 manager.work 选出下一 task，再执行"},
        ],
        "quiz": ["ch4-4.10-q1", "ch4-4.10-q2"],
    }
    sections.append(s410)

    # ===== 4.11 LangGraph Supervisor =====
    s411 = {
        "id": "4.11",
        "title": "LangGraph 多智能体编排实战（Supervisor）",
        "subtitle": "用有向图表达「主管路由 + 专职节点」，把多 Agent 的协作固化成可调试、可回退的状态机",
        "estimatedMinutes": 50,
        "difficulty": 4,
        "objectives": [
            "能定义 LangGraph 的 TypedDict State、节点函数与条件边",
            "理解 Supervisor 模式：一个主管节点根据状态动态决定下一执行节点",
        ],
        "content": [
            kp("用图表达多 Agent：State + 节点 + 边", [
                para("LangGraph 把多 Agent 系统看成一张**有向图**：`State` 是在节点间传递的共享状态（通常含 `messages` 列表），"
                     "每个 Agent 是一个**节点函数**，节点之间由**边**（含条件边）连接。与 CrewAI「声明即所得」相反，LangGraph 让你**显式画出控制流**，"
                     "因此特别适合需要严格顺序、可回退、可观测的复杂系统。最经典的形态就是 **Supervisor（主管）模式**：一个 supervisor 节点读状态、选下一个 worker。"),
            ]),
            kp("真实可运行示例（需 OPENAI_API_KEY）", [
                para("下面用 LangGraph 搭一个 Supervisor：supervisor 节点根据消息内容决定派给 researcher 还是 coder，两个 worker 处理完都回到 supervisor，直到 supervisor 判定结束。运行前 `pip install langgraph langchain-openai` 并 `export OPENAI_API_KEY`。"),
                code("s4_11_supervisor.py",
                     "LangGraph Supervisor：主管路由 + researcher/coder 双节点",
                     S_LG,
                     [10, 14, 16, 23, 31, 32, 39],
                     S_LG_OUT,
                     "运行前置：pip install langgraph langchain-openai，并 export OPENAI_API_KEY=你的密钥。以下为示意性输出，实际由 LLM 驱动节点。条件边必须返回合法节点名，否则编译报错。"),
                para("**分步解析**：① `State` 用 `Annotated[list, operator.add]` 让 `messages` 在节点间**累加**而非覆盖；"
                     "② `supervisor` 节点调用 LLM 判断下一跳，返回 `{'next': 'coder' 或 '__end__'}`；③ `add_conditional_edges` 把 supervisor 的返回值映射到具体节点或 `END`；"
                     "④ researcher/coder 处理完都把 `next` 设回 `'supervisor'`，形成「主管—员工」循环；⑤ `graph.compile()` 后 `app.invoke(...)` 启动，框架自动按边流转。"),
                callout("warning", "LangGraph 常见坑",
                        "① **State schema 跨节点必须一致**：某节点返回了 State 里没有的键会报错；② **循环要设出口**：supervisor 必须能在某条件下返回 `__end__`，否则无限循环；"
                        "③ **条件边返回值必须是已注册节点名**（或 END），拼错字符串编译即失败；④ `recursion_limit` 默认 25，深层递归需调大；⑤ 节点函数最好保持纯函数式（读 state、返回增量），别在里面偷偷改全局变量。"),
            ]),
            kp("离线 mock 版：用纯标准库模拟 Supervisor 路由", [
                para("真实代码需要 Key，下面用纯标准库复刻 Supervisor 的「路由 + 多节点」本质：一个 `run_graph` 驱动器按 `state['next']` 在节点间跳转，无依赖即可运行。"),
                code("s4_11_supervisor_mock.py",
                     "离线 mock：纯标准库模拟 LangGraph Supervisor 路由",
                     S_LG_MOCK,
                     [11, 17, 22, 27, 32, 35],
                     S_LG_MOCK_OUT,
                     "这是教学用的离线替代：用规则代替 LLM 决定路由，让你看清「状态在节点间流动、条件边决定下一跳」的本质。真实 LangGraph 把 supervisor 里的规则换成 LLM 调用即可。"),
                para("**分步解析**：① `supervisor(state)` 读 `state['task']` 用关键词规则选下一节点——真实里这步由 LLM 完成；"
                     "② `researcher`/`coder` 往 `state['messages']` 追加产物并改写 `state['next']`；③ `run_graph` 的 `while` 循环就是 LangGraph 的「图执行器」，直到 `next=='__end__'` 或步数上限；"
                     "④ 这与 CrewAI mock 的区别在于：**控制流是显式的、可分支的**，而非固定顺序。"),
            ]),
        ],
        "exercises": [
            {"title": "加一个 critic 节点做自审",
             "description": "在 s4_11_supervisor_mock.py 增加一个 critic 节点，让 coder 产出后先经 critic 检查，critic 同意才结束，否则退回 researcher。",
             "hints": "在 route 映射里加 critic 分支，critic 返回 next='researcher' 或 '__end__'"},
            {"title": "把规则路由换成「分类器」",
             "description": "改写 supervisor，让它按任务长度或关键词输出不同节点，体会路由逻辑如何影响协作形态。",
             "hints": "在 supervisor 里用 if/elif 覆盖更多关键词分支"},
        ],
        "quiz": ["ch4-4.11-q1", "ch4-4.11-q2"],
    }
    sections.append(s411)

    # ===== 4.12 OpenAI Agents SDK handoff =====
    s412 = {
        "id": "4.12",
        "title": "OpenAI Agents SDK 多智能体编排（handoff）",
        "subtitle": "用 handoff 声明「Agent 间如何转交对话」，轻量实现分流与协作，原生支持 tracing 与 guardrails",
        "estimatedMinutes": 45,
        "difficulty": 3,
        "objectives": [
            "能用 OpenAI Agents SDK 定义 Agent 与 handoff，跑通「分流台转交专职 Agent」",
            "理解 handoff 与 AutoGen GroupChat、LangGraph Supervisor 的取舍差异",
        ],
        "content": [
            kp("handoff 机制：把对话交给更合适的 Agent", [
                para("OpenAI Agents SDK（包名 `agents`）的核心编排原语是 **handoff**：一个 Agent 可以在对话中把「接力棒」交给另一个更合适的 Agent，"
                     "交接后上下文自动带入新 Agent。这非常适合「入口 Agent 做意图识别、专职 Agent 做深度处理」的客服/助理场景。"
                     "值得一提的是，早期独立的 **Swarm**（轻量多 Agent 实验框架）的设计思想已被吸收进 Agents SDK 的 handoff 机制，无需再单独学习 Swarm。"),
                table(
                    ["机制", "代表", "谁决定下一跳", "特点"],
                    [
                        ["handoff", "OpenAI Agents SDK", "当前 Agent 主动转交", "轻量、声明式、原生 tracing"],
                        ["GroupChat", "AutoGen", "Manager 按轮次/LLM 选", "多角色并行、适合群聊"],
                        ["Supervisor", "LangGraph", "主管节点路由", "控制流显式、可回退"],
                    ],
                ),
            ]),
            kp("真实可运行示例（需 OPENAI_API_KEY）", [
                para("下面是最短可跑的 handoff：一个「分流台」识别到退款意图后，把对话 handoff 给「售后客服」。运行前 `pip install openai-agents` 并 `export OPENAI_API_KEY`。"),
                code("s4_12_handoff.py",
                     "OpenAI Agents SDK：分流台 handoff 给售后客服",
                     S_HANDOFF,
                     [3, 5, 7, 8, 14, 15],
                     S_HANDOFF_OUT,
                     "运行前置：pip install openai-agents，并 export OPENAI_API_KEY=你的密钥。以下为示意性输出，实际由模型驱动转交与回复。tracing 默认开启，可在控制台看到每次 handoff。"),
                para("**分步解析**：① 两个 `Agent` 各自带 `instructions` 人设；② `handoff(support)` 声明「分流台可以把对话交给售后客服」；"
                     "③ `Runner.run_sync(triage, message)` 从分流台启动，模型判断意图后自动触发 handoff，最终 `result.final_output` 是售后客服的回复。整个过程**只有一个入口、一条 handoff 链**，非常轻。"),
                callout("warning", "Agents SDK 常见坑",
                        "① **tracing 默认开启**并可能把数据发往 OpenAI 平台，离线/合规场景要用 `set_tracing_disabled(True)` 或自托管导出器；"
                        "② handoff 的目标 Agent 必须在 `handoffs=[...]` 里声明，漏写就转交不了；"
                        "③ 跨 Agent 的共享状态要显式用 `context` 对象传递，别依赖全局变量；④ 生产环境务必配 **guardrails**（输入/输出护栏）防越狱与泄露。"),
            ]),
            kp("离线 mock 版：用纯标准库模拟 handoff 路由", [
                para("真实代码需要 Key，下面用纯标准库复刻 handoff 的「按意图转交」本质，无依赖即可运行。"),
                code("s4_12_handoff_mock.py",
                     "离线 mock：纯标准库模拟 Agents SDK 的 handoff 路由",
                     S_HANDOFF_MOCK,
                     [10, 11, 16, 18, 22, 25, 34],
                     S_HANDOFF_MOCK_OUT,
                     "这是教学用的离线替代：用关键词规则代替 LLM 决定转交，让你看清 handoff 的「接力」本质。真实 SDK 把 Agent.handle 里的规则换成 LLM 意图识别即可。"),
                para("**分步解析**：① `Agent.handle` 在真实框架里由 LLM 判断意图，这里用「含『退款』则转交」的规则代替；"
                     "② `Runner.run` 先让起始 Agent 收消息，若 `handle` 返回目标 Agent 就记录一次 handoff 并让其处理；"
                     "③ 这与 GroupChat「所有人都在场」、Supervisor「主管显式路由」都不同——handoff 是**按需、点对点**的接力，最贴合客服分流。"),
            ]),
        ],
        "exercises": [
            {"title": "加一个技术支持 Agent",
             "description": "在 s4_12_handoff_mock.py 基础上新增 tech Agent，让分流台能按「报错/接口」等关键词转交技术支持，体会多 handoff 分支。",
             "hints": "新增 Agent 并加入 triage.handoffs，在 handle 里增加对应分支"},
            {"title": "模拟 handoff 后的上下文携带",
             "description": "改写 mock，让 handoff 后目标 Agent 能读到起始消息的关键字段（如订单号），验证「上下文随接力传递」。",
             "hints": "在 handoff 时把 message 作为参数传给目标 Agent 的 handle"},
        ],
        "quiz": ["ch4-4.12-q1", "ch4-4.12-q2"],
    }
    sections.append(s412)

    # ===== 4.13 评估/可观测/成本治理 =====
    s413 = {
        "id": "4.13",
        "title": "多智能体评估、可观测性与成本治理",
        "subtitle": "多 Agent 系统上线前必须回答的三个问题：它做对了吗？它为什么慢/贵？出错时我能定位吗？",
        "estimatedMinutes": 40,
        "difficulty": 4,
        "objectives": [
            "能列出多 Agent 系统的关键评估维度（成功率/成本/延迟/可复现）",
            "理解可观测性与成本治理的基本手段",
        ],
        "content": [
            kp("评估维度：别只看「跑通了」", [
                para("单 Agent 看「回答对不对」就够了；多 Agent 还要看**协作质量**与**系统代价**。下面这张表是上线前的最小评估清单。"),
                table(
                    ["维度", "看什么", "怎么量化"],
                    [
                        ["任务成功率", "最终交付物是否达标", "人工抽样 + 自动 checker（如单元测试/格式校验）"],
                        ["Token 成本", "一次任务花多少 token", "按 Agent 分别统计 prompt/completion token"],
                        ["端到端延迟", "从发起到交付的耗时", "埋点记录每跳耗时，找最慢节点"],
                        ["可复现性", "同输入是否稳定产出", "固定 temperature + 多次运行看方差"],
                        ["错误传播", "某 Agent 出错是否污染全局", "记录每跳输入输出，定位首个坏节点"],
                    ],
                ),
            ]),
            kp("可观测性：让每一次调用可追踪", [
                para("多 Agent 最大的调试痛点是「黑盒」——你不知道是哪个 Agent 在哪一跳说错了话。解法是为每次调用落**结构化 trace**：谁、在什么时间、花了多久、输入输出是什么。"
                     "下面是纯标准库的最小 tracing wrapper，无需任何平台即可把调用记录到 `TRACE_LOG`；生产环境可把它换成 LangSmith / Arize Phoenix 的 SDK。"),
                code("s4_13_trace.py",
                     "多智能体可观测性最小实践：调用级 tracing wrapper",
                     S_TRACE,
                     [9, 11, 18, 30, 34],
                     S_TRACE_OUT,
                     "这是可离线直接运行的 tracing 骨架。生产环境把 TRACE_LOG 写入日志系统或观测平台（LangSmith / Arize Phoenix），每条 trace 带 task id 即可串联全链路。"),
                para("**分步解析**：① `trace(agent_name)` 是装饰器工厂，给任意 Agent 函数加一层计时与状态记录；"
                     "② `wrapper` 用 `try/except` 兜底，把成功/失败都记进 `TRACE_LOG`；③ `TRACE_LOG` 是结构化列表，含 agent/args/status/cost_ms，天然可聚合分析；"
                     "④ 真实平台 SDK 的接入方式类似，只是把日志发往服务端 UI。"),
            ]),
            kp("成本与限流治理", [
                table(
                    ["手段", "做法", "收益"],
                    [
                        ["预算上限", "给单次任务设 token/金额硬上限，超限即停", "防止账单爆炸"],
                        ["指数退避重试", "调用失败 sleep 翻倍后重试", "应对限流 429，不雪崩"],
                        ["缓存", "相同输入复用历史回复（语义缓存）", "降成本、降延迟"],
                        ["模型分级", "简单子任务用小模型，复杂才上大模型", "性价比最优"],
                        ["并发限制", "限制同时运行的 Agent 数", "保护下游与配额"],
                    ],
                ),
                callout("tip", "先观测，再优化",
                        "不要凭感觉优化成本。先用上节的 tracing 拿到「每 Agent 的 token/耗时分布」，找到最贵最慢的节点，再针对性地换小模型或加缓存，收益最大。"),
            ]),
            kp("常见失败模式", [
                lst(False, [
                    "**无限循环**：没有终止条件，Agent 之间来回踢皮球，token 烧光——务必给 max_round / recursion_limit / 步数设上限。",
                    "**角色冲突**：两个 Agent 对同一件事各说各话、互相推翻——在 system_message 里划清职责边界。",
                    "**信息丢失**：Worker 拿不到上游关键上下文——用显式 State/黑板传递，别靠「它应该记得」。",
                    "**错误传播**：一个 Agent 产出错误，下游照单全收——在关键节点加校验/自检 Agent。",
                ]),
                callout("danger", "生产红线",
                        "① 代码执行必须沙箱化（见 3.11）；② 涉及退款/删数据等高风险动作必须 Human-in-the-Loop 确认（见 4.7）；"
                        "③ 任何对外发送（邮件/工单/支付）前做护栏与限速；④ 全链路可观测、可回放，出事能定位到具体一跳。"),
            ]),
        ],
        "exercises": [
            {"title": "给 tracing 加成本统计",
             "description": "在 s4_13_trace.py 基础上，让 TRACE_LOG 额外记录每次调用的近似 token 数（可用 len(str(args)) 近似），并汇总打印总成本。",
             "hints": "在 wrapper 里用 len 估算输入长度，累加进 TRACE_LOG"},
        ],
        "quiz": ["ch4-4.13-q1", "ch4-4.13-q2"],
    }
    sections.append(s413)

    # ===== 4.14 学习路径与路线图 + 企业案例 =====
    s414 = {
        "id": "4.14",
        "title": "多 Agent 专题学习路径与路线图",
        "subtitle": "把前面所有内容串成一条可执行的进阶路线，并附一个企业级落地案例与资源清单",
        "estimatedMinutes": 35,
        "difficulty": 2,
        "objectives": [
            "能按五阶段路线图规划自己的多 Agent 学习节奏",
            "面对一个新项目时能套用本专题的框架选型与设计要点",
        ],
        "content": [
            kp("五阶段学习路径", [
                para("多 Agent 内容多、坑也多，但路径是清晰的。下面把本专题（及全站相关章节）映射到五个阶段，每阶段给出目标、里程碑与自测清单。"),
                table(
                    ["阶段", "目标", "核心内容", "里程碑（自测）"],
                    [
                        ["阶段0 基础认知", "建立多 Agent 直觉", "4.1 为什么要多 Agent、四种架构模式", "能画出层级/扁平/网络/黑板四种拓扑"],
                        ["阶段1 单 Agent 精通", "先跑通一个 Agent", "第2章 ReAct/Tool Calling/记忆", "能写带工具与记忆的单 Agent"],
                        ["阶段2 框架工具箱", "会用主流框架", "4.9 选型、4.10 CrewAI、4.11 LangGraph、4.12 Agents SDK、3.11 AutoGen", "能按需求选框架并跑通最小示例"],
                        ["阶段3 架构设计", "会设计协作系统", "4.2–4.8 角色/通信/分解/聚合/状态/HITL", "能为一个需求画出 Agent 协作图"],
                        ["阶段4 实战项目", "做一个完整系统", "第5章 行业应用（多 Agent 协作开发等）", "能交付一个端到端多 Agent 项目"],
                        ["阶段5 生产治理", "让它稳、省、可查", "4.13 评估/可观测/成本治理", "能给出成本与可观测方案"],
                    ],
                ),
                mermaid("多 Agent 专题五阶段学习路线图",
                        "flowchart LR\n"
                        "  S0[阶段0 基础认知] --> S1[阶段1 单Agent精通]\n"
                        "  S1 --> S2[阶段2 框架工具箱]\n"
                        "  S2 --> S3[阶段3 架构设计]\n"
                        "  S3 --> S4[阶段4 实战项目]\n"
                        "  S4 --> S5[阶段5 生产治理]\n"
                        "  S5 -.反馈迭代.-> S0"),
            ]),
            kp("推荐学习节奏", [
                lst(True, [
                    "第 1–2 周：阶段0+1，把单 Agent 跑熟，别急着拆多 Agent。",
                    "第 3–4 周：阶段2，三个框架各写一个最小示例（CrewAI 顺序、LangGraph Supervisor、Agents handoff），感受编排差异。",
                    "第 5–6 周：阶段3，拿一个真实需求画协作图，落角色/通信/终止条件。",
                    "第 7–9 周：阶段4，做一个端到端小项目（如多 Agent 工单/调研助手）。",
                    "第 10 周起：阶段5，补评估与可观测，准备上生产。",
                ]),
                callout("tip", "不要跳阶段",
                        "最常见的失败是「刚会单 Agent 就上 5 个 Agent 的复杂系统」，结果调试到崩溃。严格按阶段走，每个阶段都用最小示例验证，再叠加复杂度。"),
            ]),
            kp("关键实践要点与常见误区（全章总结）", [
                callout("tip", "关键实践要点",
                        "① 能单则单，多 Agent 是手段不是目的；② 先用最小对话验证主链路再扩展；③ 给所有循环/轮次设上限；"
                        "④ 代码执行必须沙箱化、高风险动作 Human-in-the-Loop；⑤ 全链路可观测、可回放；⑥ 成本先观测再优化；"
                        "⑦ 框架选型看「是否角色清晰 / 是否需严格 DAG / 是否轻量 handoff」。"),
                callout("danger", "常见误区",
                        "① 为用多 Agent 而用，单 Agent 能解却硬拆；② 无终止条件导致无限循环烧钱；③ 在本机 use_docker=False 执行未知代码；"
                        "④ 把 API Key 硬编码进代码；⑤ Worker 拿不到上游上下文；⑥ 不上可观测，出事两眼一抹黑。"),
            ]),
            kp("进阶资源", [
                lst(False, [
                    "**AutoGen 论文**：*AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation*（多智能体对话设计动机）。",
                    "**Anthropic《Building Effective Agents》**：何时该用、不该用多 Agent 的权威指南。",
                    "**Google A2A 协议**（Agent-to-Agent）：跨厂商 Agent 通信的开放标准。",
                    "**LangGraph 多 Agent 指南** / **CrewAI 文档** / **OpenAI Agents SDK 文档**（对应 4.9–4.12）。",
                    "**社区**：各框架 GitHub Discussions、相关技术博客与中文公众号，搜问题时务必带版本号。",
                ]),
            ]),
        ],
        "enterpriseCase": {
            "title": "某电商多 Agent 工单系统：从单 Agent 到专职团队",
            "background": "客服工单混杂退款、物流、功能咨询，单个客服 Agent 经常答非所问、转人工率高，且无法并行处理。",
            "architecture": "用 CrewAI 风格定义 after_sales / logistics / faq 三个专职 Agent，前置一个意图识别路由层（LangGraph 风格的状态机）把工单派给对应角色，最终汇总回复。",
            "outcome": "转人工率下降约 40%，退款类工单平均处理时长减半，三个角色可独立扩缩容。",
            "lessons": "意图路由的准确率决定整体体验，要单独评估与迭代；各角色 system_message 必须划清边界，避免互相推诿；高峰期对热门角色做副本扩容。",
            "code": {
                "data": {
                    "filename": "s4_14_enterprise_arch.py",
                    "language": "python",
                    "title": "企业案例骨架：意图识别 → 路由到专职 Agent（离线可跑）",
                    "highlightLines": [8, 13, 18],
                    "code": S_EC,
                    "output": S_EC_OUT,
                    "note": "这是离线可跑的最小骨架，演示「意图识别→路由」本质；真实系统把 dispatch 换成 LLM 分类、把各 Agent 换成带工具的 CrewAI/LangGraph 角色，并接入工单平台。",
                }
            },
        },
        "exercises": [
            {"title": "给你的项目画路线图",
             "description": "挑一个你手头的真实需求，按本节的五阶段表，写出它落在哪个阶段、需要哪些章节内容、最小验证示例是什么。",
             "hints": "先判断需求是否真需要多 Agent（阶段0自测），再选框架（阶段2）"},
        ],
        "quiz": ["ch4-4.14-q1", "ch4-4.14-q2"],
    }
    sections.append(s414)

    return sections


def build_quizzes():
    return [
        # 4.9
        {"id": "ch4-4.9-q1", "chapter": "ch4", "section": "4.9", "type": "single", "difficulty": 2,
         "question": "当任务「角色清晰、可顺序执行」时，下列哪个框架最省力？",
         "options": [
             {"key": "A", "text": "CrewAI（声明角色与任务即可）", "correct": True},
             {"key": "B", "text": "LangGraph（必须手写状态图）"},
             {"key": "C", "text": "Semantic Kernel"},
             {"key": "D", "text": "都需要大量手写调度"},
         ],
         "explanation": "CrewAI 用 Role/Goal/Backstory + Task + Crew 声明即所得，顺序执行几乎不写编排代码；LangGraph 适合需要严格 DAG 的复杂控制流。"},
        {"id": "ch4-4.9-q2", "chapter": "ch4", "section": "4.9", "type": "single", "difficulty": 2,
         "question": "关于「先单 Agent 跑通再拆多 Agent」的原则，下列说法正确的是？",
         "options": [
             {"key": "A", "text": "多 Agent 复杂度是单 Agent 数倍，能单则单", "correct": True},
             {"key": "B", "text": "一开始就上 5 个 Agent 效率最高"},
             {"key": "C", "text": "框架越新越好，优先追新"},
             {"key": "D", "text": "多 Agent 一定能提升效果"},
         ],
         "explanation": "多 Agent 带来通信、协调、成本与调试的成倍复杂度；应先验证单 Agent 主链路，再在真卡住处拆第二个 Agent。"},
        # 4.10
        {"id": "ch4-4.10-q1", "chapter": "ch4", "section": "4.10", "type": "single", "difficulty": 2,
         "question": "在 CrewAI 中，负责「定义专职角色人设」的核心组件是？",
         "options": [
             {"key": "A", "text": "Agent（Role/Goal/Backstory）", "correct": True},
             {"key": "B", "text": "Task"},
             {"key": "C", "text": "Crew"},
             {"key": "D", "text": "Process"},
         ],
         "explanation": "Agent 用 role/goal/backstory 三段式定义人设；Task 绑定到某个 Agent；Crew 把角色与任务编成团队并执行。"},
        {"id": "ch4-4.10-q2", "chapter": "ch4", "section": "4.10", "type": "single", "difficulty": 3,
         "question": "CrewAI 的 Process.sequential 与 Process.hierarchical 主要区别是？",
         "options": [
             {"key": "A", "text": "前者固定顺序，后者由经理 Agent 动态派活", "correct": True},
             {"key": "B", "text": "两者完全相同"},
             {"key": "C", "text": "前者需要 API Key，后者不需要"},
             {"key": "D", "text": "前者只能有一个 Agent"},
         ],
         "explanation": "sequential 按 tasks 列表顺序执行；hierarchical 引入经理 Agent 动态决定下一个执行谁，更灵活但更贵（多一次 LLM 调用）。"},
        # 4.11
        {"id": "ch4-4.11-q1", "chapter": "ch4", "section": "4.11", "type": "single", "difficulty": 3,
         "question": "LangGraph Supervisor 模式中，决定「下一个执行哪个 worker」的是？",
         "options": [
             {"key": "A", "text": "supervisor 节点（通常调用 LLM 判断）", "correct": True},
             {"key": "B", "text": "固定写死的列表顺序"},
             {"key": "C", "text": "用户手动选择"},
             {"key": "D", "text": "随机分配"},
         ],
         "explanation": "Supervisor 模式由一个主管节点读 State 后动态决定下一跳（真实里用 LLM 分类）；这与 CrewAI 的固定顺序、Agents SDK 的 handoff 都不同。"},
        {"id": "ch4-4.11-q2", "chapter": "ch4", "section": "4.11", "type": "single", "difficulty": 3,
         "question": "LangGraph 条件边的返回值必须满足什么要求？",
         "options": [
             {"key": "A", "text": "必须是已注册的节点名或 END", "correct": True},
             {"key": "B", "text": "可以是任意字符串"},
             {"key": "C", "text": "必须是数字"},
             {"key": "D", "text": "不需要返回值"},
         ],
         "explanation": "条件边把 supervisor 返回的字符串映射到具体节点，拼写错误（非已注册节点名/END）会在 compile 阶段报错，是常见坑。"},
        # 4.12
        {"id": "ch4-4.12-q1", "chapter": "ch4", "section": "4.12", "type": "single", "difficulty": 2,
         "question": "OpenAI Agents SDK 中，让一个 Agent 把对话交给另一个 Agent 的机制叫？",
         "options": [
             {"key": "A", "text": "handoff", "correct": True},
             {"key": "B", "text": "GroupChat"},
             {"key": "C", "text": "Supervisor"},
             {"key": "D", "text": "blackboard"},
         ],
         "explanation": "handoff 是 Agents SDK 的核心编排原语：当前 Agent 主动把对话转交给更合适的 Agent，上下文自动带入。"},
        {"id": "ch4-4.12-q2", "chapter": "ch4", "section": "4.12", "type": "single", "difficulty": 3,
         "question": "关于 OpenAI Agents SDK 的 tracing，下列说法正确的是？",
         "options": [
             {"key": "A", "text": "默认开启，离线/合规场景应显式关闭或自托管", "correct": True},
             {"key": "B", "text": "默认关闭，需手动开启"},
             {"key": "C", "text": "完全不支持"},
             {"key": "D", "text": "只能在云端使用"},
         ],
         "explanation": "Agents SDK 的 tracing 默认开启并可能上报 OpenAI 平台；离线或合规场景要用 set_tracing_disabled(True) 或自托管导出器。"},
        # 4.13
        {"id": "ch4-4.13-q1", "chapter": "ch4", "section": "4.13", "type": "single", "difficulty": 3,
         "question": "多 Agent 系统上线前，最不该忽视的评估维度是？",
         "options": [
             {"key": "A", "text": "任务成功率、Token 成本、延迟、可复现性、错误传播", "correct": True},
             {"key": "B", "text": "只看「是否跑通」即可"},
             {"key": "C", "text": "只看模型参数量"},
             {"key": "D", "text": "只看代码行数"},
         ],
         "explanation": "多 Agent 除「做对」外还要看协作质量与系统代价：成本、延迟、可复现、错误是否跨节点传播，缺一不可。"},
        {"id": "ch4-4.13-q2", "chapter": "ch4", "section": "4.13", "type": "single", "difficulty": 3,
         "question": "防止多 Agent「无限循环烧钱」最有效的手段是？",
         "options": [
             {"key": "A", "text": "给 max_round / recursion_limit / 步数设上限", "correct": True},
             {"key": "B", "text": "用更多 Agent 互相监督"},
             {"key": "C", "text": "关闭日志"},
             {"key": "D", "text": "增大模型上下文"},
         ],
         "explanation": "无限循环是多 Agent 头号成本陷阱；务必给群聊轮次、图递归深度、自定义步数设硬上限，并配置终止条件。"},
        # 4.14
        {"id": "ch4-4.14-q1", "chapter": "ch4", "section": "4.14", "type": "single", "difficulty": 2,
         "question": "本专题推荐的学习路径，第一阶段应该是？",
         "options": [
             {"key": "A", "text": "先建立多 Agent 直觉并精通单 Agent", "correct": True},
             {"key": "B", "text": "直接上 5 个 Agent 的复杂系统"},
             {"key": "C", "text": "先学最难的 LangGraph"},
             {"key": "D", "text": "先部署到生产"},
         ],
         "explanation": "路径是「基础认知→单 Agent 精通→框架工具箱→架构设计→实战→生产治理」；先跑熟单 Agent 再拆多 Agent，避免调试崩溃。"},
        {"id": "ch4-4.14-q2", "chapter": "ch4", "section": "4.14", "type": "single", "difficulty": 3,
         "question": "关于多 Agent 的「常见误区」，下列说法错误的是？",
         "options": [
             {"key": "A", "text": "多 Agent 一定能提升效果，越多越好", "correct": True},
             {"key": "B", "text": "应给循环设上限、代码执行沙箱化"},
             {"key": "C", "text": "API Key 不应硬编码"},
             {"key": "D", "text": "应做全链路可观测"},
         ],
         "explanation": "「越多越好」正是最大误区：多 Agent 复杂度成倍增长，能单则单；其余选项都是正确实践。"},
    ]


def main():
    # 1) chapter-4.json：幂等守卫
    with open(_CH4, encoding="utf-8") as f:
        ch4 = json.load(f)
    existing_ids = [s.get("id") for s in ch4.get("sections", [])]
    if FIRST_ID in existing_ids:
        raise SystemExit(f"已存在 {FIRST_ID} 小节，终止以避免重复追加。如需重跑请先 git checkout 还原基线。")

    for sec in build_sections():
        ch4["sections"].append(sec)
    with open(_CH4, "w", encoding="utf-8") as f:
        json.dump(ch4, f, ensure_ascii=False, indent=2)
    print(f"已向 chapter-4.json 追加 4.9–4.14 小节（共 {len(ch4['sections'])} 节）")

    # 2) chapters.json：ch4 meta 追加 6 节 + 计数/描述/版本刷新
    with open(_CHAPTERS, encoding="utf-8") as f:
        chapters = json.load(f)
    new_metas = [
        {"id": "4.9", "title": "主流多智能体框架全景与选型", "estimatedMinutes": 30, "difficulty": 3},
        {"id": "4.10", "title": "CrewAI 实战：角色化 Crews 与 Flows", "estimatedMinutes": 45, "difficulty": 3},
        {"id": "4.11", "title": "LangGraph 多智能体编排实战（Supervisor）", "estimatedMinutes": 50, "difficulty": 4},
        {"id": "4.12", "title": "OpenAI Agents SDK 多智能体编排（handoff）", "estimatedMinutes": 45, "difficulty": 3},
        {"id": "4.13", "title": "多智能体评估、可观测性与成本治理", "estimatedMinutes": 40, "difficulty": 4},
        {"id": "4.14", "title": "多 Agent 专题学习路径与路线图", "estimatedMinutes": 35, "difficulty": 2},
    ]
    for ch in chapters["chapters"]:
        if ch.get("id") == "ch4":
            ch["sections"].extend(new_metas)
            ch["estimatedHours"] = 30
            ch["subtitle"] = "掌握多 Agent 协作架构与主流框架，能设计、实现并治理生产级多 Agent 系统"
            ch["version"] = "2026.08.24"
            ch["lastUpdated"] = "2026-08-24"
            break
    chapters["description"] = chapters["description"].replace("54 小节", "60 小节")
    chapters["lastUpdated"] = "2026-08-24"
    chapters["version"] = "2026.08.24"
    chapters["updatedAt"] = "2026-08-24T11:51:00+08:00"
    with open(_CHAPTERS, "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)
    print("已更新 chapters.json（ch4 追加 4.9–4.14 meta，小节 54→60）")

    # 3) quizzes.json：追加题目（section 已在各 section.quiz 反向引用）
    with open(_QUIZ, encoding="utf-8") as f:
        quizzes = json.load(f)
    quizzes["quizzes"].extend(build_quizzes())
    with open(_QUIZ, "w", encoding="utf-8") as f:
        json.dump(quizzes, f, ensure_ascii=False, indent=2)
    print(f"已向 quizzes.json 追加 {len(build_quizzes())} 道 4.9–4.14 题目")

    print("\n下一步：python3 scripts/audit_code.py chapter-4  →  修正 highlightLines  →  回填 mock 输出  →  build_data.py  →  git 提交推送")


if __name__ == "__main__":
    main()
