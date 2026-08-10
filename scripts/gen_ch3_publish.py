#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 3.6（MCP）与 3.7（Skill）补充「从零创建 → 关键配置 → 打包发布 → 版本管理」完整工程化教程。

落点（已与用户确认）：
  - 3.6 在「深入解析与实战」heading 之前插入 15 块 + 2 练习 + 3 资源。
  - 3.7 在 content 末尾追加 14 块 + 2 练习 + 4 资源。
  - 不新增 section、不重编号，避免再次触发 quiz 双向关联与进度失效。
  - 顺带修复 3.7 的两个既有 quiz bug（6 题缺 correct；chapterQuizzes 引用未随重编号迁移）。

幂等保护：若两段哨兵 heading 已存在则直接退出，重复运行不会重复追加。

运行：python3 scripts/gen_ch3_publish.py
之后必跑：python3 scripts/audit_code.py（须 0 问题）
        → 实跑每个 python 块比对 output → build_data.py → verify_build.py → git 提交
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "assets", "data")


# ---------------------------------------------------------------------------
# 内容块构造助手（逐字复用 gen_ch3_skill.py）
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


# ---------------------------------------------------------------------------
# 代码源（离线可运行；python 块 output 经实跑逐字节核对）
# ---------------------------------------------------------------------------

SRC_SCAFFOLD = r'''# 用 uv 初始化一个 MCP Server 工程（uv 是 Python 官方推荐的打包工具）
uv init mcp-weather --lib
cd mcp-weather

# 安装 MCP Python SDK（FastMCP 在其中）
uv add "mcp[cli]"

# 本地冒烟：以开发模式拉起 Server，验证 stdio 握手是否正常
uv run mcp dev src/mcp_weather/server.py

# 跑通后锁定依赖，保证别人复现一致
uv lock
'''

SRC_PYPROJECT = r'''[project]
name = "mcp-weather"
version = "0.1.0"
description = "A minimal MCP server exposing a weather tool"
readme = "README.md"
requires-python = ">=3.10"
dependencies = ["mcp>=1.2.0"]

[project.scripts]
mcp-weather = "mcp_weather.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
'''

SRC_CLIENT_CFG = r'''{
  "mcpServers": {
    "weather": {
      "command": "uvx",
      "args": ["--from", "mcp-weather", "mcp-weather"],
      "env": { "OPENWEATHER_API_KEY": "填入你的密钥" }
    },
    "weather-local": {
      "command": "uv",
      "args": ["--directory", "/abs/path/to/mcp-weather", "run", "mcp-weather"]
    },
    "weather-node": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    }
  }
}
'''

SRC_SERVER_JSON = r'''{
  "name": "io.github.yourname/mcp-weather",
  "description": "MCP server exposing weather lookup and alerts as tools",
  "version": "0.1.0",
  "repository": { "url": "https://github.com/yourname/mcp-weather" },
  "homepage": "https://github.com/yourname/mcp-weather#readme",
  "packages": [
    {
      "registryType": "pypi",
      "identifier": "mcp-weather",
      "runtimeHint": "uvx",
      "transport": ["stdio"]
    }
  ]
}
'''

SRC_PUBLISH = r'''# 1) 先发到 TestPyPI 验证安装链路，不出错再上正式源
uv build
uv publish --publish-url https://test.pypi.org/legacy/ dist/*

# 2) 正式发布（推荐配置 Trusted Publishing / OIDC，免长期 token）
uv publish dist/*

# 3) 别人即可一行安装并运行你的 Server
uvx mcp-weather
'''

SRC_GUARD = r'''from dataclasses import dataclass

@dataclass
class ToolSchema:
    name: str
    required: list
    optional: list
    returns: str

def bump(level, base="1.0.0"):
    maj, min_, pat = (int(x) for x in base.split("."))
    if level == "major":
        return f"{maj+1}.0.0"
    if level == "minor":
        return f"{maj}.{min_+1}.0"
    return f"{maj}.{min_}.{pat+1}"

def diff_level(old, new):
    if old.name != new.name or set(old.required) != set(new.required) or old.returns != new.returns:
        return "major"
    if set(new.optional) > set(old.optional) or old.optional != new.optional:
        return "minor"
    return "patch"

OLD = ToolSchema("query_order", ["order_id"], ["detail"], "dict")
NEW = ToolSchema("query_order", ["order_id"], ["detail", "lang"], "dict")

if __name__ == "__main__":
    level = diff_level(OLD, NEW)
    print(f"{OLD.name}: {level} -> {bump(level)}")
'''

