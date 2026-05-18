---
name: stage-11-story-volume-expansion
overview: 将明代 / 书坊学徒 / 书坊焚稿案从短流程 Demo 扩写为章节级可玩推理剧本，覆盖场景、线索、NPC 盘问、出示证据、线索组合/推理节点、多结局规则、测试与阶段报告。
todos:
  - id: audit-current-volume
    content: 使用 [subagent:code-explorer] 核验现有体量、引用关系和冲突
    status: completed
  - id: expand-story-data
    content: 使用 [skill:Code] 扩写事件、场景、热点、线索和章节小节
    status: completed
    dependencies:
      - audit-current-volume
  - id: expand-npc-rules
    content: 使用 [skill:Code] 扩展 NPC 对话、证据反应和历史回声
    status: completed
    dependencies:
      - expand-story-data
  - id: wire-rules-ui
    content: 使用 [skill:Code] 联调推理组合、状态机、结局规则和前端展示
    status: completed
    dependencies:
      - expand-npc-rules
  - id: add-acceptance-tests
    content: 使用 [skill:test-runner] 增加体量、引用、路线和结局测试
    status: completed
    dependencies:
      - wire-rules-ui
  - id: run-security-checks
    content: 使用 [skill:security-auditor] 检查中文化、密钥、AI 越权和前端越权
    status: completed
    dependencies:
      - add-acceptance-tests
  - id: write-stage-report
    content: 生成阶段 11 完成报告并建议强模型审查
    status: completed
    dependencies:
      - run-security-checks
---

## User Requirements

将现有《史隙》明代 / 书坊学徒 / 书坊焚稿案，从短流程 Demo 扩写为接近商业推理游戏章节体量的完整可玩剧本。扩写必须落到可运行数据、规则、Mock 响应和必要的前后端展示联动中，而不是单独写成长篇 Markdown。

## Product Overview

章节保持视觉小说舞台、右侧案卷调查、底部对话的体验结构。玩家从雨夜书坊火起被卷入，自证脱困，调查多处场景，点击红字线索，盘问许掌柜、阿沈、顾闻、陆峥，出示证据，完成线索组合和思维疑团，经历“火灾不是意外”“烧毁的不是普通诗稿”“封口令背后另有链路”等反转，最终根据证据链和人物信任进入多结局。

## Core Features

- 保留五阶段：intro、investigation、reversal、choice、ending，并扩展为 12–18 个剧情小节。
- 扩展 8–10 个场景或子场景、24–36 个调查热点、30–45 条有效线索、18 条以上红色高亮。
- 为 4 名核心 NPC 扩展多层盘问、证据击破、信任变化和信息边界。
- 增加 6–10 组线索组合和 8–12 个思维疑团或连续推理节点，由玩家逐步拼出真相。
- 保留并强化 5 个中文结局：焚稿自保、误信告发、暗藏残页、身陷诏狱、引火反查。
- 所有用户可见文本保持中文，Mock Demo、AI fallback 和视觉 fallback 保持可用。

## Tech Stack Selection

- 后端：沿用现有 Python FastAPI、Pydantic 模型、JSON 数据驱动、Mock 数据回退、后端状态机规则。
- 前端：沿用现有 React、TypeScript、现有组件结构和样式体系，仅做必要类型与展示增强。
- 数据：继续使用现有 `backend/data` 下事件、场景、线索、NPC、Mock 对话、结局和 RAG JSON 文件。
- 测试：沿用现有 pytest 后端测试；前端按现有 `npm run build` 做构建验证。

## Implementation Approach

本阶段以“数据扩写优先、最小代码扩展”为策略：先把章节大纲、场景、热点、线索、NPC 证据反应、组合、推理节点和结局条件落入现有 JSON 数据，再只为现有模型无法承载的字段做最小 Pydantic 和 TypeScript 同步。后端仍作为阶段推进、线索释放、组合成立、推理结果和结局 ID 的唯一权威，前端只展示可操作项并提交已有接口请求。

当前已确认现状：明代主线已有 5 个场景、8 个热点、15 条线索、10 条红字线索、3 组组合、5 个结局、4 个 NPC；证据出示反应共 10 组，其中顾闻和陆峥规则数量不足目标。阶段 11 需要补足至 8–10 场景、24–36 热点、30–45 线索、18 条以上红字、6–10 组合、8–12 推理节点和 12–18 组证据反应。

