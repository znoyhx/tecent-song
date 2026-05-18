# 阶段 11：章节级剧本体量扩写 Prompt

## 1. 你的角色

你是《史隙》章节级剧本扩写执行模型。你的任务不是写一篇长篇小说，而是在现有明代 / 书坊学徒 / 书坊焚稿案基础上，把短流程 Demo 扩展成接近商业推理游戏章节的完整可玩剧本。

目标效果参考用户给出的《山河旅探》第一章《无妄之祸》式结构：强钩子开场、危机卷入、回忆前情、现场调查、证物获得、NPC 盘问、出示证据、思维疑团、连续推理选择、反转、最终指证、真相动机、尾声钩子。

你必须把这些结构转化为《史隙》自己的明代历史悬疑内容，禁止照搬示例的人物、案件、诡计、台词和现代侦探设定。

## 2. 必须先阅读的文档

必须阅读：

- `CODEBUDDY.md`
- `docs/PRD.md`
- `docs/develop/04_data_model_design.md`
- `docs/develop/05_game_state_machine.md`
- `docs/develop/07_npc_and_permission_system.md`
- `docs/develop/08_clue_system.md`
- `docs/develop/13_api_contracts.md`
- `docs/develop/14_mock_demo_plan.md`
- `docs/develop/17_testing_and_acceptance.md`
- `docs/periodPrompt/00_global_rules.md`
- 当前明代事件数据：`backend/data/events/ming_bookshop_fire.json`
- 当前场景数据：`backend/data/scenes/ming_bookshop_scenes.json`
- 当前线索数据：`backend/data/clues/ming_bookshop_clues.json`
- 当前 NPC 数据：`backend/data/npcs/ming_bookshop_npcs.json`
- 当前 Mock 场景响应：`backend/data/mock/scene_responses.json`
- 当前 Mock NPC 对话：`backend/data/mock/dialogues/*.json`
- 当前结局数据：`backend/data/endings/ming_bookshop_endings.json`
- 当前后端状态机入口：`backend/app/services/game_engine.py`
- 当前前端类型与展示组件：`frontend/src/types/game.ts`、`frontend/src/components/clue/*`、`frontend/src/components/dialogue/*`、`frontend/src/components/ending/*`

如果文档、数据结构和代码存在冲突，先停止并报告冲突，不要自行重构目录。

## 3. 阶段目标

必须完成：

- 把明代 / 书坊学徒 / 书坊焚稿案扩写为一章完整推理游戏剧本。
- 保留既有 5 阶段：`intro`、`investigation`、`reversal`、`choice`、`ending`，但每个阶段内部必须有更多可玩节点。
- 剧本必须包含：序幕、前情/回忆、初始危机、自证或脱困、开放调查、NPC 盘问、证据出示、思维疑团、连续推理选择、中段反转、最终指证、多结局、历史回声。
- 明确主要角色、隐藏关系、公开目标、真实动机、信息边界和被证据击破的谎言。
- 扩展可调查场景和子场景，形成“视觉小说舞台 + 右侧案卷调查 + 底部对话”的完整章节节奏。
- 扩展线索和证物，使真相必须由玩家逐步拼出，不能由 NPC 直接说出。
- 扩展出示证据、线索组合和推理选择，使玩家有类似“证物栏出示 / 思维疑团 / 指证”的推理操作。
- 保留至少 5 个中文结局：自保、秩序、真相、悲剧、隐藏，并让结局条件引用扩写后的线索、flags、scores、risk 和 NPC 信任度。
- 保持所有用户可见文本为中文。
- 保持 Mock Demo 可跑通；真实 AI 不可用时仍有中文 fallback。

不完成：

- 不扩写北宋、晚唐完整主线。
- 不重写产品 PRD。
- 不重构整体前后端架构。
- 不新增无关玩法系统。
- 不让 AI 决定阶段、关键线索释放或结局 ID。

## 4. 目标体量标准

