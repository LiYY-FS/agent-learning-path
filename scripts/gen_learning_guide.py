#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_learning_guide.py —— 为章节 3.2（LangChain）与 3.3（LangGraph）在「实战部分」之前
插入一个独立带标题的「系统学习引导」模块，使结构变为「先讲解学习、后实战练习」。

插入位置：content 数组中 `深入解析与实战` 标题所在下标之前。
模块形态：heading「系统学习引导」+ 学习路径 + 核心概念讲解 + 原理说明 + 关键知识点梳理。
约束：不新增任何 `code` 块（仅 heading/knowledgePoint/paragraph/table/callout/list/mermaid），
      以零审计风险且不影响既有 code 块的 highlightLines。

幂等保护：若目标 section 已含「系统学习引导」heading，则跳过（提示先 git checkout 还原再跑）。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "assets", "data")
CHAPTER = os.path.join(DATA_DIR, "chapter-3.json")

TARGET_HEADING = "深入解析与实战"
NEW_HEADING = "系统学习引导"


# ---------- helper 副本（与 gen_ch456 / gen_enrich 同源风格）----------
def kp(title, *blocks):
    return {"type": "knowledgePoint", "title": title, "content": list(blocks)}


def para(text):
    return {"type": "paragraph", "text": text}


def table(headers, rows):
    return {"type": "table", "data": {"headers": headers, "rows": rows}}


def callout(variant, title, text):
    return {"type": "callout", "variant": variant, "title": title, "text": text}


def lst(items, ordered=False):
    return {"type": "list", "ordered": ordered, "items": items}


def heading(text):
    return {"type": "heading", "text": text}


def md(title, src):
    return {"type": "mermaid", "data": {"title": title, "code": src}}


# ---------- 3.2 LangChain 系统学习引导 ----------
def build_32():
    return [
        heading(NEW_HEADING),
        kp(
            "本节学习路径：先建立认知，再动手",
            para(
                "LangChain 不是「少写几行代码」的语法糖，而是一套把横切关注点（换模型、重试、流式、追踪）"
                "抽象成统一接口的框架。动手写代码前，先把下面四条认知走通，再回头看每个实战文件，你会快很多。"
            ),
            lst(
                ordered=True,
                items=[
                    "第 1 步 · 懂定位：知道 LangChain 四层包各自负责什么，什么时候该用、什么时候不该用（见下方核心概念）。",
                    "第 2 步 · 懂组合范式：掌握 LCEL 的 `prompt | model | parser`，理解「所有组件都是 Runnable」这一统一协议。",
                    "第 3 步 · 懂五大概念的职责边界：Chain / Agent / Memory / Tool / LCEL 各自解决什么问题，组合时谁负责哪一段。",
                    "第 4 步 · 懂坑：版本碎片、抽象过厚、旧 Memory 已废弃、RAG 先查检索——动手前先有心理预期。",
                ],
            ),
            callout(
                "tip",
                "建议读法",
                "先通读本节的「核心概念讲解」与「原理说明」，再逐个运行 `3_2_*.py` 与 `s3_2_*.py`。"
                "每跑通一个，回头对照「关键知识点梳理」确认自己真懂了，而不是只让代码跑起来。",
            ),
        ),
        kp(
            "核心概念讲解：LangChain 的认知模型",
            para(
                "记住一句话：**一切皆组件，用 `|` 组合成链**。PromptTemplate、Model、OutputParser、Retriever、"
                "Agent 都是可替换的组件；LCEL 用 `|` 把它们串成管道。这种「声明式组合」让流水线可读、可测、可复用。"
            ),
            table(
                headers=["概念", "一句话", "写代码时的落点"],
                rows=[
                    ["Chain", "操作序列（如 prompt|model|parser）", "`LCEL` 管道 / `RunnableSequence`"],
                    ["Agent", "自主决策实体，自己决定调不调工具", "`AgentExecutor` + `create_tool_calling_agent`"],
                    ["Memory", "跨轮对话的历史上下文", "`RunnableWithMessageHistory`（旧 `ConversationBufferMemory` 已废弃）"],
                    ["Tool", "模型可调用的外部能力", "`@tool` 装饰器，docstring 即工具说明书"],
                    ["LCEL", "把上述组件黏合成的管道表达式语言", "`prompt | model | parser`"],
                ],
            ),
            callout(
                "note",
                "底层统一接口是 Runnable 协议",
                "每个组件都实现 `invoke / batch / stream / ainvoke`，所以任意组件能接任意组件，"
                "拼出来的结果仍是 Runnable，可以继续拼。这是 LangChain 可组合性的根源。",
            ),
        ),
        kp(
            "原理说明：为什么用 LCEL 而非手写函数",
            para(
                "手写嵌套函数也能跑通，但随着需求变多（流式、批处理、重试、降级、异步），样板代码会指数膨胀。"
                "LCEL 的妙处是：只要组件符合 `Runnable` 协议，你就**免费获得**这五种能力，不用自己实现。"
                "代价是抽象层厚，报错常穿越多条 Runnable，需要 LangSmith 或逐节点打印来定位。"
            ),
            md(
                "LCEL 管道与免费能力",
                "flowchart LR\n  A[PromptTemplate] -->|pipe| B[ChatModel]\n  B -->|pipe| C[OutputParser]\n  C --> D[结构化结果]\n  B -.免费获得.-> E[stream / batch / retry / fallback / async]",
            ),
            callout(
                "warning",
                "抽象过厚导致调试黑盒",
                "链一复杂，报错堆栈全是 Runnable 内部。务必接 LangSmith（`LANGSMITH_TRACING=true`）"
                "或自己 print 每一步输入输出；不要盲目升级 langchain 大版本，breaking change 频繁。",
            ),
        ),
        kp(
            "关键知识点梳理：动手前你必须能答出",
            lst(
                items=[
                    "能画出 `prompt | model | parser` 的数据流向，并说清每一步的输入输出类型。",
                    "能解释 `Runnable` 协议的四个方法（invoke/batch/stream/ainvoke）各自适用什么场景。",
                    "能说清 LCEL 相对手写嵌套函数的五个免费能力（流式/批处理/异步/重试/降级）。",
                    "知道旧 `ConversationBufferMemory` 已废弃，多轮记忆该用 `RunnableWithMessageHistory`。",
                    "知道 `@tool` 的 docstring 是模型选工具的唯一依据，参数要有类型注解。",
                    "知道 RAG 答非所问时先查 `retriever` 召回的片段，而不是先怀疑模型。",
                ]
            ),
            callout(
                "danger",
                "易错速记",
                "① 用旧 Memory 体系 → 改用 `RunnableWithMessageHistory`；② 工具 docstring 含糊 → 模型选错工具；"
                "③ Agent 不设 `max_iterations` → 死循环烧钱；④ RAG 不先查检索 → 在模型上白费功夫；"
                "⑤ 裸调 SDK 也行就不必上 LangChain → 别为用而用。",
            ),
        ),
    ]


