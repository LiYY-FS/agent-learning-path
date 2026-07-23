"""
Agent 化客服系统 — 完整可运行版
===========================
基于 OpenAI Function Calling 的自主决策客服 Agent，
支持知识库搜索、订单查询、人工转接三大工具。

使用前请先配置环境变量（见下方「配置说明」）。
"""

import json
import os
import logging
from typing import Any

from openai import OpenAI

# ============================================================
#  1. 配置区 — 使用前必须填写
# ============================================================

# 方式 A（推荐）：通过环境变量配置，不将密钥硬编码到代码中
#   export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
#   export OPENAI_BASE_URL="https://api.openai.com/v1"    # OpenAI 官方
#   export OPENAI_BASE_URL="https://api.你的代理域名/v1"   # 或第三方代理/中转
#   export CS_AGENT_MODEL="gpt-4o"                          # 模型名称

# 方式 B：直接在下方填写（仅用于本地测试，切勿提交到 Git）
client = OpenAI(
    # api_key="sk-xxxxxxxxxxxxxxxx",        # ← 填写你的 API Key
    # base_url="https://api.openai.com/v1", # ← 填写 API Base URL（OpenAI 官方或中转地址）
)

# 模型名称 — 根据你所用的 API 服务商选择可用模型
# 常见选项: "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4-turbo"
# 注意：原代码中的 "gpt-5" 在多数 API 服务商处尚不可用，请替换为实际可用的模型
MODEL_NAME = os.getenv("CS_AGENT_MODEL", "gpt-4o")  # ← 默认模型，可通过环境变量覆盖

