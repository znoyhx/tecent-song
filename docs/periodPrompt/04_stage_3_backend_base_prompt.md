# 阶段 3：后端基础服务 Prompt

## 1. 你的角色

你是后端基础服务执行开发模型。你的任务是实现符合 API 合约的 FastAPI 后端基础能力，让前端和 Mock Demo 以稳定后端状态为权威。

## 2. 必须先阅读的文档

- `CODEBUDDY.md`
- `docs/develop/02_technical_architecture.md`
- `docs/develop/04_data_model_design.md`
- `docs/develop/05_game_state_machine.md`
- `docs/develop/08_clue_system.md`
- `docs/develop/12_backend_development_plan.md`
- `docs/develop/13_api_contracts.md`
- `docs/develop/14_mock_demo_plan.md`
- `docs/periodPrompt/00_global_rules.md`
- 当前 `backend/` 代码

## 3. 阶段目标

实现后端基础服务：

- `GET /api/health`
- `GET /api/dynasties`
- `GET /api/roles`
- `POST /api/session/start`
- `GET /api/session/{session_id}`
- `POST /api/dialogue` 的 Mock 实现
- `POST /api/investigate`
- `POST /api/choice`
- `POST /api/ending/resolve`
- 中文错误响应
- 基础测试

本阶段可预留 AIClient 接口，但不做真实 AI 调用。

## 4. 当前阶段禁止事项

- 禁止用真实 AI 替代 Mock 基础服务。
- 禁止改变 `13_api_contracts.md` 字段。
- 禁止前端暴露 API Key。
- 禁止日志打印 Key。
- 禁止让前端决定阶段跳转。
- 禁止英文用户可见错误信息。

## 5. 允许修改的文件范围

- `backend/app.py`
- `backend/config.py`
- `backend/requirements.txt`
- `backend/routers/`
- `backend/models/`
- `backend/services/`
- `backend/data/`
- `backend/tests/`
- `docs/periodPrompt/reports/stage_3_backend_base_report.md`

## 6. 不允许修改的文件范围

- `frontend/`，除非只为适配已定 API 合约且先说明
- `docs/PRD.md`
- `docs/develop/*.md`
- 密钥文件

## 7. 具体开发任务

### 任务 1：模型与数据加载

- 任务目标：用 Pydantic 定义核心模型，加载 JSON 数据。
- 参考文档：`04_data_model_design.md`。
- 输出：可按 ID 获取 dynasty、role、scene、npc、clue、ending。
- 验收标准：缺字段报中文清晰错误。

### 任务 2：会话服务

- 任务目标：创建和读取 `GameSessionState`。
- 参考文档：`05_game_state_machine.md`。
- 输出：初始 stage 为 `intro`。
- 验收标准：session 可读取，状态字段完整。

### 任务 3：调查和线索服务

- 任务目标：调查热点释放线索。
- 参考文档：`08_clue_system.md`。
- 输出：中文调查文本、新线索、状态更新。
- 验收标准：重复获得线索不会重复加入。

### 任务 4：Mock 对话和结局

- 任务目标：实现 Mock NPC 回复和结局判定。
- 参考文档：`14_mock_demo_plan.md`。
- 输出：中文 NPC 回复和中文结局。
- 验收标准：无真实 AI 也可通关。

## 8. 数据与接口要求

所有 API 响应必须符合 `13_api_contracts.md`。错误响应示例：

```json
{"error":{"code":"SESSION_NOT_FOUND","message":"未找到当前游戏会话","details":{}}}
```

## 9. 中文化要求

后端返回给前端展示的所有 `message`、`text`、`title`、`summary`、`dialogue`、`error.message` 必须中文。

## 10. AI 接入要求

本阶段不做真实 AI 调用。可以创建 `AIClient` 空接口或 Mock 实现，但不能声称真实 AI 测试成功。

## 11. 模型必须执行的自测步骤

- 安装后端依赖。
- 启动后端。
- 调用 `GET /api/health`。
- 调用 `POST /api/session/start`。
- 调用 `GET /api/session/{session_id}`。
- 调用 `POST /api/investigate`。
- 调用 `POST /api/dialogue`。
- 调用 `POST /api/choice`。
- 调用 `POST /api/ending/resolve`。
- 运行后端测试。
- 检查错误响应中文。

## 12. 人工验收方式

使用 curl、PowerShell 或 API 客户端：

1. 启动后端。
2. 访问 `/api/health`，期望中文/结构化正常状态。
3. 创建明代会话。
4. 调查后院灰烬，期望获得“烧焦残页”。
5. 与“阿沈”对话，期望中文 Mock 回复。
6. 提交关键选择。
7. 解析结局，期望中文结局。

## 13. 完成后必须返回的报告格式

```md
# 阶段完成报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. 自测结果

## 4. 中文化检查结果

## 5. AI 接入测试结果
本阶段未调用真实 AI。

## 6. 图片生成测试结果
本阶段未调用图片生成。

## 7. 人工验收方法

## 8. 未完成事项

## 9. 阻塞问题

## 10. 是否建议进入下一阶段

## 11. 是否需要强模型审查
```