扩写后必须达到以下最低体量。若现有代码结构暂时无法全部承载，必须先报告缺口，再做最小必要字段或服务扩展。

| 类别 | 最低要求 | 说明 |
| --- | --- | --- |
| 剧情部分 | 5 大阶段、12–18 个剧情小节 | 每个小节要有目标、触发条件、展示文本和下一步 |
| 主要角色 | 4 名既有 NPC + 1–2 名可选边缘人物或离场人物记录 | 不强制增加可对话 NPC；可用证词、文书、回忆呈现 |
| 场景/子场景 | 8–10 个可进入地点或子场景 | 可在既有 5 场景内拆分：前厅、账房、后院火场、刻版间、后门、雨巷、码头/城门、问话处等 |
| 调查热点 | 24–36 个热点 | 每个热点要可点击、可重复点击不重复加线索 |
| 线索/证物 | 30–45 条 | 包含物证、证言、文书、矛盾点、推理结论、历史制度线索 |
| 红色高亮 | 18 条以上 | 首次出现的关键线索必须红字可点 |
| NPC 对话规则 | 每名核心 NPC 至少 6–10 条规则 | 覆盖默认追问、出示证据、信任变化、阶段变化 |
| 出示证据反应 | 12–18 组 | 至少覆盖许掌柜、阿沈、顾闻、陆峥 |
| 线索组合 | 6–10 组 | 组合结果要产生 flags、score/risk 或阶段推进条件 |
| 推理选择 | 8–12 个 | 包含单选、证物出示、人物指证、地点/物件指证 |
| 误导线 | 至少 3 条 | 例如灯油走水、顾闻纵火、阿沈偷稿；后续必须有修正证据 |
| 中段反转 | 至少 2 次 | 例如“烧的不是诗稿”与“封口令不等于陆峥真知情” |
| 结局 | 5 个可达 | 每个结局有标题、摘要、正文、NPC 去向、历史回声 |
| 剧本文字量 | 数据内用户可见中文正文合计建议 12000 字以上 | 不含代码、字段名、测试断言 |

## 5. 章节级剧本结构模板

必须把明代书坊焚稿案整理为以下可玩结构。字段名可沿用现有 JSON，但内容要覆盖这些节点。

### 第一部分：序幕与卷入

目标：让玩家在 1 分钟内理解“我为什么必须查”。

必须包含：

- 雨夜书坊火起的强画面。
- 玩家作为书坊学徒被卷入：可能被怀疑看守失职、私藏残页或协助焚稿。
- 许掌柜、阿沈、陆峥至少一人当场施压。
- 首个可点击红字线索出现。
- 玩家获得第一个明确目标：自证、护住书坊、查清被烧的到底是什么。

参考结构：

```text
【剧情】雨夜、火光、纸灰、封门、问话。
【调查操作 1】点击前厅或后院的关键物件。
【获得线索】第一条表层线索。
【阶段目标】证明火不是普通走水，或证明自己没有私藏文书。
```

### 第二部分：前情 / 回忆 / 关系铺垫

目标：补足案发前人物关系和误导信息。

必须包含：

- 玩家回忆火起前一晚的书坊日常。
- 许掌柜对某批稿件异常紧张。
- 阿沈曾在三更后离开刻版间或说法矛盾。
- 顾闻曾冒雨来取稿，却不肯说明真实目的。
- 陆峥或官面压力曾提前出现痕迹。
- 至少 3 个“当时看似普通、后面变成证据”的伏笔。

### 第三部分：初始自证或脱困

目标：让玩家通过观察和证据从被动嫌疑中获得调查资格。

必须包含：

- 一组小型推理选择，不要求立刻指出真凶。
- 至少 3 条证据用于解释玩家为何不是主谋或为何事件不是意外。
- 错选可以增加 risk 或触发 NPC 低信任回复，但不能直接死局。

示例问题形态：

