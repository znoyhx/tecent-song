# 02 技术架构

## 总体架构图

```text
Browser / React + TypeScript
  ├─ GameShell UI
  ├─ SceneView
  ├─ DialoguePanel
  ├─ ClueSidebar
  └─ Zustand Store or React Context
        ↓ HTTP JSON
FastAPI Backend
  ├─ API Routes
  ├─ GameStateService
  ├─ SceneService
  ├─ ClueService
  ├─ NPCService
  ├─ DialogueOrchestrator
  ├─ ConsistencySupervisor
  ├─ EndingService
  ├─ RAGService
  ├─ AIClient
  └─ LogService
        ↓
Data Layer
  ├─ JSON seed data
  ├─ SQLite session/log storage
  ├─ Keyword RAG index (MVP)
  └─ ChromaDB / cloud vector DB (later)
```

## 前端技术栈

- `React + TypeScript`。
- `Vite` 推荐作为开发构建工具。
- `Tailwind CSS` 负责样式。
- `Zustand` 或 `React Context` 管理轻量游戏状态。MVP 推荐 `Zustand`，因为状态结构清晰且不需要复杂样板代码。
- `fetch` 封装 API 调用，不引入复杂 GraphQL 或 RPC。

## 后端技术栈

- `Python FastAPI`。
- `Pydantic` 定义请求、响应、数据模型。
- `SQLite` 保存会话状态和 AI 调用日志。
- JSON 文件保存初始内容包。
- `.env` 保存模型 API Key、模型名、超时、Mock 开关。
- 后续可接 `ChromaDB` 或腾讯云向量数据库。

## 数据存储方式

MVP 分三层：

1. `backend/data/`：固定游戏内容，JSON 可读可改。
2. `backend/db/game.sqlite`：运行时会话、对话记录、AI 日志索引。
3. `backend/logs/`：原始 prompt、原始 response、调试文件。

首版也可以先用内存 + JSON 文件，待 API 跑通后再加 SQLite，但接口设计必须不依赖内存实现。

## AI 服务封装方式

所有模型调用只能通过后端 `AIClient`：

```text
DialogueOrchestrator -> AIClient.generate_json(...) -> raw response
SupervisorService -> AIClient.generate_json(...) -> supervisor result
HistoryEchoService -> AIClient.generate_text/json(...)
VisualPromptService -> AIClient.generate_json(...)
```

前端不得直接请求 DeepSeek、SiliconFlow、腾讯云模型或 CodeBuddy 内部模型。

## RAG 服务位置

`RAGService` 位于后端服务层。MVP 先实现关键词检索：

```text
query + dynasty_id + stage -> candidate chunks -> top 3 context snippets
```

后续替换为向量检索时，`DialogueOrchestrator` 不应改动，只替换 `RAGService.retrieve()` 内部实现。

## 状态机位置

状态机在后端 `GameStateService` 或独立 `StateMachineService` 中。前端只展示状态，不决定阶段跳转、线索释放合法性和结局。

## 一致性监管器位置

监管器在后端 AI 输出之后、状态更新之前：

```text
AI raw output -> parse -> supervisor check -> repair/fallback -> apply state update
```

监管器失败时不能把未审查内容直接返回前端。

## 前后端数据流

```text
用户点击/输入
  ↓
前端构造 action request
  ↓
后端读取 session state
  ↓
后端执行业务服务
  ↓
返回 scene/dialogue/clues/state_delta
  ↓
前端更新 UI
```

## 单次 NPC 对话完整链路

1. 前端调用 `POST /api/dialogue`，携带 `session_id`、`npc_id`、`message`、`presented_clue_ids`。
2. 后端读取 `GameSessionState`。
3. 后端读取 `NPCProfile` 和 `NPCKnowledgePermission`。
4. 后端检查该 NPC 当前阶段是否可对话。
5. 后端用玩家输入、线索和 NPC 主题检索 RAG。
6. 构造 JSON-only prompt。
7. 调用 AI 或 Mock。
8. 解析返回 JSON。
9. 监管器检查。
10. 失败则修复；修复失败则使用 fallback。
11. `ClueService` 判断释放线索是否合法。
12. `GameStateService` 更新信任度、线索、flags、scores、risk、stage。
13. 返回前端。

## 失败兜底链路

```text
AI 超时/异常
  ↓
使用同 NPC + 当前阶段的 fallback 回复
  ↓
不释放新关键线索，除非规则明确允许
  ↓
记录 ai_call.success=false
  ↓
前端显示“对方迟疑片刻……”类自然文本
```

```text
AI 返回非 JSON
  ↓
尝试提取 JSON 块
  ↓
失败则调用 RepairAgent
  ↓
仍失败则 fallback
```
