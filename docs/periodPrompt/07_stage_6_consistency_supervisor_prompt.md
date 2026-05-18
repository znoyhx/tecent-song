# 阶段 6：一致性监管器 Prompt

## 1. 你的角色

你是一致性监管器执行开发模型。你的任务是在 AI 输出应用到游戏状态前拦截违规内容，并提供修复或 fallback。

## 2. 必须先阅读的文档

- `CODEBUDDY.md`
- `docs/develop/06_ai_dialogue_pipeline.md`
- `docs/develop/07_npc_and_permission_system.md`
- `docs/develop/10_consistency_supervisor.md`
- `docs/develop/17_testing_and_acceptance.md`
- `docs/develop/21_code_review_checklist.md`
- `docs/periodPrompt/00_global_rules.md`
- 当前 `backend/services/supervisor.*`
- 当前 AI 对话服务

## 3. 阶段目标

监管器必须拦截：

- 现代词。
- 错朝代元素。
- NPC 剧透。
- NPC 身份越权。
- 非法线索释放。
- 非 JSON 输出。
- 剧情阶段跳跃。
- 英文用户可见文本。

必须支持：

- 失败后重试修复。
- 重试失败后 fallback。
- 测试用例。
- 人工触发测试。
- 监管报告不泄露 Key。

## 4. 当前阶段禁止事项

- 禁止让未监管 AI 输出直接返回前端。
- 禁止无限重试。
- 禁止打印完整 prompt 中的 Key 或敏感配置。
- 禁止把英文 AI 回复直接展示给用户。
- 禁止跳过非法线索检查。
- 禁止修改状态机规则来迁就 AI。

## 5. 允许修改的文件范围

- `backend/services/supervisor.*`
- `backend/services/repair_agent.*`
- `backend/services/dialogue_orchestrator.*`
- `backend/data/prompts/supervisor.md`
- `backend/data/prompts/repair.md`
- `backend/tests/test_supervisor.*`
- `docs/periodPrompt/reports/stage_6_consistency_supervisor_report.md`

## 6. 不允许修改的文件范围

- 前端 Key 配置。
- 密钥文件。
- `docs/PRD.md`。
- `docs/develop/*.md`。
- 无关 Mock 数据。

## 7. 具体开发任务

### 任务 1：规则检查器

- 任务目标：实现非 JSON、禁词、英文可见文本、非法线索、阶段跳跃检查。
- 参考文档：`10_consistency_supervisor.md`。
- 输出：`SupervisorResult`。
- 验收标准：违规样例均不通过。

### 任务 2：语义检查接口

- 任务目标：为剧透、越权、人设漂移预留或实现 AI 检查。
- 输出：可配置开启。
- 验收标准：没有 Key 时规则检查仍工作。

### 任务 3：修复与 fallback

- 任务目标：监管失败后最多修复一次，仍失败则 fallback。
- 输出：中文 fallback。
- 验收标准：前端不会展示违规文本。

### 任务 4：测试用例

- 任务目标：覆盖 8 类检查项。
- 输出：单元测试。
- 验收标准：测试可运行并通过。

## 8. 数据与接口要求

监管器输入输出使用 `10_consistency_supervisor.md` 中的 JSON。`issues` 必须包含 `type`、`severity`、`detail`，`detail` 为中文。

## 9. 中文化要求

监管器必须把英文用户可见文本视为违规。例如 AI 返回 “Loading” 或 “I do not know” 应触发 `english_visible_text`。

## 10. AI 接入要求

若启用 AI 语义监管，必须真实调用且记录测试；若未启用，不能声称 AI 监管成功。规则监管必须不依赖真实 AI。

## 11. 模型必须执行的自测步骤

- 测试现代词：“手机”。
- 测试错朝代：“八旗”。
- 测试剧透：“幕后上级就是某某”。
- 测试身份越权：“书坊学徒命令锦衣卫撤离”。
- 测试非法线索释放。
- 测试非 JSON。
- 测试阶段跳跃。
- 测试英文回复。
- 测试 repair 或 fallback。

## 12. 人工验收方式

1. 启动后端。
2. 调用监管器测试接口或运行测试脚本。
3. 输入包含“手机”的 NPC 回复，期望被拦截。
4. 输入英文 NPC 回复，期望被拦截或改中文。
5. 输入非法线索 ID，期望不进入 `discovered_clue_ids`。
6. 在前端触发 AI 失败，期望看到中文 fallback。

## 13. 完成后必须返回的报告格式

```md
# 阶段完成报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. 自测结果

## 4. 中文化检查结果

## 5. AI 接入测试结果
说明是否启用真实 AI 语义监管；规则监管测试必须列出。

## 6. 图片生成测试结果
本阶段不涉及图片生成。

## 7. 人工验收方法

## 8. 未完成事项

## 9. 阻塞问题

## 10. 是否建议进入下一阶段

## 11. 是否需要强模型审查
```
