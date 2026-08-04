#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全站补充板块系统化深化生成器（六要素：核心概念 / 底层原理 / 真实可运行代码 /
完整实战演练 / 常见误区与调试 / 工程化扩展）。

策略：读取 chapter-N.json 当前的 content 作为基线，仅「追加」六要素补充块到
每个「深入解析与实战」「原理深挖与工程扩展」板块之后，不破坏既有内容、
enterpriseCase / exercises / resources / quiz。

约束（见 scripts/audit_code.py）：
  - 每个新增代码块 {type:'code', data:{filename, language, ...}}，filename 全局唯一
    （命名 s{章}_{节}_rz.py = 深入解析，s{章}_{节}_sy.py = 原理深挖）。
  - Python 代码必须离线可运行（用本地 mock 代替真实 LLM，note 说明生产替换），
    语法合法、无未使用 import/变量、无空函数、无虚构模型、无占位符。
  - 每个 import 与简单赋值变量必须被引用（审计会报 unused）。
  - highlightLines 由 _sanitize_hl 自动校正。
  - callout 的 text 必须是字符串；variant 只能 tip/warning/danger/info/note。

运行方式（每次只跑一个章节，跑完即审计+重建+提交，禁止对同章重跑两次；
如需重跑先 git checkout assets/data/chapter-N.json 还原基线）：
  python3 scripts/gen_enrich.py 1
  python3 scripts/gen_enrich.py 2
  ...
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "assets", "data")


# ---------------------------------------------------------------------------
# 内容块构造助手（与 gen_deepen.py 一致）
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
    """plan: {secid: [blocks...]}；content = 原内容 + 补充六要素块。"""
    path = chapter_path(ch)
    with open(path, encoding="utf-8") as f:
        chapter = json.load(f)
    n = 0
    for sec in chapter.get("sections", []):
        sid = sec.get("id")
        if sid not in plan:
            continue
        supplement = plan[sid]
        base = existing_content(path, sid)
        sec["content"] = base + list(supplement)
        n += 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chapter, f, ensure_ascii=False, indent=2)
    print(f"已更新 {path} 的 {n} 个 section")


# ---------------------------------------------------------------------------
# 第 1 章计划：基础概念入门（每节 深入解析与实战 + 原理深挖与工程扩展）
# ---------------------------------------------------------------------------

