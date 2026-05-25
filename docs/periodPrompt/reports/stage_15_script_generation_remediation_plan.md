# Stage 15 生成剧本质量整改方案

生成日期：2026-05-23  
关联报告：

- `docs/periodPrompt/reports/stage_15_ai_script_generation_report.md`
- `docs/periodPrompt/reports/stage_15_song_generation_audit_report.md`

## 1. 背景与目标

Stage 15 已跑通北宋/晚唐 AI 剧本生成闭环：DeepSeek 多轮生成、图片生成、图片门禁、热点校准、导入 generated session 都能完成。但审计发现两个 P0 质量问题：

- 中文关键词在测试请求中被编码破坏，落盘为 `["??", "??", "??", "????"]`，后端未拒绝明显无效输入。
- 生成剧本只达到 Stage 15 最低闭环规格，规模明显低于明代固定 Demo，无法替代完整章节体验。

本方案目标不是让 DeepSeek 一次性写出超长 JSON，而是建立“受控扩写 + 后端硬门禁 + 可回归测试”的生成机制：允许 DeepSeek 反复扩充剧本，但每轮只扩明确模块，并由后端校验规模、引用、可达性和图片资产覆盖，避免越扩越乱。

## 2. 验收标准

整改完成后，任一新生成的北宋/晚唐剧本至少达到以下规格；不足时 job 必须失败或进入待修复状态，不得标记 completed。

| 类别 | 最低目标 | 阻塞条件 |
| --- | ---: | --- |
| 场景 | 8-10 个 | 少于 8 个阻塞 |
| 调查热点 | 24-36 个 | 少于 24 个阻塞 |
| 线索/证物 | 30-45 条 | 少于 30 条阻塞 |
| 线索组合 | 6-10 个 | 少于 6 个阻塞 |
| 推理疑团 deductions | 8-12 个 | 少于 8 个阻塞 |
| 剧情小节 chapter_sections | 12-18 个 | 少于 12 个阻塞 |
| 最终选择 | 5 个 | 少于 5 个阻塞 |
| 结局 | 5 个 | 少于 5 个阻塞 |
| 场景图 | 8-10 张 | 必需场景图未 approved 阻塞 |
| 线索图 | 至少覆盖关键线索 | 核心线索缺图或乱码文字主体阻塞 |
| 中文关键词 | 真实中文或有效字符 | 全问号、乱码替换符、全符号阻塞 |
| 对话分流 | 推荐对话走固定规则，自由输入才走大模型 | 默认推荐回复触发 DeepSeek 阻塞 |

## 3. 总体方案

推荐方案：保留现有 DeepSeek 多轮链路，但把“整包生成 + 整包修复”升级为“骨架生成 + 分模块扩写 + 结构合并 + 体量监管”。

不推荐直接把完整剧本反复交给 DeepSeek 说“继续扩写”。这样容易带来四类问题：已有 ID 被改名、真相链被重写、图片资产 owner 映射断裂、结局条件和阶段可达性失效。正确做法是让 DeepSeek 每轮只返回指定模块的 append/update patch，并声明不可修改核心真相、已有 ID 和已通过校验的资产关系。

新的生成链路：

1. `pitch_generation`：生成案件核心、真相链、误导线和章节规格计划。
2. `script_skeleton_generation`：生成最小但完整的 ScriptPackage 骨架和全局 ID 注册表。
3. `scene_clue_expansion`：扩充 locations、hotspots、clues、visual_assets。
4. `dialogue_reasoning_expansion`：扩充 dialogue_rules、clue_graph、deductions。
5. `chapter_choice_ending_expansion`：扩充 chapter_sections、choices、endings。
6. `volume_gate_review`：后端统计规模、引用和可达性，不达标则进入定向补写。
7. `refinement_repair`：DeepSeek 只修 gate 指出的缺口，不整包自由改写。
8. `script_supervisor`：现有时代、剧透、线索链、视觉字段监管。
9. `visual_generation`：按升级后的资产数量生成图片。
10. `image_quality_gate`、`hotspot_calibration`、`script_import`：按新规模验收。

## 4. 乱码治理

### 4.1 请求输入乱码

后端需要在 `POST /api/scripts/generate` 前置校验关键词：

- 拒绝只包含 `?`、`？`、`�`、空白或标点的关键词。
- 拒绝中文占比过低且无有效字母/数字的关键词。
- 拒绝包含常见 mojibake 片段的关键词，例如 `Ã`、`Â`、`å`、`ç`、`é` 连续异常组合。
- job、AI prompt、日志 input_summary 中必须保存原始有效关键词。

建议新增错误码：

```text
KEYWORDS_ENCODING_INVALID
```

用户提示：

```text
关键词疑似编码损坏，请重新输入中文关键词后再生成。
```

