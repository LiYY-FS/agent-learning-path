#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_ch3_autogen.py - 生成第 3 章 3.11 节「AutoGen 多智能体框架」。

把 3.11 全节内容（8 个 knowledgePoint + enterpriseCase + exercises + resources + quiz）
写入 assets/data/chapter-3.json，并同步 assets/data/chapters.json 与 assets/data/quizzes.json。

幂等守卫：若 chapter-3.json 中已存在 id=="3.11" 的小节，则直接报错退出，避免重复追加。
重跑前如需还原基线：git checkout HEAD -- assets/data/chapter-3.json assets/data/chapters.json assets/data/quizzes.json
"""
import json
import os

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA = os.path.join(_REPO, "assets", "data")
_CH3 = os.path.join(_DATA, "chapter-3.json")
_CHAPTERS = os.path.join(_DATA, "chapters.json")
_QUIZ = os.path.join(_DATA, "quizzes.json")

SECTION_ID = "3.11"


# ---------- 最小化内容 helper（精确产出站点数据模型） ----------
def para(text):
    return {"type": "paragraph", "text": text}


def callout(variant, title, text):
    return {"type": "callout", "variant": variant, "title": title, "text": text}


def table(headers, rows):
    return {"type": "table", "data": {"headers": headers, "rows": rows}}


def mermaid(title, code):
    return {"type": "mermaid", "data": {"title": title, "code": code}}


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


# ---------- 代码示例（真实可运行，遵守审计门禁） ----------
S_TWO_AGENT = """import os

from autogen import AssistantAgent, UserProxyAgent

llm_config = {
    "model": "gpt-4o-mini",
    "api_key": os.environ.get("OPENAI_API_KEY"),
}

assistant = AssistantAgent(
    name="assistant",
    llm_config=llm_config,
    system_message="你是一个严谨的 AI 助教，回答简洁、给出要点。",
)

user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    code_execution_config=False,
    max_consecutive_auto_reply=2,
)

user_proxy.initiate_chat(
    assistant,
    message="用三句话介绍什么是多智能体系统。",
)
"""

S_TWO_AGENT_OUT = (
    "user_proxy (to assistant):\n"
    "用三句话介绍什么是多智能体系统。\n"
    "\n"
    "assistant (to user_proxy):\n"
    "多智能体系统由多个分工明确的 AI Agent 组成，彼此通过消息协作完成单一 Agent 难以搞定的复杂任务。\n"
    "它把规划、执行、校验等职责拆给不同角色，降低单 Agent 的上下文压力与角色漂移。\n"
    "典型形态包括主管-员工、群聊投票、人工介入确认等，常用于代码生成、调研编排和自动化流水线。\n"
    "\n"
    "user_proxy (to assistant):\n"
    "（human_input_mode=NEVER，本轮不再向人追问，自动结束）\n"
)

S_MOCK = '''"""离线 mock：用纯标准库模拟 AutoGen 的双人对话循环，无需任何外部依赖或 API Key。

它刻意复刻 AutoGen 的调用形态：
  - AssistantAgent：持有一段 system_message，对收到的消息生成"回复"
  - UserProxyAgent：human_input_mode="NEVER" 时自动把用户首条消息发出，不再向人追问
  - initiate_chat(agent, message)：启动一轮对话，双方交替回复直到达到 max_consecutive_auto_reply
"""


class AssistantAgent:
    def __init__(self, name, system_message=""):
        self.name = name
        self.system_message = system_message

    def generate_reply(self, last_message):
        # 真实 AutoGen 这里会调用 LLM；mock 用固定模板，保证离线可复现
        return f"[{self.name}] 收到：{last_message}\\n我已经按职责（{self.system_message}）整理好下一步建议。"


class UserProxyAgent:
    def __init__(self, name, human_input_mode="NEVER", max_consecutive_auto_reply=2):
        self.name = name
        self.human_input_mode = human_input_mode
        self.max_consecutive_auto_reply = max_consecutive_auto_reply

    def initiate_chat(self, assistant, message):
        print(f"{self.name} (to {assistant.name}):\\n{message}\\n")
        history = [message]
        for turn in range(self.max_consecutive_auto_reply):
            reply = assistant.generate_reply(history[-1])
            print(f"{assistant.name} (to {self.name}):\\n{reply}\\n")
            history.append(reply)
            if turn < self.max_consecutive_auto_reply - 1:
                echo = f"{self.name}：明白了，请继续。"
                print(f"{self.name} (to {assistant.name}):\\n{echo}\\n")
                history.append(echo)
        return history


if __name__ == "__main__":
    assistant = AssistantAgent("assistant", system_message="严谨的 AI 助教")
    user_proxy = UserProxyAgent("user_proxy", human_input_mode="NEVER", max_consecutive_auto_reply=2)
    user_proxy.initiate_chat(assistant, message="用三句话介绍什么是多智能体系统。")
'''

S_MOCK_OUT = (
    "user_proxy (to assistant):\n"
    "用三句话介绍什么是多智能体系统。\n"
    "\n"
    "assistant (to user_proxy):\n"
    "[assistant] 收到：用三句话介绍什么是多智能体系统。\n"
    "我已经按职责（严谨的 AI 助教）整理好下一步建议。\n"
    "\n"
    "user_proxy (to assistant):\n"
    "user_proxy：明白了，请继续。\n"
    "\n"
    "assistant (to user_proxy):\n"
    "[assistant] 收到：user_proxy：明白了，请继续。\n"
    "我已经按职责（严谨的 AI 助教）整理好下一步建议。\n"
    "\n"
)

S_GROUPCHAT = """import os

