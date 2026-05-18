# 12 后端开发计划

## 后端服务结构

```text
backend/
├── app.py
├── config.py
├── routers/
│   ├── health.py
│   ├── catalog.py
│   ├── session.py
│   ├── dialogue.py
│   ├── investigate.py
│   ├── choice.py
│   └── ending.py
├── models/
│   ├── game.py
│   ├── npc.py
│   ├── clue.py
│   ├── ai.py
│   └── api.py
├── services/
│   ├── data_loader.py
│   ├── game_state.py
│   ├── state_machine.py
│   ├── scene_service.py
│   ├── clue_service.py
│   ├── npc_service.py
│   ├── dialogue_orchestrator.py
│   ├── ai_client.py
│   ├── rag_service.py
│   ├── supervisor.py
│   ├── ending_service.py
│   └── log_service.py
└── tests/
```

## 配置和环境变量

`.env` 示例：

```text
APP_ENV=development
USE_MOCK_AI=true
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=replace_me
DEEPSEEK_MODEL=replace_with_current_model
AI_TIMEOUT_SECONDS=20
AI_MAX_RETRIES=1
DATABASE_URL=sqlite:///./db/game.sqlite
```

API Key 只由后端读取。前端不得出现 `DEEPSEEK_API_KEY`、`SILICONFLOW_API_KEY` 等变量。

## 错误处理原则

- 业务错误返回结构化 JSON。
- AI 失败不导致游戏崩溃。
- 状态不存在返回 `404 SESSION_NOT_FOUND`。
- 非法阶段操作返回 `409 INVALID_STAGE_ACTION`。
- 非法线索返回 `400 CLUE_NOT_DISCOVERED`。

## 后端开发任务列表

### B1 初始化 FastAPI 工程

- 任务目标：创建后端工程、健康检查和配置读取。
- 涉及文件：`backend/app.py`、`config.py`、`requirements.txt`、`routers/health.py`。
- 输入数据：无。
- 输出结果：`GET /api/health` 返回正常。
- 禁止改动：前端目录和文档。
- 验收标准：`python -m uvicorn app:app --reload` 可启动。
- 模型等级：低级模型可做。

### B2 定义 Pydantic 模型

- 任务目标：实现核心数据模型。
- 涉及文件：`backend/models/*.py`。
- 输入数据：`04_data_model_design.md`。
- 输出结果：模型可被路由和服务导入。
- 禁止改动：字段名不得偏离文档。
- 验收标准：模型单测通过。
- 模型等级：普通模型，强模型审查。

### B3 实现数据加载服务

- 任务目标：加载 dynasty、role、scene、npc、clue、ending JSON。
- 涉及文件：`services/data_loader.py`、`backend/data/*`。
- 输入数据：固定 JSON。
- 输出结果：按 ID 查询内容。
- 禁止改动：状态机逻辑。
- 验收标准：缺字段时报清晰错误。
- 模型等级：低级模型可做。

### B4 实现会话与状态机

- 任务目标：创建会话、读取会话、阶段转移。
- 涉及文件：`services/game_state.py`、`services/state_machine.py`、`routers/session.py`。
- 输入数据：start request、事件模板。
- 输出结果：返回初始 state。
- 禁止改动：AI 服务。
- 验收标准：intro 到 ending 的状态测试通过。
- 模型等级：普通模型，强模型审查。

### B5 实现场景调查和线索服务

- 任务目标：热点调查、线索加入、线索组合。
- 涉及文件：`scene_service.py`、`clue_service.py`、`routers/investigate.py`。
- 输入数据：scene/hotspot/clue ids。
- 输出结果：返回新线索和状态变化。
- 禁止改动：NPC 权限。
- 验收标准：15 条线索可按规则获得。
- 模型等级：普通模型。

### B6 实现 Mock NPC 对话

- 任务目标：无真实 AI 情况下完成 NPC 回复和线索释放。
- 涉及文件：`dialogue_orchestrator.py`、`npc_service.py`、`backend/data/mock_dialogues/`。
- 输入数据：session、npc、message、presented clues。
- 输出结果：结构化对话响应。
- 禁止改动：AIClient 外部接口。
- 验收标准：一局完整通关不依赖真实 API。
- 模型等级：普通模型。

### B7 实现 AIClient 和日志

- 任务目标：封装模型调用、超时、重试、日志。
- 涉及文件：`ai_client.py`、`log_service.py`。
- 输入数据：prompt、schema name。
- 输出结果：`AIResponse`。
- 禁止改动：前端。
- 验收标准：API Key 不出现在响应和日志摘要中。
- 模型等级：强模型审查。

### B8 实现监管器

- 任务目标：拦截非 JSON、现代词、错朝代、剧透、越权、非法线索。
- 涉及文件：`supervisor.py`、`tests/test_supervisor.py`。
- 输入数据：AIResponse、state、permissions。
- 输出结果：SupervisorResult。
- 禁止改动：数据模型字段。
- 验收标准：7 类检查都有测试。
- 模型等级：强模型。

### B9 实现结局判定和历史回声

- 任务目标：按规则判定 5 个结局，生成或 Mock 历史回声。
- 涉及文件：`ending_service.py`、`routers/ending.py`。
- 输入数据：state、choice id。
- 输出结果：ending response。
- 禁止改动：前端选择组件。
- 验收标准：每个结局可被测试触发。
- 模型等级：普通模型，强模型审查文本质量。