```text
【推理选择】火势最先不是从灯油架烧起，说明什么？
A. 灯油自然翻倒
B. 有人移动过起火点
C. 纸张本身会自燃
正确方向：B
```

### 第四部分：开放调查

目标：形成类似完整推理游戏的“场景调查 + 证物栏 + NPC 盘问”。

必须覆盖至少 4 类调查：

- 现场物证：火场、灰烬、门闩、油味、刻版、残页。
- 文书证据：稿单、账册、封条、搜检告示、残缺抄录。
- 人物证言：许掌柜、阿沈、顾闻、陆峥的前后矛盾。
- 历史制度线索：文书搜检、书坊风险、锦衣卫权限、粮册敏感性。

每个调查热点应尽量具备：

```json
{
  "hotspot_id": "唯一 ID",
  "label": "中文按钮名",
  "description": "玩家点击前看到的中文提示",
  "clue_ids": ["释放的线索 ID"],
  "required_stage": "investigation 或 reversal",
  "required_clue_ids": [],
  "repeat_text": "重复点击时的中文提示"
}
```

若当前模型不支持这些字段，只能做最小兼容扩展，并同步更新类型和测试。

### 第五部分：NPC 盘问与出示证据

目标：每个 NPC 都要有“默认说法、被证据击破、进一步透露、仍然保留边界”的多层反应。

必须为每名核心 NPC 设计：

- 公开说法。
- 可被发现的矛盾。
- 害怕或隐瞒的原因。
- 出示 2–4 条关键线索后的不同反应。
- 信任度变化。
- 可释放的新线索或新问题。
- 禁止直接说出的真相边界。

NPC 设计要求：

| NPC | 扩写重点 |
| --- | --- |
| 许掌柜 | 书坊生计、保命、自保谎言、知道哪些稿件不该留 |
| 阿沈 | 刻工视角、三更动静、后门/刻版间矛盾、弱者恐惧 |
| 顾闻 | 表面像嫌疑人，实际护送抄录；不能过早说出完整真相 |
| 陆峥 | 官面压力、命令边界、并非全知；可在隐藏路线中出现摇摆 |

### 第六部分：思维疑团与线索组合

目标：把“玩家已拿到的线索”转化为可操作推理节点，而不是直接播放真相。

至少设计 6 个思维疑团：

- 火是意外走水吗？
- 被烧毁的只是诗稿吗？
- 谁有机会移动旧书箱或残页？
- 顾闻为何冒雨回到书坊？
- 陆峥为何只盯残页而不问火因？
- 封口令背后是否还有上游命令？

每个疑团必须包含：

```json
{
  "deduction_id": "唯一 ID",
  "question": "中文疑团问题",
  "required_clue_ids": ["可参与判断的线索"],
  "correct_clue_ids": ["正确证据"],
  "wrong_feedback": "错误选择后的中文反馈",
  "success_text": "推理成立后的中文结论",
  "effects": {
    "add_flags": ["推理 flag"],
    "score_delta": {"truth": 1},
    "risk_delta": 0
  }
}
```

若现有数据结构没有 `deductions`，可以先用 `combos`、dialogue rules、choice preconditions 承载；如必须新增字段，同步更新后端解析和测试。

### 第七部分：中段反转

目标：至少完成两次“玩家认知变化”。

必须包含：

1. 第一反转：火灾不是意外，且目标不是普通诗稿。
2. 第二反转：粮册抄录牵出封口令，但陆峥未必知道完整上游动机。
3. 可选第三反转：某个看似保护书坊的人其实提前清理过证据。

反转不能靠 NPC 口述直接给出，必须由线索组合、出示证据或推理选择触发。

### 第八部分：最终推理与指证

目标：形成类似“连续追问 + 出示证据 + 指证人物/物件”的结案段落。

必须设计 8–12 个连续推理节点，至少包含：

