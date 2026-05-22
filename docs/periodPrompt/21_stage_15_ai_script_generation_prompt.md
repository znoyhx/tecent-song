# 阶段 15：DeepSeek AI 剧本生成 P0 Prompt

## 1. 你的角色

你是《史隙》AI 剧本生成系统执行模型。你的任务是实现北宋 / 晚唐入口的“关键词 -> DeepSeek 多轮生成剧本 -> 图片生成与质量门禁 -> 热点定位 -> 剧本概览与选人 -> 进入生成剧本”闭环。

一句话边界：

> 明代继续是稳定固定 Demo；北宋和晚唐才进入 AI 剧本生成。生成流程必须真实、可追踪、可失败，不允许用假进度、占位图或 Mock 结果冒充完成。

本阶段不是重写整套游戏，不是替换明代书坊焚稿案，也不是做纯文本故事生成。你要把生成结果导入现有 React + Phaser + FastAPI 游戏框架，让生成剧本可玩、可验收、可回退。

## 2. 必须先阅读的文档

必须阅读：

- `CODEBUDDY.md`
- `docs/PRD.md`
- `docs/develop/04_data_model_design.md`
- `docs/develop/05_game_state_machine.md`
- `docs/develop/06_ai_dialogue_pipeline.md`
- `docs/develop/08_clue_system.md`
- `docs/develop/10_consistency_supervisor.md`
- `docs/develop/13_api_contracts.md`
- `docs/develop/15_real_ai_integration_plan.md`
- `docs/develop/16_visual_asset_plan.md`
- `docs/develop/17_testing_and_acceptance.md`
- `docs/develop/23_ai_script_generation_requirements.md`
- `docs/periodPrompt/00_global_rules.md`
- 当前阶段 Prompt：`docs/periodPrompt/21_stage_15_ai_script_generation_prompt.md`
- 当前后端入口：`backend/app/main.py`、`backend/app/routers/game.py`、`backend/app/routers/visual.py`
- 当前后端服务：`backend/app/services/game_engine.py`、`backend/app/services/dialogue_orchestrator.py`、`backend/app/services/supervisor.py`、`backend/app/services/repair_agent.py`、`backend/app/services/visual_prompt_agent.py`、`backend/app/services/image_generation_service.py`
- 当前前端入口：`frontend/src/App.tsx`
- 当前游戏页：`frontend/src/pages/GamePage.tsx`
- 当前类型：`frontend/src/types/game.ts`
- 当前 API helper：`frontend/src/api/client.ts`
- 当前样式：`frontend/src/styles/global.css`

如果文档、代码和当前数据结构冲突，先停止并报告冲突，不要自行大规模重构。

## 3. 阶段目标

必须完成：

- 明代入口仍直接启动现有书坊焚稿案 Demo，不进入 AI 剧本生成。
- 北宋 / 晚唐入口进入关键词填写页。
- 用户填写 1-8 个关键词后，调用后端 AI 剧本生成 job。
- 后端新增脚本生成 API、job 状态 API、生成剧本启动 API。
- 后端真实调用 DeepSeek 生成结构化 `ScriptPackage`。
- 剧本至少经过“初稿、编剧审稿、逻辑 QA、修复合并”4 轮 DeepSeek 打磨。
- 生成过程有真实 job steps，前端流程图严格跟随后端状态，不允许假进度。
- 等待页可以轮播历史名人名句，但名句只做过渡，不推动进度。
- 生成 `script_overview` 和 `playable_identities`。
- 生成 `visual_style_guide`、`appearance_lock`、`era_feature_checklist`、`hotspot_positioning`。
- 生成场景图、人物图、核心线索图，并通过 `ImageQualityGate`。
- 占位图、空白图、fallback 图、旧缓存图、错风格图、错朝代图不能计入完成。
- 图片未通过质量门禁时，必须改写 prompt 并重新请求生图。
- 必需图片通过后，基于 approved 图片执行热点坐标校准。
- job 完成后进入“剧本概览 + 选人”页。
- 选人页使用生成剧本的 `playable_identities`，不能使用静态身份卡。
- 选择身份后调用 `POST /api/session/start-generated`，进入生成剧本首场景。
- 生成剧本可用现有调查、对话、线索栏、Phaser 舞台和结局系统游玩。
- 前后端构建和关键测试通过。
- 完成报告写入 `docs/periodPrompt/reports/stage_15_ai_script_generation_report.md`。

不完成：

