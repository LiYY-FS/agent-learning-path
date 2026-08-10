#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第三章新增 3.7「Agent Skill 与能力封装」节生成器。

做两件事：
  1. 重编号原 3.7/3.8/3.9 → 3.8/3.9/3.10（chapter-3.json + chapters.json + quizzes.json
     中的 section id、quiz id 前缀、quiz.section 字段全部同步），为 3.7 腾位。
  2. 在 3.6 MCP 之后插入新节 3.7，并补 6 道 quiz（ch3-3.7-q1..q6）。

承上启下：3.6 MCP 讲「工具怎么被标准化传输」，3.7 讲「能力怎么被封装、组合、分发」；
与 2.4 Tool Calling 区分——2.4 讲模型调函数的协议，3.7 讲把一项业务能力打包成
可复用单元的工程抽象。

运行：python3 scripts/gen_ch3_skill.py
之后必跑：python3 scripts/audit_code.py（须 0 问题）→ 比对 code 真实输出 →
python3 scripts/build_data.py → git 提交。
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "assets", "data")


# ---------------------------------------------------------------------------
# 内容块构造助手（与 gen_enrich.py / gen_deepen.py 一致）
# ---------------------------------------------------------------------------

def _sanitize_hl(src, hl):
    """修正 highlightLines：越界/空行/纯注释行吸附到最近有效代码行；全无效则清空。"""
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


def heading(text):
    return {"type": "heading", "text": text}


def lst(items, ordered=False):
    return {"type": "list", "ordered": ordered, "items": items}


# ---------------------------------------------------------------------------
# 新节 3.7「Agent Skill 与能力封装」内容
# ---------------------------------------------------------------------------

