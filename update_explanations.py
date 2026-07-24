# -*- coding: utf-8 -*-
"""为 agent-learning-path 补充/刷新「详解」类内容（零基础友好，与最新代码同步）。
修改 chapter-1.json（客服示例旁新增独立 TOOLS 详解）与 chapter-2.json
（刷新第三节 Tool Calling、补充 Agent Loop/ReAct、RAG、记忆、进阶工具调用）。
两个文件均为 JSON round-trip 安全，整体 json.dump 重写无碍。
"""
import json, os

DATA = "assets/data"

def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)

def save(name, obj):
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")

# ---------- 通用 block 构造 ----------
def para(text):       return {"type": "paragraph", "text": text}
def callout(variant, title, text):
    return {"type": "callout", "variant": variant, "title": title, "text": text}
def mermaid(title, code):
    return {"type": "mermaid", "data": {"title": title, "code": code}}
def code_block(filename, language, title, highlight, code):
    return {"type": "code", "data": {"filename": filename, "language": language,
            "title": title, "highlightLines": highlight, "code": code}}

# ============================================================
# chapter-1：在 section 0 末尾插入独立「TOOLS 详解」
# ============================================================
ch1 = load("chapter-1.json")

tools_detail = {
    "type": "knowledgePoint",
    "title": "TOOLS 详解：工具是怎么被定义和调用的（零基础版）",
    "content": [
        para("在上面的「企业级案例」里，客服 Agent 能查知识库、查订单、转人工——它为什么能“调用”这些功能？"
             "秘密就在一个叫 **TOOLS** 的清单里。本节用最直白的方式讲清楚三件事："
             "TOOLS 长什么样、为什么长这样、以及一次工具调用从发起到拿到结果，到底经历了什么。"),
        para("先给你看一眼 TOOLS 长什么样（简化自上面的 customer_service_agent.py）："),
        code_block(
            "tools_snippet.py", "python",
            "TOOLS 清单长什么样（简化自客服示例）",
            [3, 4, 5, 9, 10, 11],
            "# TOOLS 清单：告诉模型“你有哪些工具可用”\n"
            "TOOLS = [\n"
            "    {\"type\": \"function\", \"function\": {\n"
            "        \"name\": \"search_knowledge_base\",\n"
            "        \"description\": \"搜索客服知识库获取标准答案\",\n"
            "        \"parameters\": {\n"
            "            \"type\": \"object\",\n"
            "            \"properties\": {\"query\": {\"type\": \"string\"}},\n"
            "            \"required\": [\"query\"]\n"
            "        }\n"
            "    }},\n"
            "    # ... 还可以继续加 query_order、transfer_to_human 等\n"
            "]"
        ),
        para("**为什么外层要套一层 `{\"type\": \"function\", ...}`？** 这是初学者最容易困惑的点，也是 OpenAI 的“可扩展”设计："
             "“type”是一个类型标签，表示“这是什么种类的工具”。目前最常见的是 `function`（普通函数），"
             "但同一套协议未来还能挂别的类型（例如代码解释器、图片生成、MCP 工具）。"
             "所以协议规定：先写 type 说明种类，再在里层用 function 写“这个函数具体叫什么、干什么、要什么参数”。"
             "多包这一层，将来加新类型时不用推翻重写整个结构。"),
        para("里层 `function` 的三项是工具自己的“身份证”："),
        {
            "type": "table",
            "data": {
                "headers": ["字段", "作用", "给谁看 / 怎么用"],
                "rows": [
                    ["**name**", "工具的唯一名字", "模型靠它来“点名”调用，比如 search_knowledge_base"],
                    ["**description**", "人类语言说明这个工具干什么", "模型靠这段描述决定“该不该用这个工具”；写得越清楚，越不会用错"],
                    ["**parameters**", "用 JSON Schema 描述调用要传哪些参数", "模型按这个格式生成参数（类型、必填项等）"]
                ]
            }
        },
        callout("note", "小知识：什么是 JSON Schema？",
                "parameters 里用的 “JSON Schema” 是一种描述数据结构的通用格式，相当于填表时的说明："
                "“姓名：文本，必填；年龄：数字，选填”。你不需要背它，照着例子改名字和类型即可。"),
        para("光定义工具还不够——真正“跑起来”靠一个**循环**。下面用大白话走一遍客服示例里的流程："),
        {
            "type": "list",
            "ordered": True,
            "items": [
                "你把“用户问题 + TOOLS 清单”一起发给模型；",
                "模型读完后，可能直接回答，也可能说“我要调用 search_knowledge_base，参数是 {query:'退货政策'}”——这叫 **tool_calls**（工具调用请求）；",
                "你的程序真的去执行这个函数，拿到结果（比如“支持 7 天无理由退货”）；",
                "把“函数名 + 结果”**回填**回对话历史；",
                "再带着新结果问一次模型，它就能给出最终的自然语言回答。"
            ]
        },
        callout("danger", "99% 新手会踩的坑：回填顺序",
                "第 2 步模型返回的工具调用，必须先把那条“带 tool_calls 的助手消息”原样追加进 messages，"
                "然后才能把工具结果以 role=\"tool\" 追加进去。少做第一步，第二次调用模型会直接报 HTTP 400 错误。"
                "原因：模型要求对话记录是一份“完整剧本”——它刚才说“我要调工具 A”，剧本里必须留着这句，"
                "后面“工具 A 的结果是……”才接得上。记住一句话：凡有 tool_calls，先 append 助手消息，再 append 每条 role=\"tool\" 结果，顺序不能反、不能漏。"),
        para("现在回去看上面的企业级案例代码，你会发现它正是这么做的："
             "`messages.append(message)` 先存助手消息，再 `for tc in message.tool_calls` 把每个结果以 role=\"tool\" 回填。"
             "理解了这条主线，你就掌握了 Function Calling 的命脉。"),
        callout("tip", "一个控制开关：tool_choice",
                "示例里写了 `tool_choice=\"auto\"`，意思是“让模型自己决定调不调工具、调哪个”。"
                "后面「进阶工具调用能力」一节会讲另外几种取值（强制调、禁止调、指定调某个）。")
    ]
}