- 指出火起点异常的证据。
- 指出被烧物并非普通诗稿。
- 指出顾闻为何不是单纯纵火者。
- 指出阿沈说谎但不是主谋。
- 指出许掌柜自保行为造成证据断裂。
- 指出陆峥命令矛盾。
- 指出封口令或上游压力。
- 进入最终选择：保命、交官、护证、逼证、反查。

注意：本项目主 Demo 不一定要做单一“真凶伏法”结局。结案段落的核心应是“玩家还原事件链并做历史压力下的选择”。

### 第九部分：多结局与历史回声

每个结局必须引用玩家实际发现的线索和选择，不得只有一句泛泛总结。

结局要求：

- `ending_survival`：焚稿自保。短期活路明确，但证据消失。
- `ending_order`：误信告发。秩序合上案卷，但真相被压低。
- `ending_truth`：暗藏残页。证据被护出，但代价转移到相关人物身上。
- `ending_tragedy`：身陷诏狱。高风险推进失败，弱者先被吞没。
- `ending_hidden`：引火反查。必须由更完整证据链、陆峥/顾闻信任、封口令线索共同触发。

每个结局必须包含：

- 中文标题。
- 中文摘要。
- 400 字以内结局正文。
- 至少 3 名 NPC 去向。
- 历史回声，至少引用 2 条关键线索或 1 条关键选择 + 1 个 NPC 命运。

## 6. 当前阶段禁止事项

- 禁止照搬用户示例中的《山河旅探》人物、案件、台词、机关和真相。
- 禁止把扩写做成纯 Markdown 长文而不落到可运行数据或可验证规则。
- 禁止删除现有明代主流程、Mock fallback、AI fallback、视觉 fallback。
- 禁止修改 `docs/PRD.md`、`CODEBUDDY.md`、`docs/develop/*.md`，除非用户明确要求。
- 禁止读取、输出、复制、打印任何 API Key。
- 禁止把 DeepSeek、硅基流动或其他密钥写进 Markdown、JSON、前端、日志或测试输出。
- 禁止让前端决定 `current_stage`、关键线索释放或结局 ID。
- 禁止让 AI 直接新增关键线索、跳阶段或决定结局。
- 禁止为了凑数量新增无效线索；每条线索必须参与调查、对话、组合、推理或结局至少一处。
- 禁止新增英文用户可见文本。
- 禁止破坏北宋、晚唐现有轻量入口。
- 禁止大规模重构目录或替换现有技术栈。

## 7. 允许修改的文件范围

可创建/修改：

- `backend/data/events/ming_bookshop_fire.json`
- `backend/data/scenes/ming_bookshop_scenes.json`
- `backend/data/clues/ming_bookshop_clues.json`
- `backend/data/npcs/ming_bookshop_npcs.json`
- `backend/data/mock/scene_responses.json`
- `backend/data/mock/dialogues/*.json`
- `backend/data/mock/history_echoes.json`
- `backend/data/endings/ming_bookshop_endings.json`
- `backend/data/rag_sources/ming_bookshop_*.json`（仅补充与扩写剧本直接相关的明代书坊资料）
- `backend/app/models/game_models.py`（仅当新增字段确有必要）
- `backend/app/services/game_engine.py`（仅当新增字段或推理节点确有必要）
- `backend/app/services/dialogue_orchestrator.py`（仅联调扩写后的对话规则）
- `backend/app/services/history_echo_generator.py`（仅联调扩写后的历史回声上下文）
- `frontend/src/types/game.ts`（仅同步新增字段类型）
- `frontend/src/components/clue/*`（仅展示更多调查、线索、组合、疑团）
- `frontend/src/components/dialogue/*`（仅展示更多对话与出示证据）
- `frontend/src/components/ending/*`（仅展示扩写后的结局字段）
- `frontend/src/mock/entryFlow.ts`（仅同步明代入口中的线索数、场景数、剧本摘要）
- `backend/tests/test_api.py`
- `backend/tests/test_demo_acceptance.py`
- `backend/tests/test_endings_paths.py`
- `backend/tests/test_logic.py`
- 可新增 `backend/tests/test_chapter_script_volume.py`
- `docs/periodPrompt/reports/stage_11_story_volume_expansion_report.md`

