# 03 推荐目录结构

## 原则

当前仓库只有 `docs/` 与 `CODEBUDDY.md`。后续应在现有结构上增量增加 `frontend/`、`backend/`、`docs/develop/`，不要无理由推翻。低级模型不得重命名 `docs/PRD.md`、`CODEBUDDY.md` 或本目录文档。

## 推荐结构

```text
HistoryGame/
├── CODEBUDDY.md
├── docs/
│   ├── PRD.md
│   ├── help/
│   │   └── Imagegenerate.md
│   └── develop/
│       └── *.md
├── frontend/
│   ├── package.json
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   ├── scene/
│   │   │   ├── dialogue/
│   │   │   ├── clue/
│   │   │   ├── npc/
│   │   │   └── ending/
│   │   ├── pages/
│   │   ├── store/
│   │   ├── types/
│   │   ├── mock/
│   │   └── styles/
│   └── tests/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   ├── routers/
│   ├── models/
│   ├── services/
│   ├── data/
│   │   ├── dynasties/
│   │   ├── roles/
│   │   ├── events/
│   │   ├── scenes/
│   │   ├── npcs/
│   │   ├── clues/
│   │   ├── endings/
│   │   ├── prompts/
│   │   └── rag_sources/
│   ├── db/
│   ├── logs/
│   └── tests/
└── assets/
    ├── placeholders/
    ├── scenes/
    ├── npcs/
    └── clues/
```

## 目录职责

| 目录 | 职责 |
| --- | --- |
| `docs/` | 产品、规划、开发执行文档。 |
| `docs/develop/` | 给模型和开发者使用的阶段执行文档。 |
| `frontend/` | 前端网页游戏实现。 |
| `frontend/src/components/scene/` | 场景背景、热点、场景文本展示。 |
| `frontend/src/components/dialogue/` | NPC 对话框、输入框、推荐追问、出示线索 UI。 |
| `frontend/src/components/clue/` | 红色高亮、线索栏、线索详情、组合面板。 |
| `frontend/src/components/npc/` | NPC 立绘/剪影、情绪状态、姓名牌。 |
| `frontend/src/components/ending/` | 结局卡、历史回声、重开按钮。 |
| `frontend/src/api/` | 前端 API 请求封装。 |
| `frontend/src/store/` | 前端状态管理。 |
| `frontend/src/types/` | 与后端响应一致的 TypeScript 类型。 |
| `backend/routers/` | FastAPI 路由。 |
| `backend/models/` | Pydantic 模型。 |
| `backend/services/` | 游戏状态、AI、RAG、监管器、线索、结局服务。 |
| `backend/data/` | 可编辑内容 JSON 和 prompt 模板。 |
| `backend/tests/` | pytest 测试。 |
| `assets/` | 前端可引用的本地图片资源。 |

## AI Prompt 位置

Prompt 模板放在：

```text
backend/data/prompts/
├── npc_dialogue.md
├── supervisor.md
├── repair.md
├── history_echo.md
└── visual_prompt.md
```

代码读取模板后填充变量。不要把长 prompt 硬编码在业务函数中。

## 游戏数据位置

```text
backend/data/events/ming_bookshop_fire.json
backend/data/scenes/ming_bookshop_scenes.json
backend/data/npcs/ming_bookshop_npcs.json
backend/data/clues/ming_bookshop_clues.json
backend/data/endings/ming_bookshop_endings.json
backend/data/rag_sources/ming_rules.md
```

## 测试位置

- 后端单测：`backend/tests/`。
- 前端组件测试：`frontend/tests/` 或 `frontend/src/**/*.test.tsx`。
- E2E 可后置，使用 Playwright。

## 禁止低级模型随意重构的目录/文件

- `docs/PRD.md`：产品源文档，只能读。
- `CODEBUDDY.md`：Agent 指导文件，只能在用户要求时更新。
- `docs/develop/*.md`：执行文档，只能在强模型审查后更新。
- `backend/models/`：API 合约稳定后不得随意改字段。
- `backend/data/*`：低级模型只能修改被任务指定的数据文件。
- `frontend/src/types/`：必须与 API 合约同步，不得自行改名。

## 低级模型新增文件规则

低级模型新增文件必须满足：

1. 文件路径在任务说明中明确列出。
2. 不移动已有目录。
3. 不删除旧逻辑。
4. 不创建重复服务，例如已有 `ClueService` 时不得新增 `CluesManager2`。
5. 完成后说明新增/修改文件。