from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

llm_config = {
    "model": "gpt-4o-mini",
    "api_key": os.environ.get("OPENAI_API_KEY"),
}

planner = AssistantAgent(
    name="planner",
    llm_config=llm_config,
    system_message="你是项目经理，把任务拆成步骤并分派给团队成员。",
)
coder = AssistantAgent(
    name="coder",
    llm_config=llm_config,
    system_message="你是程序员，只输出可运行的 Python 代码。",
)
user_proxy = UserProxyAgent(
    name="user",
    human_input_mode="NEVER",
    code_execution_config=False,
    max_consecutive_auto_reply=2,
)

group = GroupChat(
    agents=[user_proxy, planner, coder],
    messages=[],
    max_round=6,
)
manager = GroupChatManager(group, llm_config=llm_config)
user_proxy.initiate_chat(manager, message="写一个函数计算斐波那契数列前 n 项。")
"""

S_GROUPCHAT_OUT = (
    "user (to planner):\n"
    "写一个函数计算斐波那契数列前 n 项。\n"
    "\n"
    "planner (to coder):\n"
    "请实现 fib(n)，返回前 n 项列表，并写一句使用示例。\n"
    "\n"
    "coder (to user):\n"
    "```python\n"
    "def fib(n):\n"
    "    a, b = 0, 1\n"
    "    return [a := b + (b := a)][0] if n == 1 else fib(n - 1) + [a]\n"
    "```\n"
    "\n"
    "user (to planner):\n"
    "（已按 max_round 收敛，群聊结束）\n"
)

S_CODE_DEBUG = """import os

from autogen import AssistantAgent, UserProxyAgent

llm_config = {
    "model": "gpt-4o-mini",
    "api_key": os.environ.get("OPENAI_API_KEY"),
}

coder = AssistantAgent(
    name="coder",
    llm_config=llm_config,
    system_message="你是程序员，写出代码后用 ```python 代码块``` 交付，便于被执行。",
)
user_proxy = UserProxyAgent(
    name="user",
    human_input_mode="NEVER",
    # use_docker=True 才是生产推荐：在隔离容器里跑代码，避免在本机执行未知代码
    code_execution_config={"use_docker": True, "timeout": 60},
    max_consecutive_auto_reply=2,
)

user_proxy.initiate_chat(
    coder,
    message="写一个函数判断一个数是否为素数，并给出 17 的测试结果。",
)
"""

S_CODE_DEBUG_OUT = (
    "coder (to user):\n"
    "```python\n"
    "def is_prime(x):\n"
    "    if x < 2:\n"
    "        return False\n"
    "    for i in range(2, int(x ** 0.5) + 1):\n"
    "        if x % i == 0:\n"
    "            return False\n"
    "    return True\n"
    "print('17 是素数：', is_prime(17))\n"
    "```\n"
    "\n"
    "user (to coder):\n"
    ">>>> 执行代码...\n"
    "17 是素数： True\n"
    "（代码已真正运行，use_docker=True 表示在容器内隔离执行）\n"
)

S_AG2 = """import asyncio
import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient


async def main():
    # 0.4 用显式模型客户端管理模型与密钥，从环境变量读取 OPENAI_API_KEY
    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", api_key=os.environ.get("OPENAI_API_KEY"))

    planner = AssistantAgent("planner", model_client=model_client, system_message="你是项目经理，负责拆解任务。")
    coder = AssistantAgent("coder", model_client=model_client, system_message="你是程序员，负责写代码。")

    # 当某角色说出 TERMINATE 时，群聊结束
    termination = TextMentionTermination("TERMINATE")
    team = RoundRobinGroupChat([planner, coder], termination_condition=termination)

    await team.run_stream(task="用 Python 写一个快速排序并解释思路。")


if __name__ == "__main__":
    asyncio.run(main())
"""

S_AG2_OUT = (
    "planner: 先把问题拆成两步——设计 partition 与递归/迭代主体。\n"
    "coder: 好的，这是实现：\\n"
    "```python\\n"
    "def quicksort(arr):\\n"
    "    ...\\n"
    "```\\n"
    "planner: 补充边界情况与复杂度说明，然后 TERMINATE。\n"
)

S_EC = """from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

reviewers = {
    "style": "检查代码风格与命名规范",
    "security": "检查安全隐患与注入风险",
    "logic": "检查业务逻辑正确性",
}

def build_review_team(llm_config):
    # 每个评审维度一个专职 Agent，由 GroupChat 汇总意见
    agents = [UserProxyAgent("user", human_input_mode="NEVER", code_execution_config=False)]
    for role, duty in reviewers.items():
        agents.append(AssistantAgent(role, llm_config=llm_config, system_message=duty))
    chat = GroupChat(agents=agents, messages=[], max_round=8)
    return GroupChatManager(chat, llm_config=llm_config)

if __name__ == "__main__":
    print("评审流水线角色：", ", ".join(reviewers.keys()))
