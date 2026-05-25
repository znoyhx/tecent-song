# Stage 15 北宋生成强审查报告

生成时间：2026-05-23  
生成 job：`job_b049ae46effe`  
生成剧本：`p0_song_001_46effe`  
标题：`汴京书影`  
资产目录：`assets/generated/visuals/generated/p0_song_001_46effe/`  
图片检查拼图：`docs/periodPrompt/reports/p0_song_001_46effe_asset_contact_sheet.jpg`

## 1. 总结论

本次北宋生成链路真实跑通：DeepSeek 5 轮调用全部成功，`fallback_used=false`；图片生成服务也真实产出 15 张 PNG，并通过现有 `ImageQualityGate`；生成剧本可以通过 `/api/session/start-generated` 进入游戏，首场景热点可调查并释放线索。

但如果按“必须达到明代 Demo 水准”验收，本次剧本不通过。核心原因是剧本规模只有 Stage 15 最低规格，而不是明代 Demo 的完整章节体量：场景、热点、线索、对话、选择和结局数量均明显不足。视觉资产没有发现空白图、SVG 占位图、fallback 图或旧缓存冒充 approved，但线索图存在 AI 乱码文字和物件特写不够稳定的问题，现有门禁还不能替代视觉理解审查。

## 2. API 请求与 job 结果

本次通过后端 API 发起：

- `POST /api/scripts/generate`
- 目标朝代：`song`
- 原计划关键词：`汴河、贡茶、夜市、失踪账册`

注意：实际落盘关键词变成了 `["??", "??", "??", "????"]`。这次是从 PowerShell here-string 发起请求时触发的中文编码问题，但后端没有识别 `??` 这类无效关键词并拒绝生成，这是需要修复的输入校验缺口。

job 最终结果：

- `status=completed`
- `progress=100`
- `ready_for_overview=true`
- `script_id=p0_song_001_46effe`
- `blocking_issues=[]`
- DeepSeek 调用：5/5 成功，0 次 fallback

## 3. 剧本规模对比

| 指标 | 北宋生成 `p0_song_001_46effe` | 明代 Demo `书坊焚稿案` | 是否达到明代 Demo 水准 |
| --- | ---: | ---: | --- |
| 阶段数 | 5 | 5 | 是 |
| 场景/地点 | 5 | 9 | 否 |
| 热点 | 6 | 30 | 否 |
| NPC | 4 | 4 | 是 |
| 线索 | 6 | 35 | 否 |
| 对话规则 | 2 | 36 | 否 |
| 线索组合/推理 | 3 个 clue_graph | 明代 8 combos + 8 deductions | 否 |
| 章节段落 | 无等价字段 | 15 | 否 |
| 选择 | 2 | 5 | 否 |
| 结局 | 2 | 5 | 否 |
| 剧本文本量 | 约 13,892 字符 | 约 34,071 字符 | 否 |

判断：当前生成 prompt/schema 的最低约束是 `5 场景 / 4 NPC / 6 线索 / 6 热点`，这只能满足 Stage 15 基础闭环，不足以复刻明代 Demo 的玩法密度。若下一阶段要求生成剧本“直接可替代明代 Demo”，需要把 hard requirements 提升到接近 Stage 11 体量。

## 4. 图片与占位图检查

job 视觉质量摘要：

| 类型 | required | approved | rejected | regenerated | blocked |
| --- | ---: | ---: | ---: | ---: | ---: |
| 场景图 | 5 | 5 | 0 | 0 | 0 |
| 人物图 | 4 | 4 | 0 | 0 | 0 |
| 线索图 | 6 | 6 | 4 | 4 | 0 |

文件层检查：

- 15 张必需图片均存在。
- 均为 PNG 光栅图，尺寸均为 `1024x1024`。
- 文件大小约 `1.58MB - 2.12MB`，不是空文件或极小占位文件。
- `quality_gate.status` 均为 `approved`。
- `approved_path` 均指向本次 script 目录，不是旧明代素材或 fallback 路径。
- 未发现 SVG、空白图、fallback 图、旧缓存图冒充 approved。

