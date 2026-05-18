# 15 真实 AI 接入方案

## 接入原则

先有 Mock Demo，再接真实 AI。真实 AI 接入必须可开关、可记录、可回退。模型输出必须结构化，优先 JSON。

## 模型封装

统一接口：

```python
class AIClient:
    def generate_json(self, module: str, prompt: str, schema_name: str) -> AIResponse: ...
    def generate_text(self, module: str, prompt: str) -> AIResponse: ...
```

Provider 实现：

- `DeepSeekClient`：调用 DeepSeek 兼容接口。
- `TencentModelClient`：后续如需腾讯云模型时实现。
- `MockAIClient`：读取固定 JSON。
- `CodeBuddyModelClient`：仅在开发环境有可用内部能力时封装，不让前端直接调用。

## API Key 位置

- 放在 `backend/.env`。
- 通过 `backend/config.py` 读取。
- 不写入前端，不写入日志，不写入响应。
- 不读取或复制 `docs/DeepseekAPIKey` 内容到代码。

## 前端为什么不能暴露 API Key

浏览器代码会被用户下载，任何放在前端的 Key 都会泄露。所有 AI、生图和向量库请求必须由后端代理。

## 失败兜底

```text
模型调用失败/超时
  ↓
记录 AIResponse(success=false)
  ↓
使用 MockAIClient 或 fallback 文本
  ↓
前端显示自然过渡，不暴露技术错误
```

## 输出格式约束

Prompt 必须声明：

- 只输出 JSON。
- 不输出 Markdown。
- 不解释规则。
- 必须符合 schema。

后端必须解析和监管，不能相信模型自称合法。

## 模型分工

| 模块 | 推荐模型 | 原因 |
| --- | --- | --- |
| NPCDialogueAgent | 中高质量模型 | 需要角色感和约束遵守 |
| ConsistencySupervisor | 强模型或规则优先 | 错误会破坏演示 |
| RepairAgent | 强模型 | 修复需要理解违规点 |
| HistoryEchoGenerator | 中高质量模型 | 文本质量影响路演 |
| VisualPromptAgent | 普通模型可用 | 结构化提示词较稳定 |
| RAG 关键词检索 | 不用模型 | 降低成本 |

## 必须用强模型的地方

- 监管器 AI 语义审查。
- 修复剧透、越权和错朝代输出。
- 生成最终路演用历史回声。

## 可用普通模型的地方

- 视觉提示词草稿。
- 普通 NPC 问候或非关键回复。
- 文案润色。

## AI 调用日志

每次调用记录：

```json
{
  "call_id":"call_001",
  "timestamp":"2026-05-15T16:32:00+08:00",
  "module":"NPCDialogueAgent",
  "provider":"deepseek",
  "model":"configured_model",
  "input_summary":"阿沈 investigation 对话",
  "prompt_path":"logs/prompts/call_001.txt",
  "response_path":"logs/responses/call_001.json",
  "latency_ms":3200,
  "success":true,
  "supervisor_pass":true,
  "fallback_used":false
}
```

日志中不得记录完整 API Key。

## Prompt 调试

- Prompt 模板放 `backend/data/prompts/`。
- 每次调用保存填充后的 prompt。
- DebugPanel 可显示 `input_summary`、`latency_ms`、`supervisor_pass`，不显示密钥。
- 为每个 Agent 建最小单测，使用 Mock 模型返回。

## 测试验收

- 无 Key 时 Mock 模式可运行。
- 有 Key 时 `test_deepseek_connection.py` 能返回 JSON。
- 模型返回散文时进入修复或 fallback。
- AI 回复不合法时不会污染状态。