SRC_TREE = r'''skill-weather/
├── SKILL.md            # 必需：能力声明 + 使用说明
├── scripts/            # 可选：脚本（如数据抓取、格式转换）
│   └── fetch.py
├── references/         # 可选：详细文档，被 SKILL.md 引用
│   └── api.md
└── assets/             # 可选：模板、示例、静态资源
    └── sample.json
'''

SRC_SKILL_MD = r'''---
name: weather-skill
description: 查询指定城市的实时天气与预警。当用户问"今天天气""是否下雨""气象预警"时使用；关键词：天气、气温、降雨、预警。
license: MIT
compatibility: 需要 Python 3.10+ 与 OpenWeather API key
metadata:
  author: yourname
  version: 1.0.0
allowed-tools: Read Bash(python *)
---

# Weather Skill

## Instructions
1. 从用户输入抽取城市名与日期。
2. 调用 scripts/fetch.py 获取天气数据。
3. 按用户语言格式化输出，附预警提示。

## Rules
- 缺失城市名时先追问，不要猜测。
- 不缓存超过 10 分钟的数据。

## Examples
用户："北京今天天气怎么样？"
→ 调用 fetch.py 北京今日，返回气温与降雨概率。
'''

SRC_PACKAGE = r'''# 1) 用官方校验器检查 SKILL.md 合法性（安装方式见官方仓库说明，不在此编造）
skills-ref validate ./skill-weather

# 2) 以目录形式分发（用户级 / 项目级）
#    用户级：~/.workbuddy/skills/skill-weather/
#    项目级：<repo>/.workbuddy/skills/skill-weather/

# 3) 团队用 Git 仓库分发，其他人 clone 后软链到 skills 目录
git clone git@github.com:yourname/skill-weather.git
ln -s "$(pwd)/skill-weather" ~/.workbuddy/skills/skill-weather
'''

SRC_SEMVER = r'''def parse(v):
    return tuple(int(x) for x in v.split("."))

def compatible(required, candidate):
    r = parse(required)
    c = parse(candidate)
    if c[0] != r[0]:
        return False
    return c >= r

def resolve(name, required, registry):
    cands = [v for (n, v) in registry if n == name and compatible(required, v)]
    if not cands:
        return None
    return max(cands, key=parse)

REGISTRY = [
    ("order_lookup", "1.0.0"),
    ("order_lookup", "1.2.0"),
    ("order_lookup", "2.0.0"),
    ("order_lookup", "1.4.1"),
]

if __name__ == "__main__":
    print("require ^1.0.0 ->", resolve("order_lookup", "1.0.0", REGISTRY))
    print("require ^1.2.0 ->", resolve("order_lookup", "1.2.0", REGISTRY))
    print("require ^2.0.0 ->", resolve("order_lookup", "2.0.0", REGISTRY))
'''


# ---------------------------------------------------------------------------
# 3.6 新增内容（插在「深入解析与实战」heading 之前）
# ---------------------------------------------------------------------------

