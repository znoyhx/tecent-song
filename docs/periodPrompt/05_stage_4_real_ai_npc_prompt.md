# 阶段 4：真实 AI NPC 接入 Prompt

## 1. 你的角色

你是真实 AI NPC 接入执行模型。你的任务是在保留 Mock 的前提下，后端安全接入 DeepSeek，让 NPC 对话可真实调用模型并返回中文结构化 JSON。

## 2. 必须先阅读的文档

- `CODEBUDDY.md`
- `docs/develop/06_ai_dialogue_pipeline.md`
- `docs/develop/07_npc_and_permission_system.md`
- `docs/develop/10_consistency_supervisor.md`
- `docs/develop/15_real_ai_integration_plan.md`
- `docs/develop/17_testing_and_acceptance.md`
- `docs/periodPrompt/00_global_rules.md`
- 当前 `backend/services/ai_client.py` 或等价文件
- 当前后端配置文件

## 3. 阶段目标

必须完成：

- 后端封装 `AIClient`。
- 从安全环境变量读取 DeepSeek API Key。
- 支持真实调用 DeepSeek。
- NPC 对话 prompt 包含角色卡、知识权限、已发现线索、当前阶段、RAG 预留上下文。
- AI 返回结构化 JSON。
- 支持推荐追问。
- 支持 fallback 到 Mock。
- 写真实 AI 测试脚本或接口测试。
- 输出不泄露 Key 的测试记录。

不完成：图片生成、完整 RAG 向量库、多朝代扩展。

## 4. 当前阶段禁止事项

- 禁止前端接触 DeepSeek Key。
- 禁止在日志、Markdown、控制台打印完整 Key。
- 禁止用 Mock 冒充真实 AI 测试。
- 禁止让 AI 决定阶段或结局。
- 禁止跳过 JSON 解析和 fallback。
- 禁止英文用户可见文本。
- 禁止删除 Mock 模式。

## 5. 允许修改的文件范围

- `backend/config.py`
- `backend/services/ai_client.py`
- `backend/services/dialogue_orchestrator.py`
- `backend/services/log_service.py`
- `backend/data/prompts/`
- `backend/tests/test_deepseek_connection.py`
- `backend/tests/test_ai_dialogue_json.py`
- `docs/periodPrompt/reports/stage_4_real_ai_npc_report.md`

## 6. 不允许修改的文件范围

- `frontend/` 中任何 Key 相关代码
- `docs/DeepseekAPIKey`
- `docs/ImageGenerateKey`
- `docs/PRD.md`
- `docs/develop/*.md`
- 状态机核心规则，除非测试暴露 bug 且先说明

## 7. 具体开发任务

### 任务 1：配置读取

- 任务目标：从 `.env` 或安全环境变量读取 DeepSeek 配置。
- 参考文档：`15_real_ai_integration_plan.md`。
- 输入：`DEEPSEEK_API_KEY`、模型名、超时。
- 输出：配置对象只暴露存在性，不暴露 Key 内容。
- 验收标准：Key 缺失时给中文错误和 Mock fallback。

### 任务 2：AIClient 实现

- 任务目标：实现 `generate_json()`。
- 涉及文件：`ai_client.py`。
- 输出：`AIResponse`，包含 success、latency、fallback_used。
- 验收标准：真实调用成功时可解析 JSON。

### 任务 3：NPC Prompt 模板

- 任务目标：创建中文 NPC 对话 Prompt。
- 涉及文件：`backend/data/prompts/npc_dialogue.md`。
- 输入：NPC 角色卡、权限、线索、玩家输入。
- 输出：只允许 JSON。
- 验收标准：AI 输出字段符合 `06_ai_dialogue_pipeline.md`。

### 任务 4：真实 AI 测试记录

- 任务目标：记录真实调用结果。
- 涉及文件：`docs/periodPrompt/reports/stage_4_real_ai_npc_report.md`。
- 输出：测试时间、接口、输入摘要、是否真实 API、成功状态、格式、fallback、问题、建议。
- 验收标准：报告不含 Key。

## 8. 数据与接口要求

AI 返回 JSON 必须包含：

```json
{
  "npc_dialogue": "中文字符串",
  "npc_action": "中文字符串",
  "emotion": "fearful|calm|angry|hesitant|defensive",
  "released_clue_ids": [],
  "highlight_clues": [],
  "suggested_questions": ["中文问题"],
  "state_update_suggestion": {
    "npc_trust_delta": 0,
    "truth_score_delta": 0,
    "order_score_delta": 0,
    "survival_score_delta": 0,
    "risk_level_delta": 0,
    "new_flags": []
  }
}
```

## 9. 中文化要求

AI 给玩家看的 `npc_dialogue`、`npc_action`、`suggested_questions` 必须中文。若 AI 返回英文，必须进入修复或 fallback。

## 10. AI 接入要求

本阶段必须真实调用 DeepSeek。判断不是 Mock 的方式：

- `USE_MOCK_AI=false` 或等价配置。
- 测试记录中 `是否调用真实 API：是`。
- AI 调用日志存在真实 latency。
- fallback_used 为 false 的成功样例至少 1 条。

Key 只能检查存在性，不能输出内容。

## 11. 模型必须执行的自测步骤

- 检查 DeepSeek Key 是否存在但不打印。
- 启动后端。
- 调用 DeepSeek 连通性测试。
- 测试阿沈 NPC 对话 JSON。
- 测试玩家出示线索后的 AI 回复。
- 模拟 Key 缺失或超时，验证 fallback。
- 运行 AI JSON 解析测试。
- 执行中文输出检查。

## 12. 人工验收方式

1. 设置真实 AI 模式。
2. 启动后端和前端。
3. 进入明代书坊焚稿案。
4. 与“阿沈”对话，输入：“你昨夜三更后到底听见了什么？”
5. 期望看到自然中文 NPC 回复。
6. 打开 AI 日志，确认模块为 `NPCDialogueAgent`，`success=true`，`fallback_used=false`。
7. 临时关闭 Key 或设置 Mock，确认 fallback 中文回复可用。

## 13. 完成后必须返回的报告格式

```md
# 阶段完成报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. 自测结果

## 4. 中文化检查结果

## 5. AI 接入测试结果
- 测试时间：
- 测试接口：
- 输入摘要：
- 是否调用真实 API：
- 是否成功：
- JSON 格式是否正确：
- 是否 fallback：
- 问题：
- 下一步建议：

## 6. 图片生成测试结果
本阶段不涉及图片生成。

## 7. 人工验收方法

## 8. 未完成事项

## 9. 阻塞问题

## 10. 是否建议进入下一阶段

## 11. 是否需要强模型审查
```
