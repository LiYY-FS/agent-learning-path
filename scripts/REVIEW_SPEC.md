# 章节内容审核机制 (Review Spec)

> 本机制用于保证 `chapter-3.json` ~ `chapter-6.json` 的内容质量。
> 作者 agent 负责更新内容，独立的 **reviewer agent** 负责审核、校验与最终决断。

## 1. 章节范围 (Scope)

- **目标章节**：`assets/data/chapter-3.json`、`chapter-4.json`、`chapter-5.json`、`chapter-6.json`
  （共 4 章 36 个 section）。
- **最小审核单元**：单个 `section`（section 内字段齐全性、内容质量、代码正确性、一致性、资源有效性）。
- **豁免规则**：概念性 / 趋势章节（3.7 Dify、5.4 内容运营、6.x 趋势）可豁免
  “必须含可运行代码”，但仍需内容充实、字段齐全、无虚构事实、有可学习要点。

## 2. 更新触发条件 (Trigger)

- **自动触发**：当 `assets/data/chapter-N.json` 被修改（git diff 检测到变更）后，
  自动触发对该章节全部 section 的审核。
- **手动触发**：显式指令“审核第 X 章”或“复核 Y.Y”。
- **首次全量**：本任务启动时，对 ch3–ch6 执行“更新 → 审核”循环。

## 3. Agent 检查接口 (Reviewer Interface)

- **角色**：独立 `reviewer` 子 agent（`general-purpose`，独立上下文，**不共享作者上下文**）。
- **调用方式**：作者 agent 使用 `Agent` 工具启动 reviewer，传入：
  - 章节文件路径；
  - 下方检查清单 `CHECKLIST`；
  - 约束：只读审核，**不修改任何文件**；输出严格 JSON。
- **检查清单 (CHECKLIST)**（**major** = 阻断必须修复；**minor** = 建议优化不阻断）：
  1. **字段齐全（minor）**：`objectives≥1`、`content≥1`、
     `enterpriseCase{title,background,architecture,outcome,lessons}` 均非空、
     `exercises≥1`。`resources` / `quiz` 缺失记为 **minor**，不阻断门禁。
  2. **内容质量（major）**：无占位 / TODO / 空壳；
     趋势 / 概念章节（3.7、5.4、6.x）也须有具体数据、案例或可学习要点，
     **不允许整节仅 1 张表 + 泛化描述**。
  3. **代码正确性（major）**：代码聚焦章节（3.2–3.6、4.x、5.x 非概念节）的
     Python 代码块必须可 `ast.parse`、无函数空壳、无硬编码占位结果、
     无未使用 import、无悬空 `code` 引用（enterpriseCase.code 须为内联对象或真实存在文件）、
     无虚构模型版本号（如 `gpt-5`、`Claude Opus 4.8`、`Gemini 3.5`）。
  4. **一致性（major）**：section 标题 / objectives 与实际内容匹配；
     若提供 `quiz`，其 id **必须**在 `quizzes.json` 定义（**悬空 id = major**）。
  5. **资源有效性（minor）**：若提供 `resources`，链接须非空、格式合法、非占位、
     非无效编号（如错误 arXiv 号）；缺失记为 minor。
- **输出契约 (Output Contract)**：

```json
{
  "chapter": "ch3",
  "sections": [
    {
      "section": "3.3",
      "status": "pass | reject",
      "score": 0,
      "issues": [
        {"dimension": "代码正确性", "severity": "major", "detail": "generate_answer 为空壳"}
      ],
      "suggestions": ["实现 generate_answer 调用 LLM 生成最终回复"]
    }
  ],
  "summary": "本轮审核结论..."
}
```

- **严重度**：`major`（阻断，必须修复后重审）/ `minor`（建议优化，可不阻断）。

## 4. 通过 / 驳回处理逻辑 (Pass / Reject Logic)

- **通过 (pass)**：reviewer 对某 section 输出 `status:"pass"`（无 major issue）
  → 写入 `review_status.json` 标记该 section `passed` + timestamp + reviewer 摘要
  → 允许 `git commit` 该章节。
- **驳回 (reject)**：输出 `status:"reject"`（含 major issue）
  → 作者 agent 读取 `issues`，回到作者角色修复该 section
  → 再次调用 reviewer 重新审核（每 section 最多 **2 轮**重试）
  → 仍 `reject` 则标记 `blocked` 并升级人工确认（不自动合并）。
- **门禁 (Gate)**：任何章节若存在 `rejected` / `blocked` 的 section，
  **禁止 `git push` 到 main**。仅当全章 section 均 `passed` 才允许 push。
- **状态持久化**：`.workbuddy/review/review_status.json` 记录每章节每 section 的最终状态，
  作为 CI 门禁依据。