CONTENT_36_NEW = [
    heading("从零发布一个 MCP Server：完整工程化流程"),

    kp("第 1 步：脚手架与本地冒烟",
        para("先有一个能跑的 Server，再谈发布。用 `uv` 初始化工程、装 SDK、本地以开发模式拉起，确认 stdio 握手正常——这是后面所有发布动作的前提。"),
        code("3_6_scaffold.sh", "bash", "用 uv 初始化工程并本地冒烟测试",
            SRC_SCAFFOLD, hl=[2, 6, 9],
            note="uv 是 Python 官方推荐的打包/虚拟环境工具；`mcp dev` 会启动一个带调试界面的本地 Server。这一步不联网、不发布，纯粹验证代码本身能跑。"),
    ),

    kp("第 2 步：声明依赖与入口点（决定 uvx 能否一行拉起）",
        para("`[project]` 写元数据与依赖；关键在于 `[project.scripts]`——它把你的模块函数注册成一个控制台命令。没有它，`uvx mcp-weather` 就找不到入口，别人只能从源码跑。"),
        code("pyproject.toml", "toml", "pyproject.toml：元数据 + 依赖 + 控制台入口",
            SRC_PYPROJECT, hl=[7, 9],
            note="把版本钉死在 dependencies 里（如 mcp>=1.2.0）能保证别人装到兼容的 SDK。`[project.scripts]` 的 `模块:函数` 写法决定 `uvx` 拉起时执行哪个函数。"),
    ),

    code("claude_desktop_config.json", "json", "客户端接入配置：三种启动形态",
        SRC_CLIENT_CFG, hl=[4, 9],
        note="形态一：已发布包用 `uvx` 一行拉起；形态二：源码用 `uv --directory` 跑；形态三：Node 生态用 `npx`。`env` 用于注入密钥，切勿把密钥写进 `args`（会被记录到进程命令行）。"),

    table(
        ["配置项", "含义", "最佳实践"],
        [
            ["command", "启动 Server 的可执行文件", "写绝对路径，GUI 宿主不继承 shell 的 PATH"],
            ["args", "传给 command 的参数列表", "密钥不要进 args；放 env；路径用绝对路径"],
            ["env", "注入的环境变量", "只放必要密钥，避免泄露到进程参数"],
            ["stdio vs http", "传输方式", "本地优先 stdio；跨网络/多租户用 Streamable HTTP"],
        ],
    ),

    callout("danger", "配置四大坑",
        "① GUI 宿主（如桌面客户端）不继承 shell 的 PATH，必须写 `uvx`/`python` 的绝对路径，否则报 command not found。② 密钥硬编码进 `args` 会被记录到系统进程列表，一律走 `env`。③ 改完配置要**完全退出重启**宿主进程，仅重开对话不生效。④ Windows 商店版 Python 路径被虚拟化，建议用官方安装包的绝对路径。"),

    kp("第 4 步：发布到 PyPI，让别人 `uvx` 一键安装",
        para("本地能跑 ≠ 别人能装。把包构建并发布到 PyPI（或 TestPyPI 先行验证），别人就能 `uvx mcp-weather` 直接拉起。推荐配置 Trusted Publishing（OIDC），用 CI 的临时凭证发布，免长期 token。"),
        code("3_6_publish.sh", "bash", "构建并发布到 PyPI（TestPyPI 先行验证）",
            SRC_PUBLISH, hl=[2, 6, 9],
            note="先发 TestPyPI 验证安装链路，避免把坏包发到正式源。`uv publish` 走 PyPI 的 Trusted Publishing 时不需要在本地保存 token。"),
    ),

    kp("第 5 步：上架官方 Registry，让发现机制生效",
        para("PyPI 只解决「能装上」，但 Agent 宿主还需要一个**发现**入口——这就是官方 MCP Registry。你提交一份 `server.json` 清单，注册表据此展示你的 Server 并生成安装配置。"),
        code("server.json", "json", "server.json：官方 Registry 清单（字段照真实 schema）",
            SRC_SERVER_JSON, hl=[2, 3, 4, 7],
            note="`name` 是反向 DNS 命名空间（恰好一个斜杠）；`description` **硬上限 100 字符**，要极简；`version` 走 semver；`packages[].registryType` 标包来源（pypi/npm/oci/nuget/mcpb），`runtimeHint` 标拉起方式（uvx/npx/docker）。"),
    ),

    table(
        ["server.json 字段", "约束", "说明"],
        [
            ["name", "反向 DNS，恰好一个 /，≤200", "命名空间隔离，如 io.github.<user>/<server>"],
            ["description", "≤100 字符（硬约束）", "极简一句话，是用户在注册表里看到的唯一摘要"],
            ["version", "≤255，建议 semver", "与 PyPI 包版本保持一致"],
            ["packages[].registryType", "pypi/npm/oci/nuget/mcpb", "包从哪个源安装"],
            ["packages[].runtimeHint", "uvx/npx/docker/dnx", "宿主用什么命令拉起"],
            ["packages[].transport", "stdio / http 等", "Server 支持的传输方式"],
        ],
    ),

    callout("tip", "所有权验证与发布命令",
        "发布前要在 README 里放一行所有权标记 `mcp-name: io.github.<user>/<server>`，注册表据此确认你拥有该命名空间（Docker 版用 `LABEL io.modelcontextprotocol.server.name=`）。随后用官方发布器：`mcp-publisher validate server.json` → `mcp-publisher login <方式>` → `mcp-publisher publish`（具体安装方式以官方仓库说明为准，本文不编造命令）。"),

    kp("第 6 步：版本管理——三条独立的版本线",
        para("MCP Server 的「版本」其实有三条互相独立的线，别混为一谈：① **协议版本**（如 2025-06-18，在握手时协商，决定支持哪些原语）；② **包版本**（PyPI/npm 上的 semver，决定装哪份代码）；③ **server.json 的 version**（注册表展示用，通常与包版本对齐）。改了代码 bump 包版本，但协议没升级就不该动协议版本号。"),
    ),

    table(
        ["变更类型", "判定为", "例子"],
        [
            ["删工具 / 改必填参数名或类型 / 改返回结构", "major（破坏性）", "把 `order_id` 必填改成 `order_no`"],
            ["加工具 / 加可选参数 / 加新能力不影响旧调用", "minor（兼容新增）", "给 `query_order` 增加可选 `lang`"],
            ["改 docstring / 修 bug / 性能优化", "patch（无契约变化）", "修正返回文案里的错别字"],
        ],
    ),

    code("3_6_mcp_version_guard.py", "python", "工具契约版本守卫：自动判定 major/minor/patch",
        SRC_GUARD, hl=[16, 17], output="query_order: minor -> 1.1.0",
        note="对比新旧工具 schema：必填参数、返回结构变了就是 major；只新增可选参数就是 minor；其余是 patch。`bump` 按 semver 给出建议新版本。把这段接进 CI，每次改 tool 都自动提示该 bump 哪一位。"),

    callout("warning", "弃用流程",
        "破坏性变更不要「直接删」。旧工具名至少保留一个 minor 周期，在 `description` 前缀标注 `deprecated` 并指向替代工具，等调用方都迁移完再删除。这样下游 Agent 不会因为一次升级集体崩掉。"),

    table(
        ["维度", "Python 生态", "Node 生态"],
        [
            ["工程元数据", "pyproject.toml", "package.json"],
            ["控制台入口", "[project.scripts]", "bin 字段"],
            ["构建+发布", "uv build + uv publish", "npm publish"],
            ["一行拉起", "uvx <pkg>", "npx <pkg>"],
            ["注册表来源", "registryType: pypi", "registryType: npm"],
        ],
    ),
]