# 插入为 section 0 的最后一个 content 块（渲染时紧邻其后的企业级案例）
ch1["sections"][0]["content"].append(tools_detail)
save("chapter-1.json", ch1)
print("chapter-1.json: 已插入独立 TOOLS 详解 (section 0 content 末尾)")

# ============================================================
# chapter-2：刷新第三节 + 新增进阶工具调用；补充 Agent Loop/ReAct、RAG、记忆
# ============================================================
ch2 = load("chapter-2.json")

# ---- 第三节（sections[3]）block 0 “Function Calling 协议”：补充“为什么嵌套”+回填铁律 ----
sec3 = ch2["sections"][3]
blk0 = sec3["content"][0]  # Function Calling 协议
# 在现有 content（paragraph + mermaid + code）之后追加两段
blk0["content"].append(para(
    "**为什么 TOOLS 要写成 `{\"type\": \"function\", \"function\": {...}}` 这种“套两层”的结构？** "
    "“type”是工具种类的标签：当前主流是 `function`（普通函数），但同一套协议预留了扩展空间，"
    "未来还能挂代码解释器、图片生成、MCP 工具等其它类型。所以先写 type 标明种类，再用里层 function 写具体定义——"
    "多包一层，是为了将来加新类型时不必推翻重写。里层三项各司其职："
    "`name` 是模型“点名”调用时用的唯一名字；`description` 是给模型看的人类语言说明，模型靠它判断“该不该用这个工具”；"
    "`parameters` 用 JSON Schema 描述调用要传哪些参数、各自什么类型、哪些必填。"
))
blk0["content"].append(callout(
    "danger", "回填铁律（务必记住）",
    "当模型返回了 `tool_calls`，你必须：① 先把那条“带 tool_calls 的助手消息”原样 `messages.append(message)` 进历史；"
    "② 再把每个工具的执行结果以 `role=\"tool\"` + `tool_call_id` 追加进去。少做第①步，第二次调用模型会直接报 HTTP 400。"
    "原因：模型把对话当成一份“完整剧本”，它说“我要调工具 A”之后，剧本里必须留着这句，"
    "“工具 A 的结果是……”才能接上。上面 function_calling.py 与第一章客服示例都严格遵循此顺序。"
))

# ---- 第三节 block 2 “工具定义最佳实践”：补一行“结果回填正确” ----
blk2 = sec3["content"][2]  # 工具定义最佳实践
tbl = None
for b in blk2["content"]:
    if b.get("type") == "table":
        tbl = b["data"]; break
if tbl is not None:
    tbl["rows"].append([
        "**结果回填正确**",
        "有 tool_calls 时，先 append 助手消息，再 append role=tool 结果",
        "漏掉助手消息 → 第二次调用报 400；见“回填铁律”"
    ])

