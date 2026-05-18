# 真实 AI 接入测试 Prompt

## 1. 你的角色

你是真实 DeepSeek AI 接入测试模型。你的任务是只测试和记录真实文本 AI 能力，不开发新功能，不用 Mock 冒充真实测试。

## 2. 必须先阅读的文档

- `CODEBUDDY.md`
- `docs/develop/06_ai_dialogue_pipeline.md`
- `docs/develop/10_consistency_supervisor.md`
- `docs/develop/15_real_ai_integration_plan.md`
- `docs/develop/17_testing_and_acceptance.md`
- `docs/periodPrompt/00_global_rules.md`
- 当前 AIClient、DialogueOrchestrator、Supervisor 代码

## 3. 阶段目标

必须测试：

- DeepSeek Key 是否存在但不打印。
- 真实 DeepSeek 连通性。
- NPC 对话真实调用。
- 结构化 JSON 输出。
- 错误 fallback。
- 一致性监管器。
- 测试记录不泄露 Key。

## 4. 当前阶段禁止事项

- 禁止用 Mock 冒充真实测试。
- 禁止打印完整 Key。
- 禁止把测试 prompt 中的敏感配置写入报告。
- 禁止修改业务逻辑来通过测试。
- 禁止英文用户可见 AI 输出。

## 5. 允许修改的文件范围

- `backend/tests/test_deepseek_connection.*`
- `backend/tests/test_ai_dialogue_json.*`
- `backend/tests/test_ai_fallback.*`
- `docs/periodPrompt/reports/real_ai_integration_test_report.md`

如发现小 bug，可先报告；未经允许不要修改业务代码。

## 6. 不允许修改的文件范围

- 前端代码。
- 密钥文件。
- `docs/PRD.md`。
- `docs/develop/*.md`。
- 状态机和线索规则。

## 7. 具体开发任务

### 任务 1：配置检查

- 任务目标：确认 DeepSeek Key 存在。
- 输出：存在/不存在，不输出内容。
- 验收标准：报告无 Key 明文。

### 任务 2：真实连通性测试

- 任务目标：调用真实模型生成一个最小中文 JSON。
- 输出：测试记录。
- 验收标准：`是否调用真实 API：是`，JSON 可解析。

### 任务 3：NPC 对话测试

- 任务目标：用阿沈角色卡测试中文 NPC 对话。
- 输出：AIResponse 和 SupervisorResult 摘要。
- 验收标准：玩家可见内容中文，字段完整。

### 任务 4：fallback 测试

- 任务目标：模拟超时、Key 缺失或无效响应。
- 输出：fallback 记录。
- 验收标准：中文 fallback 生效，游戏不崩溃。

### 任务 5：监管器测试

- 任务目标：测试现代词、英文输出、非法线索被拦截。
- 输出：监管结果摘要。
- 验收标准：违规不进入状态。

## 8. 数据与接口要求

测试输入摘要可以记录：`NPC=阿沈，阶段=investigation，玩家问题=你昨夜三更后到底听见了什么？`。不要记录 API Key。

## 9. 中文化要求

AI 返回给玩家看的字段必须中文。如果 AI 返回英文，本测试应标记失败或 fallback 成功。

## 10. AI 接入要求

本 Prompt 必须真实调用 DeepSeek。若 Key 不存在、变量名不明或网络不可达，必须停止并反馈：缺少什么、为什么阻塞、如何补齐、可先做哪些不阻塞任务、是否建议强模型介入。

## 11. 模型必须执行的自测步骤

- 检查 Key 存在性但不打印。
- 运行真实连通性测试。
- 运行 NPC JSON 测试。
- 运行 fallback 测试。
- 运行监管器测试。
- 检查测试报告不含 Key。
- 检查 AI 展示文本中文。

## 12. 人工验收方式

用户查看：

- `docs/periodPrompt/reports/real_ai_integration_test_report.md`
- 后端 AI 调用日志摘要

期望看到：

- 至少 1 次真实 API 成功。
- 至少 1 条中文 NPC JSON 回复。
- 至少 1 次 fallback 测试。
- 至少 1 次监管器违规拦截。
- 无 Key 明文。

## 13. 完成后必须返回的报告格式

```md
# 真实 AI 接入测试报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. 自测结果

## 4. 中文化检查结果

## 5. AI 接入测试结果
- 测试时间：
- 测试接口：
- 测试输入摘要：
- 是否调用真实 API：
- 是否成功：
- 返回内容是否符合格式：
- 是否 fallback：
- 发现的问题：
- 下一步修复建议：

## 6. 图片生成测试结果
本 Prompt 不测试图片生成。

## 7. 人工验收方法

## 8. 未完成事项

## 9. 阻塞问题

## 10. 是否建议进入下一阶段

## 11. 是否需要强模型审查
```