# ---------- 3.3 LangGraph 系统学习引导 ----------
def build_33():
    return [
        heading(NEW_HEADING),
        kp(
            "本节学习路径：从线性链到状态图",
            para(
                "LCEL 是「有向无环、单向流动」的管道，适合一次性任务；一旦需要循环、分支、共享状态、暂停恢复，"
                "就该上 LangGraph。动手前先把下面四条走通，再看 `s3_3_*.py` 与 `langgraph_agent.py` 会更顺。"
            ),
            lst(
                ordered=True,
                items=[
                    "第 1 步 · 懂动机：清楚 LCEL 走不通的四件事（循环 / 分支 / 共享状态 / 可暂停），这是上图的理由。",
                    "第 2 步 · 懂三件套：State schema、Node（返回增量）、Edge（含条件边）的契约。",
                    "第 3 步 · 懂归约与路由：Reducer 如何合并状态、`add_conditional_edges` + 路由函数如何选路。",
                    "第 4 步 · 懂持久化与 HITL：Checkpointer + `thread_id` 实现续跑，`interrupt` 实现人工干预。",
                ],
            ),
            callout(
                "tip",
                "建议读法",
                "先读「核心概念讲解」与「原理说明」，再逐个运行 `3_3_*.py` 和 `langgraph_agent.py`。"
                "重点观察 State 如何在节点间累积、`trace` 字段如何用 reducer 拼接出完整轨迹。",
            ),
        ),
        kp(
            "核心概念讲解：状态图的三要素",
            para(
                "LangGraph 把流程建模成「有状态的图」：**Node** 是处理函数（签名 `(state)->dict`，只返回要改的字段）；"
                "**Edge** 是流转关系（无条件边 / 条件边 / 内置 START、END）；**State** 是全图共享的数据"
                "（TypedDict 声明，配合 Reducer 决定覆盖还是累加）。"
            ),
            table(
                headers=["要素", "契约", "注意点"],
                rows=[
                    ["State schema", "TypedDict 或 Pydantic 声明全局共享数据", "reducer 字段用 `Annotated[T, operator.add]` 做累加"],
                    ["Node", "`(state) -> 部分状态字典` 的普通函数或 Runnable", "只返回要改的字段，不要返回整个 state"],
                    ["Edge", "`add_edge` 无条件 / `add_conditional_edges` 条件路由", "条件边返回值必须是节点名或 END"],
                    ["Reducer", "决定多节点返回值如何合并", "覆盖（默认）vs 累加（operator.add / add_messages）"],
                ],
            ),
            callout(
                "note",
                "节点只返回「增量」是关键约定",
                "对带 reducer 的字段（如消息列表用 `add_messages`），返回整个 state 会造成「旧值+旧值」重复累加。"
                "统一用 `Annotated[list[AnyMessage], add_messages]`，节点只返回新增消息。",
            ),
        ),
        kp(
            "原理说明：图为什么比链更适合有分支/循环的 Agent",
            para(
                "ReAct 循环的本质是「根据观察决定下一步」，这天然是图——每一步按条件选下一个节点，而非直线链。"
                "LangGraph 把这种「动态路由」显式建模，所以多步、需回退/分支/人工的 Agent 用图更自然。"
                "代价是图比链复杂，简单线性任务不必上图。"
            ),
            md(
                "LangGraph 循环图：think ⇄ execute_tool",
                "flowchart TD\n  S([START]) --> T[think 节点<br/>调 LLM]\n  T --> R{should_continue?}\n  R -->|有 tool_calls| E[execute_tool 节点]\n  E -->|ToolMessage| T\n  R -->|无 tool_calls| X([END])\n  State[(\"State: messages + reducer\")] -.读写.-> T\n  State -.读写.-> E",
            ),
            callout(
                "warning",
                "循环必须有护栏",
                "图默认 `recursion_limit=25` 只是最后保险丝，业务侧要自己加终止条件"
                "（如 `MAX_TOOL_ROUNDS` 计数器）。需要更长链路时调用侧放宽 `graph.invoke(inputs, {\"recursion_limit\": 50})`。",
            ),
        ),
        kp(
            "关键知识点梳理：动手前你必须能答出",
            lst(
                items=[
                    "能说清 LCEL 走不通的四件事，以及它们为什么需要图。",
                    "能写出 StateGraph 三件套：定义 State → 注册 Node → 连 Edge → compile。",
                    "能解释 Reducer（覆盖 vs 累加），并说清为什么节点只返回增量。",
                    "能用 `add_conditional_edges` + 路由函数实现分支，且返回值类型用 `Literal` 声明。",
                    "能说清 Checkpointer + `thread_id` 如何实现断点续跑与多用户隔离。",
                    "能说出 HITL 的两种断点（interrupt_before / interrupt）及其恢复方式。",
                ]
            ),
            callout(
                "danger",
                "易错速记",
                "① 节点返回整个 state → reducer 字段重复累加；② 忘 `set_entry_point` / 条件边返回非节点名 → 运行时才报错；"
                "③ 循环无护栏 → `GraphRecursionError`；④ 忽略持久化 → 进程重启丢状态；"
                "⑤ 动态 `interrupt` 恢复时节点会从头重跑 → 副作用别写在 interrupt 之前。",
            ),
        ),
    ]