## 8. 不允许修改的文件范围

不允许修改：

- `docs/PRD.md`
- `CODEBUDDY.md`
- `docs/develop/*.md`
- `docs/DeepseekAPIKey`
- `docs/ImageGenerateKey`
- `.codebuddy/`
- 无关前端页面和样式
- 无关后端服务
- 北宋、晚唐完整主线数据，除非只是保持入口兼容
- 已生成图片文件，除非用户明确要求重新生成视觉资产

## 9. 具体开发任务

### 任务 1：梳理现有短剧本和目标差距

- 任务目标：确认当前明代主线已有场景、线索、NPC、结局和测试覆盖。
- 参考文档：`docs/PRD.md`、`docs/periodPrompt/00_global_rules.md`。
- 涉及文件：只读检查 `backend/data/*`、`backend/app/services/game_engine.py`、`backend/tests/*`。
- 输出：列出当前体量和目标体量差距。
- 验收标准：报告中明确当前已有数量与需扩写数量。

### 任务 2：设计章节级剧本大纲

- 任务目标：先写出可执行的章节结构，再改数据。
- 输入：明代书坊焚稿案现有真相“烧毁的不是普通诗稿，而是夹带在诗稿中的辽东粮册抄录”。
- 输出：12–18 个剧情小节，每个小节包含：阶段、触发条件、场景、涉及 NPC、可调查点、可获得线索、可进入的下一节点。
- 验收标准：大纲覆盖序幕、回忆、自证、调查、反转、推理、抉择、结局。

### 任务 3：扩展场景和调查热点

- 任务目标：把现有 5 场景扩展为 8–10 个场景或子场景，并提供 24–36 个调查热点。
- 涉及文件：`backend/data/scenes/ming_bookshop_scenes.json`、`backend/data/mock/scene_responses.json`。
- 输出：中文场景描述、红字高亮、热点按钮、调查反馈、重复点击反馈。
- 验收标准：每个热点 ID 都能在场景和响应中找到对应关系；点击不会报“未找到对应调查点”。

### 任务 4：扩展线索和证物

- 任务目标：把线索从当前数量扩展到 30–45 条，并保证每条线索有玩法作用。
- 涉及文件：`backend/data/clues/ming_bookshop_clues.json`。
- 线索类型至少包含：
  - 物证
  - 文书
  - 证言
  - 矛盾点
  - 推理结论
  - 历史制度线索
- 验收标准：每条线索至少满足以下之一：可由热点获得、可由 NPC 释放、可用于出示证据、可用于线索组合、可影响结局。

### 任务 5：扩展 NPC 对话和出示证据反应

- 任务目标：让每名核心 NPC 形成多层盘问体验。
- 涉及文件：`backend/data/mock/dialogues/*.json`、必要时 `backend/app/services/dialogue_orchestrator.py`。
- 输出：每名 NPC 至少 6–10 条对话规则；全案至少 12–18 组出示证据反应。
- 验收标准：同一 NPC 在不同阶段、不同出示证据、不同信任度下有明显不同中文回复。

### 任务 6：扩展线索组合和思维疑团

- 任务目标：让玩家通过线索组合和推理选择逐步推出真相。
- 涉及文件：`backend/data/events/ming_bookshop_fire.json`、必要时 `backend/app/models/game_models.py`、`backend/app/services/game_engine.py`、`frontend/src/components/clue/*`。
- 输出：6–10 组线索组合，8–12 个推理选择或疑团节点。
- 验收标准：组合和推理结果能增加 flags、truth/order/survival 分数、risk 或 NPC trust，并参与阶段推进或结局判定。

### 任务 7：扩展最终推理和多结局条件

