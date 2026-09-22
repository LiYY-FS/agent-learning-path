#!/usr/bin/env python3
"""Rebuild deep learning content for chapters 4-6 from JSON sources."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "assets" / "data"
TODAY = "2026-09-21"
VERSION = "2026.09.21"
TIMESTAMP = "2026-09-21T09:00:00+08:00"


def kp(title, blocks):
    return {"type": "knowledgePoint", "title": title, "content": blocks}


def p(text):
    return {"type": "paragraph", "text": text}


def c(title, text, variant="info"):
    return {"type": "callout", "variant": variant, "title": title, "text": text}


def t(headers, rows):
    return {"type": "table", "data": {"headers": headers, "rows": rows}}


def l(items, ordered=False):
    return {"type": "list", "ordered": ordered, "items": items}


def h(text):
    return {"type": "heading", "text": text}


def code(filename, title, lines, highlight, output, note):
    return {"type": "code", "data": {"filename": filename, "language": "python", "title": title, "highlightLines": highlight, "code": "\n".join(lines), "output": output, "note": note}}


def section(sid, title, objective, blocks, exercises, resources, quiz, enterprise=None):
    out = {"id": sid, "title": title, "subtitle": objective, "estimatedMinutes": 45, "difficulty": 4, "objectives": [objective], "content": blocks, "exercises": exercises, "resources": resources, "quiz": quiz}
    if enterprise:
        out["enterpriseCase"] = enterprise
    out["lastUpdated"] = TODAY
    out["version"] = VERSION
    out["updatedAt"] = TIMESTAMP
    return out


def ec(title, bg, arch, outcome, lessons, fn, code_title, lines, hl, output, note):
    return {"title": title, "background": bg, "architecture": arch, "outcome": outcome, "lessons": lessons, "code": {"filename": fn, "language": "python", "title": code_title, "highlightLines": hl, "code": "\n".join(lines), "output": output, "note": note}}


def build_ch4():
    return [
        section("4.1", "多 Agent 架构模式", "能按控制流选择层级、网络、黑板、事件驱动或自治协作", [
            p("多 Agent 不是简单堆角色，而是设计一套可预测的控制流。层级结构适合命令清晰；网络协作适合探索；黑板模型适合共享事实；事件驱动适合异步系统；自治协作适合开放环境。"),
            t(["模式", "适用场景", "风险", "最小验证"], [["层级", "审批流、主管调度", "主管误判", "记录 supervisor 路由"], ["网络", "研究、多源探索", "重复劳动", "统计去重率"], ["黑板", "共享状态", "状态污染", "状态 diff 审计"], ["事件驱动", "实时系统", "乱序重复", "幂等 + 死信"], ["自治协作", "开放环境", "不可控", "预算 + 终止条件"]]),
            kp("可运行架构选择器", [code("arch_selector.py", "多 Agent 架构选择器：按复杂度选择控制流", ["COMPLEXITY = {\"query\": 1, \"workflow\": 2, \"explore\": 3, \"realtime\": 4}", "def choose(flags):", "    score = sum(COMPLEXITY[f] for f in flags)", "    if score <= 1:", "        return \"single-agent\"", "    if score <= 2:", "        return \"hierarchical\"", "    if score <= 3:", "        return \"blackboard\"", "    return \"event-driven\""] + ["", "if __name__ == \"__main__\":", "    print(choose([\"query\"]))", "    print(choose([\"workflow\", \"explore\"]))", "    print(choose([\"realtime\", \"explore\"]))"], [6, 8, 10], "single-agent\nblackboard\nevent-driven", "这是架构设计的第一步：先量化复杂度，再选控制流。真实项目还会叠加延迟、成本、权限和安全等级。")]),
            kp("层级主管：可追踪路由", [code("supervisor.py", "层级主管：主管节点选择 worker", ["ROUTES = {\"refund\": \"after_sales\", \"code\": \"coder\", \"faq\": \"faq\"}", "def route(goal):", "    return ROUTES.get(goal, \"faq\")"] + ["", "def run(goal):", "    return f\"supervisor -> {route(goal)}\"", "", "if __name__ == \"__main__\":", "    print(run(\"refund\"))", "    print(run(\"unknown\"))"], [3, 6], "supervisor -> after_sales\nsupervisor -> faq", "层级模式的关键不是有主管，而是主管的每次决策可记录、可回放、可评估。")]),
            c("生产提示", "上线前给每种架构准备评估集：层级看路由准确率，网络看去重率，黑板看状态污染，事件驱动看幂等和重复消费。")], [{"title": "为你的需求选架构", "description": "为客服、研究、报表、审批各选一种架构并说明理由。", "hints": "先问控制流是否清晰，再问状态是否共享"}, {"title": "画架构评估矩阵", "description": "从延迟、成本、可观测、恢复能力四列打分。", "hints": "每一项都必须能解释取舍"}], [{"type": "doc", "title": "Anthropic Building Effective Agents", "url": "https://www.anthropic.com/research/building-effective-agents", "note": "先判断是否需要复杂 Agent 系统"}, {"type": "doc", "title": "LangGraph Multi-agent systems", "url": "https://langchain-ai.github.io/langgraph/", "note": "图和 supervisor 模式参考"}], ["ch4-4.1-q1", "ch4-4.1-q2"], ec("银行审批 Agent 平台", "审批链路涉及资料核验、风控、合规和人工复核。", "层级架构：supervisor 判断任务类型，worker 做核验/风控/合规，HITL 节点处理高风险。", "路由准确率、审计完整率、平均耗时都可独立统计。", "主管层必须可解释；worker 必须可独立回归测试。", "bank_ec.py", "审批流水线：层级路由 + 人工门", ["STAGES = {\"docs\": \"document_check\", \"risk\": \"risk_check\", \"pay\": \"payment\"}", "def next_stage(goal):", "    return STAGES.get(goal, \"human_review\")", "if __name__ == \"__main__\":", "    print(next_stage(\"risk\"))", "    print(next_stage(\"pay\"))"], [3, 6], "risk_check\nhuman_review", "生产审批系统中，路由必须能追踪到具体规则，不能只看最终结果。"))
    ], [
        section("4.2", "角色分工与设计", "能设计可测试、可交接、可独立评估的 Agent 角色", [
            p("角色设计是多人协作在 Agent 系统中的映射。每个角色要有输入契约、输出契约、权限、失败行为和交接协议；否则多 Agent 很快变成互相推诿和重复劳动。"),
            t(["角色", "职责", "不该做", "评估重点"], [["Router", "分类和路由", "生成最终答案", "准确率、误分类"], ["Worker", "完成具体任务", "越界修改状态", "任务成功率"], ["Critic", "检查质量和风险", "替代用户决策", "漏检率、误报率"], ["Human Gate", "确认高风险", "处理低风险流水", "确认耗时、覆盖"]]),
            kp("角色契约设计", [code("role_contract.py", "Agent 角色契约：职责、权限、输出", ["class Role:", "    def __init__(self, name, can_do, must_not_do, output_schema):", "        self.name = name", "        self.can_do = can_do", "        self.must_not_do = must_not_do", "        self.output_schema = output_schema", "    def handoff(self, reason, payload):", "        return {\"role\": self.name, \"reason\": reason, \"payload\": payload}"] + ["", "if __name__ == \"__main__\":", "    writer = Role(\"writer\", [\"draft\"], [\"publish\"], [\"draft\", \"confidence\"])", "    print(writer.handoff(\"needs_review\", {\"word_count\": 500}))"], [3, 8], "{'role': 'writer', 'reason': 'needs_review', 'payload': {'word_count': 500}}", "契约让角色变成可测试组件，而不是只有 prompt 的人设。")]),
            kp("交接协议", [code("handoff_protocol.py", "角色交接协议：带原因和载荷", ["def handoff(src, dst, reason, payload):", "    return {\"from\": src, \"to\": dst, \"reason\": reason, \"payload\": payload}"] + ["", "if __name__ == \"__main__\":", "    print(handoff(\"analyst\", \"writer\", \"report_ready\", {\"sections\": 4}))"], [2], "{'from': 'analyst', 'to': 'writer', 'reason': 'report_ready', 'payload': {'sections': 4}}", "交接协议要让审计人员知道：谁交给谁、为什么、带了什么。")]),
            c("常见坑", "角色人设写得漂亮但没有契约时，模型会按语义自由发挥，系统很难评测。先把输入/输出/失败条件写清楚。")], [{"title": "写角色卡", "description": "为 Router/Researcher/Critic 各写一张角色卡。", "hints": "每张卡至少包含输入、输出、禁止动作"}, {"title": "设计交接日志", "description": "定义每次 handoff 必须记录的字段。", "hints": "reason 和 payload 是最低要求"}], [{"type": "doc", "title": "CrewAI Agents", "url": "https://docs.crewai.com/agents/", "note": "角色化 Crews 的角色定义方式"}], ["ch4-4.2-q1", "ch4-4.2-q2"]),
    ], [
        section("4.3", "Agent 间通信协议", "能选择消息、事件、共享状态或工具调用作为通信机制", [
            p("Agent 间通信的难点不是传一句话，而是控制语义、版本、幂等和可观测。消息适合明确请求；事件适合解耦异步系统；共享状态适合黑板协作；工具调用适合强类型动作。"),
            t(["协议", "语义", "优点", "挑战"], [["Request/Response", "一问一答", "易理解", "耦合强"], ["Event", "状态变化", "解耦", "乱序/重复"], ["Shared State", "黑板", "信息集中", "竞争污染"], ["Tool Call", "强类型动作", "可校验", "工具爆炸"]]),
            kp("消息 envelope", [code("message_envelope.py", "Agent 消息 envelope", ["from dataclasses import dataclass"] + ["", "@dataclass", "class Msg:", "    kind: str", "    sender: str", "    body: dict"] + ["", "def send(m):", "    return {\"kind\": m.kind, \"from\": m.sender, \"body\": m.body}"] + ["", "if __name__ == \"__main__\":", "    print(send(Msg(\"task\", \"planner\", {\"goal\": \"analyze\"})))"], [6, 11], "{'kind': 'task', 'from': 'planner', 'body': {'goal': 'analyze'}}", "envelope 不是仪式感，它让日志、路由、重放和安全检查都有稳定字段。")]),
            kp("事件驱动的幂等", [code("event_idempotent.py", "事件消费幂等示例", ["SEEN = set()", "def consume(event_id, action):", "    if event_id in SEEN:", "        return f\"duplicate:{event_id}\"", "    SEEN.add(event_id)", "    return action"] + ["", "if __name__ == \"__main__\":", "    print(consume(\"e1\", \"send_email\"))", "    print(consume(\"e1\", \"send_email\"))"], [4, 7], "send_email\nduplicate:e1", "事件系统必须防重复执行，否则同一个 Agent 事件可能触发多次扣款或发送。")]),
            c("生产落地", "所有通信都加 trace_id、from、to、kind、payload 和 timestamp；高风险事件必须支持重放前检查。")], [{"title": "设计事件 schema", "description": "为 order.created 和 refund.requested 写 JSON schema。", "hints": "schema 要有版本字段"}, {"title": "处理乱序事件", "description": "设计 timestamp 和 event_id 组合的乱序策略。", "hints": "幂等优先于顺序优先"}], [{"type": "doc", "title": "MCP Specification", "url": "https://modelcontextprotocol.io/", "note": "工具与资源通信标准"}], ["ch4-4.3-q1", "ch4-4.3-q2"]),
    ], [
        section("4.4", "任务分解与编排", "能把长任务拆成计划、执行、验证和收敛四阶段", [
            p("任务分解的核心是降低单次模型决策半径。计划要小步；执行要可验证；失败要可恢复；最终结果要能被 checker 判定。"),
            t(["阶段", "产物", "检查点", "失败处理"], [["Plan", "步骤清单", "目标一致", "重规划"], ["Execute", "中间结果", "格式正确", "重试/跳过"], ["Verify", "校验结果", "覆盖约束", "回滚"], ["Synthesize", "最终答案", "引用可查", "人工复核"]]),
            kp("可运行任务分解器", [code("task_planner.py", "任务分解与预算检查", ["def plan(goal):", "    return [\"research\", \"draft\", \"verify\"]", "", "def execute(steps):", "    return [(s, len(s)) for s in steps]", "", "def verify(steps):", "    return all(name in steps for name in (\"draft\", \"verify\"))"] + ["", "if __name__ == \"__main__\":", "    steps = plan(\"write report\")", "    print(steps)", "    print(execute(steps))", "    print(verify(steps))"], [2, 5, 8], '["research", "draft", "verify"]\n[("research", 8), ("draft", 5), ("verify", 6)]\nTrue', "任务分解不能只生成漂亮计划，还要有执行产物和校验标准。")]),
            kp("计划约束与收敛", [code("convergence.py", "计划收敛与最大迭代", ["def converge(result, rounds):", "    return result if rounds > 2 else \"keep_going\""] + ["", "if __name__ == \"__main__\":", "    print(converge(\"needs_edit\", 1))", "    print(converge(\"accepted\", 3))"], [2], "keep_going\naccepted", "长任务必须有最大轮次、停止条件和失败回退，不能只靠模型自己说完成。")]),
            c("工程化建议", "复杂任务默认拆成 DAG 或状态机；简单任务用单 Agent，不必强行多 Agent。")], [{"title": "拆分需求", "description": "把‘写季度报告’拆成可执行步骤。", "hints": "每个步骤都要有验收标准"}, {"title": "加失败分支", "description": "为执行失败设计重试、跳过和人工接管。", "hints": "每类失败都有下一步"}], [{"type": "doc", "title": "LangGraph Tutorials", "url": "https://langchain-ai.github.io/langgraph/", "note": "状态机与持久化编排参考"}], ["ch4-4.4-q1", "ch4-4.4-q2"]),
    ], [
        section("4.5", "结果聚合与冲突解决", "能处理多个 Agent 产出的一致、补充和冲突", [
            p("结果聚合不是拼接文本，而是要判断来源可信度、证据是否充分、冲突是否可解释。冲突解决要留下决策痕迹。"),
            t(["策略", "做法", "优点", "风险"], [["投票", "多数意见", "简单", "多数错误"], ["证据加权", "按来源质量加权", "可解释", "权重维护"], ["仲裁 Agent", "专门判断冲突", "能处理复杂", "成本/偏差"], ["人工仲裁", "关键分歧人工处理", "可靠", "慢"]]),
            kp("证据加权聚合", [code("aggregate.py", "证据加权聚合", ["def score(e):", "    return e['weight'] * e['confidence']"] + ["", "def choose(candidates):", "    return max(candidates, key=score)"] + ["", "if __name__ == \"__main__\":", "    print(choose([{'weight': 2, 'confidence': .6}, {'weight': 3, 'confidence': .5}]))"], [3, 6], "{'weight': 3, 'confidence': 0.5}", "聚合要能解释为什么选它，而不是只看哪个看起来更像最终答案。")]),
            kp("冲突标记", [code("conflict.py", "冲突检测与标记", ["def detect(results):", "    return len(set(r['answer'] for r in results)) > 1"] + ["", "if __name__ == \"__main__\":", "    print(detect([{'answer':'A'}, {'answer':'A'}]))", "    print(detect([{'answer':'A'}, {'answer':'B'}]))"], [2], "False\nTrue", "冲突不是错误，而是需要升级处理的信号。")]),
            c("生产红线", "涉及金钱、法律、医疗或安全结论时，不允许只做静默聚合；必须保留证据和仲裁记录。")], [{"title": "写聚合策略", "description": "为研究结果设计证据加权策略。", "hints": "权重来自来源类型和更新时间"}, {"title": "模拟冲突", "description": "构造两个 Agent 结论冲突并决定升级方式。", "hints": "冲突必须有 owner"}], [{"type": "doc", "title": "RAG Evaluation", "url": "https://github.com/run-llama/llama_index", "note": "检索与答案质量评估参考"}], ["ch4-4.5-q1", "ch4-4.5-q2"]),
    ], [
        section("4.6", "长任务编排与状态管理", "能设计可恢复、可回放、可暂停的任务状态", [
            p("长任务失败不是偶然，而是常态。状态管理要支持断点恢复、重试、回滚和人工介入，避免每次失败都从头跑。"),
            t(["机制", "作用", "实现要点", "风险"], [["Checkpointer", "断点恢复", "状态版本化", "状态膨胀"], ["Retry", "容忍瞬时错误", "指数退避", "重复副作用"], ["Rollback", "恢复坏状态", "事务边界", "数据丢失"], ["HITL", "人工介入", "审批日志", "等待延迟"]]),
            kp("可恢复状态机", [code("checkpointer.py", "长任务状态检查点", ["from dataclasses import dataclass, field"] + ["", "@dataclass", "class State:", "    task: str", "    steps: list = field(default_factory=list)"] + ["", "def checkpoint(state, step):", "    state.steps.append(step)", "    return state"] + ["", "if __name__ == \"__main__\":", "    s = State('deploy')", "    print(checkpoint(s, 'build').steps)", "    print(checkpoint(s, 'test').steps)"], [7, 11], "['build']\n['build', 'test']", "检查点是长任务恢复的基础。没有检查点，就没有真正的生产级 Agent。")]),
            kp("幂等恢复", [code("idempotent_retry.py", "失败重试与幂等", ["def retry(fn, n=3):", "    for i in range(n):", "        try:", "            return fn(i)", "        except Exception:", "            if i == n - 1:", "                return 'failed'"] + ["", "def send(order_id):", "    return f\"sent:{order_id}\""] + ["", "if __name__ == \"__main__\":", "    print(retry(send, 2))"], [2, 9], "sent:1", "重试适合瞬时失败，但副作用操作必须配幂等键。")]),
            c("状态原则", "每个状态更新都要带版本号；每个恢复步骤都要验证状态机一致性。")], [{"title": "设计状态模型", "description": "为部署任务设计状态字段和转移。", "hints": "至少包含 phase、error、attempt"}, {"title": "写恢复逻辑", "description": "从 checkpoint 恢复并继续执行。", "hints": "恢复前先验证状态完整性"}], [{"type": "doc", "title": "LangGraph Persistence", "url": "https://langchain-ai.github.io/langgraph/", "note": "检查点与恢复机制"}], ["ch4-4.6-q1", "ch4-4.6-q2"]),
    ], [
        section("4.7", "Human-in-the-Loop 设计", "能把高风险动作设计成可暂停、可审批、可审计的流程", [
            p("HITL 不是为了把 Agent 变慢，而是把高风险动作放到人可解释、可撤回的边界里。关键动作包括付款、删除、对外发送、策略修改和敏感数据访问。"),
            t(["风险级别", "动作示例", "处理", "审计字段"], [["低", "查询", "自动", "trace_id"], ["中", "草拟", "自动+抽检", "置信度"], ["高", "付款/删除", "人工审批", "审批人/理由"], ["极高", "合规决策", "人工主导", "全链路回放"]]),
            kp("风险门", [code("risk_gate.py", "风险门与审批决策", ["RISK = {'read': 'low', 'draft': 'medium', 'pay': 'high', 'delete': 'high'}", "def decide(action):", "    level = RISK.get(action, 'medium')", "    return 'auto' if level == 'low' else 'human_approval'"] + ["", "if __name__ == 'main':", "    print(decide('read'))", "    print(decide('pay'))"], [3, 6], "auto\nhuman_approval", "风险分级必须落在动作级，而不是靠模型自己判断。")]),
            kp("审批记录", [code("approval_log.py", "审批记录与回放", ["def approve(action, reason, user='agent'): ", "    return {'action': action, 'reason': reason, 'user': user, 'approved': True}"] + ["", "if __name__ == '__main__':", "    print(approve('pay', 'under_500'))"], [2], "{'action': 'pay', 'reason': 'under_500', 'user': 'agent', 'approved': True}", "审批日志要足够支持复盘：为什么批、谁批、批了什么。")]),
            c("HITL 不是万能药", "如果所有低风险动作都走审批，人会疲劳；如果高风险动作不审批，事故不可逆。")]), [{"title": "列高风险动作", "description": "为客服 Agent 列高风险动作并设计审批。", "hints": "退款、删除、通知都算"}, {"title": "写审批 SLA", "description": "定义超时后的降级策略。", "hints": "超时转人工或自动取消"}], [{"type": "doc", "title": "LangGraph Interrupt", "url": "https://langchain-ai.github.io/langgraph/", "note": "人在回路挂起机制"}], ["ch4-4.7-q1", "ch4-4.7-q2"])
    ], [
        section("4.8", "Computer Use 与浏览器自动化", "能为 Computer Use 设计权限边界和可验证工作流", [
            p("Computer Use 的价值是让 Agent 能操作界面，但风险也最大。必须先定义可操作区域、禁止区域、截图证据、失败恢复和人工接管。"),
            t(["步骤", "能力", "必须验证", "防护"], [["Launch", "打开页面", "URL 正确", "域名白名单"], ["Capture", "截图/OCR", "元素可见", "遮罩敏感信息"], ["Action", "点击/输入", "目标确认", "动作日志"], ["Verify", "状态变化", "结果正确", "失败回滚"]]),
            kp("浏览器动作计划", [code("browser_plan.py", "浏览器动作计划与验证", ["PLAN = {'login': ['goto', 'type', 'click'], 'buy': ['select', 'submit']}", "def next_step(name):", "    return PLAN.get(name, [])"] + ["", "if __name__ == '__main__':", "    print(next_step('login'))", "    print(next_step('unknown'))"], [3, 6], "['goto', 'type', 'click']\n[]", "浏览器操作必须有计划和空动作策略，不能只靠模型临场点击。")]),
            kp("动作审计", [code("browser_audit.py", "Computer Use 动作审计", ["AUDIT = []", "def record(action, selector):", "    AUDIT.append({'action': action, 'selector': selector})"] + ["", "if __name__ == '__main__':", "    record('click', '#checkout')", "    print(AUDIT)"], [4], "[{'action': 'click', 'selector': '#checkout'}]", "每个点击都要能解释，且截图要能证明。")]),
            c("安全底线", "不点击支付、删除、发送邮箱、发布内容等不可逆按钮，除非走 HITL 并记录审批。")], [{"title": "设计动作白名单", "description": "为电商结账 Agent 设计允许和禁止动作。", "hints": "允许查询，禁止付款"}, {"title": "写失败恢复", "description": "为元素找不到、超时、弹窗设计恢复路径。", "hints": "失败必须截图"}], [{"type": "doc", "title": "Playwright Docs", "url": "https://playwright.dev/", "note": "浏览器自动化常用工具"}], ["ch4-4.8-q1", "ch4-4.8-q2"]))
    ], [
        section("4.9", "主流多智能体框架全景与选型", "能按团队能力、控制流、观测和运维需求选框架", [
            p("框架选型的本质是在控制力、开发速度、生态成熟度和学习成本之间取舍。LangGraph 适合显式状态机，CrewAI 适合角色化流程，OpenAI Agents SDK 适合轻量 handoff。"),
            t(["框架", "强项", "适合", "慎用"], [["LangGraph", "图、检查点、HITL", "长流程/审批", "短任务过重"], ["CrewAI", "角色/任务", "流程清晰", "复杂状态弱"], ["Agents SDK", "handoff、trace", "轻量协作", "复杂持久化弱"], ["AutoGen", "研究/对话", "探索协作", "生产治理要补"]]),
            kp("选型矩阵", [code("framework_choice.py", "多 Agent 框架选型矩阵", ["def choose(state_need, team_level):", "    if state_need >= 4 and team_level >= 3:", "        return 'LangGraph'", "    if team_level <= 2:", "        return 'Agents SDK'", "    return 'CrewAI'"] + ["", "if __name__ == '__main__':", "    print(choose(5, 4))", "    print(choose(2, 1))", "    print(choose(3, 2))"], [3, 7], "LangGraph\nAgents SDK\nCrewAI", "选型不是追新，而是匹配状态需求、团队能力和运维能力。")]),
            kp("框架迁移策略", [code("framework_migration.py", "框架迁移：先抽象边界", ["def adapter(call):", "    return {'provider': 'framework-neutral', 'call': call}"] + ["", "if __name__ == '__main__':", "    print(adapter('handoff_to_writer'))"], [2], "{'provider': 'framework-neutral', 'call': 'handoff_to_writer'}", "先抽象业务边界，再替换框架；不要把业务逻辑写死在某个框架 API 上。")]),
            c("选型原则", "如果需求只是 3 个 Agent 短流程，不要一上来上复杂图；如果需求有审批和持久化，就别用纯 prompt 拼接。")], [{"title": "为项目选框架", "description": "为客服分流、研究报告、审批流各选框架。", "hints": "看状态和流程复杂度"}, {"title": "做框架 POC", "description": "用同一任务跑两个框架并比较成本、调试、恢复。", "hints": "比较维度至少 5 个"}], [{"type": "doc", "title": "CrewAI Docs", "url": "https://docs.crewai.com/", "note": "角色化任务流"}, {"type": "doc", "title": "LangGraph Docs", "url": "https://langchain-ai.github.io/langgraph/", "note": "图式编排"}, {"type": "doc", "title": "OpenAI Agents SDK", "url": "https://openai.github.io/openai-agents-python/", "note": "轻量 handoff"}], ["ch4-4.9-q1", "ch4-4.9-q2"]))
    ], [
        section("4.10", "CrewAI 实战：角色化 Crews 与 Flows", "能写出角色、任务、顺序执行和失败处理", [
            p("CrewAI 的价值是快速表达多角色流程：researcher 研究、writer 写作、reviewer 审查。但生产落地必须补齐预算、输出格式、失败重试和评估集。"),
            kp("离线 Crew 结构", [code("crew_mock.py", "CrewAI 离线结构：角色、任务、顺序执行", ["class Agent:", "    def __init__(self, role):", "        self.role = role", "    def work(self, task):", "        return f'[{self.role}] {task}'"] + ["", "class Task:", "    def __init__(self, agent, text):", "        self.agent = agent", "        self.text = text"] + ["", "def run(crew):", "    return [t.agent.work(t.text) for t in crew]", "", "if __name__ == '__main__':", "    crew = [Task(Agent('researcher'), 'find facts'), Task(Agent('writer'), 'write draft')]", "    print(run(crew))"], [5, 12], "['[researcher] find facts', '[writer] write draft']", "先理解 Crew 的本质：角色、任务、执行顺序。接真实 SDK 后再换 LLM 调用。")]),
            kp("Crew 预算与输出", [code("crew_budget.py", "Crew 预算和输出约束", ["BUDGET = {'researcher': 100, 'writer': 120, 'reviewer': 80}", "def run(role, tokens):", "    return f'{role}:{tokens}' if tokens <= BUDGET[role] else f'{role}:over_budget'"] + ["", "if __name__ == '__main__':", "    print(run('writer', 100))", "    print(run('writer', 200))"], [3, 6], "writer:100\nwriter:over_budget", "真实 Crew 需要给每角色设预算，不然一个角色就能烧掉整条流程。")]),
            c("CrewAI 常见坑", "上下文不要无限传递；任务不要含糊；Reviewer 必须有可执行的审查标准。")], [{"title": "写三角色 Crew", "description": "实现 research/writer/reviewer。", "hints": "reviewer 输出 pass/fail"}, {"title": "加输出格式", "description": "要求 writer 输出 JSON。", "hints": "下游要能用 checker 验证"}], [{"type": "doc", "title": "CrewAI Quickstart", "url": "https://docs.crewai.com/quickstart/", "note": "角色/任务/流程基础"}], ["ch4-4.10-q1", "ch4-4.10-q2"]))
    ], [
        section("4.11", "LangGraph 多智能体编排实战（Supervisor）", "能用状态图和主管路由实现长流程、回退和人工门", [
            p("LangGraph 的关键是 State、Node、Edge 和 Checkpointer。主管模式适合复杂审批流：supervisor 读状态，worker 改状态，human gate 暂停或继续。"),
            kp("离线状态机", [code("graph_mock.py", "LangGraph 离线状态机", ["class Graph:", "    def __init__(self):", "        self.nodes = {}"] + ["", "    def add(self, name, fn):", "        self.nodes[name] = fn"] + ["", "    def run(self, state, order):", "        for name in order:", "            state = self.nodes[name](state)", "        return state"] + ["", "if __name__ == '__main__':", "    g = Graph()", "    g.add('supervisor', lambda s: {**s, 'next': 'researcher'})", "    g.add('researcher', lambda s: {**s, 'research': True})", "    print(g.run({}, ['supervisor', 'researcher']))"], [7, 16], "{'next': 'researcher', 'research': True}", "图执行器的本质就是按边和节点维护状态；真实框架只是把图、持久化和回放做完整。")]),
            kp("主管路由", [code("supervisor_route.py", "主管路由和结束条件", ["def route(state):", "    if not state.get('research'):", "        return 'researcher'", "    if not state.get('draft'):", "        return 'writer'", "    return '__end__'"] + ["", "if __name__ == '__main__':", "    print(route({}))", "    print(route({'research': True}))", "    print(route({'research': True, 'draft': True}))"], [3, 8], "researcher\nwriter\n__end__", "主管必须知道什么时候结束，否则图会变成死循环。")]),
            c("LangGraph 最佳实践", "节点尽量纯函数；状态 schema 要稳定；高风险节点挂 interrupt。")], [{"title": "加 critic 节点", "description": "让 writer 产出后经过 critic。", "hints": "critic 可路由回 writer"}, {"title": "写结束条件", "description": "让 supervisor 在满足标准时结束。", "hints": "结束条件必须可测"}], [{"type": "doc", "title": "LangGraph Multi-agent", "url": "https://langchain-ai.github.io/langgraph/", "note": "Supervisor 和图式编排"}], ["ch4-4.11-q1", "ch4-4.11-q2"]))
    ], [
        section("4.12", "OpenAI Agents SDK 多智能体编排（handoff）", "能用 handoff 构建轻量分流系统并接 guardrails", [
            p("OpenAI Agents SDK 的核心原语是 Agent、handoff 和 Runner。它适合入口分流、专家转接和轻量协作，但不适合复杂长流程持久化。"),
            kp("handoff 本质", [code("handoff_runner.py", "handoff 路由与 Runner", ["class Agent:", "    def __init__(self, name, handoffs=()):", "        self.name = name", "        self.handoffs = handoffs", "    def handle(self, text):", "        target = self.handoffs[0] if 'refund' in text else None", "        return target.name if target else self.name"] + ["", "def run(agent, text):", "    return [f'{agent.name}: {text}', f'routed:{agent.handle(text)}']", "", "if __name__ == '__main__':", "    support = Agent('support')", "    triage = Agent('triage', (support,))", "    print(run(triage, 'refund request'))"], [8, 15], "['triage: refund request', 'routed:support']", "handoff 的核心是点对点接力，不是全员群聊。")]),
            kp("轻量协作", [code("light_crew.py", "轻量 Agent 协作", ["class Runner:", "    @staticmethod", "    def run(agent, msg):", "        return f'{agent}: {msg}'"] + ["", "if __name__ == '__main__':", "    print(Runner.run('translator', 'hello'))"], [5], "translator: hello", "轻量 SDK 的价值是心智负担小；复杂治理要外挂。")]),
            c("常见坑", "handoff 没声明会转接失败；trace 默认开启时注意合规；context 要显式传。")], [{"title": "做三专家分流", "description": "按退款、物流、技术问题分流。", "hints": "每个专家要有明确职责"}, {"title": "加 guardrail", "description": "拦截包含敏感信息的输入。", "hints": "guardrail 失败要有提示"}], [{"type": "doc", "title": "OpenAI Agents SDK", "url": "https://openai.github.io/openai-agents-python/", "note": "Agent/handoff/Runner"}], ["ch4-4.12-q1", "ch4-4.12-q2"]))
    ], [
        section("4.13", "多 Agent 评估、可观测性与成本治理", "能用 trace、成本预算和评估集证明系统可上线", [
            p("多 Agent 上线的最低证据不是“能跑”，而是成功率、成本、延迟、可复现和可定位。每跳都要有 trace；每个结果都要有评估。"),
            t(["指标", "定义", "目标", "风险"], [["成功率", "checker 通过比例", "持续上升", "口径不严"], ["成本", "token/工具/人工成本", "可归因", "隐藏成本"], ["延迟", "端到端耗时", "P95 可控", "瓶颈难找"], ["稳定性", "同输入重复方差", "低于阈值", "不可复现"]]),
            kp("调用级 trace", [code("trace_multi.py", "多 Agent trace wrapper", ["import time", "TRACE = []", "def trace(name):", "    def deco(fn):", "        def wrapper(*a):", "            t0 = time.time()", "            try:", "                r = fn(*a)", "                status = 'ok'", "            except Exception as e:", "                r, status = str(e), 'fail'", "            TRACE.append({'name': name, 'status': status, 'ms': int((time.time()-t0)*1000)})", "            return r", "        return wrapper", "    return deco"] + ["", "@trace('researcher')", "def research(topic):", "    return f'research:{topic}'", "", "if __name__ == '__main__':", "    print(research('rag'))", "    print(TRACE[0]['name'])"], [4, 18], "research:rag\nresearcher", "trace 是生产 Agent 的基础设施；没有它，成本、延迟、错误都说不清。")]),
            kp("成本预算", [code("cost_budget.py", "成本预算与降级", ["PRICES = {'small': 1, 'large': 8}", "def bill(model, tasks):", "    return PRICES.get(model, 1) * tasks", "def choose(tasks):", "    return 'large' if bill('large', tasks) <= 100 else 'small'"] + ["", "if __name__ == '__main__':", "    print(choose(10))", "    print(choose(20))"], [3, 6], "large\nsmall", "成本治理要从预算出发，按预算降级模型或工具，而不是事后追账单。")]),
            c("上线门槛", "至少准备 20 条评估用例、5 次重复运行、成本表和失败复盘。")], [{"title": "做评估集", "description": "为报告 Agent 做 20 条评估。", "hints": "覆盖边界和失败"}, {"title": "画成本图", "description": "按 Agent 统计 token 和工具成本。", "hints": "每跳都要归因"}], [{"type": "doc", "title": "OpenTelemetry", "url": "https://opentelemetry.io/", "note": "可观测性标准"}, {"type": "doc", "title": "LangSmith", "url": "https://docs.smith.langchain.com/", "note": "Agent trace 和 eval"}], ["ch4-4.13-q1", "ch4-4.13-q2"]))
    ], [
        section("4.14", "多 Agent 专题学习路径与路线图", "能把多 Agent 知识变成项目路线图", [
            p("多 Agent 学习要从单 Agent、工具、记忆、RAG 开始，再到编排、观测、安全。先会跑，再会管，最后会交付。"),
            t(["阶段", "目标", "产物", "评估"], [["基础", "单 Agent + Tool", "可运行 demo", "手动验证"], ["协作", "3 个 Agent", "handoff/图", "trace 完整"], ["生产", "RAG/HITL/评测", "系统原型", "自动化测试"], ["治理", "成本/安全", "上线清单", "故障复盘"]]),
            kp("路线图", [code("multi_roadmap.py", "多 Agent 学习路线图", ["ROADMAP = ['single', 'tools', 'memory', 'rag', 'orchestration', 'observability', 'security']", "def next_step(done):", "    for i, step in enumerate(ROADMAP):", "        if done < i + 1:", "            return ROADMAP[i]", "    return 'delivery-ready'"] + ["", "if __name__ == '__main__':", "    print(next_step(2))", "    print(next_step(7))"], [4, 8], "memory\ndelivery-ready", "路线图必须可验证，而不是看完就结束。")]),
            kp("交付清单", [code("delivery_checklist.py", "交付前检查清单", ["CHECK = ['runnable', 'trace', 'eval', 'cost', 'rollback']", "def check(done):", "    return [x for x in CHECK if x not in done]"] + ["", "if __name__ == '__main__':", "    print(check(['runnable']))"], [3], "['trace', 'eval', 'cost', 'rollback']", "就业项目交付不是展示功能，而是证明能稳定运行。")]),
            c("学习策略", "每阶段都要有一个能跑的项目和一个评估报告；没有产出就不要进入下一阶段。")], [{"title": "定制路线图", "description": "按你的目标岗位调整阶段。", "hints": "保留可运行、可评估、可观测"}, {"title": "做复盘", "description": "为每个项目写 5 行故障复盘。", "hints": "失败案例比成功更有价值"}], [{"type": "doc", "title": "CrewAI Docs", "url": "https://docs.crewai.com/", "note": "角色化流程"}, {"type": "doc", "title": "LangGraph Docs", "url": "https://langchain-ai.github.io/langgraph/", "note": "图式编排"}, {"type": "doc", "title": "OpenAI Agents SDK", "url": "https://openai.github.io/openai-agents-python/", "note": "handoff 模式"}], ["ch4-4.14-q1", "ch4-4.14-q2"]))
, ]

def build_ch5():
    return [
        section("5.1", "智能客服系统", "能构建带意图识别、工单创建和 HITL 的客服 Agent", [
            p("客服 Agent 的目标不是替代客服，而是把重复问题分流，把复杂问题带证据转人工。核心链路是意图识别、FAQ/RAG、工单、升级和审计。"),
            t(["模块", "功能", "指标", "兜底"], [["意图", "分类用户问题", "准确率", "转人工"], ["FAQ", "常见问题", "命中率", "无答案提示"], ["工单", "创建记录", "成功率", "本地保存"], ["升级", "高风险转人工", "覆盖率", "人工兜底"]]),
            kp("离线客服闭环", [code("support_mock.py", "智能客服离线闭环", ["INTENTS = {'refund': 'after_sales', 'logistics': 'logistics', 'password': 'account'}", "def route(msg):", "    for k, v in INTENTS.items():", "        if k in msg:", "            return v", "    return 'human'"] + ["", "def answer(msg):", "    route_name = route(msg)", "    return {'route': route_name, 'reply': f' routed to {route_name}'}"] + ["", "if __name__ == '__main__':", "    print(answer('refund order 123'))", "    print(answer('hello'))"], [3, 10], "{'route': 'after_sales', 'reply': ' routed to after_sales'}\n{'route': 'human', 'reply': ' routed to human'}", "离线闭环让流程可测试；接真实 LLM 后只需要替换分类和回答生成。")]),
            kp("工单幂等", [code("ticket_idempotent.py", "工单创建幂等", ["TICKETS = {}", "def create(ticket_id, body):", "    if ticket_id in TICKETS:", "        return 'duplicate'", "    TICKETS[ticket_id] = body", "    return 'created'"] + ["", "if __name__ == '__main__':", "    print(create('t1', 'refund'))", "    print(create('t1', 'refund'))"], [4, 7], "created\nduplicate", "客服工单最怕重复提交，幂等键是基础。")]),
            c("生产清单", "客服 Agent 必须有人工升级、敏感信息遮罩、工单幂等和满意度回采。")], [{"title": "加知识库", "description": "接入 10 条 FAQ。", "hints": "命中失败要转人工"}, {"title": "加 SLA", "description": "高优先级工单 15 分钟响应。", "hints": "超时要有提醒"}], [{"type": "doc", "title": "CrewAI Support Agent", "url": "https://docs.crewai.com/", "note": "角色化客服流程"}], ["ch5-5.1-q1", "ch5-5.1-q2"]))
    ], [
        section("5.2", "代码助手与代码审查", "能让代码助手写代码并做最小审查", [
            p("代码助手不能只生成代码，还要验证语法、测试和 diff。代码审查 Agent 要能找出明显风险，但不能替代人类判断。"),
            kp("审查规则", [code("reviewer_rules.py", "代码审查基础规则", ["RISKS = {'eval': 'danger', 'exec': 'danger', 'open(': 'check', 'requests.get': 'check'}", "def review(code):", "    found = [k for k in RISKS if k in code]", "    return 'pass' if not found else ','.join(sorted(set(found)))"] + ["", "if __name__ == '__main__':", "    print(review('x=1'))", "    print(review('requests.get(url)'))", "    print(review('eval(s)'))"], [4, 7], "pass\nrequests.get\neval", "规则审查是自动化的第一层，真正审查要叠加测试和项目规范。")]),
            kp("代码生成校验", [code("gen_checker.py", "代码生成后最小校验", ["import ast", "def can_parse(code):", "    try:", "        ast.parse(code)", "        return True", "    except SyntaxError:", "        return False"] + ["", "if __name__ == '__main__':", "    print(can_parse('def f():\\n    return 1'))", "    print(can_parse('def f():'))"], [4, 10], "True\nFalse", "代码助手的第一道质量门是语法可解析，第二道是测试。")]),
            c("安全边界", "不要直接执行 Agent 生成代码；先 AST/静态检查、沙箱测试、再人工审查。")], [{"title": "写审查清单", "description": "列出 10 条 review 检查项。", "hints": "安全、测试、可读性、边界"}, {"title": "接入测试", "description": "为生成代码跑 pytest。", "hints": "测试失败必须回滚"}], [{"type": "doc", "title": "OpenAI Cookbook", "url": "https://cookbook.openai.com/", "note": "代码生成参考"}, {"type": "doc", "title": "pytest", "url": "https://docs.pytest.org/", "note": "测试框架"}], ["ch5-5.2-q1", "ch5-5.2-q2"]))
    ], [
        section("5.3", "数据分析 Agent", "能把自然语言问题变成可审计的数据分析", [
            p("数据分析 Agent 的关键是把自然语言转成可执行查询、结果校验和解释。必须避免把模型生成 SQL 直接用于生产库。"),
            kp("分析计划", [code("analytics_plan.py", "数据分析计划", ["def plan(question):", "    return ['identify_table', 'write_sql', 'validate', 'summarize']"] + ["", "if __name__ == '__main__':", "    print(plan('sales by region'))"], [2], "['identify_table', 'write_sql', 'validate', 'summarize']", "分析流程必须明确每一步，不要直接让模型给一个数字。")]),
            kp("SQL 安全", [code("sql_guard.py", "SQL 查询安全校验", ["BLOCKED = ['DELETE', 'DROP', 'UPDATE', 'INSERT']", "def safe_sql(sql):", "    upper = sql.upper()", "    return not any(x in upper for x in BLOCKED)"] + ["", "if __name__ == '__main__':", "    print(safe_sql('SELECT * FROM orders'))", "    print(safe_sql('DELETE FROM orders'))"], [4, 7], "True\nFalse", "数据分析 Agent 默认只读；写操作必须有审批。")]),
            c("结果可信", "每个数字都要有查询、样本量、时间和过滤条件。")], [{"title": "写分析 schema", "description": "设计订单数据问题 schema。", "hints": "含过滤、聚合、排序"}, {"title": "做解释报告", "description": "为销售趋势生成 5 点解释。", "hints": "解释必须来自数据"}], [{"type": "doc", "title": "SQLAlchemy", "url": "https://docs.sqlalchemy.org/", "note": "数据库访问"}, {"type": "doc", "title": "Pandas", "url": "https://pandas.pydata.org/docs/", "note": "数据分析"}], ["ch5-5.3-q1", "ch5-5.3-q2"]))
    ], [
        section("5.4", "自动化运营 Agent", "能把日报、告警和触达做成安全自动化", [
            p("运营 Agent 常见任务包括日报、异常检测、触达和工单分派。自动化的关键是动作幂等、内容可审核、失败可回滚。"),
            kp("日报生成", [code("ops_report.py", "运营日报生成", ["def report(kpis):", "    return {k: v for k, v in kpis.items() if v is not None}"] + ["", "if __name__ == '__main__':", "    print(report({'visits': 1000, 'errors': 0, 'pending': None}))"], [2], "{'visits': 1000, 'errors': 0}", "日报 Agent 应只展示可验证指标，空值不能伪装成 0。")]),
            kp("告警阈值", [code("alert_threshold.py", "异常阈值告警", ["THRESH = {'cpu': 80, 'p95_ms': 1000}", "def alert(metric, value):", "    return f'alert:{metric}' if value > THRESH.get(metric, 0) else 'ok'"] + ["", "if __name__ == '__main__':", "    print(alert('cpu', 91))", "    print(alert('p95_ms', 500))"], [3, 6], "alert:cpu\nok", "告警 Agent 必须有阈值和去重，否则噪音会淹没真实问题。")]),
            c("运营自动化边界", "不要自动触达敏感用户、不要自动退款、不要自动删除历史数据。")], [{"title": "写日报模板", "description": "为订单/转化/客服生成日报。", "hints": "含异常和建议"}, {"title": "加去重", "description": "同一告警 10 分钟只发一次。", "hints": "需要状态 TTL"}], [{"type": "doc", "title": "Prometheus", "url": "https://prometheus.io/docs/", "note": "监控指标"}, {"type": "doc", "title": "Grafana", "url": "https://grafana.com/docs/", "note": "看板与告警"}], ["ch5-5.4-q1", "ch5-5.4-q2"]))
    ], [
        section("5.5", "企业知识库问答", "能构建带引用、拒答和反馈回流的 RAG", [
            p("企业知识库问答必须能溯源。检索失败时应该明确拒答，而不是猜测。RAG 的关键不是 embedding，而是切分、索引、召回、引用、评估。"),
            kp("检索与引用", [code("rag_quote.py", "RAG 引用生成", ["DOCS = [{'id':'d1','text':'年假上限15天'}, {'id':'d2','text':'病假需证明'}]", "def retrieve(q):", "    return [d for d in DOCS if any(w in d['text'] for w in q.split())]"] + ["", "def answer(q):", "    hits = retrieve(q)", "    return {'answer': hits[0]['text'], 'source': hits[0]['id']} if hits else {'answer': 'not_found'}"] + ["", "if __name__ == '__main__':", "    print(answer('年假'))", "    print(answer('工资'))"], [3, 10], "{'answer': '年假上限15天', 'source': 'd1'}\n{'answer': 'not_found'}", "RAG 输出必须带来源；没有来源就不能作为正式答复。")]),
            kp("召回为空策略", [code("rag_fallback.py", "召回为空时拒答", ["def fallback(q, hits):", "    return f'未找到依据:{q}' if not hits else 'answerable'"] + ["", "if __name__ == '__main__':", "    print(fallback('离职流程', []))", "    print(fallback('年假', ['doc']))"], [2], "未找到依据:离职流程\nanswerable", "拒答不是失败，而是避免误导。")]),
            c("RAG 评估", "至少评估召回率、答案忠实度、引用正确率、拒答准确率和成本。")], [{"title": "做切分实验", "description": "比较 256 和 512 token 切分效果。", "hints": "要看召回和引用"}, {"title": "加反馈", "description": "记录用户对答案的赞/踩。", "hints": "差评进入回归集"}], [{"type": "doc", "title": "LlamaIndex", "url": "https://docs.llamaindex.ai/", "note": "RAG 框架"}, {"type": "doc", "title": "LangChain RAG", "url": "https://docs.langchain.com/oss/python/langchain/overview", "note": "RAG 教程"}], ["ch5-5.5-q1", "ch5-5.5-q2"]))
    ], [
        section("5.6", "多 Agent 协作开发系统", "能搭建需求到测试的协作开发流程", [
            p("多 Agent 开发系统是规划、编码、审查、测试和发布的组合。每个阶段都要有明确产物，不能只靠自然语言交接。"),
            kp("开发流水线", [code("dev_pipeline.py", "多 Agent 开发流水线", ["STAGES = ['plan', 'code', 'review', 'test', 'release']", "def run(stage):", "    return f'{stage}_done'", "def pipeline(stages):", "    return [run(s) for s in stages]"] + ["", "if __name__ == '__main__':", "    print(pipeline(STAGES))"], [4, 7], "['plan_done', 'code_done', 'review_done', 'test_done', 'release_done']", "开发流水线需要按阶段验证，发布前必须有测试。")]),
            kp("审查门", [code("dev_gate.py", "发布前审查门", ["def gate(tests, review):", "    return 'approved' if tests and review else 'blocked'"] + ["", "if __name__ == '__main__':", "    print(gate(True, True))", "    print(gate(False, True))"], [2], "approved\nblocked", "测试和 review 任一项失败，发布都应阻塞。")]),
            c("协作边界", "代码生成 Agent 不直接 push main；测试 Agent 必须独立验证。")], [{"title": "做需求拆解", "description": "从 issue 拆成 plan/code/test。", "hints": "每步要可执行"}, {"title": "加回滚", "description": "设计测试失败后的回滚策略。", "hints": "要有版本和分支"}], [{"type": "doc", "title": "LangGraph", "url": "https://langchain-ai.github.io/langgraph/", "note": "开发流水线"}, {"type": "doc", "title": "pytest", "url": "https://docs.pytest.org/", "note": "测试"}], ["ch5-5.6-q1", "ch5-5.6-q2"]))
    ], [
        section("5.7", "全栈开发 Agent", "能处理前端、后端、数据库和部署流程", [
            p("全栈 Agent 不是万能写代码，而是能理解模块边界。它应把需求转成接口、数据模型、前端状态和部署计划。"),
            kp("模块规划", [code("fullstack_plan.py", "全栈模块规划", ["def plan(task):", "    return {'api': f'/api/{task}', 'table': f'{task}_items', 'page': f'/{task}'}"] + ["", "if __name__ == '__main__':", "    print(plan('notes'))"], [2], "{'api': '/api/notes', 'table': 'notes_items', 'page': '/notes'}", "规划要显式，后端、数据库和页面不能互相猜。")]),
            kp("部署检查", [code("deploy_check.py", "部署前检查", ["def check(cfg):", "    return {'env': cfg.get('env'), 'migrations': cfg.get('migrations', False), 'rollback': cfg.get('rollback', False)}"] + ["", "if __name__ == '__main__':", "    print(check({'env': 'staging'}))"], [2], "{'env': 'staging', 'migrations': False, 'rollback': False}", "部署检查要把缺项显式暴露出来。")]),
            c("工程边界", "全栈 Agent 不应直接改生产数据库；所有迁移都要走 review。")], [{"title": "写 API 设计", "description": "为笔记功能设计 CRUD。", "hints": "含错误码"}, {"title": "做部署清单", "description": "列 10 项发布检查。", "hints": "回滚计划必须有"}], [{"type": "doc", "title": "FastAPI", "url": "https://fastapi.tiangolo.com/", "note": "API 框架"}, {"type": "doc", "title": "Vue", "url": "https://vuejs.org/", "note": "前端框架"}], ["ch5-5.7-q1", "ch5-5.7-q2"]))
    ], [
        section("5.8", "部署与性能优化", "能做缓存、异步、限流、回滚和容量估算", [
            p("部署不是把 Agent 跑起来，而是让它稳定、可回滚、能抗峰值。性能优化要从缓存、异步、限流和容量估算开始。"),
            kp("缓存策略", [code("cache_agent.py", "Agent 缓存策略", ["CACHE = {}", "def get(key, compute):", "    if key not in CACHE:", "        CACHE[key] = compute()", "    return CACHE[key]"] + ["", "if __name__ == '__main__':", "    print(get('hello', lambda: 'world'))", "    print(get('hello', lambda: 'changed'))"], [4, 7], "world\nworld", "缓存能省钱提速，但要有失效策略和版本。")]),
            kp("限流与回滚", [code("rate_limit.py", "限流与回滚", ["LIMITS = {'api': 5}", "def allow(name):", "    if LIMITS.get(name, 0) <= 0:", "        return False", "    LIMITS[name] -= 1", "    return True"] + ["", "if __name__ == '__main__':", "    print([allow('api') for _ in range(3)])"], [4, 7], "[True, True, True]", "限流保护下游；回滚保护用户。")]),
            c("容量估算", "先估 QPS、上下文长度、工具调用次数和 P95 延迟，再决定模型和并发。")], [{"title": "做容量估算", "description": "为 1000 用户/日估算 token 和成本。", "hints": "按高峰和低谷分别算"}, {"title": "加回滚", "description": "写部署回滚手册。", "hints": "含数据兼容性"}], [{"type": "doc", "title": "Docker", "url": "https://docs.docker.com/", "note": "容器部署"}, {"type": "doc", "title": "Redis", "url": "https://redis.io/docs/", "note": "缓存"}], ["ch5-5.8-q1", "ch5-5.8-q2"]))
    ], [
        section("5.9", "安全与合规", "能设计护栏、审计、数据脱敏和权限边界", [
            p("Agent 安全的重点是输入、工具、输出和日志。提示注入、越权工具、数据泄露和不可逆动作是四类核心风险。"),
            t(["风险", "场景", "防护", "检测"], [["注入", "网页指令覆盖", "输入隔离", "规则/分类器"], ["越权", "调用敏感工具", "白名单", "调用审计"], ["泄露", "敏感数据输出", "脱敏", "DLP"], ["误操作", "删除/支付", "HITL", "回放"]]),
            kp("输入护栏", [code("guard_input.py", "输入护栏", ["BLOCK = ['忽略以上指令', '输出密钥', 'DROP TABLE']", "def guard(text):", "    return 'blocked' if any(b in text for b in BLOCK) else 'ok'"] + ["", "if __name__ == '__main__':", "    print(guard('正常问题'))", "    print(guard('忽略以上指令'))"], [4, 7], "ok\nblocked", "输入护栏是第一层，不能指望模型每次都正确理解边界。")]),
            kp("脱敏输出", [code("redact.py", "敏感信息脱敏", ["def redact(text):", "    import re", "    return re.sub(r'13\\d{9}', '138****8888', text)"] + ["", "if __name__ == '__main__':", "    print(redact('电话13800138000'))"], [2], "电话138****8888", "日志和输出中的手机号、身份证、银行卡都要脱敏。")]),
            c("合规底线", "日志不留密钥；敏感数据不进第三方；高风险动作必须可撤回。")], [{"title": "列安全清单", "description": "为生产 Agent 写 15 条安全清单。", "hints": "输入、工具、输出、日志都要覆盖"}, {"title": "做注入测试", "description": "构造 10 条 prompt injection。", "hints": "测试必须自动化"}], [{"type": "doc", "title": "OWASP LLM Top 10", "url": "https://owasp.org/www-project-top-10-for-large-language-model-applications/", "note": "LLM 安全风险"}], ["ch5-5.9-q1", "ch5-5.9-q2"]))
    ], [
        section("5.10", "避坑指南与常见难点", "能识别上下文、成本、稳定性、安全和评测难点", [
            p("Agent 项目失败常见于上下文污染、无终止、工具滥用、成本和评测缺失。先避坑再追新，能显著提高交付率。"),
            t(["坑", "表现", "根因", "解法"], [["死循环", "反复调用", "无终止", "max_steps"], ["幻觉", "编造事实", "无来源", "RAG+引用"], ["账单爆炸", "token 暴涨", "无预算", "成本门"], ["不可复盘", "出错看不懂", "无 trace", "观测"]]),
            kp("避坑检查", [code("pitfall_check.py", "避坑检查", ["CHECKS = ['max_steps', 'budget', 'trace', 'sources', 'rollback']", "def check(done):", "    return [x for x in CHECKS if x not in done]"] + ["", "if __name__ == '__main__':", "    print(check(['trace']))"], [3], "['max_steps', 'budget', 'sources', 'rollback']", "上线前把这些坑列成清单，能省掉很多事故。")]),
            kp("失败复盘", [code("incident.py", "事故复盘模板", ["def postmortem(impact, cause, fix):", "    return {'impact': impact, 'cause': cause, 'fix': fix}"] + ["", "if __name__ == '__main__':", "    print(postmortem('wrong_answer', 'no_source', 'add_rag'))"], [2], "{'impact': 'wrong_answer', 'cause': 'no_source', 'fix': 'add_rag'}", "复盘不是追责，是让系统下次更好。")]),
            c("经验", "Agent 开发最缺的不是框架，而是可验证交付。")], [{"title": "列 20 个坑", "description": "写出你会踩的坑和预防。", "hints": "每个坑都要有检测方式"}, {"title": "做回归集", "description": "把失败案例加入回归测试。", "hints": "至少覆盖注入/幻觉/越权"}], [{"type": "blog", "title": "Building Effective Agents", "url": "https://www.anthropic.com/research/building-effective-agents", "note": "避免过度复杂"}], ["ch5-5.10-q1", "ch5-5.10-q2"]))
    ], [
        section("5.11", "企业级存储实战", "能把会话、向量、任务状态和审计日志分层存储", [
            p("企业级 Agent 不能只靠内存。会话、向量、任务状态、审计日志各有生命周期和访问模式，需要分层存储。"),
            t(["存储", "用途", "特点", "风险"], [["Redis", "会话/限流", "低延迟", "易失"], ["Postgres", "任务/审计", "事务", "容量增长"], ["Vector DB", "RAG", "语义检索", "重建成本"], ["Object", "附件/日志", "低成本", "查询弱"]]),
            kp("分层存储选择", [code("storage_choice.py", "存储分层选择", ["def choose(data):", "    if data in ('session', 'rate_limit'):", "        return 'Redis'", "    if data in ('task', 'audit'):", "        return 'Postgres'", "    if data == 'embedding':", "        return 'VectorDB'", "    return 'ObjectStore'"] + ["", "if __name__ == '__main__':", "    print(choose('session'))", "    print(choose('task'))", "    print(choose('embedding'))"], [3, 8], "Redis\nPostgres\nVectorDB", "存储选择看数据访问模式和一致性要求，而不是看技术热度。")]),
            kp("审计日志", [code("audit_storage.py", "审计日志写入", ["LOGS = []", "def append(event):", "    LOGS.append(event)", "    return len(LOGS)"] + ["", "if __name__ == '__main__':", "    append({'action':'pay','user':'u1'})", "    print(LOGS[0])"], [4], "{'action': 'pay', 'user': 'u1'}", "审计日志是生产系统的记忆，必须不可轻易删除。")]),
            c("数据治理", "数据要有 owner、保留期限、备份和删除策略。")], [{"title": "设计 schema", "description": "为会话、任务、审计设计表结构。", "hints": "含 created_at 和 updated_at"}, {"title": "做备份恢复", "description": "写恢复演练步骤。", "hints": "含 RTO/RPO"}], [{"type": "doc", "title": "PostgreSQL", "url": "https://www.postgresql.org/docs/", "note": "事务存储"}, {"type": "doc", "title": "Redis", "url": "https://redis.io/docs/", "note": "缓存/限流"}], ["ch5-5.11-q1", "ch5-5.11-q2"]))
, ]

def build_ch6():
    return [
        section("6.1", "Agent OS 与 Agent 操作系统", "能解释 Agent OS 的调度、权限、状态和观测层", [
            p("Agent OS 是把很多 Agent 当作可调度工作负载的运行时层。它不是某个聊天机器人，而是调度、权限、状态、日志、预算和生命周期的统一底座。"),
            t(["能力", "解决的问题", "没有它的后果", "生产形态"], [["Scheduler", "谁先跑/并发多少", "任务堆积", "队列+优先级"], ["Quota", "预算和限流", "成本失控", "token/金额配额"], ["Sandbox", "权限隔离", "越权调用", "白名单/容器"], ["Observability", "定位问题", "黑盒调试", "trace/log/metrics"]]),
            kp("最小 Agent OS", [code("agent_os.py", "最小 Agent OS：注册、调度、预算", ["from dataclasses import dataclass", "@dataclass", "class Job:", "    owner: str", "cost: int = 10"] + ["", "class OS:", "    def __init__(self):", "        self.jobs = []", "        self.budget = 100"] + ["", "    def submit(self, owner):", "        job = Job(owner)", "        if self.budget >= job.cost:", "            self.budget -= job.cost", "            self.jobs.append(job)", "            return f'submitted:{owner}'", "        return 'budget_exhausted'"] + ["", "if __name__ == '__main__':", "    os = OS()", "    print(os.submit('researcher'))", "    print(os.submit('writer'))"], [8, 13], "submitted:researcher\nsubmitted:writer", "Agent OS 的核心是统一运行时，不是业务 prompt。")]),
            kp("权限白名单", [code("permissions.py", "Agent 权限白名单", ["ALLOW = {'researcher': {'search'}, 'coder': {'editor', 'test'}}", "def can_use(agent, tool):", "    return tool in ALLOW.get(agent, set())"] + ["", "if __name__ == '__main__':", "    print(can_use('coder', 'test'))", "    print(can_use('coder', 'payment'))"], [3, 6], "True\nFalse", "权限必须落在工具粒度，否则一个 Agent 可以调用全公司工具。")]),
            c("落地建议", "先把 trace、预算、权限做进运行时，再讨论复杂 Agent 协作。")], [{"title": "设计配额", "description": "为 researcher/writer/reviewer 设计预算。", "hints": "按调用和 token 分别设"}, {"title": "画 OS 架构", "description": "画出调度、权限、状态和观测层。", "hints": "每层都要有接口"}], [{"type": "doc", "title": "AutoGen Runtime", "url": "https://microsoft.github.io/autogen/", "note": "运行时参考"}, {"type": "paper", "title": "AIOS", "url": "https://arxiv.org/abs/2403.16971", "note": "Agent OS 论文"}], ["ch6-6.1-q1", "ch6-6.1-q2"], ec("Agent 平台化", "20 个内部 Agent 脚本各自运行，成本、权限、状态散乱。", "引入运行时统一调度、工具白名单、预算、trace。", "故障和成本可按 Agent 归因。", "运行时要足够薄，业务不绑死在平台 API。", "platform.py", "平台注册与调度", ["class Runtime:", "    def __init__(self):", "        self.budget = 100"] + ["", "    def run(self, agent):", "        return agent if self.budget > 0 else 'blocked'", "", "if __name__ == '__main__':", "    print(Runtime().run('agent1'))"], [6], "agent1", "运行时层让团队从一堆脚本进入平台化治理。"))
    ], [
        section("6.2", "具身智能与物理 Agent", "能理解感知、决策、执行在物理世界中的闭环", [
            p("物理 Agent 把 LLM 的规划能力与机器人/设备的感知执行连接起来。关键是安全、动作约束、仿真验证和可恢复。"),
            t(["环节", "输入", "输出", "安全要求"], [["Perceive", "传感器", "状态", "噪声校验"], ["Plan", "目标", "动作序列", "风险等级"], ["Execute", "动作", "环境变化", "速度/限位"], ["Recover", "异常", "恢复动作", "急停策略"]]),
            kp("感知-决策-执行", [code("embodied_loop.py", "物理 Agent 闭环", ["def sense():", "    return {'battery': 80, 'obstacle': False}", "def decide(state):", "    return 'move' if not state['obstacle'] else 'stop'"] + ["", "def act(action):", "    return f'executed:{action}'"] + ["", "if __name__ == '__main__':", "    print(act(decide(sense())))", "    print(act(decide({'obstacle': True})))"], [4, 9], "executed:move\nexecuted:stop", "物理 Agent 必须能感知、决策并执行，同时每个动作都要有安全约束。")]),
            kp("安全策略", [code("safety_policy.py", "物理动作安全策略", ["SAFE = {'pick': 1, 'drop': 0, 'charge': 1}", "def allow(action):", "    return bool(SAFE.get(action, 0))"] + ["", "if __name__ == '__main__':", "    print(allow('pick'))", "    print(allow('drop'))"], [3], "True\nFalse", "物理风险比软件更不可逆，默认拒绝未知动作。")]),
            c("开发原则", "先仿真再实机；所有高风险动作都要有人监督和急停。")], [{"title": "写动作状态机", "description": "为机械臂 pick/place 写状态机。", "hints": "包含失败状态"}, {"title": "做仿真清单", "description": "列出上机前必须通过的仿真项。", "hints": "碰撞、电池、超时"}], [{"type": "doc", "title": "ROS 2", "url": "https://docs.ros.org/", "note": "机器人系统"}, {"type": "doc", "title": "MuJoCo", "url": "https://mujoco.org/", "note": "物理仿真"}], ["ch6-6.2-q1", "ch6-6.2-q2"]))
    ], [
        section("6.3", "AGI 路线与 Agent 演进", "能区分研究路线、产品演进和可工程化能力", [
            p("AGI 不是 Agent 工程的目标口号。当前 Agent 工程应关注可靠、可控、可评估、可组合的能力增量，而不是预测未来。"),
            t(["阶段", "能力", "工程意义", "限制"], [["任务专用", "单一任务", "可测试", "泛化弱"], ["工具增强", "调用工具", "能力强", "风险高"], ["长记忆", "跨会话", "个性化", "隐私风险"], ["规划与反思", "多步", "复杂任务", "错误累积"]]),
            kp("能力演进", [code("agent_evolution.py", "Agent 能力演进", ["STAGE = {0: 'prompt', 1: 'tool', 2: 'memory', 3: 'planning'}", "def capability(level):", "    return STAGE.get(level, 'unknown')"] + ["", "if __name__ == '__main__':", "    print(capability(1))", "    print(capability(3))"], [3, 6], "tool\nplanning", "工程上要把能力拆成可验证阶段，而不是笼统说 AGI。")]),
            kp("演进验收", [code("evolution_gate.py", "能力演进验收门", ["def gate(capabilities):", "    required = {'tool', 'memory', 'eval'}", "    return required <= set(capabilities)"] + ["", "if __name__ == '__main__':", "    print(gate(['tool', 'eval']))", "    print(gate(['tool', 'memory', 'eval']))"], [3, 6], "False\nTrue", "能力演进必须有验收门，否则只是功能堆积。")]),
            c("务实看法", "不要为 AGI 叙事写系统，要为可验证能力写系统。")], [{"title": "写能力矩阵", "description": "按工具、记忆、规划、评估列矩阵。", "hints": "每格写现状和目标"}, {"title": "做能力路线", "description": "把项目能力拆成季度路线。", "hints": "每季要可交付"}], [{"type": "paper", "title": "AIOS", "url": "https://arxiv.org/abs/2403.16971", "note": "Agent OS 与未来"}], ["ch6-6.3-q1", "ch6-6.3-q2"]))
    ], [
        section("6.4", "多模态 Agent", "能处理文本、图像、语音和结构化数据", [
            p("多模态 Agent 不只是调用视觉模型，而是理解不同模态的可靠性、成本和引用方式。图像/语音/文件各有预处理和验证策略。"),
            t(["模态", "任务", "关键能力", "风险"], [["文本", "推理/写作", "长上下文", "幻觉"], ["图像", "识别/OCR", "定位/裁剪", "识别错误"], ["语音", "转写/摘要", "降噪/分段", "隐私"], ["表格", "抽取/校验", "schema", "解析错"]]),
            kp("多模态路由", [code("multimodal_route.py", "多模态输入路由", ["def route(kind):", "    return {'text': 'llm', 'image': 'vision', 'audio': 'asr', 'pdf': 'ocr'}[kind]"] + ["", "if __name__ == '__main__':", "    print(route('image'))", "    print(route('audio'))"], [2, 5], "vision\nasr", "多模态先分类输入，再决定调用哪个能力；不要把视觉识别当普通文本。")]),
            kp("结构化抽取", [code("extract_schema.py", "多模态结构化抽取", ["def extract(image):", "    return {'ocr': True, 'schema': ['invoice', 'amount', 'date']}"] + ["", "if __name__ == '__main__':", "    print(extract('receipt'))"], [2], "{'ocr': True, 'schema': ['invoice', 'amount', 'date']}", "多模态输出要落 schema，才能进入下游业务系统。")]),
            c("成本与引用", "图像/语音通常更贵，输出必须带来源和置信度。")], [{"title": "做截图 Agent", "description": "从截图提取页面状态并生成操作建议。", "hints": "要校验元素存在"}, {"title": "做发票抽取", "description": "从图片抽取金额、日期、商户。", "hints": "金额要二次校验"}], [{"type": "doc", "title": "OpenAI Vision", "url": "https://platform.openai.com/docs/guides/vision", "note": "视觉模型使用"}, {"type": "doc", "title": "Tesseract", "url": "https://tesseract-ocr.github.io/tessdoc/", "note": "OCR 参考"}], ["ch6-6.4-q1", "ch6-6.4-q2"]))
    ], [
        section("6.5", "Agent 安全与对齐", "能设计安全边界、护栏、评估和人工接管", [
            p("Agent 安全是生产落地的底线。它包括提示注入、工具越权、数据泄露、模型幻觉、失控循环和不可逆动作。"),
            t(["风险", "影响", "防护", "验证"], [["Prompt Injection", "指令被覆盖", "隔离+检测", "红队测试"], ["Tool Abuse", "越权工具", "白名单", "权限审计"], ["Data Leak", "敏感信息外泄", "脱敏/DLP", "日志扫描"], ["Runaway", "无限循环", "max_steps", "压力测试"]]),
            kp("安全分层", [code("security_layers.py", "Agent 安全分层", ["def layer(action):", "    if action == 'read':", "        return 'allow'", "    if action == 'send':", "        return 'review'", "    return 'deny'"] + ["", "if __name__ == '__main__':", "    print(layer('read'))", "    print(layer('send'))", "    print(layer('delete'))"], [3, 8], "allow\nreview\ndeny", "安全不是单点 prompt，而是输入、工具、输出、日志四层防线。")]),
            kp("对齐评估", [code("alignment_eval.py", "对齐评估", ["def eval_output(answer, policy):", "    return answer not in policy.forbidden"] + ["", "if __name__ == '__main__':", "    print(eval_output('can help', type('P', (), {'forbidden': ['harm']})))"], [2], "True", "对齐评估要把政策变成可运行检查。")]),
            c("安全原则", "高风险动作默认拒绝；所有放行都要有日志。")], [{"title": "做红队集", "description": "写 20 条提示注入。", "hints": "覆盖网页、邮件、文档"}, {"title": "设计策略", "description": "列出 10 类禁止输出。", "hints": "含隐私、法律、金融"}], [{"type": "doc", "title": "OWASP LLM Top 10", "url": "https://owasp.org/www-project-top-10-for-large-language-model-applications/", "note": "安全标准"}, {"type": "doc", "title": "NIST AI RMF", "url": "https://www.nist.gov/itl/ai-risk-management-framework", "note": "AI 风险管理"}], ["ch6-6.5-q1", "ch6-6.5-q2"]))
    ], [
        section("6.6", "Agent 经济与市场化", "能理解能力商品化、调用计费和服务市场", [
            p("Agent 经济把能力变成服务：注册、调用、计费、评价和结算。企业要关注单位经济，而不是只看 demo 效果。"),
            t(["角色", "职责", "收入", "风险"], [["Provider", "提供能力", "按调用收费", "质量波动"], ["Consumer", "调用能力", "节省成本", "供应商依赖"], ["Marketplace", "撮合", "抽佣", "信任"], ["Auditor", "评估", "审计费", "标准争议"]]),
            kp("服务计费", [code("billing.py", "Agent 服务计费", ["RATE = {'translate': 1, 'vision': 4, 'report': 10}", "def bill(service, calls):", "    return RATE[service] * calls"] + ["", "if __name__ == '__main__':", "    print(bill('vision', 3))", "    print(bill('report', 1))"], [3, 6], "12\n10", "服务能力市场化必须能按调用、质量和失败计费。")]),
            kp("能力注册", [code("service_registry.py", "能力注册与发现", ["REG = {}", "def register(name, price):", "    REG[name] = price"] + ["", "def discover(name):", "    return REG.get(name)"] + ["", "if __name__ == '__main__':", "    register('translate', 1)", "    print(discover('translate'))"], [4, 9], "1", "注册和发现是服务市场的基础。")]),
            c("单位经济", "要算清毛利、失败补偿、退费和人工复核成本。")], [{"title": "做服务报价", "description": "为翻译、报告、视觉抽取做报价。", "hints": "含失败补偿"}, {"title": "做评价机制", "description": "设计调用方评价能力。", "hints": "要能防刷分"}], [{"type": "doc", "title": "MCP", "url": "https://modelcontextprotocol.io/", "note": "工具市场基础"}], ["ch6-6.6-q1", "ch6-6.6-q2"]))
    ], [
        section("6.7", "开源生态动态", "能理解 LangGraph、CrewAI、MCP、本地模型与评估生态", [
            p("开源生态让 Agent 开发更快，也让选型更容易混乱。关键是看协议、持久化、工具生态、观测能力和本地部署边界。"),
            t(["项目/协议", "类型", "价值", "关注点"], [["LangGraph", "框架", "图式编排", "学习成本"], ["CrewAI", "框架", "角色化流程", "复杂状态"], ["MCP", "协议", "工具统一", "安全"], ["LlamaIndex", "框架", "RAG", "检索评估"], ["Ollama", "本地", "本地模型", "硬件"]]),
            kp("生态地图", [code("ecosystem.py", "Agent 生态地图", ["def layer(name):", "    return {'MCP': 'protocol', 'LangGraph': 'orchestration', 'LlamaIndex': 'rag', 'Ollama': 'runtime'}[name]"] + ["", "if __name__ == '__main__':", "    print(layer('MCP'))", "    print(layer('LangGraph'))"], [2, 5], "protocol\norchestration", "选型前先分层，别把协议、框架和运行时混在一起。")]),
            kp("本地模型", [code("local_model.py", "本地与云端混合策略", ["def choose(sensitive):", "    return 'local' if sensitive else 'cloud'"] + ["", "if __name__ == '__main__':", "    print(choose(True))", "    print(choose(False))"], [2], "local\ncloud", "本地模型不是万能，但在隐私和成本场景里非常关键。")]),
            c("跟进原则", "每个季度看协议演进和事故案例，不要追每个发布会。")], [{"title": "建生态雷达", "description": "列 10 个项目并说明用途。", "hints": "含协议、框架、评估"}, {"title": "做迁移评估", "description": "从 CrewAI 到 LangGraph 评估迁移成本。", "hints": "看状态和编排 API"}], [{"type": "doc", "title": "MCP", "url": "https://modelcontextprotocol.io/", "note": "工具协议"}, {"type": "doc", "title": "LangGraph", "url": "https://langchain-ai.github.io/langgraph/", "note": "图式编排"}, {"type": "doc", "title": "LlamaIndex", "url": "https://docs.llamaindex.ai/", "note": "RAG"}, {"type": "doc", "title": "Ollama", "url": "https://ollama.com/", "note": "本地模型"}], ["ch6-6.7-q1", "ch6-6.7-q2"]))
    ], [
        section("6.8", "学习资源与社区", "能建立持续学习和作品集积累方法", [
            p("学习资源不是越多越好，而是要围绕实践形成闭环：读、跑、评、复盘、发。社区是反馈和纠错的来源。"),
            t(["资源类型", "用途", "用法", "产出"], [["官方文档", "掌握 API", "按例跑通", "笔记+demo"], ["论文", "理解趋势", "精读关键页", "摘要"], ["开源项目", "学习实现", "读核心模块", "小改造"], ["社区", "验证问题", "提问/贡献", "issue/PR"]]),
            kp("学习闭环", [code("learning_loop.py", "学习闭环", ["def learn(resource):", "    return f'read->{resource}->run->review'"] + ["", "if __name__ == '__main__':", "    print(learn('langgraph'))"], [2], "read->langgraph->run->review", "学习资源要转化成可运行项目和复盘，不然后面会忘。")]),
            kp("作品集", [code("portfolio.py", "作品集结构", ["def project(name):", "    return {'repo': name, 'readme': True, 'demo': True, 'eval': False}"] + ["", "if __name__ == '__main__':", "    print(project('rag-bot'))"], [2], "{'repo': 'rag-bot', 'readme': True, 'demo': True, 'eval': False}", "就业作品集必须暴露差距，比如缺 eval 就补 eval。")]),
            c("持续学习", "每周跑一个官方例子，每月做一次复盘，每季度更新一次技术栈。")], [{"title": "建资源清单", "description": "按框架、协议、评估分类。", "hints": "只保留你能用的"}, {"title": "做 30 天计划", "description": "把资源变成 30 天行动表。", "hints": "每天一个输出"}], [{"type": "doc", "title": "OpenAI Docs", "url": "https://platform.openai.com/docs", "note": "模型/API"}, {"type": "doc", "title": "LangGraph", "url": "https://langchain-ai.github.io/langgraph/", "note": "图式编排"}, {"type": "doc", "title": "CrewAI", "url": "https://docs.crewai.com/", "note": "角色化流程"}, {"type": "doc", "title": "MCP", "url": "https://modelcontextprotocol.io/", "note": "工具协议"}], ["ch6-6.8-q1", "ch6-6.8-q2"]))
    ], [
        section("6.9", "就业冲刺包：从学习到 Agent 开发岗", "能用项目、评测、成本、安全和复盘证明求职能力", [
            p("就业冲刺不是补几个 demo，而是证明你能交付可运行、可评估、可上线的 Agent 系统。面试要回答：目标是什么、怎么拆、怎么验证、失败怎么处理、成本多少。"),
            t(["阶段", "时间", "交付物", "达标标准"], [["基础闭环", "1-3周", "工具Agent", "有 trace、预算、测试"], ["知识增强", "4-6周", "RAG问答", "有引用、拒答、评估"], ["生产工程", "7-9周", "LangGraph流水线", "HITL、检查点、回滚"], ["求职冲刺", "10-12周", "作品集", "成本表、复盘、架构说明"]]),
            kp("项目交付骨架", [code("career_deliverable.py", "Agent 项目交付骨架", ["from dataclasses import dataclass, field"] + ["", "@dataclass", "class Delivery:", "    project: str", "    eval_cases: int = 0", "    trace: bool = False", "    cost_report: bool = False"] + ["", "    def ready(self):", "        return self.eval_cases >= 20 and self.trace and self.cost_report"] + ["", "if __name__ == '__main__':", "    d = Delivery('rag-bot', 24, True, True)", "    print(d.ready())"], [8, 13], "True", "就业项目要证明能交付，而不是只展示功能。")]),
            kp("面试证据", [code("interview_evidence.py", "面试证据组织", ["def evidence(project):", "    return [f'{project}: goals', f'{project}: architecture', f'{project}: eval', f'{project}: cost', f'{project}: incident']"] + ["", "if __name__ == '__main__':", "    print(evidence('support-agent'))"], [2], "['support-agent: goals', 'support-agent: architecture', 'support-agent: eval', 'support-agent: cost', 'support-agent: incident']", "面试时把项目拆成目标、架构、评测、成本、事故五层讲。")]),
            c("求职原则", "作品集里有失败复盘比只有成功 demo 更有说服力。")]), [{"title": "做作品集", "description": "选 3 个项目补齐 README、eval、成本。", "hints": "先选能讲清的项目"}, {"title": "写 1 页架构", "description": "为项目画架构和风险边界。", "hints": "一页讲完"}], [{"type": "doc", "title": "LangGraph", "url": "https://langchain-ai.github.io/langgraph/", "note": "生产编排"}, {"type": "doc", "title": "CrewAI", "url": "https://docs.crewai.com/", "note": "角色化流程"}, {"type": "doc", "title": "MCP", "url": "https://modelcontextprotocol.io/", "note": "工具生态"}], ["ch6-6.9-q1", "ch6-6.9-q2"], ec("把学习做成求职资产", "学习完框架但无法证明生产能力。", "每个项目要求 README、运行命令、评估报告、成本表、事故复盘。", "候选人能 30 分钟讲清架构和取舍。", "作品集的核心是证据链。", "asset.py", "求职资产检查", ["ASSETS = ['repo', 'readme', 'eval', 'cost', 'incident']", "def missing(done):", "    return [a for a in ASSETS if a not in done]"] + ["", "if __name__ == '__main__':", "    print(missing(['repo']))"], [3], "['readme', 'eval', 'cost', 'incident']", "缺哪项补哪项，作品集才完整。"))
, ]

def update_chapter(filename, sections):
    path = DATA / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    meta = {k: v for k, v in data.items() if k != "sections"}
    data = meta
    data["sections"] = sections
    data["lastUpdated"] = TODAY
    data["version"] = VERSION
    data["updatedAt"] = TIMESTAMP
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    update_chapter("chapter-4.json", build_ch4())
    update_chapter("chapter-5.json", build_ch5())
    update_chapter("chapter-6.json", build_ch6())
    print("已重写第 4-6 章为更完整的学习内容")


if __name__ == "__main__":
    main()