自动化 smoke 请求应改为 UTF-8 安全方式：

- 优先用前端真实请求测试。
- 命令行测试使用 UTF-8 JSON 文件。
- 避免 PowerShell here-string 直接承载中文 JSON。

### 4.2 线索图乱码文字

图片乱码不是文件编码问题，而是文生图模型不擅长画可读文字。整改方向是减少“画字”，改为“画物证特征”。

线索图 prompt 调整：

- 文书类线索禁止要求生成可读正文。
- 用封泥、折痕、残缺、墨色新旧、刀痕、血迹、烧痕、书页材质表达信息。
- `negative_prompt` 加入：可读文字、水印、乱码字、现代印刷字、英文字符。
- `required_subjects` 必须包含“物件主体占画面主要区域”“无可读文字主体”。

门禁增强：

- 接入 OCR 或视觉理解模型抽检线索图。
- 发现乱码字、水印、主体过小、场景图冒充物件特写时 rejected。
- 线索图最多重生 3 次；仍失败则 job `visual_blocked`，不导入游戏。

## 5. 剧本规模扩写设计

### 5.1 数据模型补齐

当前生成剧本已有 `clue_graph`，但导入层把 `deductions` 和 `chapter_sections` 置空，导致“思维疑团”和“章节推进”玩法密度缺失。需要扩展 `ScriptPackage`：

```text
deductions: list[ScriptDeduction]
chapter_sections: list[ScriptChapterSection]
```

字段可对齐 `backend/app/models/game_models.py` 中的 `DeductionRule` 和 `ChapterSection`：

- deduction 包含 question、required_clue_ids、correct_clue_ids、wrong_feedback、success_text、effects。
- chapter_section 包含 stage、title、trigger_conditions、scene_id、npc_ids、hotspot_ids、clue_ids、next_section_ids、goal、display_text。

`ScriptImportService` 需要把生成包中的这两个字段映射到 catalog，而不是继续返回空数组。

### 5.2 ID 注册表

扩写前先建立 ID 注册表，后续所有 DeepSeek patch 必须引用注册表：

- scene/location ID
- npc ID
- clue ID
- hotspot ID
- clue_graph rule ID
- deduction ID
- chapter_section ID
- choice ID
- ending ID
- visual_asset ID

DeepSeek 每轮输出必须声明：

```text
新增 ID、更新 ID、引用 ID、禁止修改 ID
```

后端合并时若发现 ID 重复、引用不存在、已锁定 ID 被改写，直接拒绝该轮输出并要求定向修复。

### 5.3 受控扩写循环

将用户的“反复给 DeepSeek 扩充”落成受控循环：

```text
while volume_gate 未通过 and repair_round <= 3:
  1. 后端生成缺口报告
  2. DeepSeek 只补缺口模块
  3. 后端合并 patch
  4. 运行 schema 校验、引用校验、volume gate
```

缺口报告示例：

```json
{
  "missing": {
    "locations": 3,
    "hotspots": 18,
    "clues": 24,
    "deductions": 8,
    "chapter_sections": 12,
    "choices": 3,
    "endings": 3
  },
  "locked_truth_chain_clue_ids": ["clue_01", "clue_02"],
  "forbidden_changes": ["story.hidden_truth", "world", "existing ids"]
}
```

DeepSeek 不应返回整包；优先返回：

```json
{
  "patch_type": "append_script_modules",
  "append": {
    "locations": [],
    "clues": [],
    "deductions": [],
    "chapter_sections": []
  },
  "update": {
    "stages": [],
    "visual_assets": []
  }
}
```

## 6. 对话分流策略

当前对话框包含两类输入：

- 默认推荐对话：系统提供的对话选项按钮，例如 `replySuggestions` / `suggested_questions`。
- 玩家自由输入：玩家在文本框中自己打出的自然语言问题。

整改要求：这两类输入必须走不同处理路径。默认推荐对话是剧本设计的一部分，必须走固定对话规则；只有玩家自由输入才允许调用 DeepSeek。

### 6.1 默认推荐对话

默认推荐对话应视为结构化选项，不视为自然语言自由问答。

行为要求：

- 前端点击推荐按钮时，必须向后端声明来源，例如 `message_source="suggested_option"` 或 `action_type="suggested_question"`。
- 后端收到默认推荐对话后，只能匹配 `dialogue_rules`、`script_bound_chat` 或本地固定回复。
- 默认推荐对话不得调用 `DialogueOrchestrator` 的 DeepSeek 路径。
- 默认推荐对话可以释放剧本预设线索、改变 trust/risk/flags，但这些效果必须来自固定规则。
- 默认推荐对话仍需经过 Supervisor 检查，防止固定文案误放未公开真相。
- AI 日志中应记录为 `mock_dialogue`、`fixed_dialogue` 或等价本地模块名，不得出现 `NPCDialogueAgent`。

