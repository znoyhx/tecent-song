# 阶段 9：多结局与历史回声 Prompt

## 1. 你的角色

你是多结局和历史回声执行开发模型。你的任务是让结局由规则和状态判定，AI 只负责中文润色或生成历史回声，不能随机决定结局。

## 2. 必须先阅读的文档

- `CODEBUDDY.md`
- `docs/develop/05_game_state_machine.md`
- `docs/develop/08_clue_system.md`
- `docs/develop/13_api_contracts.md`
- `docs/develop/15_real_ai_integration_plan.md`
- `docs/develop/17_testing_and_acceptance.md`
- `docs/periodPrompt/00_global_rules.md`
- 当前 `backend/services/ending_service.*`
- 当前结局数据文件

## 3. 阶段目标

必须完成：

- 至少 5 个中文结局：自保、秩序、真相、悲剧、隐藏。
- 结局由状态机、线索、flags、scores、risk、NPC 信任度判定。
- 历史回声必须中文。
- 可使用 AI 生成/润色历史回声，但结局 ID 由规则决定。
- 测试至少 3 条不同结局路径。
- 前端展示中文结局页。

不完成：新增多朝代完整结局线。

## 4. 当前阶段禁止事项

- 禁止让 AI 随机选择结局。
- 禁止英文结局标题或按钮。
- 禁止忽略线索和状态直接按最后选择判定全部结局。
- 禁止破坏 Mock 结局。
- 禁止输出泄露 Key 的 AI 日志。

## 5. 允许修改的文件范围

- `backend/services/ending_service.*`
- `backend/services/history_echo_generator.*`
- `backend/data/endings/*`
- `backend/data/prompts/history_echo.md`
- `backend/tests/test_endings.*`
- `frontend/src/components/ending/*`
- `docs/periodPrompt/reports/stage_9_endings_report.md`

## 6. 不允许修改的文件范围

- 密钥文件。
- 状态机阶段基础定义，除非发现 bug 并报告。
- `docs/develop/*.md`。
- 无关前端组件。

## 7. 具体开发任务

### 任务 1：结局规则

- 任务目标：实现 5 个结局判定。
- 参考文档：`05_game_state_machine.md`。
- 输出：可测试的规则函数。
- 验收标准：每个结局可通过构造状态触发。

### 任务 2：历史回声

- 任务目标：生成引用玩家选择、关键线索和 NPC 命运的中文总结。
- 输出：`HistoryEcho`。
- 验收标准：至少引用 2 条线索或选择信息。

### 任务 3：AI 润色可选接入

- 任务目标：如果真实 AI 已接入，可用 AI 润色历史回声。
- 输出：中文结构化或文本结果。
- 验收标准：AI 失败时使用规则模板 fallback。

### 任务 4：前端结局页

- 任务目标：展示结局标题、正文、NPC 命运、历史回声、重新开始按钮。
- 验收标准：全中文，无英文按钮。

## 8. 数据与接口要求

`POST /api/ending/resolve` 返回：

```json
{
  "ending_id": "ending_truth",
  "title": "残页出城",
  "summary": "中文结局摘要",
  "history_echo": "中文历史回声",
  "npc_fates": {"npc_worker":"中文命运"}
}
```

## 9. 中文化要求

结局 ID 可英文，但标题、摘要、NPC 命运、历史回声、按钮必须中文。

## 10. AI 接入要求

如果启用 AI 历史回声：

- 必须真实调用 DeepSeek。
- 记录测试。
- fallback 使用中文模板。
- AI 不得改 `ending_id`。

如果不启用 AI，必须说明使用规则模板，不能声称真实 AI 参与。

## 11. 模型必须执行的自测步骤

- 构造自保结局状态并测试。
- 构造秩序结局状态并测试。
- 构造真相结局状态并测试。
- 如可行，测试悲剧和隐藏结局。
- 测试 AI 历史回声或模板 fallback。
- 前端查看结局页。
- 执行中文结局检查。

## 12. 人工验收方式

1. 启动前后端。
2. 走一条“交给陆峥”的路线，期望进入“秩序结局”。
3. 走一条“暗中交给顾闻”的路线，期望进入“真相结局”。
4. 走一条“销毁余稿”的路线，期望进入“自保结局”。
5. 每个结局页必须显示中文标题、中文正文、中文历史回声。
6. 查看日志确认 AI 只生成历史回声，不决定结局 ID。

## 13. 完成后必须返回的报告格式

```md
# 阶段完成报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. 自测结果

## 4. 中文化检查结果

## 5. AI 接入测试结果
说明历史回声是否真实调用 AI；若没有，说明使用中文模板 fallback。

## 6. 图片生成测试结果
本阶段不涉及图片生成。

## 7. 人工验收方法

## 8. 未完成事项

## 9. 阻塞问题

## 10. 是否建议进入下一阶段

## 11. 是否需要强模型审查
```