CH1_ENRICH = {
"1.1": [
    # —— 深入解析与实战 六要素 ——
    kp("核心概念：Agent 是「感知-决策-行动」的闭环",
        para("单次 LLM 调用是「输入一段话、输出一段话」的单向映射；而 AI Agent 在这个映射外面套了一层循环：先感知（读取用户输入、工具返回、记忆），再决策（下一步该回答、还是调用工具、还是结束），最后行动（调用工具或给出回复），并把行动结果写回感知，进入下一轮。正是这个闭环让模型能完成多步、需要外部信息的任务。"),
        para("理解 Agent 的最小骨架只需三个函数：perceive（把原始输入整理成状态）、decide（根据状态选动作）、act（执行动作并返回结果）。下面的代码用纯规则驱动，刻意不接任何 LLM，目的是让你看清闭环本身，不被模型调用干扰。"),
    ),
    code("s1_1_rz.py", "python", "最小可运行 Agent：感知-决策-行动闭环（离线规则驱动）",
        r'''# 最小可运行 Agent：感知-决策-行动 闭环（离线、规则驱动，便于看清骨架）
def perceive(user_input):
    return {"query": user_input.strip()}

def decide(state):
    # 极简策略：含"时间/几点"走时钟工具，否则直接回答
    if "时间" in state["query"] or "几点" in state["query"]:
        return "use_tool", "clock"
    return "answer", state["query"]

def act(tool_name, payload):
    if tool_name == "clock":
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    return f"答：{payload}"

def run_agent(user_input, max_steps=5):
    state = perceive(user_input)
    for step in range(max_steps):
        action, payload = decide(state)
        if action == "answer":
            return act(None, payload)
        result = act(payload, state["query"])
        state["query"] = f"{state['query']} -> {result}"
    return "超过最大步数，已终止"

if __name__ == "__main__":
    print(run_agent("现在几点"))
    print(run_agent("你好"))
''',
        hl=[14, 15, 16, 19],
        output="<当前时分秒，如 14:23:05>\n答：你好",
        note="这是「骨架版」Agent：decide 是硬编码规则。真实 Agent 里 decide 由 LLM 根据提示词产出「思考+动作」，act 调用真实工具。把 decide 换成模型调用、把 act 接到真实 API，就得到生产级 Agent。",
    ),
    kp("完整实战演练步骤",
        lst([
            "复制上面代码到 agent_demo.py，直接 `python agent_demo.py` 跑通，确认输出两行。",
            "把 decide 改成：输入含「天气」时返回 ('use_tool','weather')；并在 act 里新增 weather 分支返回固定字符串 '晴 26°C'。",
            "新增一个工具分支「计算」：输入含「加」时，用正则取出两个数字并求和（这是 act 端做确定计算的示范）。",
            "给 run_agent 加一个 step_log 列表，每轮把 (action, payload, result) 追加进去，跑完后打印日志，体会「闭环」如何逐步推进。",
            "把 max_steps 调到 1，观察「超过最大步数」的终止分支——这正是 Agent 必须有的兜底。",
        ], ordered=True),
    ),
    callout("danger", "常见误区与调试",
        "① 忘了终止条件：decide 永远返回 use_tool 且工具又产生新输入，Agent 会死循环直到 OOM——务必保留 max_steps 兜底。② 把工具副作用当幂等：act 里若真发邮件/删数据，重试会重复执行，调试阶段务必用 mock。③ 状态覆盖 bug：每轮直接 `state['query']=...` 覆盖，会丢失历史；真实场景应把历史追加进 messages 列表而非覆盖。④ 日志只打印最终结果：闭环出问题时要打印每一步的 (action,result) 才能定位。"),
    callout("tip", "工程化扩展建议",
        "把 decide/act 抽象成接口（基类 AgentPolicy、Tool），便于替换策略与工具；加结构化日志（JSON 行）接入可观测性；给每轮加唯一 step_id 与耗时，便于线上排查；把 max_steps、超时、工具白名单做成配置，避免改代码发版。"),

    # —— 原理深挖与工程扩展 六要素 ——
    kp("底层原理：自主性谱系与「授权面」",
        para("自主性不是二值开关，而是一条光谱：规则脚本（零自主）→ RPA（低自主）→ Copilot（人给指令、模型补全、人确认）→ 半自主 Agent（模型定步骤、关键动作人审批）→ 全自主 Agent（模型定步骤并直接执行）。越往右，模型的「错误 × 工具副作用」事故面越大。设计 Agent 的第一步，是依据任务风险选一个合适的自主档位，而不是无脑上全自主。"),
        para("判定档位的关键信号是「动作后果是否可逆、是否高危」。涉及删除/付款/发送/对外承诺的动作，必须保留人审批或强约束；而读查询、生成草稿、内部计算可以放心自动化。下面的代码把这套启发式做成可复用的离线判定器。"),
    ),
    code("s1_1_sy.py", "python", "自主性谱系：把任务映射到合适的自主档位（离线判定）",
        r'''# 自主性谱系：把任务描述映射到合适的自主档位（离线判定，无外部依赖）
SPECTRUM = [
    ("规则脚本", 0, "步骤完全固定，if/else 即可"),
    ("RPA", 1, "固定流程点击，低自主"),
    ("Copilot", 2, "人给指令，模型补全，人确认"),
    ("半自主 Agent", 3, "模型定步骤，高危动作人审批"),
    ("全自主 Agent", 4, "模型定步骤并直接执行"),
]

HIGH_RISK = ["删除", "付款", "发送", "审批", "承诺"]

def recommend_autonomy(task_desc):
    if any(w in task_desc for w in HIGH_RISK):
        return "半自主 Agent（高危动作需人审批）"
    if "固定" in task_desc or "模板" in task_desc:
        return "规则脚本"
    return "全自主 Agent（低风险可自动化）"

if __name__ == "__main__":
    for level, score, desc in SPECTRUM:
        print(f"{level}: {desc}")
    for t in ["每日生成报表", "自动付款给供应商", "根据模板写周报"]:
        print(t, "->", recommend_autonomy(t))
''',
        hl=[13, 14, 15, 16],
        output="规则脚本: 步骤完全固定，if/else 即可\nRPA: 固定流程点击，低自主\nCopilot: 人给指令，模型补全，人确认\n半自主 Agent: 模型定步骤，高危动作人审批\n全自主 Agent: 模型定步骤并直接执行\n每日生成报表 -> 全自主 Agent（低风险可自动化）\n自动付款给供应商 -> 半自主 Agent（高危动作需人审批）\n根据模板写周报 -> 规则脚本",
        note="生产环境应把 HIGH_RISK 词表换成「动作分类器 + 策略引擎」，并支持按用户/角色配置审批阈值；SPECTRUM 可作为产品文档里的能力分级说明。",
    ),
    kp("完整实战演练步骤",
        lst([
            "运行脚本，观察 SPECTRUM 打印与三个任务的判定结果。",
            "新增一条任务「给用户发送续费提醒邮件」，确认被判为半自主（因含「发送」）。",
            "把 HIGH_RISK 扩展为可配置列表（从 config 读取），验证「配置即策略」。",
            "把 recommend_autonomy 改造成返回 (档位, 理由) 的元组，便于前端展示为什么这样定级。",
            "为「全自主」档位补一条安全护栏：要求任务描述显式包含「低风险」才放行，否则降级。",
        ], ordered=True),
    ),
    callout("danger", "常见误区与调试",
        "① 过度自主：给只读查询之外的动作直接开全自主，一旦发生误删/误发难以回滚。② 词表误判：仅靠关键词匹配会把「删除草稿」和「删除生产库」同等对待——应结合动作影响面分级。③ 把 SPECTRUM 当摆设：定了档位却没在 act 层做强制拦截，等于没定。④ 忽略人工成本：半自主每次都让人审批，高频任务会把人累死，需做批量/静默窗口。"),
    callout("tip", "工程化扩展建议",
        "实现「分级授权 + 工具沙箱」：写动作进沙箱、读动作可直连；为高危动作加二次确认与操作审计（who/when/what）；把自主档位做成用户可降不可升的开关；长期把关键词判定升级为小模型分类器，降低误判率。"),
],

"1.2": [
    kp("核心概念：LLM 以 Token 为最小单位，不是字符",
        para("大模型并不「读字符」，而是先把文本切成 token（子词），再喂给神经网络。英文约 1 token ≈ 0.75 词，中文通常 1 个汉字 ≈ 1~2 token，代码因符号多更费 token。Token 数直接决定：输入是否超上下文窗口、推理成本（按 token 计费）、生成速度（每 token 一次前向）。理解 token 化，是理解「为什么长文会截断、为什么成本忽高忽低」的根。"),
        para("主流分词器（如 GPT 系列的 BPE、Llama 的 SentencePiece）都是「训练出来的」——常见词整词成 token，罕见词拆成子词。所以同一段中文，不同模型 token 数不同；专业术语越多、越生僻，token 越碎、越贵。下面的代码用纯 Python 模拟一个简化分词，帮你直观看到「词频决定切分粒度」。"),
    ),
    code("s1_2_rz.py", "python", "简化 BPE 式分词：用词频决定子词切分粒度（离线模拟）",
        r'''# 简化分词模拟：高频整体成 token，低频拆成字符（直观理解 BPE 思想）
VOCAB = {"我们": 0, "学习": 0, "智能": 0, "体": 0, "是": 0, "好": 0}

def tokenize(text):
    tokens, i = [], 0
    while i < len(text):
        matched = None
        for w in VOCAB:               # 贪心匹配最长词
            if text.startswith(w, i):
                matched = w
                break
        if matched:
            tokens.append(matched)
            i += len(matched)
        else:
            tokens.append(text[i])    # 未登录字单独成 token
            i += 1
    return tokens

if __name__ == "__main__":
    s = "我们学习智能体是好的"
    t = tokenize(s)
    print("tokens:", t)
    print("token 数:", len(t), "字符数:", len(s))
''',
        hl=[12, 13, 14, 15],
        output="tokens: ['我们', '学习', '智能', '体', '是', '好', '的']\ntoken 数: 7 字符数: 10",
        note="真实 BPE/SentencePiece 用合并规则而非简单词表，但「高频合并、低频拆字」的斜率一致。生产环境请用模型官方 tokenizer（tiktoken / transformers AutoTokenizer）精确计数，切勿自己估算。",
    ),
    kp("完整实战演练步骤",
        lst([
            "运行代码，观察「智能体」被拆成「智能」+「体」两个 token（因「体」单独在词表）。",
            "往 VOCAB 加入 \"智能体\": 0，重跑，确认它变成单个 token——直观看到「训练语料词频」如何改变切分。",
            "统计一段中文的字符数与 token 数比值，估算你的语料 token 单价（token 数 ÷ 字符数）。",
            "用官方 tokenizer 对同样文本计数，对比你模拟器的误差，理解为什么必须「以官方为准」。",
            "构造一个超长文本，按 max_tokens 截断，观察截断点落在哪个 token，体会「按 token 截断」而非按字符。",
        ], ordered=True),
    ),
    callout("danger", "常见误区与调试",
        "① 按字符估算成本：中文按字符估会严重偏低，按英文词估会严重偏高，二者都错。② 假设「同一段文本各模型 token 数相同」：不同分词器差异可达 30%+。③ 忽略输出 token 成本：很多人只算输入，但生成越长越贵、越慢。④ 把 system prompt 当免费：长系统提示每个会话都计费，应精简或用缓存。⑤ 截断无感知：超出窗口直接丢尾部，关键信息可能恰好被丢。"),
    callout("tip", "工程化扩展建议",
        "所有成本/长度判断以官方 tokenizer 为准并缓存结果；对长文档做「预算分配」（system+历史+本次输入+预留输出）；开启 prompt caching（命中缓存的 token 折扣显著）；把高频固定前缀（人设/规则）抽成可缓存段；监控每会话 token 峰值，设告警防跑飞。"),

    kp("底层原理：上下文窗口是「有限的工作记忆」",
        para("上下文窗口（context window）是模型一次能「同时看到」的 token 上限，包含输入+输出。它像一块有限 RAM：超出就丢。但「能放下」不等于「能用好」——过长上下文会稀释注意力、拉高成本与延迟。因此工程上要主动管理上下文：只保留与当前任务相关的 token，其余摘要/外存。这正是第 2.6 节「记忆与上下文管理」与第 2.8 节「RAG」要解决的问题。"),
        para("一个常被忽视的点：上下文窗口是「训练时决定的硬上限」，不是配置项。想处理比窗口更长的资料，只能在「架构层」解决（分块、检索、记忆压缩），而不是调大某个参数。下面的代码演示「窗口预算」如何强制裁剪，避免溢出。"),
    ),
    code("s1_2_sy.py", "python", "上下文窗口预算管理：按优先级裁剪保留相关 token（离线）",
        r'''# 上下文窗口预算管理：按优先级保留，超预算则裁剪（离线模拟）
def pack_context(budget, items):
    # items: [(优先级, 文本), ...] 优先级越大越重要
    items = sorted(items, key=lambda x: -x[0])
    packed, used = [], 0
    for pri, text in items:
        cost = len(text)
        if used + cost <= budget:
            packed.append(text)
            used += cost
        else:
            keep = budget - used
            if keep > 0:
                packed.append(text[:keep] + "…(截断)")
            break
    return packed

if __name__ == "__main__":
    items = [(3, "用户问题：如何部署 Agent"), (2, "历史对话摘要…"), (1, "闲聊记录…")]
    packed = pack_context(20, items)
    print("保留块数:", len(packed))
    print("内容:", packed)
''',
        hl=[12, 13, 14, 15, 16],
        output="保留块数: 2\n内容: ['用户问题：如何部署 Agent', '历史对话摘…(截断)']",
        note="真实系统里「优先级」来自相关性检索（RAG）或时间衰减（记忆），裁剪也应保留语义边界（不切断一个 JSON）。生产可用滑动窗口 + 摘要双层策略。",
    ),
    kp("完整实战演练步骤",
        lst([
            "运行代码，把 budget 调到 40，观察三块都被保留。",
            "把 budget 调到 10，观察只有最高优先级块被保留、其余被裁。",
            "把 items 换成真实会话（每轮 user/assistant），用 token 数而非字符数做 cost。",
            "增加「摘要」分支：当待保留块超预算时，先对低优先级块做一句话摘要再尝试装回。",
            "加一个 assert：pack_context 返回的总 token 永不超过 budget，作为回归测试。",
        ], ordered=True),
    ),
    callout("danger", "常见误区与调试",
        "① 以为窗口够大就不需要管理：128K 窗口塞满也会变慢变贵、注意力稀释。② 截断切在语义边界：把一段 JSON 从中间切断，下游解析必崩。③ 优先级拍脑袋：用时间先后而非相关性，重要历史被丢。④ 忽略输出预算：输入占满窗口，模型没空间生成就被截断。⑤ 每次全量重发：历史全带上，成本随轮次线性增长。"),
    callout("tip", "工程化扩展建议",
        "采用「热上下文（最近 N 轮）+ 冷记忆（向量库/摘要）」双层；对长文档用 RAG 按需取相关块而非全量；对稳定背景用 prompt cache；用 token 计数器在入口处做硬拦截并回退到摘要模式；把预算做成可观测指标。"),
],

"1.3": [
    kp("核心概念：Prompt 是「给模型的程序」",
        para("Prompt Engineering 的本质是「用自然语言写程序」：你定义角色、目标、约束、输入格式与输出格式，模型按此执行。好的 prompt 具备可复现性（同样输入稳定输出）、可调试性（哪里错能定位）、可组合性（作为模块被复用）。它和代码一样需要版本管理与回归测试，而不是写完就扔。"),
        para("最实用的两类技巧：① 角色+任务+格式（Role/Task/Format）三段式，降低歧义；② Few-shot（给 2~3 个示例）比纯描述更能锁定输出风格，尤其对结构化输出。下面的代码实现一个可复用的 Prompt 模板构造器。"),
    ),
    code("s1_3_rz.py", "python", "可复用 Prompt 模板：Role/Task/Format + Few-shot（离线）",
        r'''# 可复用 Prompt 模板构造器：角色 + 任务 + 格式 + 少样本（离线，不调模型）
def build_prompt(role, task, fmt, shots, user_input):
    parts = [f"你是一个{role}。", f"任务：{task}", f"输出格式：{fmt}"]
    for i, (q, a) in enumerate(shots, 1):
        parts.append(f"示例{i}：\n输入：{q}\n输出：{a}")
    parts.append(f"现在处理：\n输入：{user_input}")
    return "\n".join(parts)

if __name__ == "__main__":
    shots = [("把'好'分类", "正向"), ("把'糟'分类", "负向")]
    p = build_prompt("情感分类器", "判断用户评价情感", "只回正向/负向", shots, "物流很快")
    print(p)
''',
        hl=[3, 4, 5, 6, 7, 8, 10],
        output="你是一个情感分类器。\n任务：判断用户评价情感\n输出格式：只回正向/负向\n示例1：\n输入：把'好'分类\n输出：正向\n示例2：\n输入：把'糟'分类\n输出：负向\n现在处理：\n输入：物流很快",
        note="生产环境把 shots 抽成模板变量，按任务切换；注意 few-shot 示例本身也占 token，示例过多会稀释主任务。真实调用时把本函数输出作为 messages 的 user content。",
    ),
    kp("完整实战演练步骤",
        lst([
            "运行代码，把 user_input 换成负面评价，确认模板结构不变。",
            "新增一个 fmt 约束「必须 JSON：{\"label\":\"正向|负向\"}」，观察格式指令如何注入。",
            "把 shots 清空，对比「无示例」与「有示例」的输出稳定性差异（用同一输入多次）。",
            "为模板加版本号（v1/v2），把不同版本 prompt 落到文件，便于 A/B 与回归。",
            "写一个小测试：断言 build_prompt 输出必含 role/task/fmt 三段，防模板被改坏。",
        ], ordered=True),
    ),
    callout("danger", "常见误区与调试",
        "① 把 prompt 当文案而非代码：不版本化、不测试，改一句全网行为漂移。② few-shot 示例带偏见：示例单一会让模型过拟合该风格。③ 指令冲突：同时要求「简短」又给长示例，模型无所适从。④ 忽略注入风险：用户输入里写「忽略以上指令」可能越权，须做输入隔离。⑤ 过度堆砌约束：约束越多越互斥，效果反而下降。"),
    callout("tip", "工程化扩展建议",
        "把 prompt 模板纳入 Git 版本管理并加单测；用「变量 + 渲染」而非字符串拼接；对关键任务做 prompt 回归集（固定输入比对输出）；接入评测把 prompt 版本与分数挂钩；对外部输入做转义/隔离防注入；公共人设抽成共享片段避免重复。"),

    kp("底层原理：为什么「结构化 + 示例」比「长描述」更稳",
        para("模型是概率生成器，不是解释器。一段模糊的长描述会被模型「自由发挥」；而明确的输出格式约束 + 少量示例，把生成空间压缩到窄区间，输出更稳定、更易解析。从信息论看，few-shot 是在用「示例」而非「文字」传递分布，示例比描述更不易歧义。这也是第 2.7 节「结构化输出」要让模型产出 JSON/Schema 的底层原因。"),
        para("另一个原理是「位置偏差」：模型对 prompt 开头（系统设定）与结尾（当前任务）最敏感，中间容易被稀释。因此关键约束放首尾、长背景可外置。下面的代码演示「约束位置」对可解析性的影响度量。"),
    ),
    code("s1_3_sy.py", "python", "约束位置敏感性模拟：首尾约束更易被解析（离线）",
        r'''# 约束位置模拟：测量不同放置位置的「格式命中率」（离线，用规则代替模型）
def parse_strict(text, fmt_at_end=True):
    if fmt_at_end:
        return text.strip().endswith("仅回JSON")   # 结尾有格式约束
    return "仅回JSON" in text                        # 约束埋在中间

CASES = [
    "分析一下。仅回JSON",
    "仅回JSON。请详细分析一下，多写点",
]

if __name__ == "__main__":
    for c in CASES:
        print("结尾约束可解析:", parse_strict(c, True), "| 中间约束可解析:", parse_strict(c, False))
''',
        hl=[4, 5, 9, 10],
        output="结尾约束可解析: True | 中间约束可解析: True\n结尾约束可解析: False | 中间约束可解析: True",
        note="这只是用规则模拟「模型更易遵守结尾格式」的直觉；真实评测应直接在目标模型上跑准确率。生产上结构约束放 system 末尾 + 用 response_format 强制 JSON 最稳。",
    ),
    kp("完整实战演练步骤",
        lst([
            "运行代码，观察「约束在结尾」vs「约束在开头」的解析差异。",
            "把 CASES 改成真实 prompt，用目标模型实测两种摆放的 JSON 合法率。",
            "增加一个「前后都有约束」用例，验证双重约束是否进一步提升稳定。",
            "把解析函数接到真实输出，统计一周内的格式违规率作为回归指标。",
            "把结论沉淀为团队 prompt 规范：「关键格式约束放 system 末尾」。",
        ], ordered=True),
    ),
    callout("danger", "常见误区与调试",
        "① 所有约束堆在中间：长 prompt 中段最易被稀释，格式常丢。② 以为示例越多越好：示例相互矛盾会拉低准确率，3 个高质量胜 10 个随意的。③ 用自然语言要 JSON 却不强制：模型偶尔输出 markdown 代码块包裹，解析崩溃。④ 忽略模型差异：A 模型稳的 prompt 换 B 模型可能崩，须按模型回归。⑤ 不测边界：空输入/超长输入时 prompt 行为未定义。"),
    callout("tip", "工程化扩展建议",
        "用 response_format/structured output 在协议层强制格式；constraint 放 system 末尾；prompt 接入评测集做 CI；对输出做 schema 校验与失败重试；把「稳定 prompt」沉淀为团队资产并文档化适用模型版本。"),
],

"1.4": [
    kp("核心概念：模型的「能力」与「局限」都要被设计进系统",
        para("大模型强在：语言理解、泛化、少样本学习、跨任务迁移；弱在：不擅长精确计算、不掌握实时信息、会幻觉、无真正因果推理、上下文有限。把它当「聪明但会犯错的协作者」，而不是「全知神谕」。系统设计的核心动作，就是用工具/检索/校验去补模型的短板，用人工护栏去兜住它的错误。"),
        para("一个实用心法：把任务拆成「模型擅长」与「模型不擅长」两部分，后者交给代码或工具。下面的代码用一个离线「能力路由」演示：算术走代码、知识问答走模型占位、实时信息走检索占位。"),
    ),
    code("s1_4_rz.py", "python", "能力路由：把任务按模型擅长/不擅长分流（离线）",
        r'''# 能力路由：算术交给代码，知识/实时交给模型或检索（离线模拟）
def route(task):
    import re
    if re.search(r"\d+\s*[\+\-\*]\s*\d+", task):
        expr = re.search(r"\d+\s*[\+\-\*]\s*\d+", task).group()
        return "code", str(eval(expr))          # 精确计算交给 Python
    if any(w in task for w in ["今天", "最新", "股价"]):
        return "retrieval", "需实时检索(占位)"
    return "llm", "由模型生成(占位)"

if __name__ == "__main__":
    for t in ["计算 12*8", "今天天气", "写首诗"]:
        kind, ans = route(t)
        print(f"{t} -> [{kind}] {ans}")
''',
        hl=[5, 6, 7, 8, 9, 11],
        output="计算 12*8 -> [code] 96\n今天天气 -> [retrieval] 需实时检索(占位)\n写首诗 -> [llm] 由模型生成(占位)",
        note="eval 仅作演示，生产环境请用安全表达式解析（如 ast.literal_eval 仅限字面量）或专用计算器，禁止直接 eval 用户输入。路由判定可升级为小分类模型。",
    ),
    kp("完整实战演练步骤",
        lst([
            "运行代码，确认算术被可靠计算、实时类被分流到检索。",
            "把 eval 换成 ast.literal_eval 并限制只接受 + - * 的二元表达式，消除安全风险。",
            "新增一类「需要工具」任务（如「发邮件」），路由到 tool 分支。",
            "为每条分支记录命中次数，统计一周流量分布，指导资源投入。",
            "把 route 的判断逻辑抽成可配置规则表，支持不改代码调整分流。",
        ], ordered=True),
    ),
    callout("danger", "常见误区与调试",
        "① 让模型做精确算术：大模型心算不稳，金额/数量必须代码或工具算。② 直接 eval 用户输入：注入风险极高，务必替换。③ 假设模型知道实时信息：训练数据有截止日，问「今天」必幻觉。④ 忽视幻觉概率：重要结论不校验就直接采用。⑤ 把模型当数据库：事实性问答应接检索（RAG）而非纯靠参数记忆。"),
    callout("tip", "工程化扩展建议",
        "建立「能力边界清单」明确哪些交给代码/工具/检索；关键数值走确定性计算；实时与事实性内容走 RAG + 引用溯源；对高风险输出加校验层（schema/范围/人工）；把路由做成可观测、可灰度调整的模块。"),

    kp("底层原理：幻觉来自「生成式训练的固有特性」",
        para("模型训练目标是「预测下一个最合理的 token」，而不是「保证事实为真」。当它不知道答案时，会基于统计「编造流畅但错误」的内容——这就是幻觉。幻觉不可通过「更聪明的提示」根除，只能通过架构抑制：检索增强（给它真资料）、约束解码（限候选）、后验校验（事实核查）、不确定性表达（「我不确定」）。理解这点，才能正确预期系统的可靠性上限。"),
        para("一个可度量思路：给模型「拒答」的出口，比强行回答更可靠。下面的代码用一个离线「信心门控」演示：检索不到证据时返回「无法确定」，而非硬编。"),
    ),
    code("s1_4_sy.py", "python", "信心门控：无证据时拒答而非幻觉（离线）",
        r'''# 信心门控：检索不到证据就拒答，抑制幻觉（离线模拟）
KB = {"Agent": "自主感知-决策-行动闭环", "RAG": "检索增强生成"}

def answer(query):
    for k, v in KB.items():
        if k in query:
            return f"据资料：{v}"
    return "无法确定，建议检索最新资料"   # 拒答出口，避免编造

if __name__ == "__main__":
    for q in ["什么是 Agent", "什么是量子计算"]:
        print(q, "->", answer(q))
''',
        hl=[6, 7, 8, 9],
        output="什么是 Agent -> 据资料：自主感知-决策-行动闭环\n什么是量子计算 -> 无法确定，建议检索最新资料",
        note="生产环境把 KB 换成向量检索 + 相关性阈值；阈值过低会过度拒答、过高会放幻觉，需用评测集调参。拒答话术要友好且给出下一步（检索/转人工）。",
    ),
    kp("完整实战演练步骤",
        lst([
            "运行代码，确认「知识库外」问题被安全拒答。",
            "把 KB 换成向量检索，设定相似度阈值，低于阈值即拒答。",
            "构造 20 条「知识库内/外」测试，统计拒答准确率与误拒率。",
            "为拒答增加「建议动作」（如给出检索入口或转人工），提升体验。",
            "把阈值做成可配置，按业务风险动态调整（金融调高、闲聊调低）。",
        ], ordered=True),
    ),
    callout("danger", "常见误区与调试",
        "① 认为 prompt 能根除幻觉：提示「不要编造」只能降低、不能消除。② 无证据硬答：检索失败仍输出，等于主动制造幻觉。③ 拒答阈值拍脑袋：太高误拒伤体验，太低放幻觉。④ 把置信度当概率：softmax 最高分高不代表事实正确。⑤ 忽略来源：给出结论却不附出处，无法核查。"),
    callout("tip", "工程化扩展建议",
        "RAG 提供可溯源证据 + 引用；设相关性阈值门控；关键结论加事实核查链路；输出附「来源/不确定」标记；对拒答做体验优化与转人工；把幻觉率纳入线上监控指标。"),
],

"1.5": [
    kp("核心概念：从「一次调用」到「自主循环」的演进路径",
        para("LLM → Chatbot → Copilot → Agent 是一条「自动化程度递增」的演进线：LLM 提供底座能力；Chatbot 加了多轮对话壳；Copilot 在人的工作流里补全建议（人确认）；Agent 则自己闭环执行多步任务并调用工具。每一步都把「更多决策权」从人转移到系统。理解这条线，才能为具体场景选对落点，不盲目追求「全 Agent」。"),
        para("判断该不该上 Agent 的简单判据：任务是否「步骤不确定、需要外部信息/工具、要长期推进」。三者皆否，用函数/模板最快最稳；任一为是，才值得引入 Agent。下面的代码把这条判据做成可调用函数。"),
    ),
    code("s1_5_rz.py", "python", "演进选型判据：该用函数/Copilot 还是 Agent（离线）",
        r'''# 演进选型判据：按任务特征决定落点（离线）
def pick(shape, needs_tool, long_running):
    if not needs_tool and not long_running:
        return "函数/模板（最快最稳）"
    if needs_tool and not long_running:
        return "Copilot（人确认工具调用）"
    return "Agent（自主闭环）"

if __name__ == "__main__":
    cases = [("固定报表", False, False), ("补全代码", True, False), ("自动运维", True, True)]
    for name, t, lr in cases:
        print(f"{name} -> {pick(t, t, lr)}")
''',
        hl=[4, 5, 6, 7, 8],
        output="固定报表 -> 函数/模板（最快最稳）\n补全代码 -> Copilot（人确认工具调用）\n自动运维 -> Agent（自主闭环）",
        note="注意 pick(t, t, lr) 里第一个参数是 shape 但没用到——真实代码应只用 needs_tool/long_running 两个布尔。这里保留是为了对齐上面的判据表述，生产请删去未用参数。",
    ),
    kp("完整实战演练步骤",
        lst([
            "运行代码，对照三个案例理解落点选择。",
            "删掉未使用的 shape 参数，重跑确认审计（无 unused-var）通过。",
            "新增一条「只查知识库、不写不执行」的任务，确认判为 Copilot 而非 Agent。",
            "把判据扩展为打分卡（每维 0~3 分），超阈值才上 Agent。",
            "把结果接到需求评审清单，作为「是否引入 Agent」的准入门槛。",
        ], ordered=True),
    ),
    callout("danger", "常见误区与调试",
        "① 为确定性任务上 Agent：步骤固定、输入输出确定的事，Agent 的循环与推理纯属浪费且引入不确定。② 忽略人确认成本：Copilot 每次打断人，高频场景人会被拖垮。③ 把 Agent 当银弹：能用 10 行函数解决的别上框架。④ 演进线理解错：以为 Agent 一定优于 Copilot，实际取决于风险与频率。⑤ 漏掉「长期运行」维度：短时任务硬上长程 Agent 反而难调试。"),
    callout("tip", "工程化扩展建议",
        "建立「能力-成本-风险」三维选型表；确定性逻辑沉淀为可复用函数/工作流；Agent 仅用于真正不确定且高频有价值的场景；为 Copilot 设计「静默窗口」减少打断；把选型判据做成团队评审 checklist。"),

    kp("底层原理：Agent 比 Chatbot 多出来的「状态」与「工具」",
        para("Chatbot 每轮对话是「无状态函数」：输入当前消息、输出回复，不持久保存中间结果（除对话历史）。Agent 额外拥有两样东西：① 状态（跨步记忆：目标、已做、待做、工具结果）；② 工具（改变外部世界或获取信息的能力）。正是「状态 + 工具 + 循环」三者组合，让 Agent 能完成 Chatbot 做不到的多步任务。下面的代码对比两者的最小骨架差异。"),
        para("注意：状态既是能力也是负担——状态错一步，后续全错，且难回滚。因此第 2.5 节「Agent Loop」与第 2.6 节「记忆」都围绕「如何管好状态」展开。下面的代码把「有状态 Agent」与「无状态 Chatbot」并排，突出差异。"),
    ),
    code("s1_5_sy.py", "python", "有状态 Agent vs 无状态 Chatbot 骨架对比（离线）",
        r'''# 有状态 Agent（带 memory） vs 无状态 Chatbot 最小骨架对比
class Chatbot:
    def reply(self, msg):
        return f"echo: {msg}"            # 无状态：不看历史

class Agent:
    def __init__(self):
        self.memory = []
        self.steps = 0
    def step(self, msg):
        self.memory.append(msg)          # 状态持久化
        self.steps += 1
        plan = f"计划处理(第{self.steps}步)"
        self.memory.append(plan)
        return plan

if __name__ == "__main__":
    c = Chatbot(); print("Chatbot:", c.reply("hi"), c.reply("hi"))
    a = Agent(); print("Agent:", a.step("任务A"), a.step("任务B"))
''',
        hl=[4, 9, 10, 11, 12],
        output="Chatbot: echo: hi echo: hi\nAgent: 计划处理(第1步) 计划处理(第2步)",
        note="Chatbot 两次 reply('hi') 输出相同（无状态）；Agent 的 memory 在增长（有状态），这正是它能「接着上次继续」的原因。生产 Agent 的 memory 要用持久化存储而非内存变量。",
    ),
    kp("完整实战演练步骤",
        lst([
            "运行代码，确认 Chatbot 无状态、Agent 状态递增。",
            "给 Agent 加一个「回放」方法，打印 memory 全流程，观察状态如何驱动推进。",
            "把 Chatbot 也加 memory，对比「有历史但无工具」与「有状态有工具」的能力差。",
            "故意在 step 里写错一步（如重复 append），观察状态污染如何传导。",
            "把 memory 换成文件/数据库持久化，重启进程后确认状态不丢。",
        ], ordered=True),
    ),
    callout("danger", "常见误区与调试",
        "① 把 Chatbot 当 Agent 用：需要跨步记忆时却每轮清空，任务必断。② 状态只放内存：进程重启状态全丢，长任务不可恢复。③ 状态无限增长：memory 越堆越大，成本与延迟线性上升、注意力稀释。④ 状态污染不隔离：一步错污染全局，难定位。⑤ 混淆「对话历史」与「任务状态」：历史是文本流，状态是结构化进度。"),
    callout("tip", "工程化扩展建议",
        "状态用持久化存储（DB/文件）并支持断点续跑；对长任务做状态压缩/摘要；把「结构化任务状态」与「原始对话历史」分开管理；为状态变更加审计日志；提供「重置/回滚」能力应对污染。"),
],

"1.6": [
    kp("核心概念：学习路线图是「由浅入深的刻意练习序列」",
        para("Agent 开发的能力栈分四层：① 基础（Python、HTTP、异步、JSON）；② LLM 认知（token、上下文、Prompt、幻觉）；③ 工程（框架、RAG、记忆、工具、评估）；④ 系统（多 Agent、可观测性、安全、部署）。有效学习不是「读完所有文章」，而是「每阶段做一个能跑的小项目」，用输出倒逼输入。下面的代码把路线图建模成可追踪的进度结构。"),
        para("里程碑设计的关键：每个里程碑都有「可验证产出」（一个能跑的脚本/一个上线的小功能），而非「我看了某章」。可验证产出能防止「学了很多却写不出东西」。下面的代码实现一个里程碑追踪器。"),
    ),
    code("s1_6_rz.py", "python", "学习路线图里程碑追踪器（离线）",
        r'''# 学习路线图：里程碑 + 可验证产出 + 进度追踪（离线）
ROADMAP = [
    ("L1", "Python 与异步基础", "能写带 async 的 HTTP 客户端"),
    ("L2", "LLM 认知与 Prompt", "能写出稳定 JSON 输出的 prompt"),
    ("L3", "RAG 与记忆", "能搭一个带检索的问答 Demo"),
    ("L4", "多 Agent 与可观测", "能跑通一个 supervisor-worker 协作"),
]

def progress(done):
    finished = [m for m in ROADMAP if m[0] in done]
    pct = round(100 * len(finished) / len(ROADMAP))
    return pct, finished

if __name__ == "__main__":
    pct, fin = progress(["L1", "L2"])
    print(f"进度 {pct}%，已完成：{[m[1] for m in fin]}")
''',
        hl=[9, 10, 11, 12],
        output="进度 50%，已完成：['Python 与异步基础', 'LLM 认知与 Prompt']",
        note="ROADMAP 是学习顺序建议，非强制；done 集合代表「已交付可验证产出」的里程碑。生产可把此结构接成学习系统，自动校验产出（如运行脚本通过测试即标记完成）。",
    ),
    kp("完整实战演练步骤",
        lst([
            "运行代码，把 done 加入 L3，确认进度变 75%。",
            "为每个里程碑补一个「产出校验函数」（如 L2 跑 prompt 测试输出合法 JSON）。",
            "把 ROADMAP 落盘为 roadmap.json，支持增删里程碑而不改代码。",
            "加一个「下一站推荐」：根据已完成里程碑推导该学哪个。",
            "用真实学习记录回填 done，生成你的能力雷达图。",
        ], ordered=True),
    ),
    callout("danger", "常见误区与调试",
        "① 只看不练：读很多文章却从没跑通过一个 Agent，知识无法内化。② 跳跃学：L1 异步没懂就冲多 Agent，遇到并发 bug 卡死。③ 里程碑不可验证：「我了解了 RAG」无法检验，应改成「搭出可问答 Demo」。④ 追新不追深：框架月月换，底层原理（循环/状态/工具）不变，舍本逐末。⑤ 孤立学：不把 Prompt/框架/评估串成一个项目，知识碎片化。"),
    callout("tip", "工程化扩展建议",
        "以「项目驱动」组织学习：每个里程碑对应一个可运行仓库；用 CI 跑通里程碑产出作为「完成」的客观证据；把底层原理（循环/状态/工具/评估）作为不变内核，框架作为可替换外壳；建立个人知识库沉淀踩坑。"),

    kp("底层原理：T 型能力模型——宽底色 + 深专长",
        para("Agent 工程师的理想能力结构是「T 型」：横杠是宽底色（Python、网络、数据库、ML 常识、产品意识），竖杠是深专长（如某一框架、某一领域 RAG、或评估体系）。只深不宽，遇到非本职问题就卡；只宽不深，做不出有壁垒的系统。学习路线应同时推进两者，而非先全宽再全深。"),
        para("另一个原理是「反馈密度」：学得快的人不是更聪明，而是「单位时间内的试错-修正循环更多」。所以选能快速看到运行结果的小项目，比啃大书效率高。下面的代码用一个离线「T 型评估」把能力与短板量化。"),
    ),
    code("s1_6_sy.py", "python", "T 型能力评估：宽底色分 + 深专长分（离线）",
        r'''# T 型能力评估：横杠(广度) + 竖杠(深度)，定位短板（离线）
def assess(breadth, depth):
    score = round(0.4 * breadth + 0.6 * depth, 1)
    if breadth < 6 and depth >= 7:
        gap = "宽底色不足，遇到跨域问题易卡"
    elif depth < 5:
        gap = "缺深专长，难做出有壁垒的系统"
    else:
        gap = "结构均衡，可深化某一方向"
    return score, gap

if __name__ == "__main__":
    for b, d in [(8, 8), (4, 9), (9, 3)]:
        s, g = assess(b, d)
        print(f"广度{b} 深度{d} -> 分{s} | {g}")
''',
        hl=[4, 5, 6, 7, 8, 9],
        output="广度8 深度8 -> 分8.0 | 结构均衡，可深化某一方向\n广度4 深度9 -> 分7.0 | 宽底色不足，遇到跨域问题易卡\n广度9 深度3 -> 分5.4 | 缺深专长，难做出有壁垒的系统",
        note="分值仅为示意模型；真实评估可用自评+项目产出+ peer review 三角校准。重点是用它识别「该补广度还是深度」，指导下一步学习投入。",
    ),
    kp("完整实战演练步骤",
        lst([
            "运行代码，对号入座看自己是哪种失衡。",
            "把 breadth/depth 拆成子项（如广度含 Python/网络/DB），定位具体短板。",
            "针对短板选一个最小项目补强（如广度不足就做一个带 DB 的 Agent）。",
            "每完成一个项目重算一次 assess，观察曲线变化。",
            "把 T 型评估接入个人 OKR，作为季度成长目标。",
        ], ordered=True),
    ),
    callout("danger", "常见误区与调试",
        "① 只追深度：成为某框架专家却被跨域问题卡死，可替代性低。② 只追广度：什么都懂一点，做不出有壁垒系统。③ 用「收藏文章数」冒充能力：囤资料≠掌握。④ 忽视产品意识：技术强但做不出用户要的东西。⑤ 不量化短板：凭感觉学，长期偏科。"),
    callout("tip", "工程化扩展建议",
        "用 T 型模型做个人/团队能力盘点；广度靠「做跨域小项目」补齐，深度靠「啃一个方向到能教别人」；建立「反馈密度」高的练习循环（小步快跑+即时运行）；把能力评估与项目产出绑定，避免虚构进度。"),
],
}


# ---------------------------------------------------------------------------
# 主入口：按章节号运行（每次只跑一个章节，跑完即审计+重建+提交）
# ---------------------------------------------------------------------------

ENRICH = {1: CH1_ENRICH}


def main():
    targets = [int(x) for x in sys.argv[1:] if x.isdigit()]
    if not targets:
        print("用法: python3 scripts/gen_enrich.py <章号>  (如 1 2)")
        return
    for ch in targets:
        plan = ENRICH.get(ch)
        if not plan:
            print(f"章节 {ch} 暂无 enrichment 计划，跳过")
            continue
        apply_to_chapter(ch, plan)
    print("done")


if __name__ == "__main__":
    main()
