# 阶段 7：RAG 与知识库 Prompt

## 1. 你的角色

你是知识库与 RAG 执行开发模型。你的任务是先实现可控的中文关键词检索，并为后续向量数据库预留接口。

## 2. 必须先阅读的文档

- `CODEBUDDY.md`
- `docs/develop/09_rag_knowledge_base.md`
- `docs/develop/06_ai_dialogue_pipeline.md`
- `docs/develop/10_consistency_supervisor.md`
- `docs/develop/15_real_ai_integration_plan.md`
- `docs/periodPrompt/00_global_rules.md`
- 当前 `backend/services/rag_service.*`
- 当前 `backend/data/rag_sources/`

## 3. 阶段目标

必须完成：

- JSON / Markdown 中文知识库。
- 关键词检索 `RAGService.retrieve()`。
- 按朝代过滤。
- 检索结果进入 AI Prompt。
- 错朝代禁止项可被监管器使用。
- RAG 失败 fallback。
- 为 ChromaDB / 腾讯云向量库预留接口。

不完成：复杂向量后台、自动爬虫、大规模史料库。

## 4. 当前阶段禁止事项

- 禁止把无关朝代内容召回给明代 Demo。
- 禁止让 RAG 内容覆盖状态机规则。
- 禁止使用英文用户可见知识片段。
- 禁止因 RAG 失败导致对话不可用。
- 禁止引入重型向量库阻塞 MVP，除非明确已完成 Mock 和 AI 基础。

## 5. 允许修改的文件范围

- `backend/services/rag_service.*`
- `backend/data/rag_sources/`
- `backend/data/rules/`
- `backend/data/prompts/npc_dialogue.md`
- `backend/tests/test_rag_retrieval.*`
- `docs/periodPrompt/reports/stage_7_rag_knowledge_report.md`

## 6. 不允许修改的文件范围

- 前端 UI，除非只展示调试 RAG 结果。
- 密钥文件。
- 状态机核心规则。
- `docs/develop/*.md`。

## 7. 具体开发任务

### 任务 1：明代知识片段

- 任务目标：编写明代书坊、锦衣卫、文稿、身份边界、禁词中文片段。
- 输出：结构化 JSON 或 Markdown。
- 验收标准：每个片段有 `dynasty_id`、`topics`、`content`。

### 任务 2：关键词检索

- 任务目标：实现按朝代、主题和 query 匹配。
- 输出：top 3-5 中文片段。
- 验收标准：查询“锦衣卫 书坊 文稿”返回明代规则。

### 任务 3：Prompt 注入

- 任务目标：把检索结果注入 NPC 对话 Prompt。
- 输出：AI 可读取历史约束。
- 验收标准：Prompt 中有中文历史参考，但不超过必要数量。

### 任务 4：错朝代禁止项

- 任务目标：为监管器提供现代词和错朝代词。
- 输出：禁词配置。
- 验收标准：“手机”“互联网”“八旗”可被命中。

## 8. 数据与接口要求

`RAGService.retrieve(query, dynasty_id, stage, top_k)` 必须返回列表，失败时返回空列表并记录中文警告，不抛出导致主流程失败的异常。

## 9. 中文化要求

RAG 内容和注入 Prompt 的历史参考必须中文。不得把英文解释展示给用户。

## 10. AI 接入要求

如果真实 AI 已接入，必须测试 RAG 上下文进入 NPC Prompt。不能声称 RAG 影响 AI，除非测试记录中有输入摘要和实际调用记录。

## 11. 模型必须执行的自测步骤

- 查询“锦衣卫 书坊 文稿”。
- 查询“火油 后院 火场”。
- 查询“手机 互联网”。
- 查询错误朝代内容，确认不会召回明代外内容。
- 让 NPC 对话读取 RAG 上下文。
- 模拟 RAG 文件缺失，确认 fallback。
- 执行中文知识片段检查。

## 12. 人工验收方式

1. 启动后端。
2. 调用 RAG 测试脚本或调试接口。
3. 输入“锦衣卫 书坊 文稿”。
4. 期望返回中文明代规则。
5. 进入 NPC 对话，查看 AI 日志中的输入摘要，确认包含 RAG 上下文。
6. 临时禁用 RAG，确认对话仍有 fallback。

## 13. 完成后必须返回的报告格式

```md
# 阶段完成报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. 自测结果

## 4. 中文化检查结果

## 5. AI 接入测试结果
说明 RAG 是否进入真实 AI Prompt；若未启用真实 AI，不能声称真实影响。

## 6. 图片生成测试结果
本阶段不涉及图片生成。

## 7. 人工验收方法

## 8. 未完成事项

## 9. 阻塞问题

## 10. 是否建议进入下一阶段

## 11. 是否需要强模型审查
```
