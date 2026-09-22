#!/usr/bin/env python3
"""Add 2026-09-21 employment-ready enrichment blocks to existing chapters."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "data"
TODAY = "2026-09-21"
VERSION = "2026.09.21"


def code(filename, title, src, output, note):
    return {
        "type": "code",
        "data": {
            "filename": filename,
            "language": "python",
            "title": title,
            "highlightLines": [],
            "code": src,
            "output": output,
            "note": note,
        },
    }


def kp(title, *blocks):
    return {"type": "knowledgePoint", "title": title, "content": list(blocks)}


def para(text):
    return {"type": "paragraph", "text": text}


def table(headers, rows):
    return {"type": "table", "data": {"headers": headers, "rows": rows}}


def callout(variant, title, text):
    return {"type": "callout", "variant": variant, "title": title, "text": text}


def doc(title, url, note):
    return {"type": "doc", "title": title, "url": url, "note": note}


def update_chapter(name, section_id, appendix):
    path = DATA / name
    data = json.loads(path.read_text(encoding="utf-8"))
    for section in data.get("sections", []):
        if section.get("id") == section_id:
            section.setdefault("content", []).extend(appendix)
            section["lastUpdated"] = TODAY
            section["version"] = VERSION
            break
    else:
        raise SystemExit(f"section {section_id} not found in {name}")
    data["lastUpdated"] = TODAY
    data["version"] = VERSION
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ch3_observability():
    return [
        kp("可观测性工程化：从 demo 到生产仪表盘", [
            para("第 3 章已经讲过工具、RAG、框架和沙箱；真正上线时还要回答另一个问题：一次 Agent 执行到底经过哪些模型、哪些工具、花了多少钱、哪一步失败？可观测性就是把这些都记录成可查询的 trace。"),
            table(["指标", "为什么重要", "常见告警阈值", "治理动作"], [
                ["任务成功率", "衡量业务闭环", "低于 95%", "补失败样例、改工具 schema"],
                ["工具调用成功率", "发现外部依赖退化", "低于 98%", "加超时、降级、重试"],
                ["P95 延迟", "影响用户体验", "超过 SLA", "改缓存、改模型、拆分任务"],
                ["成本/任务", "控制商业化毛利", "超过预算", "换小模型、加缓存、减少步数"],
                ["引用命中率", "评估 RAG 可靠性", "低于 90%", "调检索、重排、chunk"],
            ]),
            code("s3_9_trace_budget.py", "可运行 trace 与预算治理骨架", r'''from dataclasses import dataclass

@dataclass
class Span:
    name: str
    model: str
    tokens: int
    latency_ms: int

def review(spans):
    total_tokens = sum(span.tokens for span in spans)
    slow = [span.name for span in spans if span.latency_ms > 2000]
    return {"total_tokens": total_tokens, "slow_spans": slow}

if __name__ == "__main__":
    trace = [Span("route", "gpt-5-mini", 180, 300), Span("research", "gpt-5", 2400, 2400)]
    print(review(trace))
''', "{'total_tokens': 2580, 'slow_spans': ['research']}", "trace 的最小可用形态不是画大图，而是先让每个关键步骤都有 name、model、tokens、latency 和 error。"),
            callout("tip", "落地顺序", "先记录 span，再做 dashboard，再做 alert；没有 span，就无法判断改 prompt、换模型还是修工具到底有没有变好。"),
        ]),
    ]


def ch6_career_pack():
    return [
        kp("就业冲刺包：把课程学成可面试资产", [
            para("就业冲刺包的目标不是再补 10 个 demo，而是让每个项目都具备证据链：目标、架构、运行命令、评测、成本、安全边界、事故复盘。面试时你可以用同一套结构讲客服 Agent、编码 Agent、RAG Agent 或多 Agent 流水线。"),
            table(["项目", "核心问题", "必须交付", "面试追问答案"], [
                ["工具 Agent", "如何可靠调用外部 API", "schema、超时、重试、trace", "失败时降级，不让用户看到半成品"],
                ["RAG 问答", "如何保证答案有依据", "检索评估、引用、拒答", "先看召回率，再看生成质量"],
                ["多 Agent 流水线", "如何避免循环和成本失控", "LangGraph 状态、预算、HITL", "每个节点都有独立评测"],
                ["上线 Agent", "如何稳定运行", "队列、指标、回滚、审计", "先灰度小流量，再看成本和失败率"],
            ]),
            code("s6_9_portfolio_gate.py", "作品集验收门：判断项目是否可面试", r'''from dataclasses import dataclass

@dataclass(frozen=True)
class PortfolioProject:
    name: str
    readme: bool
    eval_cases: int
    has_trace: bool
    has_cost_report: bool
    has_rollback: bool

def ready(project: PortfolioProject) -> bool:
    return project.readme and project.eval_cases >= 20 and project.has_trace and project.has_cost_report and project.has_rollback

if __name__ == "__main__":
    project = PortfolioProject("support-agent", True, 24, True, True, True)
    print(project.name, ready(project))
''', "support-agent True", "求职项目不是功能越多越好，而是证据越完整越好；缺什么补什么。"),
            code("s6_9_interview_story.py", "30 秒讲清 Agent 项目的结构", r'''def pitch(goal, architecture, evidence, risk):
    return {
        "goal": goal,
        "architecture": architecture,
        "evidence": evidence,
        "risk": risk,
    }

if __name__ == "__main__":
    print(pitch("退款客服自动分流", "Router + RAG + HITL", "任务完成率 92%", "高风险退款必须人工确认"))
''', "{'goal': '退款客服自动分流', 'architecture': 'Router + RAG + HITL', 'evidence': '任务完成率 92%', 'risk': '高风险退款必须人工确认'}", "面试表达要短、具体、可追问：目标、架构、证据、风险四句话先讲清。"),
            table(["岗位方向", "重点项目", "加分证据"], [
                ["应用 Agent 工程师", "客服/研究/报表 Agent", "用户反馈、A/B 实验、成本表"],
                ["平台 Agent 工程师", "LangGraph/Temporal 平台", "trace、队列、回滚、限流"],
                ["研究型 Agent 工程师", "框架复现或自研评测", "论文复现、消融实验、失败分析"],
                ["垂直领域 Agent 工程师", "编码/语音/多模态 Agent", "领域数据、领域工具、领域指标"],
            ]),
            callout("tip", "作品集原则", "每个项目至少放 README、架构图、运行命令、评测集、失败样例和成本估算；这六项比 20 张截图更有说服力。"),
            doc("LangGraph", "https://langchain-ai.github.io/langgraph/", "多 Agent 状态编排"),
            doc("OpenAI Agents SDK", "https://openai.github.io/openai-agents-python/", "Agent 运行时和 tracing"),
            doc("Langfuse", "https://langfuse.com/docs", "LLM 应用观测"),
        ]),
    ]


def sync_chapters_meta():
    chapters = []
    total_sections = 0
    for i in range(1, 7):
        data = json.loads((DATA / f"chapter-{i}.json").read_text(encoding="utf-8"))
        meta = next((c for c in chapters_meta["chapters"] if c["id"] == f"ch{i}"), None)
        if not meta:
            meta = {"id": f"ch{i}"}
        meta.update({
            "number": i,
            "title": data["title"],
            "subtitle": data["subtitle"],
            "estimatedHours": data.get("estimatedHours", 12),
            "difficulty": data.get("difficulty", 3),
            "sections": [{"id": s["id"], "title": s["title"], "estimatedMinutes": s.get("estimatedMinutes", 30), "difficulty": s.get("difficulty", 3)} for s in data.get("sections", [])],
        })
        chapters.append(meta)
        total_sections += len(data.get("sections", []))
    chapters_meta["chapters"] = chapters
    chapters_meta["lastUpdated"] = TODAY
    chapters_meta["version"] = VERSION
    chapters_meta["updatedAt"] = "2026-09-21T09:00:00+08:00"
    (DATA / "chapters.json").write_text(json.dumps(chapters_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return total_sections


chapters_meta = json.loads((DATA / "chapters.json").read_text(encoding="utf-8"))
update_chapter("chapter-3.json", "3.9", ch3_observability())
update_chapter("chapter-6.json", "6.9", ch6_career_pack())
total_sections = sync_chapters_meta()
print(f"已加深 3.9 与 6.9，并同步章节元数据；共 {total_sections} 小节")