# Agent 最大工具调用轮次（防止模型无限循环调用工具）
MAX_TOOL_ROUNDS = 3

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ============================================================
#  2. 工具定义 — Agent 可调用的函数集
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "搜索客服知识库获取标准答案。当用户咨询产品使用、退换货政策、常见问题时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "用户要搜索的关键词或问题",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_order",
            "description": "根据订单号查询用户订单的当前状态和物流信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "用户提供的订单编号",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_human",
            "description": (
                "将对话转接给人工客服。仅在以下场景使用：\n"
                "- 用户明确要求转人工\n"
                "- 用户情绪激动、表达不满\n"
                "- 问题超出知识库范围且无法自动解决\n"
                "- 涉及退款、赔偿等敏感操作"
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


# ============================================================
#  3. 工具实现 — 原代码缺失的核心部分（execute_tool 及各工具函数）
# ============================================================

def search_knowledge_base(query: str) -> str:
    """
    搜索客服知识库。
    TODO: 替换为实际的 knowledge base 查询逻辑（如向量数据库检索、Elasticsearch 等）。
    当前为模拟实现，返回示例数据。
    """
    # ====== 模拟数据（生产环境请替换为真实查询）======
    mock_kb = {
        "退换货": "支持7天无理由退货，商品需保持原包装完好。请在「我的订单」页面申请。",
        "发货时间": "下单后24小时内发货，常规3-5天送达。偏远地区可能延长1-2天。",
        "修改地址": "订单未发货前可在「我的订单」中修改收货地址；已发货请联系客服拦截。",
        "发票": "电子发票将在确认收货后24小时内发送至注册邮箱，也可在「我的发票」中下载。",
        "会员等级": "会员等级根据累计消费金额自动升级：普通→银卡(1000)→金卡(5000)→钻石(20000)。",
    }
    for keyword, answer in mock_kb.items():
        if keyword in query:
            return f"[知识库命中] {answer}"
    return f"[知识库] 未找到与「{query}」直接相关的条目，建议转人工处理。"


def query_order(order_id: str) -> str:
    """
    查询订单状态。
    TODO: 替换为真实的订单系统 API 调用。
    当前为模拟实现，返回示例数据。
    """
    # ====== 模拟数据（生产环境请替换为真实 API 调用）======
    if not order_id or not order_id.strip():
        return "[错误] 订单号不能为空"

    # 模拟：根据订单号格式返回不同状态
    if order_id.startswith("TEST"):
        return (
            f"[订单查询] 订单号：{order_id}\n"
            f"状态：已签收\n"
            f"商品：Python 高级编程（第4版）x1\n"
            f"物流：顺丰速运 SF1234567890\n"
            f"下单时间：2026-07-20 14:30:00\n"
            f"签收时间：2026-07-23 09:15:00"
        )
    elif order_id.startswith("SHIP"):
        return (
            f"[订单查询] 订单号：{order_id}\n"
            f"状态：运输中\n"
            f"物流：中通快递 ZT9876543210\n"
            f"当前位置：上海市分拨中心\n"
            f"预计送达：2026-07-25"
        )
    else:
        return f"[订单查询] 未找到订单号 {order_id}，请确认订单号是否正确。"


def transfer_to_human() -> str:
    """
    转接人工客服。
    TODO: 接入实际的人工客服系统（如工单系统、在线客服排队等）。
    当前为模拟实现，记录转人工请求。
    """
    # ====== 生产环境：此处应触发转人工流程 ======
    # 例如：创建工单、推送至客服队列、发送通知等
    logger.warning("⚠️ 触发人工转接")
    return "[转人工] 已为您转接人工客服，请稍候，客服代表将尽快接入..."


def execute_tool(function_name: str, arguments: dict[str, Any]) -> str:
    """
    工具分发器 — 根据函数名路由到对应的工具执行函数。

    原代码调用了此函数但从未定义它，属于【关键缺失】。

    Args:
        function_name: 工具名（如 "search_knowledge_base"）
        arguments:     模型生成的参数字典（已由 json.loads 解析）

    Returns:
        工具执行结果的字符串表示
    """
    tool_registry = {
        "search_knowledge_base": search_knowledge_base,
        "query_order": query_order,
        "transfer_to_human": transfer_to_human,
    }

    if function_name not in tool_registry:
        error_msg = f"[错误] 未知工具: {function_name}，可用工具: {list(tool_registry.keys())}"
        logger.error(error_msg)
        return error_msg

    func = tool_registry[function_name]

    try:
        # 调用对应工具函数，将参数解包传入
        result = func(**arguments)
        logger.info("✅ 工具执行成功: %s(%s) → %s", function_name, arguments, result[:100])
        return result
    except TypeError as e:
        error_msg = f"[错误] 工具 {function_name} 参数错误: {e}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"[错误] 工具 {function_name} 执行异常: {type(e).__name__}: {e}"
        logger.error(error_msg)
        return error_msg


# ============================================================
#  4. Agent 主逻辑
# ============================================================

SYSTEM_PROMPT = """你是电商客服助手。你的职责：
1. 根据用户问题自主判断是否需要调用工具
2. 使用 search_knowledge_base 回答产品/政策类问题
3. 使用 query_order 查询订单状态
4. 当用户情绪激动、要求转人工、或问题无法自动解决时，使用 transfer_to_human
5. 回答要简洁、专业、有礼貌

重要约束：
- 不要编造信息，如果不知道就查知识库或转人工
- 如果用户表达不满或愤怒，优先转人工"""


def customer_service_agent(user_message: str, user_id: str) -> str:
    """
    Agent 化客服主入口 — 自主决策调用工具并生成最终回复。

    Args:
        user_message: 用户输入的消息文本
        user_id:      用户唯一标识（可用于日志追踪、个性化等）

    Returns:
        Agent 生成的最终回复文本
    """

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    # 【修复】记录 user_id 到上下文，供后续可能的个性化逻辑使用
    logger.info("👤 用户 [%s] 发起咨询: %s", user_id, user_message[:80])

    try:
        # ---- 第一轮：让模型决定是否调用工具 ----
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",  # 让 Agent 自主决定是否使用工具
            # temperature=0.1,   # 可选：降低随机性以获得更确定性的工具选择
        )

        message = response.choices[0].message

        # 如果模型没有调用工具，直接返回文本回复
        if not message.tool_calls:
            content = message.content or "(无回复)"
            logger.info("💬 直接回复: %s", content[:100])
            return content

        # ---- 模型选择了工具 → 执行工具调用循环 ----
        for round_num in range(1, MAX_TOOL_ROUNDS + 1):
            logger.info("🔧 工具调用轮次 %d/%d，共 %d 个工具", round_num, MAX_TOOL_ROUNDS, len(message.tool_calls))

            # 执行本轮所有工具调用
            for tc in message.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError as e:
                    logger.error("JSON 解析失败: %s", e)
                    fn_args = {}

                logger.info("   → 调用 %s(%s)", fn_name, fn_args)
                result = execute_tool(fn_name, fn_args)

                # 将工具结果追加到消息历史（OpenAI Function Calling 标准格式）
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

            # 将模型的 assistant 消息（含 tool_calls）也追加到历史
            messages.append(message.model_dump())

            # 【修复】第二轮及之后的请求也必须携带 tools 参数，
            # 否则模型将丢失工具定义，无法继续进行 Function Calling
            follow_up = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            message = follow_up.choices[0].message

            # 如果模型不再调用工具，结束循环
            if not message.tool_calls:
                break

        # 达到最大轮次仍有工具调用，强制截断并提示
        if message.tool_calls:
            logger.warning("⚠️ 达到最大工具调用轮次 (%d)，终止循环", MAX_TOOL_ROUNDS)
            messages.append({"role": "system", "content": "请直接总结已有信息回答用户，不要再调用工具。"})
            final = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
            )
            return final.choices[0].message.content or "(生成失败)"

        content = message.content or "(无回复)"
        logger.info("✅ 最终回复: %s", content[:150])
        return content

    except Exception as e:
        error_msg = f"[系统异常] {type(e).__name__}: {e}"
        logger.exception("❌ Agent 执行失败")
        return error_msg


# ============================================================
#  5. 入口 / 测试
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Agent 化客服系统 — 测试模式")
    print(f"  模型: {MODEL_NAME}")
    print("=" * 60)

    # 简单交互式测试循环
    test_cases = [
        ("我想退货，怎么操作？", "user_001"),
        ("查一下订单 TEST20260720001", "user_002"),
        ("我要投诉！你们的服务太差了！！", "user_003"),
        ("你们有什么会员权益？", "user_004"),
    ]

    for msg, uid in test_cases:
        print(f"\n👤 用户 [{uid}]: {msg}")
        print("-" * 40)
        reply = customer_service_agent(msg, uid)
        print(f"🤖 客服: {reply}")
        print()