# ---- 第三节：新增 block 3 “进阶工具调用能力” ----
advanced = {
    "type": "knowledgePoint",
    "title": "进阶工具调用能力：tool_choice / 并行调用 / 流式 / Responses API",
    "content": [
        para("前面的例子只用到了最基础的“让模型自己决定调不调工具”。生产环境里，你往往需要对工具调用做更精细的控制。"
             "下面四个能力按“常用程度”从高到低介绍。"),
        {
            "type": "table",
            "data": {
                "headers": ["能力", "作用", "常见取值 / 说明"],
                "rows": [
                    ["**tool_choice**", "控制“要不要调工具、调哪个”",
                     "auto（默认，模型自定）；none（禁止调，只凭已有知识回答）；required（必须调至少一个）；指定工具名（强制调某个，如查订单流程）"],
                    ["**parallel_tool_calls**", "是否允许模型一次返回多个工具调用",
                     "True（默认，可并行查天气+汇率）；False（一次只调一个，避免并发副作用，如同时改两笔订单）"],
                    ["**stream（流式）**", "让回复“一点一点”传回",
                     "tool_calls 也分片到达，需累积各段 delta 再 json.loads；适合做打字机式输出"],
                    ["**Responses API**", "OpenAI 2025 年推出的更简洁统一接口",
                     "原生支持工具/文件检索/电脑操作；工具定义理念与本文一致，但调用方式更精简"]
                ]
            }
        },
        para("**tool_choice 实战**：当你确定下一步“一定要查某个系统”时，用指定工具名的 tool_choice 最稳，"
             "能避免模型“偷懒”不调。例如强制查订单："
             "`tool_choice={\"type\":\"function\",\"function\":{\"name\":\"query_order\"}}`。"),
        para("**流式工具调用**的最小累积写法（思路）：循环读取 `stream`，把每段 `delta.tool_calls` 按 `index` 拼到对应槽位，"
             "流结束后对 `function.arguments` 做 `json.loads` 得到参数字典。注意参数也是分片到达的，不能直接当完整 JSON 用。"),
        callout("note", "该先学哪个？",
                "本文所有示例基于 **Chat Completions 的 tools 参数**——目前最通用、资料最多的写法，学懂它再看 Responses API 会非常轻松。"
                "Responses API 是新选择而非替代，新手先把 tools + 回填循环练熟即可。")
    ]
}
sec3["content"].append(advanced)

# ---- 第一节（sections[0]）block 1 “Agent Loop 执行流程”：加零基础类比 ----
sec0 = ch2["sections"][0]
blk0_sec0 = sec0["content"][1]  # Agent Loop 执行流程
blk0_sec0["content"].append(callout(
    "note", "用生活类比理解 Agent Loop",
    "就像你让一位助理去办事：他先“想”下一步做什么（思考）→ 去“做”那件事，比如查资料（行动）→ 看看办得怎么样（观察）→ "
    "再“想”接下来做什么……如此循环，直到事情办完给出结果。每一轮“想→做→看”就是一次 Loop。"
    "代码里靠 `max_steps` 给这个循环设上限，防止它停不下来（比如工具一直报错时）。"
))

# ---- 第二节（sections[1]）block 0 “ReAct 核心原理”：补一个具体一轮示例 ----
sec1 = ch2["sections"][1]
blk0_sec1 = sec1["content"][0]  # ReAct 核心原理
blk0_sec1["content"].append(para(
    "把一次 ReAct 循环摊开看就很直观："
    "**Thought（思考）**“我不知道北京今天天气”→ **Action（行动）**调用 `get_weather('北京')` → "
    "**Observation（观察）**拿到“25°C 晴”→ **Thought**“信息够了，我来回答”→ 输出最终答案。"
    "可见 ReAct 与传统“纯推理”最大的不同，是每一步行动后都会拿到真实结果再继续想，而不是凭空猜。"
))

# ---- 第八节（sections[7]，索引 7）RAG：在开头插入零基础入门 ----
sec7 = ch2["sections"][7]
rag_intro = {
    "type": "knowledgePoint",
    "title": "RAG 是什么？为什么需要它？（零基础版）",
    "content": [
        para("大模型像一位博学但“不看新书”的专家——它的知识停留在训练截止日，之后发生的事它不知道。"
             "**RAG（检索增强生成，Retrieval-Augmented Generation）** 就是给这位专家配一个“随时翻看的资料库”："
             "用户提问时，先去资料库找出最相关的几段，再把这几段和问题一起交给专家，他就能基于最新资料回答。"),
        para("**为什么不直接把全部资料塞进提问？** 因为资料可能有几百万字，远超模型一次能看的“上下文窗口”"
             "（可以理解成模型的“短期记忆容量”，有上限）。所以要先“检索”出最相关的几段，再生成，既省空间又更准确。"),
        callout("note", "一句话记住 RAG",
                "让模型“开卷考试”——不修改模型本身，而是在回答时临时给它相关参考资料。"
                "相比重新训练模型（Fine-tuning），RAG 更灵活、成本更低、知识还能实时更新。")
    ]
}
sec7["content"].insert(0, rag_intro)

# ---- 第六节（sections[5]，索引 5）记忆：给 block 0 加零基础类比 ----
sec5 = ch2["sections"][5]
blk0_sec5 = sec5["content"][0]  # 短期记忆 vs 长期记忆
blk0_sec5["content"].append(callout(
    "note", "用两个比喻分清两类记忆",
    "**短期记忆**像你手上正在写的那张便签：只在当前这场对话里管用，对话一结束就扔掉；模型靠它记住“刚才聊到哪了”。"
    "**长期记忆**像公司的档案室：永久保存，需要时才去查；适合存用户偏好、历史订单等跨会话信息。"
    "所谓“向量数据库”只是一种“按意思找资料”的仓库——你不用记得原话，说个意思它就能找出最相近的内容。"
))

save("chapter-2.json", ch2)
print("chapter-2.json: 已刷新第三节、新增进阶工具调用、补充 Agent Loop/ReAct/RAG/记忆 的零基础讲解")
print("DONE")
