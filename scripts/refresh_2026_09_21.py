#!/usr/bin/env python3
"""Refresh Agent learning site content metadata for 2026-09-21."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "data"
DATE = "2026-09-21"
VERSION = "2026.09.21"
UPDATED_AT = "2026-09-21T09:00:00+08:00"
SECTION = {
    "id": "6.9",
    "title": "就业冲刺包：从学习到 Agent 开发岗",
    "subtitle": "用真实可运行项目、评测记录和面试口径证明你能独立交付 Agent",
    "estimatedMinutes": 40,
    "difficulty": 4,
    "objectives": [
        "完成 4 个可展示项目：工具 Agent、RAG 问答、多 Agent 流水线、评测仪表盘",
        "掌握 Agent 工程师面试的高频问题与回答框架",
        "建立上线清单：安全、成本、可观测性、人工审核、回滚方案",
        "把学习笔记整理成可招聘的 GitHub 项目与面试话术"
    ],
    "content": [
        {
            "type": "paragraph",
            "text": "Agent 开发岗招聘看的不是“会用几个库”，而是能否把业务需求拆成可执行链路，并能证明链路在线上稳定。建议把 90 天学习拆成 4 个项目：每个项目都要求可运行、可测试、可解释成本，并能写清楚哪些地方需要人工介入。"
        },
        {
            "type": "table",
            "data": {
                "headers": ["阶段", "时间", "交付物", "达标标准"],
                "rows": [
                    ["基础闭环", "1-3 周", "单 Agent + 2 个工具", "能在本地跑完任务并输出工具调用轨迹"],
                    ["知识增强", "4-6 周", "RAG 文档问答", "答案带引用，召回为空时走兜底"],
                    ["生产工程", "7-9 周", "LangGraph 多 Agent 流水线", "支持检查点、审批门、日志追踪、预算限制"],
                    ["求职冲刺", "10-12 周", "作品集 + 评测报告", "3 个可复现实验、1 份成本表、1 份故障复盘"]
                ]
            }
        },
        {
            "type": "code",
            "data": {
                "filename": "career_sprint.py",
                "language": "python",
                "title": "本地 Agent 冲刺演练：无需 API Key 也能跑通核心结构",
                "highlightLines": [5,12,16],
                "code": "import os\nfrom dataclasses import dataclass\n\n@dataclass\nclass AgentConfig:\n    goal: str = \"\"\n    model: str = \"gpt-5\"\n    max_steps: int = 5\n    tools: tuple[str, ...] = (\"search\", \"calculator\")\n\ndef make_agent(goal: str) -> AgentConfig:\n    return AgentConfig(goal=goal, model=os.getenv(\"OPENAI_MODEL\", \"gpt-5\"))\n\ndef run_plan(agent: AgentConfig):\n    for step in range(agent.max_steps):\n        print(f\"step {step+1}: {agent.goal} 用 {agent.tools}\")\n    return \"done\"\n\nif __name__ == \"__main__\":\n    print(run_plan(make_agent(\"做一个客服 Agent\")))",
                "output": "step 1: 做一个客服 Agent 用 (\"search\", \"calculator\")\nstep 2: 做一个客服 Agent 用 (\"search\", \"calculator\")\nstep 3: 做一个客服 Agent 用 (\"search\", \"calculator\")\nstep 4: 做一个客服 Agent 用 (\"search\", \"calculator\")\nstep 5: 做一个客服 Agent 用 (\"search\", \"calculator\")\ndone",
                "note": "这段代码不依赖外部服务，适合放进作品集作为 Agent 控制面骨架；接真实模型时只需替换 run_plan 内部的规划与工具执行。"
            }
        },
        {
            "type": "callout",
            "variant": "tip",
            "title": "面试时最容易加分的 4 句话",
            "text": "“我按任务复杂度选模型，不按品牌选模型”；“我会给每个 Agent 设 max_steps、预算、超时和重复调用检测”；“高风险动作一定走 HITL 和审计日志”；“我上线前先看失败率、引用命中率、工具错误率和单次任务成本”。"
        }
    ],
    "enterpriseCase": {
        "title": "把求职项目做成企业可复用资产",
        "background": "面试官常见追问：项目是否可运行、是否可评测、失败怎么处理、成本如何控制。",
        "architecture": "每个项目提供 README、可运行代码、测试数据、评测脚本、故障复盘和成本表；代码默认支持本地 mock，接 API 时通过环境变量切换模型。",
        "outcome": "候选人能 30 分钟内讲清楚业务目标、系统边界、关键取舍、失败案例与改进方向。",
        "lessons": "1) 可运行胜过截图；2) 评测数据胜过主观描述；3) 成本控制是生产经验的核心证据。"
    },
    "exercises": [
        {
            "title": "做一份可面试的项目 README",
            "description": "任选一个章节代码示例，补充目标、架构图、运行步骤、预期输出、失败处理、成本估算和可改进点。",
            "hints": "README 里不要只放结果，要放失败案例和如何发现它们。"
        }
    ],
    "resources": [
        {"type": "doc", "title": "Agent 项目交付清单", "url": "https://docs.crewai.com/quickstart/", "note": "从角色、任务、工具、记忆、流控角度组织 Agent 项目"},
        {"type": "doc", "title": "LangGraph 持久化与人工审核", "url": "https://langchain-ai.github.io/langgraph/", "note": "学习 checkpointer、interrupt 和恢复机制"},
        {"type": "doc", "title": "MCP 工具生态", "url": "https://modelcontextprotocol.io/", "note": "把工具接入能力封装成跨 Agent 协议"}
    ],
    "quiz": ["ch6-6.9-q1", "ch6-6.9-q2"]
}
QUIZZES = [
    {
        "id": "ch6-6.9-q1",
        "question": "以下哪项最能证明一个 Agent 项目具备生产意识？",
        "options": ["界面做得漂亮", "有可运行代码、评测数据、成本控制与人工审核机制", "只使用最新模型"],
        "correctAnswer": 1,
        "explanation": "生产意识体现在可复现、可观测、可控成本和可控风险，而不是单一模型或界面。"
    },
    {
        "id": "ch6-6.9-q2",
        "question": "Agent 开发岗作品集里，README 最重要的内容是什么？",
        "options": ["依赖列表越多越好", "目标、架构、运行步骤、预期输出、失败处理、成本和改进方向", "只放最终演示截图"],
        "correctAnswer": 1,
        "explanation": "招聘者需要通过 README 判断你是否能解释设计取舍、验证结果并控制风险。"
    }
]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def save(name, data):
    (DATA / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_all_dates(data):
    data["lastUpdated"] = DATE
    data["version"] = VERSION
    data["updatedAt"] = UPDATED_AT
    return data


def text_to_date(text):
    text = text.replace("2026 年 8 月 20 日", DATE)
    text = text.replace("2026 年 8 月 24 日", DATE)
    text = text.replace("2026 年 9 月 21 日", DATE)
    text = text.replace("2026.09.21", VERSION)
    return text


def walk(obj):
    if isinstance(obj, str):
        return text_to_date(obj)
    if isinstance(obj, list):
        return [walk(v) for v in obj]
    if isinstance(obj, dict):
        return {k: walk(v) for k, v in obj.items()}
    return obj


def ensure_chapter_6_9():
    ch = load("chapter-6.json")
    ch["sections"] = [s for s in ch.get("sections", []) if s.get("id") != SECTION["id"]]
    ch["sections"].append(SECTION)
    ch["estimatedHours"] = 14
    ch["subtitle"] = "理解 Agent OS、多模态、物理 Agent、就业冲刺与社区生态"
    save("chapter-6.json", update_all_dates(ch))

    meta = load("chapters.json")
    for chm in meta["chapters"]:
        chm["lastUpdated"] = DATE
        chm["version"] = VERSION
        if chm.get("id") == "ch6":
            chm["estimatedHours"] = 14
            chm["subtitle"] = "理解 Agent OS、多模态、物理 Agent、就业冲刺与社区生态"
            chm["sections"] = [s for s in chm.get("sections", []) if s.get("id") != "6.9"]
            chm["sections"].append({k: SECTION[k] for k in ["id", "title", "estimatedMinutes", "difficulty"]})
    meta["description"] = "2026-09-21 更新的 AI Agent 开发学习路线：覆盖最新模型、MCP、Agent SDK、LangGraph、多 Agent、RAG、评测与就业冲刺项目。"
    save("chapters.json", update_all_dates(meta))

    q = load("quizzes.json")
    q["quizzes"] = [x for x in q.get("quizzes", []) if x.get("id") not in {item["id"] for item in QUIZZES}]
    q["quizzes"].extend(QUIZZES)
    save("quizzes.json", update_all_dates(q))


def update_appendix_dates():
    save("appendix.json", update_all_dates(walk(load("appendix.json"))))
    save("glossary.json", update_all_dates(walk(load("glossary.json"))))
    save("redis.json", update_all_dates(walk(load("redis.json"))))


def update_readme():
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("| 第 6 章 前沿趋势 | 10h | ★★☆ | Agent OS、AGI、多模态、安全、社区生态 |", "| 第 6 章 前沿趋势 | 14h | ★★☆ | Agent OS、AGI、多模态、安全、社区生态、就业冲刺包 |")
    if "就业冲刺包" not in text:
        text += "\n## 2026-09-21 就业冲刺更新\n\n- 新增“就业冲刺包”：90 天求职路线、4 个项目、评测记录、面试高频问题与上线清单。\n- 全站课程数据、章节元数据、测验题库与页面版本统一更新到 2026-09-21。\n- 代码示例继续优先支持本地 mock / 无外部依赖运行；需要接真实 API 时通过环境变量切换模型。\n"
    path.write_text(text, encoding="utf-8")



if __name__ == "__main__":
    ensure_chapter_6_9()
    for n in ["chapter-1.json", "chapter-2.json", "chapter-3.json", "chapter-4.json", "chapter-5.json"]:
        save(n, update_all_dates(walk(load(n))))
    update_appendix_dates()
    update_readme()
    print("✅ refreshed course data to", DATE)