EXERCISES_36_NEW = [
    {
        "title": "写一份自己的 server.json 并本地自洽校验",
        "description": "仿照正文示例，为你的一个 MCP Server 写 `server.json`：反向 DNS 命名空间、≤100 字符的 description、semver 的 version，以及一个 pypi 包声明。然后逐项核对：`name` 是否恰好一个斜杠、`description` 是否真不超 100 字符、`packages[].registryType` 与 `runtimeHint` 是否匹配。",
        "hints": "把 description 复制到字符计数器里确认长度；`name` 用 `io.github.<你的用户名>/<服务名>` 这种反向 DNS 形式最稳妥。",
    },
    {
        "title": "为一个工具走完「破坏性变更 + 弃用」全流程",
        "description": "选正文 `query_order` 工具，把必填参数 `order_id` 改名为 `order_no`（这是 major 级破坏性变更）。按弃用流程：保留旧 `order_id` 至少一个 minor 周期、在 description 标注 deprecated 并指向新参数、用 `3_6_mcp_version_guard.py` 确认级别为 major，最后说明何时可以安全删除旧参数。",
        "hints": "破坏性变更的核心是「给下游迁移窗口」，而不是「立刻干净」。写清楚删除旧参数的触发条件（如：下一个 major 版本）。",
    },
]