- 不用 AI 替换明代稳定 Demo。
- 不让前端直接调用 DeepSeek。
- 不让前端直接调用生图服务。
- 不让 Phaser 决定剧情规则、线索释放、阶段跳转或结局。
- 不用 Mock 冒充真实 AI 生成。
- 不用占位图冒充通过图片验收。
- 不做完全任意历史时期生成；P0 只支持北宋和晚唐 / 唐后期。
- 不把生成剧本做成只能阅读的长文。

## 4. 当前阶段禁止事项

- 禁止修改 `docs/DeepseekAPIKey`、`docs/ImageGenerateKey` 或把其中内容复制到任何代码、日志、Markdown。
- 禁止在前端、日志、报告或测试输出中打印完整 API Key。
- 禁止 `POST /api/scripts/generate` 默认为明代生成新剧本。
- 禁止前端用定时器假装推进生成流程图。
- 禁止 job 未完成时进入剧本概览。
- 禁止图片未全部 approved 时进入正式生成剧本 session。
- 禁止用旧明代数据、静态北宋 / 晚唐预览卡、静态身份卡冒充生成结果。
- 禁止把 AI 输出直接写入游戏状态，必须先 schema 校验、剧本监管、修复。
- 禁止 NPC 在早期直接泄露最终真相。
- 禁止用户可见英文文本。
- 禁止破坏现有明代 Demo、DialoguePanel、ClueSidebar、EndingPanel、PhaserStage 回退。

## 5. 允许修改的文件范围

可创建 / 修改：

