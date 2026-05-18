# 阶段 1：Mock Demo Prompt

## 1. 你的角色

你是 Mock Demo 执行开发模型。你的目标是不依赖真实 AI，先跑通“明代 / 书坊学徒 / 书坊焚稿案”的完整中文可玩闭环。

## 2. 必须先阅读的文档

必须阅读：

- `CODEBUDDY.md`
- `docs/develop/01_mvp_scope.md`
- `docs/develop/03_directory_structure.md`
- `docs/develop/04_data_model_design.md`
- `docs/develop/05_game_state_machine.md`
- `docs/develop/07_npc_and_permission_system.md`
- `docs/develop/08_clue_system.md`
- `docs/develop/13_api_contracts.md`
- `docs/develop/14_mock_demo_plan.md`
- `docs/develop/17_testing_and_acceptance.md`
- `docs/periodPrompt/00_global_rules.md`

## 3. 阶段目标

必须完成：

- 可启动的前后端最小工程。
- Mock 模式完整跑通明代书坊焚稿案。
- 5 阶段剧情：引子、调查、反转、抉择、结局。
- 4 个 NPC：许掌柜、阿沈、顾闻、陆峥。
- 至少 5 个中文场景。
- 至少 15 条中文线索。
- 至少 5 个中文结局。
- 红色关键线索文本。
- 右侧线索栏。
- 出示线索逻辑。
- 选择进入结局。

不完成：真实 AI、RAG 向量库、真实图片生成、复杂部署。

## 4. 当前阶段禁止事项

- 禁止接入真实 AI 后声称阶段完成。
- 禁止用英文 UI。
- 禁止自由扩展北宋、晚唐完整剧情。
- 禁止让前端决定状态机跳转。
- 禁止删除 Mock 能力。
- 禁止读取或打印 API Key。
- 禁止跳过自测。

## 5. 允许修改的文件范围

可创建/修改：

- `frontend/`
- `backend/`
- `assets/placeholders/`
- `docs/periodPrompt/reports/stage_1_mock_demo_report.md`

## 6. 不允许修改的文件范围

不允许修改：

- `docs/PRD.md`
- `CODEBUDDY.md`
- `docs/develop/*.md`
- `docs/DeepseekAPIKey`
- `docs/ImageGenerateKey`

## 7. 具体开发任务

### 任务 1：初始化工程

- 任务目标：创建可启动前端和后端。
- 参考文档：`11_frontend_development_plan.md`、`12_backend_development_plan.md`。
- 涉及文件：`frontend/`、`backend/`。
- 输入：无。
- 输出：前端页面和 `GET /api/health`。
- 验收标准：前端和后端可分别启动。

### 任务 2：创建 Mock 数据

- 任务目标：实现中文明代书坊焚稿案数据。
- 参考文档：`08_clue_system.md`、`07_npc_and_permission_system.md`。
- 涉及文件：`backend/data/*`。
- 输入：15 条线索、4 NPC、5 场景、5 结局。
- 输出：可加载 JSON。
- 验收标准：所有引用 ID 一致，文本全中文。

### 任务 3：实现基础 API

- 任务目标：实现健康检查、会话、调查、Mock 对话、选择、结局。
- 参考文档：`13_api_contracts.md`。
- 涉及文件：`backend/routers/*`、`backend/services/*`。
- 输出：API 返回结构化中文响应。
- 验收标准：能从 session start 到 ending resolve。

### 任务 4：实现最小前端 UI

- 任务目标：展示场景、NPC、对话、线索栏、选择、结局。
- 参考文档：`11_frontend_development_plan.md`。
- 涉及文件：`frontend/src/*`。
- 输出：中文游戏界面。
- 验收标准：用户可点击红色线索并在线索栏看到详情。

## 8. 数据与接口要求

必须实现或预留：

- `GET /api/health`
- `GET /api/dynasties`
- `GET /api/roles`
- `POST /api/session/start`
- `GET /api/session/{session_id}`
- `POST /api/dialogue`
- `POST /api/investigate`
- `POST /api/choice`
- `POST /api/ending/resolve`

Mock 对话响应必须与未来真实 AI 响应 schema 一致。

## 9. 中文化要求

所有页面、按钮、错误、Loading、线索、NPC 回复、结局必须中文。完成后必须搜索用户可见英文残留。若发现 `Start`、`Loading`、`Error`、`Submit` 等，必须改为中文。

## 10. AI 接入要求

本阶段不接入真实 AI，不能伪造真实 AI 测试结论。必须保留 `USE_MOCK_AI=true` 或等价配置。不得读取 API Key。

## 11. 模型必须执行的自测步骤

必须执行或说明无法执行原因：

- 安装前端依赖。
- 安装后端依赖。
- 启动后端并调用 `GET /api/health`。
- 启动前端并打开页面。
- 调用 `POST /api/session/start`。
- 调用 `POST /api/investigate` 获得线索。
- 调用 `POST /api/dialogue` 验证 Mock NPC 回复。
- 调用 `POST /api/choice` 和 `POST /api/ending/resolve`。
- 运行已有测试或新增基础测试。
- 执行中文 UI 自检。

## 12. 人工验收方式

用户应按以下路径验收：

1. 启动后端，例如 `python -m uvicorn app:app --reload`，以实际项目命令为准。
2. 启动前端，例如 `npm run dev`，以实际项目命令为准。
3. 打开前端地址。
4. 点击“开始新局”或等价中文按钮。
5. 选择“明代”和“书坊学徒”。
6. 进入“书坊前厅”。
7. 点击红色文字“辽东粮册”或火场相关红色线索。
8. 确认右侧线索栏出现“烧焦残页”。
9. 与“阿沈”对话，出示“刻工矛盾证言”。
10. 期望看到中文回复和新线索。
11. 做最终选择。
12. 期望看到中文结局和历史回声。

如果页面出现英文按钮或英文错误提示，本阶段不通过。

## 13. 完成后必须返回的报告格式

```md
# 阶段完成报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. 自测结果

## 4. 中文化检查结果

## 5. AI 接入测试结果
本阶段未接入真实 AI，使用 Mock，不得声称真实 AI 成功。

## 6. 图片生成测试结果
本阶段未接入图片生成。

## 7. 人工验收方法

## 8. 未完成事项

## 9. 阻塞问题

## 10. 是否建议进入下一阶段

## 11. 是否需要强模型审查
```