RESOURCES_36_NEW = [
    {"type": "doc", "title": "MCP Registry 说明（官方）", "url": "https://modelcontextprotocol.io/registry/about", "note": "讲清楚 Server 如何上架、命名空间与所有权验证机制"},
    {"type": "doc", "title": "modelcontextprotocol/registry 代码库", "url": "https://github.com/modelcontextprotocol/registry", "note": "官方注册表实现与发布器 mcp-publisher 的源码"},
    {"type": "doc", "title": "server.json Schema（2025-12-11）", "url": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json", "note": "上架清单的字段级约束，写 server.json 时照此校验"},
]


# ---------------------------------------------------------------------------
# 3.7 新增内容（追加到 content 末尾）
# ---------------------------------------------------------------------------

CONTENT_37_NEW = [
    heading("从零创建并发布一个 Skill：SKILL.md 工程实践"),

    kp("从「Python class 抽象」到「文件约定」",
        para("前面用 Python class 演示了 Skill 的抽象，但真实工程里业界收敛成一个 **Markdown 文件（SKILL.md）** 而不是一段代码。原因很实在：Markdown 可读、可被 git diff、可版本化、不需要运行时即可被调度器「读」到——调度器在启动时就扫描所有 SKILL.md 的声明，按需再加载正文，比把逻辑编译进二进制更容易分发与审计。"),
    ),

    code("3_7_skill_tree.txt", "plaintext", "Skill 目录布局",
        SRC_TREE, hl=None,
        note="`SKILL.md` 是必需项；`scripts/`（脚本）、`references/`（长文档）、`assets/`（模板/示例）都是可选的，按需添加。目录名建议与 SKILL.md 里的 `name` 一致。"),

    code("SKILL.md", "markdown", "完整 SKILL.md 示例（frontmatter 全字段 + body 结构）",
        SRC_SKILL_MD, hl=[2, 3, 9],
        note="frontmatter 用 `---` 包裹；body 是给模型看的使用说明，常见三段：Instructions（步骤）/ Rules（约束）/ Examples（示例）。`allowed-tools` 是实验性字段，声明这个 Skill 允许调用哪些工具。"),

    table(
        ["frontmatter 字段", "必填", "约束"],
        [
            ["name", "是", "≤64；小写字母/数字/连字符；不可首尾或连续连字符；须与目录名一致"],
            ["description", "是", "≤1024；第三人称；写清「做什么 + 何时用」+ 触发关键词"],
            ["license", "否", "许可证标识，如 MIT"],
            ["compatibility", "否", "≤500；运行环境/依赖要求"],
            ["metadata", "否", "任意键值，常放 author / version"],
            ["allowed-tools", "否", "空格分隔的工具名（实验性）"],
        ],
    ),

    callout("danger", "name 命名四条硬规则",
        "① 只能小写字母、数字、连字符；② 不能以连字符开头或结尾；③ 不能有连续连字符（`my--skill` 非法）；④ 必须与目录名完全一致。反例：`WeatherSkill`（大写）、`-weather`（开头连字符）、`weather-`（结尾连字符）、`wea--ther`（连续连字符）全部非法。"),

    kp("description 是唯一的发现入口",
        para("模型/调度器在海量 Skill 里只靠 `description` 决定「这次要不要调你」。写好描述 = 写清两件事：**做什么** + **何时用**，并带够触发关键词。"),
        table(
            ["写法", "示例"],
            [
                ["差", "处理天气相关事务（太含糊，模型判断不了何时用）"],
                ["好", "查询指定城市实时天气与预警；用户问\"今天天气\"\"是否下雨\"\"气象预警\"时使用；关键词：天气、气温、降雨、预警"],
            ],
        ),
    ),

    table(
        ["加载阶段", "加载内容", "预算"],
        [
            ["启动时常驻", "frontmatter 的 metadata", "约 100 tokens"],
            ["激活时", "SKILL.md 的 body（Instructions/Rules/Examples）", "< 5000 tokens"],
            ["按需", "references/ 下的长文档、scripts/ 下的脚本", "用户触发时才读"],
        ],
    ),

    callout("tip", "控制体积，详情下沉",
        "SKILL.md 正文尽量压在 500 行内；把 API 细节、字段表、长示例放进 `references/`，在 body 里用一行引用指向它（如「详见 references/api.md」）。引用只做一层，不要链式跳转，否则模型容易中途丢失上下文。"),

    kp("第 5 步：打包与分发",
        para("Skill 的分发单元就是那个目录。校验通过后，可以放用户级目录（`~/.workbuddy/skills/`）、项目级目录（仓库内 `.workbuddy/skills/`），或整个丢进 Git 仓库让团队 clone + 软链。"),
        code("3_7_skill_package.sh", "bash", "校验、打包、安装路径",
            SRC_PACKAGE, hl=[2, 10, 11],
            note="`skills-ref validate` 校验 SKILL.md 合法性（安装方式以官方仓库说明为准）。用户级与项目级并存时通常项目级优先，便于团队锁定版本。"),
    ),

    kp("版本管理与同名多版本解析",
        para("Skill 也需要版本化：同名 Skill 升级不能破坏旧调用方，团队还可能同时装了多个版本。下面的小程序演示如何解析「满足兼容约束的最高版本」。"),
        code("3_7_skill_semver.py", "python", "semver 解析 + 兼容判定 + 同名多版本 resolve",
            SRC_SEMVER, hl=[12, 13, 14], output="require ^1.0.0 -> 1.4.1\nrequire ^1.2.0 -> 1.4.1\nrequire ^2.0.0 -> 2.0.0",
            note="`compatible` 实现 `^` 语义：主版本相同且 >= 下限。`resolve` 从注册表里挑出兼容的最高版本。当两个团队都叫 `order_lookup` 时，靠 `name` 加命名空间（如 `team-a/order_lookup`）区分，再走这套解析。"),
    ),

    table(
        ["变更类型", "判定为", "例子"],
        [
            ["改 name / 删 scripts 入口 / 收紧 allowed-tools", "major", "把 `weather-skill` 改名为 `wx-skill`"],
            ["加能力、加 references、放宽 allowed-tools", "minor", "新增「空气质量」查询子能力"],
            ["改文案、修示例、补描述", "patch", "修正 Examples 里的笔误"],
        ],
    ),

    callout("warning", "弃用与迁移",
        "下线一个 Skill 不要「直接删」。在 `metadata` 里标注 `deprecated: true` 并指向替代 Skill，保留一个版本周期让调用方迁移，再正式移除。命名空间（如 `team-a/order_lookup`）能有效隔离不同团队的同名 Skill，避免误解析到错误版本。"),

    table(
        ["维度", "Skill（SKILL.md）", "MCP Server（server.json）"],
        [
            ["分发单元", "目录（SKILL.md + 附属文件）", "包（pypi/npm/oci）+ server.json"],
            ["安装方式", "复制/软链/Git 仓库", "uvx / npx / docker 拉起"],
            ["版本载体", "SKILL.md 内 metadata.version", "包版本 + server.json version"],
            ["发现机制", "调度器扫描目录读 description", "注册表 + 客户端配置"],
            ["权限边界", "allowed-tools 声明", "宿主授予的进程权限"],
            ["是否跨进程", "通常同进程内加载", "独立进程，stdio/http 通信"],
        ],
    ),
]


EXERCISES_37_NEW = [
    {
        "title": "写一个 SKILL.md 并本地校验",
        "description": "为「订单查询」能力写一个 SKILL.md：遵守 name 命名四规则、写清 description（做什么+何时用+关键词）、用 Instructions/Rules/Examples 三段组织 body。然后用 `skills-ref validate` 校验，修正所有报错。",
        "hints": "先想清楚「这个能力解决什么业务目标」，description 就从这里提炼；body 的 Examples 用真实用户问句 → 期望动作的形式，模型最容易对齐。",
    },
    {
        "title": "为同名多版本 resolve 增加命名空间隔离",
        "description": "在 `3_7_skill_semver.py` 基础上，把注册表项从 `(name, version)` 扩展为 `(namespace, name, version)`，让 `resolve` 先按命名空间过滤再按版本解析。给 `team-a/order_lookup` 与 `team-b/order_lookup` 各放两个版本，验证不会串版本。",
        "hints": "命名空间可以简单拼成 `namespace/name` 作为注册表 key；`compatible` 与 `parse` 逻辑不变，只是过滤条件多一层。",
    },
]

RESOURCES_37_NEW = [
    {"type": "doc", "title": "Agent Skills 规范（官方）", "url": "https://agentskills.io/specification", "note": "SKILL.md 的字段级权威定义与渐进式披露预算"},
    {"type": "doc", "title": "agentskills/agentskills 参考实现", "url": "https://github.com/agentskills/agentskills", "note": "官方校验器 skills-ref 与示例 Skill 的源码"},
    {"type": "doc", "title": "MCP Registry 说明（对照阅读）", "url": "https://modelcontextprotocol.io/registry/about", "note": "理解 Server 如何上架，与 Skill 的分发形态做对照"},
    {"type": "doc", "title": "modelcontextprotocol/registry 代码库", "url": "https://github.com/modelcontextprotocol/registry", "note": "注册表实现，印证「分发单元 / 发现机制」的差异"},
]


# ---------------------------------------------------------------------------
# Bug 修复
# ---------------------------------------------------------------------------

SEC_MAP = {"3.7": "3.8", "3.8": "3.9", "3.9": "3.10"}
CORRECT_BY_ID = {
    "ch3-3.7-q1": "B",   # Skill 把工具链+流程+权限打包，Tool 是原子函数
    "ch3-3.7-q2": "B",   # description 让模型/调度器知道何时调用
    "ch3-3.7-q3": "B",   # 权限最大化是反模式，正确做法是最小化
    "ch3-3.7-q4": ["A", "B"],  # MCP 与 Skill 分属不同层次、正交互补
    "ch3-3.7-q5": "B",   # Semantic Kernel 的 Plugin（原名 Skill）
    "ch3-3.7-q6": ["A", "B", "C"],  # 大杂烩/权限过宽/缺描述都是误区
}


def remap_qid(qid):
    return re.sub(r'^(ch3-)(3\.[789])(-q\d+)$',
                  lambda m: m.group(1) + SEC_MAP[m.group(2)] + m.group(3), qid)


def fix_quizzes():
    p = os.path.join(DATA_DIR, "quizzes.json")
    q = json.load(open(p, encoding="utf-8"))

    # Bug 1: 给 6 道题补 correct
    n = 0
    for x in q["quizzes"]:
        if x["id"] in CORRECT_BY_ID:
            correct = CORRECT_BY_ID[x["id"]]
            correct = correct if isinstance(correct, list) else [correct]
            for o in x["options"]:
                o["correct"] = (o["key"] in correct)
            n += 1

    # Bug 2: chapterQuizzes 引用未随重编号迁移（ch3-3.7/3.8/3.9 -> 3.8/3.9/3.10）
    m = 0
    for entry in q.get("chapterQuizzes", []):
        if not isinstance(entry, dict):
            continue
        qs = entry.get("questions", [])
        for i, ref in enumerate(qs):
            new = remap_qid(ref)
            if new != ref:
                qs[i] = new
                m += 1

    json.dump(q, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"已更新 quizzes.json：补 correct {n} 题；迁移 chapterQuizzes 引用 {m} 处")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    p3 = os.path.join(DATA_DIR, "chapter-3.json")
    c3 = json.load(open(p3, encoding="utf-8"))

    sec36 = next(s for s in c3["sections"] if s["id"] == "3.6")
    sec37 = next(s for s in c3["sections"] if s["id"] == "3.7")

    # 幂等哨兵
    SENT1 = "从零发布一个 MCP Server：完整工程化流程"
    SENT2 = "从零创建并发布一个 Skill：SKILL.md 工程实践"
    if any(b.get("text") == SENT1 for b in sec36["content"]) and \
       any(b.get("text") == SENT2 for b in sec37["content"]):
        print("检测到哨兵 heading 已存在，视为已生成，直接退出（幂等保护）。")
        sys.exit(0)

    # 3.6：插在「深入解析与实战」heading 之前
    idx = next(i for i, b in enumerate(sec36["content"])
               if b.get("type") == "heading" and b.get("text") == "深入解析与实战")
    sec36["content"][idx:idx] = CONTENT_36_NEW
    sec36["exercises"].extend(EXERCISES_36_NEW)
    sec36["resources"].extend(RESOURCES_36_NEW)

    # 3.7：追加到末尾
    sec37["content"].extend(CONTENT_37_NEW)
    sec37["exercises"].extend(EXERCISES_37_NEW)
    sec37["resources"].extend(RESOURCES_37_NEW)

    json.dump(c3, open(p3, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"已更新 chapter-3.json：3.6 插入 {len(CONTENT_36_NEW)} 块 (+{len(EXERCISES_36_NEW)}练习 +{len(RESOURCES_36_NEW)}资源)；"
          f"3.7 追加 {len(CONTENT_37_NEW)} 块 (+{len(EXERCISES_37_NEW)}练习 +{len(RESOURCES_37_NEW)}资源)")

    fix_quizzes()
    print("\n下一步：python3 scripts/audit_code.py（须 0 问题）")


if __name__ == "__main__":
    main()