- 任务目标：把结尾从简单选择扩展为“证据链成立后进入最终抉择”。
- 涉及文件：`backend/data/events/ming_bookshop_fire.json`、`backend/data/endings/ming_bookshop_endings.json`、`backend/app/services/game_engine.py`、`backend/tests/test_endings_paths.py`。
- 输出：5 个结局全部可达，隐藏结局需要更完整证据链。
- 验收标准：不能只根据最后一个 choice 判定全部结局；至少引用线索、flags、scores、risk、NPC trust 中的 3 类条件。

### 任务 8：补充测试和验收路线

- 任务目标：证明扩写后的长剧本可运行、可通关、可验证。
- 涉及文件：`backend/tests/*`、`docs/periodPrompt/reports/stage_11_story_volume_expansion_report.md`。
- 输出：至少 1 条完整主线验收路线、3 条结局路线、1 条隐藏结局路线。
- 验收标准：测试通过或明确说明无法执行原因；人工路线能从开局走到结局。

## 10. 数据与接口要求

- 不得破坏既有 API：
  - `GET /api/health`
  - `GET /api/dynasties`
  - `GET /api/roles`
  - `POST /api/session/start`
  - `GET /api/session/{session_id}`
  - `POST /api/investigate`
  - `POST /api/dialogue`
  - `POST /api/choice`
  - `POST /api/ending/resolve`
- `POST /api/investigate` 返回的新线索必须经过后端规则过滤。
- `POST /api/dialogue` 返回的新线索必须经过后端规则过滤。
- `POST /api/choice` 前必须确认当前阶段和前置条件。
- 结局 ID 必须由后端规则决定。
- 若新增字段，必须同步更新：
  - Pydantic 模型
  - 前端 TypeScript 类型
  - 数据加载逻辑
  - 至少一个后端测试
- 所有 JSON 引用 ID 必须一致：场景、热点、线索、NPC、选择、组合、结局不得出现悬空引用。

## 11. 中文化要求

所有用户可见文本必须中文，包括：

- 场景名
- 场景描述
- 热点按钮
- 调查反馈
- 红字高亮
- 线索标题和详情
- 证物说明
- NPC 台词
- NPC 动作
- 玩家选项
- 推理问题
- 错误反馈
- 成功结论
- 结局标题、摘要、正文、NPC 命运、历史回声
- Loading、Error、空状态、按钮、提示

完成后必须执行中文化检查，至少搜索：

- `Start`
- `Loading`
- `Error`
- `Submit`
- `Continue`
- `Inventory`
- `Clue`
- `NPC`
- `Session`
- `Choice`
- `Ending`
- `Back`
- `Next`

代码变量名、文件名、接口字段可以英文；用户看得到的文字不可以英文。

## 12. AI 接入要求

- 本阶段重点是剧本体量和规则数据扩写，不要求新增真实 AI 能力。
- 如果真实 AI 已启用，AI 只能参与：NPC 表达、历史回声润色、氛围文本润色、视觉提示词润色。
- AI 不得决定：阶段跳转、关键线索释放、推理正确性、结局 ID。
- AI 输出必须经过一致性监管器或后端规则过滤。
- AI 失败、无 Key、超时或输出不合规时，必须使用中文 fallback。
- 不得读取、打印、复制或写入任何完整 API Key。
- 如执行真实 AI 测试，只能报告“存在/不存在”“成功/失败”“是否 fallback”，不得输出密钥。

## 13. 模型必须执行的自测步骤

必须执行或说明无法执行原因：