肉眼抽检：

- 场景图：基本能看到人物与场景一体生成，太学、国子监、樊楼、周府、御史台都有角色在场。
- 人物图：4 张人物图均为可用肖像，未见空白或占位。
- 线索图：6 张线索图都已生成，但 `asset_clue_05` 等文书类图片出现不可读 AI 乱码字；部分线索图更像“带纸张的街景/场景图”，物件特写标准不稳定。

结论：图片数量和文件门禁通过；“无占位图”基本成立；但线索图语义质量没有达到强审查标准。

## 5. 热点与 session 检查

热点校准：

- `hotspot_positioning` 数量：6
- `calibration_status=approved` 数量：6
- 均包含 `anchor_point` 和 `bbox`

生成 session 验证：

- `POST /api/session/start-generated` 成功。
- 使用身份：`identity_01`
- 会话：`s_2e2b4b55`
- 首场景：`location_taixue`
- 当前阶段：`intro`
- 首个热点 `hotspot_0` 调查成功。
- 释放线索：`clue_01`

后端监管：

- `POST /api/scripts/p0_song_001_46effe/validate` 返回 `passed=true`。

## 6. 问题清单

### P0：剧本规模未达到明代 Demo 水准

当前生成只达到 Stage 15 最低闭环，远低于明代 Demo 的调查密度。尤其是热点 `6 vs 30`、线索 `6 vs 35`、对话规则 `2 vs 36`、结局 `2 vs 5`，会导致生成剧本进入游戏后体验明显短、薄、缺少多路径推理。

建议：把生成硬约束提升到至少 `8-10 场景 / 24-36 热点 / 30-45 线索 / 6-10 clue combos / 8-12 deductions / 12-18 chapter_sections / 5 choices / 5 endings`，并让 supervisor 阻塞不足体量的结果。

### P0：中文关键词可被编码破坏后继续生成

本次请求原本传入中文关键词，但落盘为 `??`。即使这是调用端编码问题，后端也不应接受明显无效的 `?` 关键词继续生成。

建议：关键词校验增加中文/有效字符比例检查，拒绝全符号、全问号、乱码替换字符或不可见字符；自动化 smoke 请求改为 UTF-8 安全的 JSON 文件或客户端请求方式。

### P1：线索图语义门禁不足

文件门禁能挡住空图、SVG、fallback 和旧路径，但不能识别文书图上的乱码字、线索主体偏弱或“街景大于物件”的问题。本次 `asset_clue_05` 纸条文字明显不可读。

建议：线索图 prompt 强制“不生成可读文字，使用封印、折痕、血迹、缺口等视觉符号表达”；或接入视觉理解/OCR 审查，发现乱码字、水印、文字主体错误时要求重生。

### P1：场景图数量虽达 Stage 15 标准，但不达明代视觉覆盖规模

当前 5 张场景图只覆盖最低生成要求；明代 Demo 有 9 个可探索场景。即便每张图文件质量可用，整体探索空间仍不足。

建议：图像数量约束跟随剧本规模升级，场景图至少提升到 8-10 张，并确保每个主要章节/场景都有对应图片和热点。

### P2：生成 schema 缺少明代 Demo 的章节/推理等价结构

生成剧本目前有 `clue_graph`，但没有明代 Demo 中 `chapter_sections` 和 `deductions` 的等价输出，导致“章节推进”和“思维疑团”类玩法密度无法对齐。

建议：扩展 `ScriptPackage` 或 import 层，将生成剧本显式输出章节段、组合推理和选择前 deduction。

## 7. 后续验收门槛建议

下一次生成验收不应只看 job completed，而应同时满足：

- 剧本体量达到明代 Demo 指标下限。
- `keywords` 保持真实中文，不接受乱码替换。
- 15+ 张图不是终点，图像数量应随场景/线索体量增长。
- 所有线索图通过文件门禁后，还要通过视觉语义或人工抽检。
- 生成 session 至少跑通多场景、多热点、多 NPC 对话、组合推理、choice 和 ending，而不只检查首个热点。