这样做的原因是：推荐按钮本来就是设计者给出的可控分支，如果仍交给大模型处理，就会引入不必要的延迟、成本和剧透风险，也会让同一个按钮在不同时间得到不稳定回答。

### 6.2 玩家自由输入

玩家在 textarea 中手写的问题才进入真实 AI 对话链路。

行为要求：

- 前端点击“继续追问”且消息来自 textarea 时，声明 `message_source="free_text"` 或保留现有 `action_type="question"` 并额外提供来源。
- 后端只在 `free_text` 时调用 DeepSeek。
- 即使是自由输入，也必须先经过 script-bound intent 分析、RAG 上下文约束、Supervisor 和必要的 repair。
- DeepSeek 失败时可以回退到本地安全回复，但日志必须标记 `fallback_used=true`。
- 自由输入不得释放未发现线索，不得替玩家完成 deduction，不得决定结局。

### 6.3 出示证据

出示证据属于半结构化操作，默认应优先走固定规则：

- 玩家从证据浮层选择线索并点击“出示并追问”时，若没有额外手写文本，走固定证据反应。
- 如果玩家同时出示证据并手写了额外追问，可先匹配固定证据反应；只有固定规则缺失或需要解释自由追问时，才进入 DeepSeek。
- DeepSeek 不能覆盖固定规则已经释放或禁止释放的线索。

### 6.4 接口建议

建议扩展 `/api/dialogue` payload：

```json
{
  "session_id": "string",
  "npc_id": "string",
  "message": "string",
  "action_type": "question | present_clue | suggested_question",
  "message_source": "free_text | suggested_option | evidence_present",
  "presented_clue_ids": []
}
```

兼容策略：

- 未传 `message_source` 的旧请求按 `free_text` 处理，避免破坏现有手写输入。
- 前端推荐按钮必须显式传 `suggested_option`。
- 后端测试应断言 `suggested_option` 不产生 DeepSeek AI call。

## 7. 后端门禁

新增 `ScriptVolumeGate`，或并入 `ScriptSupervisor` 的 blocking 检查。建议独立服务，职责更清晰。

检查项：

- 数量是否达到目标。
- 每个热点是否能释放有效线索。
- 每条关键线索是否有来源场景、阶段、视觉资产。
- 每个 deduction 的 `required_clue_ids`、`correct_clue_ids` 是否存在。
- 每个 chapter_section 的 scene/npc/hotspot/clue 引用是否存在。
- 每个 ending 是否可由 choice、flag、clue 或 risk/trust 条件触发。
- 真相链线索是否参与 clue_graph 或 deduction。
- 生成图片 required count 是否跟随剧本规模，而不是固定 5/4/6。

建议新增 blocking code：

```text
SCRIPT_VOLUME_TOO_SMALL
HOTSPOT_VOLUME_TOO_SMALL
CLUE_VOLUME_TOO_SMALL
DEDUCTION_MISSING
CHAPTER_SECTION_MISSING
ENDING_VARIANTS_MISSING
VOLUME_REFERENCE_BROKEN
```

## 8. 图片规模联动

剧本规模升级后，图片门禁也要升级：

- scene 图数量跟随 locations，至少 8 张。
- npc 图继续覆盖核心 NPC，若扩展新可对话 NPC，则同步新增。
- clue 图不必覆盖 30-45 条全部线索，但必须覆盖关键物证、章节推进物证和结局相关物证。
- hotspot 校准数量至少 24 个，不能仍以 6 个为通过标准。
- generated session 的首屏可只展示当前场景热点，但 catalog 必须含完整章节热点。

视觉资产策略：

- 场景图：主舞台图，必须包含场景内核心 NPC 和关键物件。
- 线索图：物件特写，不要求可读文字。
- 结局图：可选，不阻塞 P0，除非前端已经展示结局图。

## 9. 实施步骤

### P0：先堵住错误输入

1. 增强 `_keywords_from_payload` 后的关键词有效性校验。
2. 新增 `KEYWORDS_ENCODING_INVALID`。
3. 增加乱码关键词单测和真实中文关键词保真测试。
4. 修改 smoke 测试调用方式，保证 UTF-8 输入。

### P0：对话入口分流

1. 前端区分推荐按钮、证据出示和 textarea 自由输入。
2. `/api/dialogue` payload 增加 `message_source` 或等价字段。
3. 后端只允许 `free_text` 进入 DeepSeek 对话链路。
4. `suggested_option` 和纯 `evidence_present` 只走固定 `dialogue_rules` / `script_bound_chat`。
5. AI 日志中默认推荐对话不得记录为 `NPCDialogueAgent`。

### P0：建立规模硬门禁