CONTENT_37 = [
    kp("什么是 Skill：从一个「工具」到一项「能力」",
        para("3.6 讲的 MCP 解决的是「工具怎么被标准化传输」——让一个 `query_order` 能被任何宿主调用。但真实业务里，用户要的不是「调用某个函数」，而是「办成一件事」：比如「处理一笔售后」要先查订单、再判规则、再生成回复、还要有权限边界。**Skill（技能）就是把这些步骤断打包成一个可复用能力单元的抽象**：它把工具链 + 提示 + 流程 + 权限封装在一起，对外只暴露一个「能做什么、什么时候做」的声明。"),
        para("打个比方：**工具是螺丝刀，Skill 是「组装一个柜子」的工艺包**。螺丝刀是原子动作，工艺包里含螺丝刀、图纸、顺序、注意事项，拿到就能产出成品。Agent 调一个 tool 是「挥一下锤子」，调一个 skill 是「委托一整道工序」。"),
    ),
    kp("Skill 的四要素：声明式描述 + 工具集 + 流程 + 权限",
        para("一个合格的 Skill 通常由四部分构成。这四要素缺一不可，是 Skill 区别于「随手写个函数」的关键。"),
        table(
            ["要素", "作用", "缺失的后果"],
            [
                ["声明式描述", "告诉模型/调度器这个能力能做什么、何时该用", "能力无法被发现，模型选错或漏选"],
                ["工具集", "封装一个或多个工具调用", "没有实际执行手段"],
                ["流程", "规定工具的调用顺序与分支", "执行混乱，结果不可复现"],
                ["权限", "声明该能力需要哪些授权", "越权操作或被误调用"],
            ],
        ),
    ),
    code("s3_7_skill.py", "python", "最小 Skill 封装：把「查订单 + 格式化」打包成一个能力单元",
        r'''# 最小 Skill 封装：把「查询订单 + 格式化」打包成一个可复用能力单元
from dataclasses import dataclass, field

@dataclass
class Skill:
    name: str
    description: str                       # 声明式描述：让调度器知道何时调用
    permissions: list = field(default_factory=list)
    def run(self, *args, **kwargs):
        raise NotImplementedError

# 模拟订单数据（真实场景对接订单微服务）
_ORDERS = {"A001": {"status": "已发货", "addr": "北京"}, "A002": {"status": "处理中", "addr": "上海"}}

class OrderLookupSkill(Skill):
    def __init__(self):
        super().__init__(name="order_lookup", description="按订单号查询订单状态与配送地址", permissions=["order:read"])
    def run(self, order_id: str) -> str:
        order = _ORDERS.get(order_id)
        if not order:
            return f"订单 {order_id} 不存在"
        return f"订单 {order_id}：{order['status']}，配送至 {order['addr']}"

if __name__ == "__main__":
    skill = OrderLookupSkill()
    print(f"技能：{skill.name} | 权限：{skill.permissions}")
    print(skill.run("A001"))
    print(skill.run("A003"))
''',
        hl=[7, 16, 18],
        output="技能：order_lookup | 权限：['order:read']\n订单 A001：已发货，配送至 北京\n订单 A003 不存在",
        note="Skill 把「查订单」这个能力连同描述、权限一起封装。调度器只看 description 决定要不要调，调起来内部自动完成查询+格式化。真实生产里 run 内部可换成 MCP 工具调用。",
    ),
    kp("Skill vs Tool / Function / Plugin / MCP：四个概念的边界",
        para("这四个词在 Agent 圈常被混用，但它们其实处在不同层次。理清边界，才知道什么时候该用哪个。"),
        table(
            ["概念", "层次", "本质", "典型代表"],
            [
                ["Function", "协议", "模型可调用的函数签名", "OpenAI Function Calling"],
                ["Tool", "实现", "一个具体的能力函数（含执行逻辑）", "LangChain Tool"],
                ["Plugin", "封装", "一组工具 + 配置的打包单元", "Semantic Kernel Plugin"],
                ["MCP", "传输", "工具标准化暴露的开放协议", "MCP Server"],
                ["Skill", "抽象", "达成一项业务目标的能力单元（工具+流程+权限）", "本节定义"],
            ],
        ),
        para("一句话总结：**Function/Tool 是「原子」，MCP 是「管道」，Skill 是「工序」**。Skill 可以内部调用 Tool，也可以通过 MCP 暴露出去——三者正交，不是替代关系。"),
    ),
    callout("tip", "跨框架映射：各家的 Skill 等价物",
        "LangChain 的 `Tool` / `Toolkit`（一组相关工具）；OpenAI Agents SDK 的 `tool` + `handoff`（handoff 本身就是一种「把整段任务交给另一个 Agent」的粗粒度能力）；Semantic Kernel 的 `Plugin`（2023 年底前叫 `Skill`，是这个词的出处）；MCP 的 `Server`（可看作「跨进程的 Skill 容器」）。**看到别家文档里的这些词，都可以和这里的 Skill 抽象对上号。**"),
    kp("Skill 的四条设计原则",
        para("写一个能用的 Skill 不难，写一个「好复用、好组合、不闯祸」的 Skill 要守四条原则："),
        lst([
            "**单一职责**：一个 Skill 只解决一件事；要办两件事就拆成两个再组合，别做大杂烩。",
            "**声明式描述**：description 写清「能做什么、什么场景用」，这是被模型选中的唯一依据。",
            "**可组合**：Skill 的输入输出尽量是纯数据（字符串/JSON），便于被另一个 Skill 串接。",
            "**权限最小化**：只申请完成该能力必需的权限，默认拒绝，按需授予。",
        ]),
    ),
    heading("深入解析与实战"),
    kp("核心概念：Skill 是「能力的中粒度封装」",
        para("Skill 的价值在于「中粒度」。粒度太细（每个函数一个 Tool）会让模型选择负担过重、容易调错；粒度太粗（一个大 Agent 干所有事）又失去复用性。Skill 卡在中间：把「达成一个明确业务目标」的若干工具固定编排在起，模型只需在「用不用这个 Skill」层面决策，不必操心内部步骤。这和人类分工是一个道理——你委托水电工「修水管」，不用告诉他先关哪个阀门。"),
    ),
    code("s3_7_compose.py", "python", "Skill 组合：把多个 Skill 编排成一个更粗粒度的能力",
        r'''# Skill 组合：把「查询」+「决策回复」编排成「售后问答」能力，对外仍是一个 Skill
_ORDERS = {"A001": {"status": "已发货", "addr": "北京"}, "A002": {"status": "处理中", "addr": "上海"}}

def skill_lookup(order_id):
    """Skill 1：查询订单"""
    return _ORDERS.get(order_id, {"status": "未知", "addr": "未知"})

def skill_decide(order):
    """Skill 2：根据状态生成回复"""
    if order["status"] == "已发货":
        return f"已发货，配送至 {order['addr']}"
    if order["status"] == "处理中":
        return f"仍在处理，配送至 {order['addr']}，请耐心等待"
    return "状态异常，已转人工"

def skill_after_sale(order_id):
    """Skill 3（组合）：查询 -> 决策，对外是「售后问答」一个能力"""
    return skill_decide(skill_lookup(order_id))

if __name__ == "__main__":
    for oid in ["A001", "A002", "A003"]:
        print(f"{oid} -> {skill_after_sale(oid)}")
''',
        hl=[13, 14, 15],
        output="A001 -> 已发货，配送至 北京\nA002 -> 仍在处理，配送至 上海，请耐心等待\nA003 -> 状态异常，已转人工",
        note="skill_after_sale 内部组合了 lookup 和 decide，对外只暴露一个能力。模型只需决定「要不要走售后问答」，不用管内部两步。这就是「中粒度封装」的复用价值。",
    ),
    kp("完整实战演练步骤",
        lst([
            "把 s3_7_skill.py 复制到本地，`python s3_7_skill.py` 跑通，确认输出三行。",
            "修改 OrderLookupSkill，让它额外返回「预计送达日期」字段，体会「封装内部变化不影响调用方」。",
            "再跑 s3_7_compose.py，观察组合后模型只需做一次决策。",
            "尝试把 skill_after_sale 拆成「带权限校验」的版本：无 order:read 权限时直接拒绝。",
        ]),
    ),
    callout("danger", "常见误区",
        "**① 大杂烩 Skill**：把查订单、发优惠券、改地址塞进一个 Skill，违背单一职责，模型选不准、测试爆。**② 权限过宽**：直接给 `order:*` 全权限，一旦被误触发就改了本不该改的数据。**③ 描述缺失或含糊**：description 写「处理订单相关事务」，模型根本判断不了何时该用，等于没有这个 Skill。"),
    heading("原理深挖与工程扩展"),
    kp("底层原理：Skill 的可分发性与「能力市场」",
        para("Skill 之所以单独成节，是因为它承载了一个 Tool 不具备的属性：**可分发性**。一个封装好的 Skill 可以被打包、版本化、上架，被不同团队、不同 Agent 乃至不同组织复用——这正是「Agent 能力市场」的底层逻辑。MCP 让工具能跨进程传输，Skill 让能力能跨团队流通；前者是管道标准，后者是商品单元。理解了这层，就能看懂为什么 OpenAI 的 GPTs Actions、Anthropic 的 MCP Server 目录、各家 Plugin 市场都在往「可分发的能力单元」收敛。"),
    ),
    code("s3_7_registry.py", "python", "Skill 注册表：声明式描述驱动发现，权限驱动准入",
        r'''# Skill 注册表：description 驱动「发现」，permissions 驱动「准入」
_SKILLS = {}

def register(skill):
    _SKILLS[skill["name"]] = skill
    return skill

def discover(query, granted):
    """按 query 关键词匹配 description，再过滤掉权限不足的"""
    matched = []
    for s in _SKILLS.values():
        if any(w in s["description"] for w in query.split()):
            if set(s["permissions"]) <= set(granted):
                matched.append(s["name"])
    return matched

register({"name": "order_lookup", "description": "查询订单状态与地址", "permissions": ["order:read"]})
register({"name": "order_refund", "description": "发起订单退款", "permissions": ["order:refund"]})
register({"name": "faq_answer", "description": "常见问题自动答复", "permissions": []})

if __name__ == "__main__":
    print("可发现(权限=order:read)：", discover("查询 订单", ["order:read"]))
    print("可发现(权限=order:read,refund)：", discover("订单 退款", ["order:read", "order:refund"]))
    print("可发现(无权限)：", discover("订单", []))
''',
        hl=[11, 13, 14],
        output="可发现(权限=order:read)： ['order_lookup']\n可发现(权限=order:read,refund)： ['order_lookup', 'order_refund']\n可发现(无权限)： []",
        note="注册表是「能力市场」的雏形：description 让能力可被搜索，permissions 让能力可被管控。真实市场还要加版本号、依赖声明、调用计量、沙箱隔离——但发现+准入这两步是底座。",
    ),
    kp("完整实战演练步骤",
        lst([
            "跑 s3_7_registry.py，确认三行输出与预期一致。",
            "给 discover 增加按「相关度排序」：匹配关键词越多排越前。",
            "新增一个需要 `order:write` 权限的 Skill，验证无该权限时不会被返回。",
            "思考：如果把每个 Skill 都包成 MCP Server，discover 逻辑要怎么改？（提示：跨进程后要加发现协议）",
        ]),
    ),
    callout("tip", "工程化扩展",
        "生产级 Skill 系统还要补：**版本化**（同名 Skill 升级不破坏旧调用方）、**依赖声明**（Skill A 依赖 Skill B）、**沙箱隔离**（Skill 内部代码跑在受限环境，防逃逸）、**调用计量与计费**。这些加上去，就是一个完整的「Agent 能力平台」。"),
]