- `backend/app/main.py`
- `backend/app/routers/game.py`（仅保留兼容或接入生成 session）
- `backend/app/routers/scripts.py`
- `backend/app/models/game_models.py`
- `backend/app/models/script_models.py`
- `backend/app/services/ai_client.py` 或既有 AI client 封装文件
- `backend/app/services/script_generation_service.py`
- `backend/app/services/script_supervisor.py`
- `backend/app/services/script_import_service.py`
- `backend/app/services/script_job_store.py`
- `backend/app/services/image_quality_gate.py`
- `backend/app/services/hotspot_calibration_service.py`
- `backend/app/services/quote_pool.py`
- `backend/app/services/image_generation_service.py`（仅复用或补充质量门禁所需字段）
- `backend/app/services/visual_prompt_agent.py`（仅补充 generated script prompt 规范）
- `backend/data/prompts/*.md` 或 `.json`
- `backend/data/generated_scripts/`
- `backend/data/quotes/*.json`
- `backend/tests/test_script_generation*.py`
- `backend/tests/test_generated_session*.py`
- `backend/tests/test_image_quality_gate*.py`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/types/game.ts`
- `frontend/src/pages/*`
- `frontend/src/components/script-generation/*`
- `frontend/src/components/start/*` 或现有入口组件
- `frontend/src/components/scene/*`（仅为生成剧本 hotspot 坐标兼容）
- `frontend/src/styles/global.css`
- `docs/periodPrompt/reports/stage_15_ai_script_generation_report.md`

## 6. 不允许修改的文件范围

默认不允许修改：

- `docs/PRD.md`
- `CODEBUDDY.md`
- `docs/develop/*.md`
- `docs/DeepseekAPIKey`
- `docs/ImageGenerateKey`
- `.codebuddy/`
- 无关前端页面
- 无关后端服务
- 明代书坊案核心数据，除非是为了兼容现有固定 Demo 启动，不得改剧情内容
- 既有图片资源，除非是生成新剧本资产落到 `assets/generated/visuals/` 或等价 generated 目录

如果确实必须修改禁止范围，先报告原因、风险和最小方案。

## 7. 具体开发任务

### 任务 1：梳理当前入口和数据流

- 任务目标：确认明代、北宋、晚唐当前入口如何启动 session。
- 涉及文件：`frontend/src/App.tsx`、入口页组件、`frontend/src/api/client.ts`、`backend/app/routers/game.py`。
- 输出：在完成报告中记录当前入口路径和需要插入生成流程的位置。
- 验收标准：明确“明代直达固定 Demo，北宋 / 晚唐进入关键词生成页”的最小改动点。

### 任务 2：定义 ScriptPackage 与 Job 模型

- 任务目标：新增后端结构化模型，承载生成剧本。
- 涉及文件：`backend/app/models/script_models.py`、必要时 `backend/app/models/game_models.py`。
- 必须包含：
  - `ScriptPackage`
  - `script_overview`
  - `playable_identities`
  - `world`
  - `story`
  - `stages`
  - `locations`
  - `npcs`
  - `relationships`
  - `clues`
  - `clue_graph`
  - `dialogue_rules`
  - `choices`
  - `endings`
  - `visual_assets`
  - `visual_style_guide`
  - `hotspot_positioning`
  - `quality_gate`
  - `job steps`
- 验收标准：模型能解析一份最小合法 generated script JSON；非法缺字段会返回明确错误。

### 任务 3：新增脚本生成 API

- 任务目标：实现异步或伪异步 job API。
- 推荐接口：

```text
POST /api/scripts/generate
GET  /api/scripts/jobs/{job_id}
GET  /api/scripts/{script_id}
POST /api/scripts/{script_id}/validate
POST /api/scripts/{script_id}/visuals/generate
POST /api/session/start-generated
```

- 兼容规则：
  - `POST /api/scripts/generate` P0 只接受 `song` 和 `late_tang`。
  - 收到 `dynasty_id=ming` 返回 `AI_GENERATION_DISABLED_FOR_STABLE_DEMO`。
  - 关键词为空返回 `KEYWORDS_REQUIRED`。
  - 关键词与朝代明显冲突返回 `KEYWORDS_CONFLICT_WITH_DYNASTY` 或进入修复建议。
- 验收标准：API 返回中文错误信息；前端不会看到英文错误文案。

### 任务 4：实现 DeepSeek 多轮剧本生成

- 任务目标：真实调用 DeepSeek 生成结构化剧本包。
- 涉及文件：AI client、`script_generation_service.py`、`backend/data/prompts/*`。
- 必须流程：
  1. pitch generation；
  2. script package generation；
  3. script doctor review；
  4. logic QA；
  5. refinement repair。
- P1 可加：
  - NPC permission audit；
  - playthrough simulation；
  - visual continuity audit；
  - image quality auditor。
- 输出必须 JSON，不是 Markdown。
- AI 失败时返回明确失败状态，不得用 Mock 冒充真实生成。
- 验收标准：有 Key 时真实调用 DeepSeek；无 Key 或上游失败时 job failed 或 fallback 标记清楚。

### 任务 5：实现 ScriptSupervisor 与 Repair

- 任务目标：检查剧本能不能玩。
- 必须检查：
  - schema 完整；
  - 朝代、称谓、官制、器物、空间不冲突；
  - 核心线索能串成真相链；
  - 阶段推进条件可达；
  - 结局可达；
  - NPC 信息边界清楚；
  - 没有早期剧透；
  - 玩家身份有调查动机和行动权限；
  - 视觉字段齐全；
  - 热点有坐标；
  - 图片质量门禁字段齐全。
- 阻塞问题不得导入游戏。
- 验收标准：构造一个线索断链样例，监管器能返回 blocking issue。

### 任务 6：接入图片生成与 ImageQualityGate

- 任务目标：生成场景图、人物图、核心线索图，并进行质量门禁。
- 涉及文件：`image_generation_service.py`、`image_quality_gate.py`、`visual_prompt_agent.py`。
- 必须生成并通过：
  - 5 张场景图；
  - 4 张主要 NPC 人物图；
  - 至少 6 张核心线索图。
- 必须拒绝：
  - 空白图；
  - 占位图；
  - fallback 图；
  - 旧缓存图；
  - 错风格图；
  - 错朝代图；
  - 没有核心线索物件的图；
  - 人物风格漂移图。
- 重试规则：
  - 每个必需资产至少 3 次自动重试；
  - 未通过时改写 prompt 并重新请求；
  - 仍失败则 job `visual_blocked` 或 `failed`；
  - 未全部 approved 不能进入正式游玩。
- 验收标准：报告中列出 required / approved / rejected / regenerated / blocked 数量。

### 任务 7：实现 HotspotCalibrationService

- 任务目标：为生成后的 approved 图片产生 Phaser 可用热点定位。
- 坐标要求：
  - 使用 `0-1` 归一化图片坐标；
  - P0 至少支持 `anchor_point` 和 `bbox`；
  - P1 支持 `polygon`；
  - 图片重生后必须重新校准。
- 验收标准：至少 6 个核心热点有 `anchor_point`、`bbox`、`calibration_status=approved`，且能映射到前端 Phaser 热点。

### 任务 8：实现 ScriptImportService 和生成 session

- 任务目标：把生成的 `ScriptPackage` 导入现有游戏引擎。
- 要求：
  - 不另起一套游戏系统；
  - 不硬编码明代 ID；
  - 生成 session 使用 `script_id + identity_id`；
  - `identity_id` 必须属于该剧本 `playable_identities`；
  - 必需图片未全部 approved 时拒绝启动正式 session。
- 验收标准：生成剧本首场景能被现有 React + Phaser 渲染；点击热点走现有调查流程。

### 任务 9：前端入口兼容

- 任务目标：改造朝代入口。
- 必须实现：
  - 明代：直接进入现有固定 Demo；
  - 北宋 / 晚唐：进入关键词填写页；
  - 关键词 1-8 个，不能为空；
  - 输入过空泛时给中文提示；
  - 生成请求失败时给中文错误。
- 验收标准：明代不出现生成表单；北宋 / 晚唐不直接进入旧预览。

### 任务 10：前端生成进度页

- 任务目标：展示真实流程图。
- 要求：
  - 读取 `GET /api/scripts/jobs/{job_id}` 的 `steps`；
  - 不用定时器假进度；
  - 展示 `running`、`passed`、`failed`、`blocked`、`retrying`；
  - 图片重试、剧本修复、热点重校准要展示；
  - job 失败停在失败节点；
  - 可以轮播历史名人名句，但名句不推动进度。
- 验收标准：后端 job 停在哪一步，前端流程图就停在哪一步。

### 任务 11：前端剧本概览与选人

- 任务目标：job 完成后展示生成结果确认页。
- 要求：
  - `status=completed` 且 `ready_for_overview=true` 才进入；
  - 概览来自 `script_overview`；
  - 可选身份来自 `playable_identities`；
  - 主图只能使用 approved 图片；
  - 不显示最终真相、隐藏线索、结局条件；
  - 选定身份后调用 `POST /api/session/start-generated`。
- 验收标准：不能出现静态北宋 / 晚唐预览卡或明代书坊案人物。

### 任务 12：测试、构建和报告

- 必须执行或说明无法执行原因：

```powershell
cd backend
python -m pytest
```

```powershell
cd frontend
npm run build
```

- 若真实 DeepSeek 或生图上游不可用，必须报告真实错误状态，不得伪造成功。
- 完成报告写入 `docs/periodPrompt/reports/stage_15_ai_script_generation_report.md`。

## 8. 数据与接口要求

新增 / 变更接口要遵守：

- 所有 AI、生图、质量审查和导入逻辑都在后端。
- 前端只调用后端 API。
- API Key 只从后端配置读取。
- job 状态必须可恢复；刷新页面后可以根据 `job_id` 或 `script_id` 继续查看。
- `GET /api/scripts/jobs/{job_id}` 必须返回：
  - `status`
  - `progress`
  - `current_step`
  - `steps`
  - `blocking_issues`
  - `transitional_quote`
  - `visual_quality`
  - `ready_for_overview`
- `POST /api/session/start-generated` 必须校验：
  - script exists；
  - job completed；
  - required images approved；
  - identity belongs to script；
  - generated script import successful。

## 9. 中文化要求

所有用户可见文本必须中文，包括：

- 关键词输入页；
- 表单错误；
- 生成流程图节点；
- job 失败原因；
- 图片质量门禁摘要；
- 名人名句；
- 剧本概览；
- 身份卡；
- 按钮；
- 空状态；
- loading；
- fallback。

完成后必须搜索并修复用户可见英文：

- `Loading`
- `Error`
- `Start`
- `Generate`
- `Retry`
- `Continue`
- `Overview`
- `Role`
- `Script`
- `Progress`
- `Failed`
- `Blocked`
- `Complete`

变量名、文件名、接口字段可以英文。

## 10. AI 接入要求

- 本阶段涉及真实 DeepSeek。
- 必须使用后端封装调用，不得前端直连。
- Prompt 必须要求 JSON 输出。
- 后端必须解析 JSON，不能相信模型自称合法。
- 每轮调用要记录：
  - module；
  - provider；
  - model；
  - input_summary；
  - latency；
  - success；
  - supervisor_pass；
  - fallback_used；
  - prompt_path / response_path。
- 日志不得包含 API Key。
- 如果 DeepSeek 不可用，返回 `AI_UNAVAILABLE` 或明确 job failed，不得把 Mock 结果标为 real。

## 11. 图片生成要求

- 本阶段涉及真实图片生成。
- 必须通过后端服务调用图片 provider。
- 生成后必须下载保存，不能依赖短期 URL。
- 图片 URL / asset route 必须前端可访问。
- 必需图片未通过 `ImageQualityGate` 不能算完成。
- 占位图、空白图、fallback 图、旧缓存图、错风格图、错朝代图不能通过。
- 图片失败必须重试并记录原因。
- 如果 provider 429 / 503 / 超时，报告真实阻塞，不得伪造图片成功。

## 12. 模型必须执行的自测步骤

必须执行或说明无法执行原因：

- `python -m pytest backend`
- `cd frontend; npm run build`
- 测试明代入口仍直达固定 Demo。
- 测试北宋入口进入关键词页。
- 测试晚唐入口进入关键词页。
- 测试关键词为空时中文报错。
- 测试 `POST /api/scripts/generate` 拒绝 `dynasty_id=ming`。
- 测试至少一次 DeepSeek 真实生成或明确记录上游不可用。
- 测试生成 job steps 真实更新。
- 测试流程图不假进度。
- 测试图片质量门禁拒绝不合格图片。
- 测试生成完成前不能进入概览页。
- 测试概览页读取 `script_overview`。
- 测试选人页读取 `playable_identities`。
- 测试 `POST /api/session/start-generated` 创建 generated session。
- 测试 generated session 首场景能显示。
- 测试点击至少一个 generated hotspot。
- 中文 UI 自检。
- 密钥泄露自检。

## 13. 人工验收方式

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
4. 选择“明代”，确认直接进入现有书坊焚稿案 Demo。
5. 返回入口，选择“北宋”。
6. 确认出现关键词输入页。
7. 输入关键词，例如：`驿站、军报、雨夜、粮草`。
8. 开始生成。
9. 确认出现真实流程图，节点随后端 job 推进。
10. 确认等待期间出现历史名人名句轮播，但进度不被名句推动。
11. 等待生成完成。
12. 确认进入剧本概览页，标题、案件、地点预览来自生成剧本。
13. 确认选人界面身份来自生成剧本。
14. 选择身份，进入游戏。
15. 确认首场景、人物、热点、线索栏和对话可用。
16. 点击至少一个热点，确认释放线索或调查反馈。

不通过情况：

- 明代进入 AI 生成页。
- 北宋 / 晚唐绕过关键词直接进旧预览。
- 前端流程图自动假进度。
- job 未完成就进入概览。
- 图片未 approved 就进入正式游玩。
- 概览页出现静态占位内容。
- 选人页出现与生成剧本无关的身份。
- 页面出现英文用户可见文本。
- Mock 结果被标记为真实 AI。
- 占位图被标记为完成图片。
- API Key 泄露。

## 14. 完成后必须返回的报告格式

```md
# 阶段完成报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. 入口兼容说明

说明明代、北宋、晚唐分别走什么路径。

## 4. 后端生成流程

说明 ScriptPackage、job、DeepSeek 多轮、supervisor、repair、import 如何工作。

## 5. 前端生成流程

说明关键词页、流程图、名句轮播、概览页、选人页如何对接后端。

## 6. 图片生成与质量门禁结果

| 类型 | 必需 | approved | rejected | regenerated | blocked |
| --- | ---: | ---: | ---: | ---: | ---: |
| 场景图 | 5 |  |  |  |  |
| 人物图 | 4 |  |  |  |  |
| 线索图 | 6 |  |  |  |  |

## 7. 热点定位结果

说明至少 6 个核心热点的坐标校准状态。

## 8. 自测结果

## 9. 中文化检查结果

## 10. AI 接入测试结果

说明真实 DeepSeek 是否调用成功；若失败，给出上游错误和 fallback 状态，不得伪造成功。

## 11. 图片生成测试结果

说明真实图片 provider 是否调用成功；若失败，给出上游错误和 visual_blocked 状态。

## 12. 人工验收方法

## 13. 未完成事项

## 14. 阻塞问题

## 15. 是否建议进入下一阶段

## 16. 是否需要强模型审查
```

## 15. 强模型审查要求

本阶段完成后必须建议强模型审查，重点检查：

- 明代是否仍为固定 Demo。
- 北宋 / 晚唐是否必须经过关键词生成。
- DeepSeek 是否真实调用，Mock 是否被清晰标记。
- 多轮打磨是否真的执行。
- job 流程图是否真实绑定后端状态。
- 图片质量门禁是否阻塞验收。
- 是否存在占位图冒充 approved。
- 热点坐标是否与 approved 图片一致。
- 剧本概览和选人是否来自生成后的 `ScriptPackage`。
- 生成剧本是否能进入现有游戏 session。
- 是否有英文用户可见文本。
- 是否有 API Key 泄露。