- 校验 JSON 格式合法。
- 校验所有场景 ID、热点 ID、线索 ID、NPC ID、choice ID、combo ID、ending ID 引用一致。
- 统计场景/子场景数量是否达到 8–10。
- 统计调查热点数量是否达到 24–36。
- 统计线索数量是否达到 30–45。
- 统计红色高亮数量是否达到 18 条以上。
- 统计出示证据反应是否达到 12 组以上。
- 统计线索组合是否达到 6 组以上。
- 测试 `POST /api/session/start`。
- 测试至少 10 个 `POST /api/investigate` 热点。
- 测试至少 4 名 NPC 的 `POST /api/dialogue`。
- 测试至少 6 组出示证据反应。
- 测试至少 6 组线索组合或推理节点。
- 测试自保、秩序、真相 3 条基础结局。
- 测试悲剧和隐藏结局，若无法自动测试必须给人工路线。
- 运行现有后端测试：`python -m pytest backend/tests`，或说明无法运行原因。
- 运行前端构建：`npm run build`，或说明无法运行原因。
- 执行中文 UI 自检。
- 检查没有密钥进入 Markdown、JSON、前端、日志或测试输出。

## 14. 人工验收方式

用户应按以下路径验收扩写后的章节体量：

1. 启动后端：

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

2. 启动前端：

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

3. 打开 `http://127.0.0.1:5173/`。
4. 选择“明代”，进入“书坊焚稿案”。
5. 确认开场不再只有短摘要，而有序幕、危机和明确目标。
6. 在至少 4 个地点点击红字线索和调查热点。
7. 确认右侧线索栏累计出现 10 条以上线索，并可查看详情。
8. 分别盘问许掌柜、阿沈、顾闻、陆峥。
9. 至少对 2 名 NPC 出示证据，确认回复变化。
10. 完成至少 2 组线索组合或思维疑团。
11. 触发中段反转，确认玩家知道“烧毁的不是普通诗稿”。
12. 进入最终抉择前，确认已有证据链摘要或推理结论。
13. 分别走至少 3 条结局路线，确认结局标题、正文、NPC 去向、历史回声均为中文。
14. 走隐藏路线，确认其不是只靠最后选择触发，而需要完整证据链和信任条件。

如果出现以下情况，本阶段不通过：

- 页面出现英文用户可见文本。
- 任一核心路线无法进入结局。
- 隐藏结局只靠最后选择即可触发。
- NPC 直接说出完整真相，玩家不需要推理。
- AI 或前端可以越权决定阶段或结局。
- Mock/fallback 被破坏。
- 出现任何完整 API Key。

## 15. 完成后必须返回的报告格式

```md
# 阶段完成报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. 剧本体量统计

| 类别 | 目标 | 实际 | 是否达标 |
| --- | --- | --- | --- |
| 场景/子场景 | 8–10 |  |  |
| 调查热点 | 24–36 |  |  |
| 线索/证物 | 30–45 |  |  |
| 红色高亮 | ≥18 |  |  |
| NPC 对话规则 | 每人 6–10 |  |  |
| 出示证据反应 | 12–18 |  |  |
| 线索组合/推理节点 | ≥6 |  |  |
| 结局 | 5 |  |  |

## 4. 关键剧情结构

说明序幕、前情、自证、调查、反转、最终推理、结局如何落地。

## 5. 自测结果

## 6. 中文化检查结果

## 7. AI 接入测试结果

说明本阶段是否使用真实 AI；如未使用，说明使用 Mock / fallback，不得声称真实 AI 成功。

## 8. 图片生成测试结果

本阶段不要求新增真实图片生成；如未执行，说明不涉及。若执行，必须说明是否真实调用、是否 fallback，且不得输出 Key。

## 9. 人工验收方法

## 10. 未完成事项

## 11. 阻塞问题

## 12. 是否建议进入下一阶段

## 13. 是否需要强模型审查
```

## 16. 强模型审查要求

本阶段属于强故事线、状态机、线索系统和结局条件的高风险扩写。完成后必须建议强模型审查，重点审查：

- 是否真的形成章节级可玩剧本，而不是长篇散文。
- 是否保持后端状态机权威。
- 是否所有关键线索都有释放条件。
- 是否所有结局由规则决定。
- 是否存在悬空 ID。
- 是否有英文用户可见文本。
- 是否泄露密钥。
- 是否破坏现有 Mock Demo、真实 AI fallback 或视觉 fallback。
