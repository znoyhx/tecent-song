# 阶段 5：状态机与线索系统完善 Prompt

## 1. 你的角色

你是状态机与线索系统执行开发模型。你的任务是让剧情阶段、线索释放、出示线索、线索组合和结局条件严格受后端规则控制。

## 2. 必须先阅读的文档

- `CODEBUDDY.md`
- `docs/develop/04_data_model_design.md`
- `docs/develop/05_game_state_machine.md`
- `docs/develop/08_clue_system.md`
- `docs/develop/13_api_contracts.md`
- `docs/develop/17_testing_and_acceptance.md`
- `docs/periodPrompt/00_global_rules.md`
- 当前 `backend/services/state_machine.*`
- 当前 `backend/services/clue_service.*`
- 当前线索 JSON

## 3. 阶段目标

必须完成：

- 后端状态机权威控制 `intro`、`investigation`、`reversal`、`choice`、`ending`。
- AI 不能直接决定跳阶段。
- 15 条线索全部可按规则获得。
- 关键线索影响阶段或结局。
- 至少 3 组线索组合。
- 出示线索必须改变至少一个 NPC 回复。
- 红色关键文本可见并可点击。
- 线索栏展示正确。

不完成：多朝代完整剧情、复杂推理图谱。

## 4. 当前阶段禁止事项

- 禁止把阶段跳转写在前端。
- 禁止让 AI 输出直接修改 `current_stage`。
- 禁止提前释放关键线索。
- 禁止删除已有 Mock 通关路径。
- 禁止英文线索标题或详情。
- 禁止自行新增无用线索凑数。

## 5. 允许修改的文件范围

- `backend/services/state_machine.*`
- `backend/services/clue_service.*`
- `backend/services/dialogue_orchestrator.*`
- `backend/data/clues/*`
- `backend/data/scenes/*`
- `backend/data/npcs/*`
- `backend/tests/test_state_machine.*`
- `backend/tests/test_clues.*`
- `frontend/src/components/clue/*`（仅限展示联调）
- `docs/periodPrompt/reports/stage_5_state_and_clue_report.md`

## 6. 不允许修改的文件范围

- `docs/PRD.md`
- `docs/develop/*.md`
- AI Key 配置
- 图片生成服务
- 无关 UI 组件

## 7. 具体开发任务

### 任务 1：阶段转移规则

- 任务目标：实现文档定义的阶段条件。
- 参考文档：`05_game_state_machine.md`。
- 输出：确定性状态转移函数。
- 验收标准：未满足条件不会跳阶段。

### 任务 2：线索释放规则

- 任务目标：每条线索有来源、阶段、条件和效果。
- 参考文档：`08_clue_system.md`。
- 输出：15 条中文线索。
- 验收标准：关键线索不能提前获得。

### 任务 3：出示线索影响 NPC

- 任务目标：玩家出示指定线索后 NPC 回复变化。
- 输入：`presented_clue_ids`。
- 输出：不同中文回复和可能新线索。
- 验收标准：至少阿沈、陆峥各有一条出示线索变化路径。

### 任务 4：线索组合

- 任务目标：实现至少 3 组组合。
- 输出：组合结果、flags、scores。
- 验收标准：组合能推动到 `reversal` 或 `choice`。

## 8. 数据与接口要求

`POST /api/investigate` 和 `POST /api/dialogue` 返回的新线索必须经过 `ClueService.can_release()`。`POST /api/choice` 前必须确认 `current_stage=choice`。

## 9. 中文化要求

线索标题、详情、组合结论、阶段提示、错误信息都必须中文。完成后扫描 `backend/data/clues`、`frontend/src/components/clue`、Mock 对话。

## 10. AI 接入要求

如果真实 AI 已接入，本阶段仍必须以后端规则过滤 AI 返回线索。AI 返回非法线索必须忽略或交给监管器。不能用 AI 代替状态机。

## 11. 模型必须执行的自测步骤

- 运行状态机单测。
- 运行线索服务单测。
- 测试 15 条线索获得路径。
- 测试线索重复点击不重复。
- 测试 3 组组合。
- 测试出示线索改变 NPC 回复。
- 测试 AI 返回非法线索时不进入状态。
- 执行中文线索检查。

## 12. 人工验收方式

1. 启动前后端。
2. 进入明代书坊焚稿案。
3. 在后院火场点击红色线索，确认线索栏增加。
4. 与阿沈对话，先不出示线索，记录回复。
5. 出示“刻工矛盾证言”，确认回复变化并可能释放“三更搬箱”。
6. 收集火起点异常、异常火油味、后门门闩松动。
7. 执行线索组合，确认出现“火灾并非意外”。
8. 达成条件后确认进入反转或抉择阶段。

## 13. 完成后必须返回的报告格式

```md
# 阶段完成报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. 自测结果

## 4. 中文化检查结果

## 5. AI 接入测试结果
如已启用真实 AI，说明非法线索过滤测试；否则说明本阶段使用 Mock。

## 6. 图片生成测试结果
本阶段不涉及图片生成。

## 7. 人工验收方法

## 8. 未完成事项

## 9. 阻塞问题

## 10. 是否建议进入下一阶段

## 11. 是否需要强模型审查
```