SECTION_37 = {
    "id": "3.7",
    "title": "Agent Skill 与能力封装",
    "subtitle": "从工具调用到可复用、可组合、可分发的能力单元",
    "estimatedMinutes": 40,
    "difficulty": 3,
    "objectives": [
        "理解 Agent Skill 作为「能力封装单元」的抽象：它把工具链 + 提示 + 流程 + 权限打包成可复用、可组合的标准件",
        "能说清 Skill 与 Tool / Function / Plugin / MCP 的关系与边界，知道它们处在不同层次而非互相替代",
        "掌握 Skill 的四条设计原则（单一职责、声明式描述、可组合、权限最小化），并能用可运行代码封装与组合 Skill",
    ],
    "content": CONTENT_37,
    "enterpriseCase": {
        "title": "电商售后能力 Skill 化",
        "background": "某电商多个 Agent（客服 Bot、商家助手、内部工单系统）都要处理「售后问答」，各自重复实现查询+判规则+回复逻辑，规则一改三处都改。",
        "architecture": "把「售后问答」封装成一个 Skill（内部组合查询 + 决策回复 + 权限校验），通过内部注册表统一发布，三个 Agent 按需调用同一份能力。",
        "outcome": "售后逻辑只维护一处，规则更新即时生效到所有 Agent；新 Agent 接入只需声明权限，0 代码即获得售后能力。",
        "lessons": "Skill 化的本质是「把重复的业务工序沉淀成可复用资产」；粒度选在「一项业务目标」最划算，太细复用低、太粗不灵活。",
        "code": {"data": {
            "filename": "3_7_after_sale_skill.py",
            "language": "python",
            "title": "售后问答 Skill：一个能力单元供多 Agent 复用",
            "highlightLines": [10, 11, 12],
            "code": (
                "# 企业案例：把「售后问答」封装成一个 Skill，多个 Agent 复用同一份能力\n"
                "_ORDERS = {\"A001\": \"已发货\", \"A002\": \"处理中\"}\n"
                "\n"
                "def lookup(order_id):\n"
                "    return _ORDERS.get(order_id, \"未知\")\n"
                "\n"
                "def reply(status):\n"
                "    if status == \"已发货\":\n"
                "        return \"您的订单已发货，请注意查收\"\n"
                "    if status == \"处理中\":\n"
                "        return \"您的订单正在处理，请耐心等待\"\n"
                "    return \"已为您转接人工客服\"\n"
                "\n"
                "def after_sale_skill(order_id):\n"
                "    # 封装：查询 -> 决策回复，对外是一个可复用能力单元\n"
                "    return reply(lookup(order_id))\n"
                "\n"
                "if __name__ == \"__main__\":\n"
                "    print(after_sale_skill(\"A001\"))\n"
                "    print(after_sale_skill(\"A003\"))\n"
            ),
            "output": "您的订单已发货，请注意查收\n已为您转接人工客服",
            "note": "三个 Agent 调同一个 after_sale_skill，售后规则只在 lookup/reply 里维护一处。新 Agent 接入无需重写逻辑，只需声明调用权限。",
        }},
    },
    "exercises": [
        {
            "title": "给 OrderLookupSkill 增加权限校验",
            "description": "在 `s3_7_skill.py` 的 `OrderLookupSkill.run` 开头加一步：若调用方未持有 `order:read` 权限，直接返回「权限不足」。要求用一个 `granted` 列表参数表示调用方当前权限，并在 `__main__` 里分别测试有权限/无权限两种情况。",
            "hints": "权限校验放在业务逻辑之前；用集合判断 `set(self.permissions) <= set(granted)` 最简洁。想想为什么权限要做成「声明 + 校验」两段而不是写死在代码里。",
        },
        {
            "title": "用注册表实现「能力市场」雏形",
            "description": "基于 `s3_7_registry.py`，扩展 `register` 让每个 Skill 带 `version` 字段；扩展 `discover` 在返回名字时同时返回版本。再写一个 `resolve(name, version)` 按「同名取最高兼容版本」解析。",
            "hints": "版本比较可以用 `tuple(map(int, v.split('.')))`。思考：当两个团队都叫 `order_lookup` 时，命名空间怎么管？",
        },
    ],
    "resources": [
        {"type": "doc", "title": "Semantic Kernel —— Plugins（原 Skills）", "url": "https://learn.microsoft.com/semantic-kernel/concepts/plugins/", "note": "Skill 概念的出处，看 Plugin 如何把原生函数封装成 AI 可调用能力"},
        {"type": "doc", "title": "OpenAI Agents SDK —— Tools 与 Handoffs", "url": "https://platform.openai.com/docs/guides/tools", "note": "tool 是原子能力，handoff 是粗粒度能力委托，对照 Skill 的中粒度定位"},
        {"type": "doc", "title": "LangChain —— Tools & Toolkits", "url": "https://python.langchain.com/docs/concepts/tools/", "note": "Toolkit 是「一组相关工具」，是 Skill 思想在 LangChain 里的体现"},
        {"type": "doc", "title": "MCP —— Servers 作为跨进程能力容器", "url": "https://modelcontextprotocol.io/docs/concepts/servers", "note": "把 3.6 的 MCP Server 和本节 Skill 对照看：管道 vs 商品"},
    ],
    "quiz": ["ch3-3.7-q1", "ch3-3.7-q2", "ch3-3.7-q3", "ch3-3.7-q4", "ch3-3.7-q5", "ch3-3.7-q6"],
}