关键技术决策：

- 优先复用 `combos` 承载线索组合和推理结论，新增 `deductions` 仅在无法清晰表达连续推理时采用。
- 热点新增 `description`、`required_stage`、`required_clue_ids`、`repeat_text` 等字段时保持默认值，避免破坏旧数据。
- `/api/investigate` 继续负责热点合法性、线索过滤、重复点击不重复加线索和阶段评估。
- `/api/dialogue` 继续通过已发现线索校验来实现证据出示，必要时前端增加“选择已发现线索出示”的轻量 UI。
- 结局判定继续集中在 `GameEngine._pick_ending`，隐藏结局必须依赖完整证据链、flags、risk 和 NPC 信任度，不可只靠最终选择。

## Implementation Notes

- 不修改 `CODEBUDDY.md`、`docs/PRD.md`、`docs/develop/*.md`、API Key 文件、无关页面、无关服务、北宋和晚唐完整主线。
- 实施前若发现文档、数据结构和代码出现实质冲突，必须停止并报告，不自行重构目录。
- 所有新增线索必须至少参与热点、NPC 释放、证据出示、组合、推理或结局之一，避免凑数。
- 避免真实 AI 依赖；若 AI 不可用，保留本地中文 Mock 和 fallback。
- 不读取、不打印、不复制、不写入任何完整密钥。
- 引用校验要覆盖场景、热点、线索、NPC、choice、combo、deduction、ending。
- 性能风险较低，核心操作是小规模 JSON 集合查找；可通过构建字典索引与集合判断避免重复遍历造成复杂逻辑膨胀。
- 日志继续使用现有 DebugLogEntry 和 AI 日志机制，只记录摘要，不记录密钥或大段敏感 payload。

## Architecture Design

现有结构是数据驱动的受控叙事引擎：

前端操作：场景调查、红字点击、NPC 对话、证据出示、最终选择
后端入口：FastAPI 路由调用 `GameEngine`
规则层：阶段机、线索释放、组合评估、NPC 信任、分数和风险
数据层：事件、场景、线索、NPC、Mock 对话、结局、历史回声 JSON
展示层：右侧案卷栏、地点和调查热点、底部对话、结局面板

本阶段只扩展这条链路，不引入新架构。若加入 `deductions`，也作为事件数据的一部分，由 `GameEngine` 统一加载、校验、结算，并通过现有会话快照或调查响应返回给前端展示。

## Directory Structure

本阶段围绕明代章节级剧本扩写，主要修改数据文件，少量同步模型、服务、类型、组件和测试。