1. 新增 `ScriptVolumeGate`。
2. 把报告中的数量标准固化为常量。
3. job 在图片生成前运行 volume gate。
4. 不达标时生成缺口报告，不进入视觉生成。

### P0：补齐 ScriptPackage 承载能力

1. 在 `script_models.py` 新增 deductions、chapter_sections。
2. 更新 normalizer，不代写核心内容，只做字段形态归一。
3. 更新 import service，真实导入 deductions/chapter_sections。
4. 更新前端类型，如接口已暴露相关字段。

### P1：改造 DeepSeek 扩写链路

1. 拆分原 `script_package_generation` 为骨架生成和模块扩写。
2. 引入 patch 合并器和 ID 注册表。
3. volume gate 未通过时最多定向修复 3 轮。
4. 所有 AI 轮次继续记录 prompt_path、response_path、fallback_used、success。

### P1：图片 prompt 和门禁升级

1. 文书类线索图禁止生成可读正文。
2. `ImageQualityGate` 加 OCR/视觉理解审查。
3. 图像 required count 跟随剧本规模。
4. 线索图主体不稳定时自动重生。

### P2：质量体验打磨

1. 对生成剧本做人工游玩验收路线。
2. 比较明代固定 Demo 的推理节奏。
3. 调整 prompt 中的误导线、中段反转和结局约束。

## 10. 测试清单

后端单测：

- `??`、`????`、`�`、全符号关键词被拒绝。
- 中文关键词通过并在 job、prompt、script_package 中保真。
- `message_source=suggested_option` 不调用 DeepSeek，不产生 `NPCDialogueAgent` 日志。
- `message_source=free_text` 在真实 AI 开启时可以调用 DeepSeek，并继续受 Supervisor 约束。
- 纯出示证据优先命中固定证据反应；固定规则存在时不调用 DeepSeek。
- 推荐对话释放的线索、trust、risk、flags 必须来自固定规则。
- 少于 8 场景、24 热点、30 线索时 volume gate blocking。
- 缺 deductions、chapter_sections、5 choices、5 endings 时 blocking。
- deduction 引用不存在的 clue 时 blocking。
- chapter_section 引用不存在的 scene/hotspot 时 blocking。
- import 后 catalog 中 deductions/chapter_sections 不为空。
- generated session 可暴露 available_deductions，正确提交 deduction 后写入 flags。

图片测试：

- 文书线索 prompt 不包含“写着某某可读文字”的要求。
- 线索图 OCR 命中文字水印或乱码时 rejected。
- scene required count 从 5 提升到至少 8。
- hotspot calibration approved 少于 24 时阻塞。

端到端测试：

- 使用中文关键词从前端发起生成，落盘关键词不变。
- 点击推荐对话按钮时响应稳定、无 DeepSeek 调用记录。
- textarea 手写追问时才出现真实 AI 调用记录。
- 出示证据按钮在有固定规则时返回固定证据反馈。
- 生成结果达到规模门禁后才进入图片生成。
- 完成后能进入 overview、选择身份、启动 generated session。
- 玩家至少能完成一条调查、一个线索组合、一个 deduction、一个最终选择和一个结局。

## 11. 风险与控制

| 风险 | 控制方式 |
| --- | --- |
| DeepSeek 长 JSON 超 token 或结构漂移 | 分模块 patch 输出，不要求单次整包超长生成 |
| 扩写后 ID 引用混乱 | ID 注册表 + patch 合并器 + 引用门禁 |
| 真相链被后续轮次改写 | 锁定 `story.hidden_truth`、核心 culprit_boundary、truth_chain |
| 推荐按钮回答不稳定或误触发 AI | 前端传 `message_source`，后端固定分流，测试断言无 AI call |
| 固定对话无法覆盖玩家真实追问 | 只有 textarea 自由输入进入 DeepSeek，固定规则缺口通过生成阶段补 dialogue_rules |
| 图片数量变多导致 429 | 保留续跑、节流、失败重试和 visual_blocked 状态 |
| 线索图继续生成乱码字 | prompt 禁止可读文字 + OCR/视觉理解门禁 |
| 体量达标但不好玩 | 增加人工验收路线和 deduction/ending 可达性测试 |

## 12. 结论

可以采用“反复让 DeepSeek 扩充”的思路，但必须把它产品化为受控扩写循环：DeepSeek 负责补内容，后端负责锁定真相、合并 patch、检查规模、验证引用和阻止不合格 job 进入图片生成。

同时，对话框必须明确区分“系统给出的默认对话选项”和“玩家自由输入”。前者走固定剧本规则，后者才走大模型。整改完成后，Stage 15 的生成剧本才具备接近明代固定 Demo 的章节密度和稳定对话体验；否则当前链路只能证明“AI 生成可以闭环”，还不能证明“AI 生成可以替代完整可玩章节”。