# ---------- 插入逻辑 ----------
def insert_module(chapter, sec_id, blocks):
    for sec in chapter.get("sections", []):
        if sec.get("id") != sec_id:
            continue
        content = sec.get("content", [])
        # 幂等保护：已存在则跳过
        for b in content:
            if b.get("type") == "heading" and b.get("text") == NEW_HEADING:
                print(f"[{sec_id}] 已存在「{NEW_HEADING}」，跳过（如需重做请先 git checkout assets/data/chapter-3.json）")
                return False
        # 定位目标标题下标
        idx = None
        for i, b in enumerate(content):
            if b.get("type") == "heading" and b.get("text") == TARGET_HEADING:
                idx = i
                break
        if idx is None:
            print(f"[{sec_id}] 未找到「{TARGET_HEADING}」标题，跳过")
            return False
        sec["content"] = content[:idx] + blocks + content[idx:]
        print(f"[{sec_id}] 已在「{TARGET_HEADING}」之前插入 {len(blocks)} 个块（「{NEW_HEADING}」）")
        return True
    print(f"[{sec_id}] 未找到该 section，跳过")
    return False


def main():
    with open(CHAPTER, "r", encoding="utf-8") as f:
        chapter = json.load(f)
    changed = False
    changed |= insert_module(chapter, "3.2", build_32())
    changed |= insert_module(chapter, "3.3", build_33())
    if changed:
        with open(CHAPTER, "w", encoding="utf-8") as f:
            json.dump(chapter, f, ensure_ascii=False, indent=2)
        print("已写回 chapter-3.json")
    else:
        print("无改动，未写回")


if __name__ == "__main__":
    main()