project-root/
├── backend/
│   ├── data/
│   │   ├── events/
│   │   │   └── ming_bookshop_fire.json  # [MODIFY] 扩展章节小节、组合、推理节点、最终推理选择和阶段推进条件引用。
│   │   ├── scenes/
│   │   │   └── ming_bookshop_scenes.json  # [MODIFY] 扩展 8–10 个场景或子场景、24–36 热点、红字高亮和热点元数据。
│   │   ├── clues/
│   │   │   └── ming_bookshop_clues.json  # [MODIFY] 扩展 30–45 条线索，补足物证、文书、证言、矛盾点、推理结论和制度线索。
│   │   ├── npcs/
│   │   │   └── ming_bookshop_npcs.json  # [MODIFY] 扩展角色公开目标、隐藏动机、知识边界和可释放线索。
│   │   ├── mock/
│   │   │   ├── scene_responses.json  # [MODIFY] 为所有新增热点补齐调查反馈、重复反馈和线索释放。
│   │   │   ├── history_echoes.json  # [MODIFY] 扩展结局历史回声模板，使其引用扩写后的证据链和人物命运。
│   │   │   └── dialogues/
│   │   │       ├── npc_owner.json  # [MODIFY] 扩展许掌柜默认说法、证据击破、自保谎言和选择阶段反应。
│   │   │       ├── npc_worker.json  # [MODIFY] 扩展阿沈三更动静、后门矛盾、弱者恐惧和作证边界。
│   │   │       ├── npc_scholar.json  # [MODIFY] 补足顾闻至少 6–10 条规则和多组证据出示反应。
│   │   │       └── npc_jinyiwei.json  # [MODIFY] 补足陆峥至少 6–10 条规则，体现命令边界和隐藏路线摇摆。
│   │   ├── endings/
│   │   │   └── ming_bookshop_endings.json  # [MODIFY] 强化 5 个结局条件、正文、NPC 去向和历史回声引用。
│   │   └── rag_sources/
│   │       └── ming_bookshop_*.json  # [MODIFY/NEW] 仅补充与明代书坊、文书搜检、粮册风险直接相关的资料。
│   ├── app/
│   │   ├── models/
│   │   │   └── game_models.py  # [MODIFY] 仅在新增热点字段或 deductions 时同步 Pydantic 类型和默认值。
│   │   └── services/
│   │       ├── game_engine.py  # [MODIFY] 更新场景开放、热点条件、组合/推理结算、阶段推进和结局判定。
│   │       ├── dialogue_orchestrator.py  # [MODIFY] 仅在对话规则字段扩展后同步允许线索与上下文构造。
│   │       └── history_echo_generator.py  # [MODIFY] 仅在结局回声需要更多上下文时扩展引用来源。
│   └── tests/
│       ├── test_api.py  # [MODIFY] 更新主流程 API 路径，保持基础通关可测。
│       ├── test_demo_acceptance.py  # [MODIFY] 验证长章节 Mock Demo 可从开局跑到结局。
│       ├── test_endings_paths.py  # [MODIFY] 验证 5 个结局条件均可达且隐藏结局非最后选择触发。
│       ├── test_logic.py  # [MODIFY] 覆盖扩写后的状态机、组合和结局规则。
│       └── test_chapter_script_volume.py  # [NEW] 统计体量、中文化、引用一致、热点响应和规则覆盖。
├── frontend/
│   └── src/
│       ├── types/
│       │   └── game.ts  # [MODIFY] 同步新增热点字段、推理节点或组合展示类型。
│       ├── components/
│       │   ├── clue/
│       │   │   └── ClueSidebar.tsx  # [MODIFY] 展示更多热点描述、组合结果和思维疑团入口。
│       │   ├── dialogue/
│       │   │   ├── ClueHotspotText.tsx  # [MODIFY] 保持红字点击，兼容新增热点条件字段。
│       │   │   └── DialoguePanel.tsx  # [MODIFY] 增加从已发现线索中选择证据出示的轻量交互。
│       │   └── ending/
│       │       └── EndingPanel.tsx  # [MODIFY] 展示扩写后的结局正文、NPC 去向、历史回声来源。
│       └── mock/
│           └── entryFlow.ts  # [MODIFY] 更新明代入口中的场景数、线索数和章节摘要。
└── docs/
└── periodPrompt/
└── reports/
└── stage_11_story_volume_expansion_report.md  # [NEW] 输出阶段完成报告、体量统计、自测、中文化和审查建议。

## Key Code Structures

如必须新增推理节点，建议采用最小模型扩展：

- `DeductionNode`：包含 deduction_id、question、required_clue_ids、correct_clue_ids、wrong_feedback、success_text、effects。
- `EventTemplate.deductions`：可选列表，默认空数组，避免影响旧事件。
- `GameState.completed_deduction_ids`：可选列表，默认空数组；也可先复用 completed_combo_ids，若 UI 和测试不需要区分则避免新增状态字段。

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 在实施前继续做多文件引用和结构核验，尤其是 JSON ID、测试路径、前端展示链路。
- Expected outcome: 形成准确的修改范围和冲突清单，避免漏改或悬空引用。

### Skill

- **Code**
- Purpose: 按计划完成受控代码和数据修改，遵循现有 FastAPI、Pydantic、React TypeScript 结构。
- Expected outcome: 扩写后的明代章节可运行，Mock Demo 和 fallback 不被破坏。

- **test-runner**
- Purpose: 编写并执行后端测试、体量统计测试、结局路径测试和前端构建验证。
- Expected outcome: 输出可复现的测试结果，无法执行时说明原因和影响。

- **security-auditor**
- Purpose: 检查密钥泄露、用户可见英文、AI 越权、前端越权决定阶段或结局等风险。
- Expected outcome: 确认无完整 API Key 进入 Markdown、JSON、前端、日志或测试输出。