NEW_QUIZZES = [
    {
        "id": "ch3-3.7-q1", "chapter": "ch3", "section": "3.7", "type": "single", "difficulty": 2,
        "question": "Skill 与 Tool 的核心区别是什么？",
        "options": [
            {"key": "A", "text": "Skill 就是 Tool 的别名，两者完全等价"},
            {"key": "B", "text": "Skill 把工具链+流程+权限打包成可复用能力单元，Tool 是原子函数调用"},
            {"key": "C", "text": "Skill 只能用在低代码平台，Tool 用在代码框架"},
            {"key": "D", "text": "Tool 比 Skill 更高级、能力更强"},
        ],
        "explanation": "Tool 是原子级函数调用，Skill 在其之上封装了达成业务目标的工具链、流程与权限，是更粗粒度的能力单元。",
    },
    {
        "id": "ch3-3.7-q2", "chapter": "ch3", "section": "3.7", "type": "single", "difficulty": 3,
        "question": "Skill 的「声明式描述（description）」最主要的作用是？",
        "options": [
            {"key": "A", "text": "给开发者看的代码注释"},
            {"key": "B", "text": "让模型/调度器知道这个能力能做什么、何时该调用"},
            {"key": "C", "text": "满足代码规范检查"},
            {"key": "D", "text": "替代正式的 API 文档"},
        ],
        "explanation": "description 是 Skill 被发现和选中的唯一依据，模型/调度器依据它判断是否调用；缺失或含糊会导致能力无法被正确路由。",
    },
    {
        "id": "ch3-3.7-q3", "chapter": "ch3", "section": "3.7", "type": "single", "difficulty": 2,
        "question": "下列哪项不是 Skill 的设计原则？",
        "options": [
            {"key": "A", "text": "单一职责"},
            {"key": "B", "text": "权限最大化"},
            {"key": "C", "text": "可组合"},
            {"key": "D", "text": "声明式描述"},
        ],
        "explanation": "Skill 的权限应遵循最小化原则，只申请完成该能力所必需的权限，避免越权风险。「权限最大化」是反模式。",
    },
    {
        "id": "ch3-3.7-q4", "chapter": "ch3", "section": "3.7", "type": "multiple", "difficulty": 3,
        "question": "关于 Skill 与 MCP 的关系，以下说法正确的有？（多选）",
        "options": [
            {"key": "A", "text": "MCP 是工具层的标准化传输协议，Skill 是能力的封装抽象，两者分属不同层次"},
            {"key": "B", "text": "两者正交互补：MCP 解决「怎么传」，Skill 解决「怎么封装组合」"},
            {"key": "C", "text": "有了 MCP 就不需要 Skill 概念"},
            {"key": "D", "text": "Skill 必须通过 MCP 暴露才能被使用"},
        ],
        "explanation": "MCP 与 Skill 分属协议层与抽象层，正交互补，不是替代关系；Skill 也可通过普通函数、插件等方式暴露，MCP 只是可选的标准化通道之一。",
    },
    {
        "id": "ch3-3.7-q5", "chapter": "ch3", "section": "3.7", "type": "single", "difficulty": 3,
        "question": "跨框架映射中，Skill 概念最接近下列哪个？",
        "options": [
            {"key": "A", "text": "LangChain 的 LLMChain"},
            {"key": "B", "text": "Semantic Kernel 的 Plugin（原名 Skill）"},
            {"key": "C", "text": "OpenAI 的 tokenizer"},
            {"key": "D", "text": "LlamaIndex 的 Index"},
        ],
        "explanation": "Semantic Kernel 早期用 Skill 命名能力封装单元，后改名 Plugin，是「Skill」这个词在主流框架中最直接的出处与对应。",
    },
    {
        "id": "ch3-3.7-q6", "chapter": "ch3", "section": "3.7", "type": "multiple", "difficulty": 3,
        "question": "设计 Skill 时的常见误区有？（多选）",
        "options": [
            {"key": "A", "text": "把多个不相关能力塞进同一个 Skill（大杂烩）"},
            {"key": "B", "text": "权限申请过宽，直接给 order:* 全权限"},
            {"key": "C", "text": "缺少声明式描述，导致模型不知道何时该用"},
            {"key": "D", "text": "让 Skill 只做一件事、职责单一"},
        ],
        "explanation": "A/B/C 都是典型误区；D 是正确做法（单一职责），不是误区。",
    },
]