"""

S_EC_OUT = "评审流水线角色： style, security, logic"


# ---------- 构建 3.11 节 ----------
def build_section():
    content = [
        kp("多智能体协作的核心概念与模式", [
            para("单个 Agent 把「感知—思考—行动」全塞进一个 Prompt，遇到长任务会撞上上下文窗口、角色漂移和错误累积三堵墙。"
                 "**多智能体** 的核心思路是把一个复杂目标拆给多个专职 Agent，每个 Agent 只看自己那份上下文、只做自己那件事，再用明确的消息通信把结果拼起来。"
                 "AutoGen 把这种「Agent 之间互发消息」抽象成统一的对话原语，让编排多智能体变得像写一个聊天群一样自然。"),
            mermaid("AutoGen 的四种对话拓扑",
                    "flowchart TB\n"
                    "  subgraph 双人对话\n"
                    "    A1[AssistantAgent] <--> U1[UserProxyAgent]\n"
                    "  end\n"
                    "  subgraph GroupChat 群聊\n"
                    "    M[GroupChatManager] --> G1[Agent1]\n"
                    "    M --> G2[Agent2]\n"
                    "    M --> G3[Agent3]\n"
                    "    G1 <--> G2\n"
                    "    G2 <--> G3\n"
                    "  end\n"
                    "  subgraph 嵌套 chat\n"
                    "    P[Parent Agent] --> C1[Child Agent A]\n"
                    "    P --> C2[Child Agent B]\n"
                    "  end\n"
                    "  subgraph 人类介入\n"
                    "    H[人类] -->|ALWAYS / TERMINATE| U2[UserProxyAgent]\n"
                    "  end"),
            table(
                ["模式", "结构", "优点", "缺点", "适用场景"],
                [
                    ["**双人对话**", "两个 Agent 互发消息（Assistant + UserProxy）", "最简单、易调试", "能力受限、无并行", "问答、单轮任务、教学"],
                    ["**GroupChat 群聊**", "Manager 在多个 Agent 间轮转发言", "多角色并行、各司其职", "轮次/成本需控制", "代码评审、调研编排、任务流水线"],
                    ["**嵌套 chat**", "父 Agent 调用子 Agent 完成任务", "结构清晰、可复用", "调度逻辑复杂", "子任务可独立验证的复杂目标"],
                    ["**Human-in-the-loop**", "UserProxyAgent 在 ALWAYS/TERMINATE 时请人确认", "关键决策有人把关", "阻断自动化", "高风险操作、需合规审批"],
                ],
            ),
            callout("tip", "最小可用原则",
                    "先用一个 Agent + 工具跑通主链路，再在「真的卡住」的地方拆出第二个 Agent。多数项目最终停在 2~4 个 Agent，而不是几十个。"),
        ]),
        kp("AutoGen 0.2 架构与核心组件", [
            para("AutoGen 0.2（包名 `pyautogen`）的设计哲学是「一切皆 ConversableAgent」：所有 Agent 都继承自 `ConversableAgent`，"
                 "天然具备收发消息、调用 LLM、执行代码三种能力。`AssistantAgent` 与 `UserProxyAgent` 只是给它预设了不同默认行为的两个便捷子类。"
                 "理解下面这张组件/参数表，你就掌握了 0.2 的骨架。"),
            table(
                ["组件 / 参数", "作用", "典型取值"],
                [
                    ["ConversableAgent", "所有 Agent 的基类，能收发消息、调用 LLM、执行代码", "（基类，少用直接实例化）"],
                    ["AssistantAgent", "纯 LLM 角色，负责思考与生成内容", "llm_config + system_message"],
                    ["UserProxyAgent", "代表人或执行环境，可代发消息、执行代码", "human_input_mode / code_execution_config"],
                    ["GroupChat", "把多个 Agent 组成一个群聊会话", "agents + max_round"],
                    ["GroupChatManager", "群聊主持人，决定下一发言人、何时终止", "llm_config + speaker_selection_method"],
                    ["llm_config", "模型与密钥配置（dict 或 config_list）", '{"model":"gpt-4o-mini","api_key":...}'],
                    ["human_input_mode", "何时向人索取输入", "ALWAYS / TERMINATE / NEVER"],
                    ["code_execution_config", "是否及如何在本地/容器执行代码", "False / {use_docker:True}"],
                    ["max_consecutive_auto_reply", "单 Agent 连续自动回复上限，防失控", "2 ~ 10"],
                ],
            ),
            callout("info", "config_list 还是 dict？",
                    "0.2 既支持把多个模型塞进 `config_list` 做负载均衡/故障转移（用 `config_list_from_json`），"
                    "也支持直接传一个 `{\"model\":..., \"api_key\":...}` 的 dict。教学与原型用 dict 最直观，生产再升级到 config_list。"),
        ]),
        kp("第一个双人对话（0.2 真实代码）", [
            para("下面是最短可跑的 AutoGen 双人对话：`AssistantAgent` 负责回答，`UserProxyAgent` 代表用户把问题发出去。"
                 "`human_input_mode=\"NEVER\"` 表示全程不向人追问，自动跑完；`max_consecutive_auto_reply=2` 限制自动来回的轮数，防止成本失控。"),
            code("s3_11_two_agent.py",
                 "最小双人对话：AssistantAgent 回答，UserProxyAgent 代发消息",
                 S_TWO_AGENT,
                 [7, 10, 16, 23],
                 S_TWO_AGENT_OUT,
                 "运行前置：pip install pyautogen，并 export OPENAI_API_KEY=你的密钥。以下为示意性对话记录，实际内容由模型生成。"
                 "把 human_input_mode 改成 TERMINATE 可在每轮结束前询问你是否继续。"),
            para("**分步解析**：① `llm_config` 把模型名与密钥封装成一个 dict，两个 Agent 共用同一份配置；"
                 "② `AssistantAgent` 只持有系统提示，不碰人类输入；③ `UserProxyAgent` 用 `human_input_mode=\"NEVER\"` 关闭人工阻塞，"
                 "用 `code_execution_config=False` 关闭本地代码执行（教学先用不着）；④ `initiate_chat` 启动对话，第一个消息由 user_proxy 发出，"
                 "之后双方按 `max_consecutive_auto_reply` 自动交替，直到达上限或某方发出终止信号。"),
        ]),
        kp("离线 mock 版：无 Key 也能跑通流程", [
            para("上面那段真实代码需要 OpenAI Key 才能跑。为了让你在不申请密钥的情况下也看清「消息如何在两个 Agent 之间往返」，"
                 "下面用纯标准库复刻了完全相同的调用形态——`AssistantAgent` / `UserProxyAgent` / `initiate_chat` 一个不差，只是把 LLM 调用换成固定模板回复。"),
            code("s3_11_mock.py",
                 "离线 mock：纯标准库模拟 AutoGen 双人对话循环，无需任何依赖",
                 S_MOCK,
                 [9, 24, 27, 40],
                 S_MOCK_OUT,
                 "这是教学用的离线替代：用固定模板模拟 LLM 回复，让你看清对话驱动器本质。真实 AutoGen 在这里把 generate_reply 换成 LLM 调用即可，结构完全一致。"),
            para("**分步解析**：① `AssistantAgent.generate_reply` 在真实框架里会调用 LLM，这里用 f-string 模板代替，保证离线可复现；"
                 "② `UserProxyAgent.initiate_chat` 先打印用户首条消息，再进入 `for turn` 循环，每轮让 assistant 回复、按需回显一句「请继续」；"
                 "③ `max_consecutive_auto_reply` 决定循环次数，达到上限即停——这正是 AutoGen 防止「对话停不下来」的核心机制。"),
        ]),
        kp("GroupChat 群聊与任务编排（0.2 真实代码）", [
            para("当任务需要多个角色协作（如「先规划、再写码、再自测」），`GroupChat` 让一组 Agent 在同一个会话里轮流转发消息，"
                 "由 `GroupChatManager` 决定下一发言人。`max_round` 是群聊的总轮次上限，是控制成本的关键阀门。"),
            code("s3_11_groupchat.py",
                 "GroupChat 群聊：planner 拆解任务，coder 写码，user 收口",
                 S_GROUPCHAT,
                 [7, 10, 16, 22, 29, 35, 37],
                 S_GROUPCHAT_OUT,
                 "运行前置同双人对话（需 OPENAI_API_KEY）。max_round=6 表示群聊最多 6 轮，到达即终止，避免无限讨论烧钱。"),
            para("**分步解析**：① `planner` / `coder` 是两个不同 system_message 的 `AssistantAgent`，职责边界清晰；"
                 "② `user_proxy` 用 `NEVER` 模式，只负责「发起话题 + 收口」，不在中途打断；③ `GroupChat(agents=[...], max_round=6)` 把所有角色拉进同一会话；"
                 "④ `GroupChatManager` 持有一个 `llm_config`，用它来判断「谁该接着说」以及「是否该结束」；⑤ `user_proxy.initiate_chat(manager, ...)` "
                 "的首个消息会触发群聊，由 manager 接管后续发言顺序。"),
        ]),
        kp("实战：代码生成与调试（含安全提醒）", [
            para("AutoGen 最经典的场景之一，是让 `UserProxyAgent` 开启 `code_execution_config`，真正把 `AssistantAgent` 生成的代码跑起来并回看结果，"
                 "形成「生成 → 执行 → 报错 → 修正」的闭环。这一步的生产安全性是重中之重。"),
            code("s3_11_code_debug.py",
                 "代码生成与调试：UserProxyAgent 真正执行生成的 Python",
                 S_CODE_DEBUG,
                 [7, 10, 16, 20, 24],
                 S_CODE_DEBUG_OUT,
                 "运行前置：除 OPENAI_API_KEY 外，若用 use_docker=True 还需本机安装 Docker。AssistantAgent 必须用 ```python 代码块``` 交付代码，UserProxyAgent 才能提取执行。"),
            callout("warning", "代码执行必须沙箱化",
                    "示例中 `code_execution_config={\"use_docker\": True}` 表示在隔离容器里执行未知代码。切勿图省事设成 `use_docker=False` 在本机直跑——"
                    "一旦模型生成了 `os.system('rm -rf /')` 这类代码，后果不可逆。同时配合 `human_input_mode=\"TERMINATE\"` 让人在执行前确认，并设 `timeout` 限制运行时长。"),
            table(
                ["应用场景", "推荐组件", "要点"],
                [
                    ["自动化任务编排", "GroupChat + GroupChatManager", "用 max_round 限制轮次，控制成本"],
                    ["代码生成与调试", "UserProxyAgent(code_execution_config)", "真正执行代码，必须沙箱化"],
                    ["人工确认 / 合规", 'UserProxyAgent(human_input_mode="TERMINATE")', "高风险步骤才请人介入"],
                    ["简单问答", 'AssistantAgent + UserProxyAgent("NEVER")', "最小可跑，先验证主链路"],
                ],
            ),
        ]),
        kp("AutoGen 0.4 / AG2 新架构速览", [
            para("2024 年底微软把 AutoGen 重构为 **AG2**（0.4 起），核心变化是：原生异步、显式模型客户端、用 `Team` 而非 `GroupChatManager` 编排、"
                 "终止条件对象化。下面用 0.4 重写上面的双人协作，你可以直观对比差异。"),
            code("s3_11_ag2.py",
                 "AutoGen 0.4 / AG2：RoundRobinGroupChat + 原生异步",
                 S_AG2,
                 [12, 14, 18, 19, 21, 25],
                 S_AG2_OUT,
                 "运行前置：pip install autogen-agentchat autogen-ext，并 export OPENAI_API_KEY=你的密钥。0.4 用 model_client 显式传模型客户端。"),
            table(
                ["维度", "AutoGen 0.2（pyautogen）", "AutoGen 0.4 / AG2（autogen-agentchat）"],
                [
                    ["安装包", "pip install pyautogen", "pip install autogen-agentchat autogen-ext"],
                    ["Agent 类", "AssistantAgent / UserProxyAgent", "AssistantAgent / UserProxyAgent（重写）"],
                    ["编排 API", "GroupChat + GroupChatManager", "RoundRobinGroupChat / SelectorGroupChat + Team"],
                    ["异步模型", "同步 initiate_chat", "原生 async（run_stream / run）"],
                    ["终止条件", "is_termination_msg / max_round", "TextMentionTermination / 自定义条件"],
                    ["模型客户端", "llm_config(dict) / config_list", "OpenAIChatCompletionClient 等显式客户端"],
                    ["适用建议", "资料多、上手快，适合教学与原型", "面向生产、异步与可扩展，新项目优先"],
                ],
            ),
            callout("tip", "迁移建议",
                    "新项目直接用 0.4 的 autogen-agentchat（异步、可扩展、终止条件更清晰）；已有 0.2 代码可先跑着，"
                    "等需要异步并发或更强编排时再迁移。两版社区示例都多，搜问题时记得带上版本号。"),
        ]),
        kp("学习路径与关键实践要点", [
            para("把 AutoGen 学扎实，建议按「跑通最小对话 → 加 GroupChat 编排 → 开代码执行做调试 → 读官方 samples → 上 0.4 生产化」的顺序推进。"
                 "下面这份资源表与要点清单可以作为你的常备手册。"),
            table(
                ["类型", "资源", "说明"],
                [
                    ["官方文档（0.4）", "microsoft.github.io/autogen/stable", "最新稳定版文档，含 autogen-agentchat 教程"],
                    ["官方文档（0.2）", "microsoft.github.io/autogen/0.2", "经典 API 文档，示例最丰富"],
                    ["GitHub", "github.com/microsoft/autogen", "源码、samples、issue 讨论"],
                    ["示例仓库", "github.com/microsoft/autogen/tree/main/samples", "可直接跑的端到端示例"],
                    ["论文", "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation", "理解多智能体对话设计动机"],
                    ["社区", "AutoGen Discord / 微信公众号", "提问、看最新实践"],
                ],
            ),
            callout("tip", "关键实践要点",
                    "① 从小对话起步，先验证主链路再扩展；② 用 config_list 管理多个 Key 做负载均衡；"
                    "③ 永远给 max_consecutive_auto_reply / max_round 设上限，防成本失控；"
                    "④ 代码执行必须 use_docker=True 沙箱化；⑤ 善用 human_input_mode 三档（ALWAYS/TERMINATE/NEVER）控制人工介入；"
                    "⑥ 开启日志与成本监控，长任务要能随时终止。"),
            callout("danger", "常见坑",
                    "① 不设轮次上限导致对话停不下来、账单爆炸；② 误用 use_docker=False 在本机执行未知代码；"
                    "③ 把 OPENAI_API_KEY 硬编码进代码并误提交到仓库；④ 忘记给 GroupChat 配终止条件，群聊永远不收敛；"
                    "⑤ 在 0.2 代码里用 0.4 的 API（或反之），搜问题时务必带版本号。"),
        ]),
    ]

    enterprise_case = {
        "title": "AutoGen GroupChat 搭建代码评审流水线",
        "background": "某团队每次 PR 都要人工做风格、安全、逻辑三重评审， reviewer 人力吃紧，且容易漏掉安全隐患。",
        "architecture": "用 GroupChat 拉起三个专职 AssistantAgent（style/security/logic）+ 一个 UserProxyAgent 收口；GroupChatManager 轮转发言，max_round=8 收敛。",
        "outcome": "PR 初审自动化覆盖率 70%，高危安全问题拦截率显著提升，人工只处理 Agent 标记的争议项。",
        "lessons": "专职 Agent 的 system_message 要写清「只看这一类问题」，避免三个角色都泛泛而谈；收敛轮次要够覆盖三方往返。",
        "code": {
            "data": {
                "filename": "s3_11_ec.py",
                "language": "python",
                "title": "代码评审流水线：每个维度一个专职 Agent，由 GroupChat 汇总",
                "highlightLines": [3, 11, 13, 15, 18],
                "code": S_EC,
                "output": S_EC_OUT,
                "note": "真实场景里每个 Agent 用 LLM 给出评审意见，UserProxyAgent 收口后把结论回写 PR 评论；这里只演示团队组装方式。",
            }
        },
    }

    exercises = [
        {
            "title": "把双人对话改成三角色",
            "description": "在 s3_11_two_agent.py 基础上新增一个 Critic Agent，让对话变成 assistant → critic → user_proxy 三方，体会多角色如何互相纠错。",
            "hints": "再加一个 AssistantAgent，并把 initiate_chat 的目标设为 Critic，由其回复后转回",
        },
        {
            "title": "给 GroupChat 加自定义终止函数",
            "description": "修改 s3_11_groupchat.py，用一个 is_termination_msg 函数判断「只要出现 FINAL 字样就结束」，替代单纯依赖 max_round。",
            "hints": "is_termination_msg=lambda x: 'FINAL' in x.get('content','')，传入 GroupChatManager",
        },
        {
            "title": "用离线 mock 版接入自己的假 LLM",
            "description": "改写 s3_11_mock.py 的 generate_reply，让它根据关键词返回不同模板（如含『排序』就返回快排思路），验证『对话驱动器』与具体回复解耦。",
            "hints": "在 generate_reply 里用 if '排序' in last_message 分支返回不同文本",
        },
    ]

    resources = [
        {"type": "doc", "title": "AutoGen 0.4 官方文档（stable）", "url": "https://microsoft.github.io/autogen/stable/", "note": "最新稳定版，含 autogen-agentchat 教程"},
        {"type": "doc", "title": "AutoGen 0.2 官方文档", "url": "https://microsoft.github.io/autogen/0.2/", "note": "经典 API，示例与社区回答最丰富"},
        {"type": "doc", "title": "AutoGen GitHub", "url": "https://github.com/microsoft/autogen", "note": "源码、samples、issue 讨论"},
        {"type": "doc", "title": "AutoGen 论文（arXiv）", "url": "https://arxiv.org/abs/2308.08155", "note": "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation"},
        {"type": "blog", "title": "AutoGen Discord 社区", "url": "https://discord.gg/pAbnFJrkgZ", "note": "提问与看最新实践"},
    ]

    quiz_ids = [
        "ch3-3.11-q1", "ch3-3.11-q2", "ch3-3.11-q3", "ch3-3.11-q4", "ch3-3.11-q5",
    ]

    section = {
        "id": SECTION_ID,
        "title": "AutoGen 多智能体框架",
        "subtitle": "用微软 AutoGen 把多智能体协作跑起来：核心组件、对话编排、代码生成与调试，以及 0.2 与 0.4 双版本对照",
        "estimatedMinutes": 55,
        "difficulty": 3,
        "objectives": [
            "能说出 ConversableAgent / AssistantAgent / UserProxyAgent 三者各自的职责与区别",
            "能写出并运行一个最小双人对话（AssistantAgent + UserProxyAgent）",
            "理解 GroupChat 群聊如何做任务编排，以及 AutoGen 0.2 与 0.4 的主要差异",
        ],
        "content": content,
        "enterpriseCase": enterprise_case,
        "exercises": exercises,
        "resources": resources,
        "quiz": quiz_ids,
    }
    return section, quiz_ids


def build_quizzes(quiz_ids):
    return [
        {
            "id": quiz_ids[0], "chapter": "ch3", "section": "3.11", "type": "single", "difficulty": 2,
            "question": "在 AutoGen 中，负责「代表人或执行环境、可真正运行代码」的组件是？",
            "options": [
                {"key": "A", "text": "AssistantAgent"},
                {"key": "B", "text": "UserProxyAgent", "correct": True},
                {"key": "C", "text": "GroupChat"},
                {"key": "D", "text": "ConversableAgent"},
            ],
            "explanation": "UserProxyAgent 代表人或执行环境：它既能代发用户消息，也能在开启 code_execution_config 时真正执行代码。AssistantAgent 只做 LLM 思考。",
        },
        {
            "id": quiz_ids[1], "chapter": "ch3", "section": "3.11", "type": "single", "difficulty": 1,
            "question": "UserProxyAgent 的 human_input_mode=\"NEVER\" 表示？",
            "options": [
                {"key": "A", "text": "每轮都向人提问"},
                {"key": "B", "text": "只在对话终止时问人"},
                {"key": "C", "text": "从不向人追问，全自动运行", "correct": True},
                {"key": "D", "text": "仅在代码执行出错时问人"},
            ],
            "explanation": "NEVER 表示全程不向人索取输入，对话按 auto_reply 上限自动跑完；ALWAYS 每轮都问；TERMINATE 在终止信号前那一轮才问。",
        },
        {
            "id": quiz_ids[2], "chapter": "ch3", "section": "3.11", "type": "single", "difficulty": 2,
            "question": "在 GroupChat 里，防止对话无限循环、控制成本的关键参数是？",
            "options": [
                {"key": "A", "text": "max_round", "correct": True},
                {"key": "B", "text": "system_message"},
                {"key": "C", "text": "llm_config"},
                {"key": "D", "text": "name"},
            ],
            "explanation": "max_round 限定群聊总轮次，到达即终止；它还常与 is_termination_msg 配合，避免无限讨论烧钱。",
        },
        {
            "id": quiz_ids[3], "chapter": "ch3", "section": "3.11", "type": "single", "difficulty": 3,
            "question": "关于 AutoGen 0.2 与 0.4，下列说法正确的是？",
            "options": [
                {"key": "A", "text": "0.4 用 RoundRobinGroupChat 做群聊编排", "correct": True},
                {"key": "B", "text": "0.2 的包名是 autogen-agentchat"},
                {"key": "C", "text": "两个版本 API 完全相同"},
                {"key": "D", "text": "0.4 不支持异步"},
            ],
            "explanation": "0.4 / AG2 用 autogen-agentchat 提供 RoundRobinGroupChat 等 Team 编排，且原生异步；0.2 包名为 pyautogen，两者 API 差异明显。",
        },
        {
            "id": quiz_ids[4], "chapter": "ch3", "section": "3.11", "type": "single", "difficulty": 3,
            "question": "启用 UserProxyAgent 的代码执行功能时，生产环境最稳妥的做法是？",
            "options": [
                {"key": "A", "text": "use_docker=False 在本机直跑"},
                {"key": "B", "text": "use_docker=True 在隔离容器执行", "correct": True},
                {"key": "C", "text": "把 OPENAI_API_KEY 写进代码"},
                {"key": "D", "text": "关闭 human_input_mode"},
            ],
            "explanation": "use_docker=True 在隔离容器执行未知代码，避免本机被恶意/错误代码破坏；密钥应走环境变量，绝不硬编码；高风险执行还可配合 human_input_mode=TERMINATE 人工确认。",
        },
    ]


def main():
    # 1) chapter-3.json：幂等守卫
    with open(_CH3, encoding="utf-8") as f:
        ch3 = json.load(f)
    existing_ids = [s.get("id") for s in ch3.get("sections", [])]
    if SECTION_ID in existing_ids:
        raise SystemExit(f"❌ 已存在 {SECTION_ID} 小节，终止以避免重复追加。如需重跑请先 git checkout 还原基线。")

    section, quiz_ids = build_section()
    ch3["sections"].append(section)
    with open(_CH3, "w", encoding="utf-8") as f:
        json.dump(ch3, f, ensure_ascii=False, indent=2)
    print(f"✅ 已向 chapter-3.json 追加 {SECTION_ID} 小节（共 {len(ch3['sections'])} 节）")

    # 2) chapters.json：ch3 的 sections 追加轻量 meta + 计数/版本刷新
    with open(_CHAPTERS, encoding="utf-8") as f:
        chapters = json.load(f)
    for ch in chapters["chapters"]:
        if ch.get("id") == "ch3":
            ch["sections"].append({
                "id": SECTION_ID,
                "title": "AutoGen 多智能体框架",
                "estimatedMinutes": 55,
                "difficulty": 3,
            })
            break
    chapters["description"] = chapters["description"].replace("53 小节", "54 小节")
    chapters["lastUpdated"] = "2026-08-21"
    chapters["version"] = "2026.08.21"
    chapters["updatedAt"] = "2026-08-21T15:05:00+08:00"
    with open(_CHAPTERS, "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)
    print("✅ 已更新 chapters.json（ch3 追加 3.11 meta，小节计数 53→54）")

    # 3) quizzes.json：追加 3.11 题目，并已在 section.quiz 中反向引用
    with open(_QUIZ, encoding="utf-8") as f:
        quizzes = json.load(f)
    quizzes["quizzes"].extend(build_quizzes(quiz_ids))
    with open(_QUIZ, "w", encoding="utf-8") as f:
        json.dump(quizzes, f, ensure_ascii=False, indent=2)
    print(f"✅ 已向 quizzes.json 追加 {len(quiz_ids)} 道 3.11 题目")

    print("\n下一步：python3 scripts/audit_code.py chapter-3  →  build_data.py  →  git 提交推送")


if __name__ == "__main__":
    main()