# ---------------------------------------------------------------------------
# 重编号 + 插入
# ---------------------------------------------------------------------------

SEC_MAP = {"3.7": "3.8", "3.8": "3.9", "3.9": "3.10"}


def remap_qid(qid):
    """ch3-3.7-q1 -> ch3-3.8-q1（仅映射 3.7/3.8/3.9）"""
    return re.sub(r'^(ch3-)(3\.[789])(-q\d+)$',
                  lambda m: m.group(1) + SEC_MAP[m.group(2)] + m.group(3), qid)


def main():
    # 1) chapter-3.json：重编号原 3.7/3.8/3.9，再在 3.6 后插入新 3.7
    p3 = os.path.join(DATA_DIR, "chapter-3.json")
    with open(p3, encoding="utf-8") as f:
        c3 = json.load(f)
    for sec in c3["sections"]:
        if sec["id"] in SEC_MAP:
            sec["id"] = SEC_MAP[sec["id"]]
            sec["quiz"] = [remap_qid(q) for q in sec.get("quiz", [])]
    idx = next(i for i, s in enumerate(c3["sections"]) if s["id"] == "3.6")
    c3["sections"].insert(idx + 1, SECTION_37)
    with open(p3, "w", encoding="utf-8") as f:
        json.dump(c3, f, ensure_ascii=False, indent=2)
    print(f"已更新 {p3}：重编号 3.7/3.8/3.9 -> 3.8/3.9/3.10，插入新节 3.7")

    # 2) chapters.json：同步重编号 + 插入 3.7 大纲条目
    pc = os.path.join(DATA_DIR, "chapters.json")
    with open(pc, encoding="utf-8") as f:
        ch = json.load(f)
    ch3 = next(c for c in ch["chapters"] if c["number"] == 3)
    for s in ch3["sections"]:
        if s["id"] in SEC_MAP:
            s["id"] = SEC_MAP[s["id"]]
    idx = next(i for i, s in enumerate(ch3["sections"]) if s["id"] == "3.6")
    ch3["sections"].insert(idx + 1, {
        "id": "3.7",
        "title": SECTION_37["title"],
        "estimatedMinutes": SECTION_37["estimatedMinutes"],
        "difficulty": SECTION_37["difficulty"],
    })
    with open(pc, "w", encoding="utf-8") as f:
        json.dump(ch, f, ensure_ascii=False, indent=2)
    print(f"已更新 {pc}：重编号 + 插入 3.7 大纲")

    # 3) quizzes.json：重编号 ch3 原 3.7/3.8/3.9 的 18 题，追加新 3.7 的 6 题
    pq = os.path.join(DATA_DIR, "quizzes.json")
    with open(pq, encoding="utf-8") as f:
        q = json.load(f)
    n = 0
    for x in q["quizzes"]:
        if x.get("chapter") == "ch3" and x.get("section") in SEC_MAP:
            x["section"] = SEC_MAP[x["section"]]
            x["id"] = remap_qid(x["id"])
            n += 1
    q["quizzes"].extend(NEW_QUIZZES)
    with open(pq, "w", encoding="utf-8") as f:
        json.dump(q, f, ensure_ascii=False, indent=2)
    print(f"已更新 {pq}：重编号 {n} 题，追加 3.7 新题 6 道")

    print("\n下一步：python3 scripts/audit_code.py（须 0 问题）")


if __name__ == "__main__":
    main()
