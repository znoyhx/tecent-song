# 阶段完成报告

## 1. 已完成内容

- 保留明代固定 Demo：明代入口仍走现有 `/api/session/start`，不进入 AI 剧本生成。
- 北宋和晚唐入口进入关键词页；晚唐入口兼容 `tang`，提交到后端时统一为 `late_tang`。
- 新增脚本生成 job API、job 状态 API、剧本读取/校验/视觉续跑 API，以及 `/api/session/start-generated`。
- DeepSeek 真实执行 5 轮：pitch、结构化剧本初稿、编剧审稿、逻辑 QA、修复合并。
- 增强 prompt 与 schema 约束，并新增后端 `ScriptPackageNormalizer`，将模型常见的自由结构归一化为严格 `ScriptPackage` 后再进入 Pydantic 校验、监管、图片门禁和导入流程。
- 新增 `ScriptSupervisor`、`ImageQualityGate`、`HotspotCalibrationService`、`ScriptImportService`。
- 生成图片保存到本地 generated 目录，并要求场景图、人物图、线索图全部 approved 后才允许进入正式生成剧本 session。
- Phaser 热点优先读取 generated `anchor_point` / `bbox`，缺失时仅对旧明代数据回退。
- 真实上游端到端已跑通：`job_5b69c108121a` 生成 `script_id=p0_001_08121a`，标题《雨夜驿变》，完成图片门禁、热点校准、导入、创建 generated session，并点击 generated hotspot 释放线索。

## 2. 修改文件列表

- `backend/app/main.py`
- `backend/app/models/game_models.py`
- `backend/app/models/script_models.py`
- `backend/app/routers/scripts.py`
- `backend/app/services/ai_client.py`
- `backend/app/services/game_engine.py`
- `backend/app/services/hotspot_calibration_service.py`
- `backend/app/services/image_generation_service.py`
- `backend/app/services/image_quality_gate.py`
- `backend/app/services/quote_pool.py`
- `backend/app/services/script_generation_service.py`
- `backend/app/services/script_import_service.py`
- `backend/app/services/script_job_store.py`
- `backend/app/services/script_normalizer.py`
- `backend/app/services/script_supervisor.py`
- `backend/app/services/visual_prompt_agent.py`
- `backend/tests/script_generation_fixtures.py`
- `backend/tests/test_generated_session.py`
- `backend/tests/test_image_quality_gate.py`
- `backend/tests/test_script_generation_api.py`
- `backend/tests/test_script_generation_models.py`
- `backend/tests/test_script_normalizer.py`
- `backend/tests/test_script_supervisor.py`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/components/script-generation/ScriptGenerationFlow.tsx`
- `frontend/src/game/scenes/MainScene.ts`
- `frontend/src/pages/StartPage.tsx`
- `frontend/src/styles/global.css`
- `frontend/src/types/game.ts`
- `docs/periodPrompt/reports/stage_15_ai_script_generation_report.md`

## 3. 入口兼容说明

- 明代：选择“明代”后直接启动固定书坊焚稿案 Demo，调用既有 session 启动路径。
- 北宋：选择“北宋”后进入关键词填写页，关键词校验通过后调用 `/api/scripts/generate`。
- 晚唐：选择“晚唐”后进入关键词填写页，前端兼容旧 `tang`，后端生成统一使用 `late_tang`。

## 4. 后端生成流程

`POST /api/scripts/generate` 创建可恢复 job，状态持久化到 `backend/data/generated_scripts/jobs/`，生成剧本持久化到 `backend/data/generated_scripts/scripts/{script_id}/`。

DeepSeek 生成链路依次执行 `pitch_generation`、`script_package_generation`、`script_doctor_review`、`logic_qa_review`、`refinement_repair`。每轮记录 module、provider、model、input_summary、latency、success、supervisor_pass、fallback_used、prompt_path、response_path；失败时 job 明确 failed 或 visual_blocked，不用 Mock 冒充完成。

模型输出先经过 JSON 解析和 `ScriptPackageNormalizer` 归一化，再进入严格 `ScriptPackage` schema 校验。监管器检查朝代冲突、现代词、线索链、阶段可达、结局可达、NPC 信息边界、早期剧透、玩家身份权限、视觉字段、热点字段和图片门禁字段。blocking issue 不会导入游戏。

图片全部通过后，`HotspotCalibrationService` 基于 approved 资产写入 0-1 归一化 `anchor_point` / `bbox`，`ScriptImportService` 将生成剧本转换为现有游戏引擎可读 catalog，generated session 使用 `script_id + identity_id` 启动。

## 5. 前端生成流程

前端入口分为固定 Demo 和生成剧本两条路径。明代不显示生成表单；北宋/晚唐显示关键词页，关键词必须为 1-8 个，空值和空泛输入显示中文错误。

进度页只读取 `GET /api/scripts/jobs/{job_id}` 的 `steps`、`progress`、`current_step`、`visual_quality` 和 `transitional_quote`。前端允许轮询后端状态，但不自增进度；名句只作为等待内容展示，不推动流程。

只有 `status=completed && ready_for_overview=true` 且存在 `script_id` 时才进入概览页。概览来自 `script_overview`，身份卡来自 `playable_identities`，不会展示最终真相、隐藏线索或结局条件。选定身份后调用 `/api/session/start-generated`。

## 6. 图片生成与质量门禁结果

真实跑通 job：`job_5b69c108121a`，生成剧本：`p0_001_08121a`。

| 类型 | 必需 | approved | rejected | regenerated | blocked |
| --- | ---: | ---: | ---: | ---: | ---: |
| 场景图 | 5 | 5 | 0 | 0 | 0 |
| 人物图 | 4 | 4 | 0 | 0 | 0 |
| 线索图 | 6 | 6 | 0 | 0 | 0 |

说明：早期图片 provider 出现过 429 和部分资产未通过状态；已通过续跑接口、同 script 文件重校验、重试节流和 stale issue 清理恢复到全部 approved。没有把占位图、空白图、fallback 图或旧缓存图标记为完成。

## 7. 热点定位结果

`p0_001_08121a` 已完成至少 6 个核心热点校准，均包含 `anchor_point`、`bbox`、`calibration_status=approved`，并已映射到 Phaser 热点。真实验证中 generated session 首场景 `loc_qing_shiyi` 出现 `hotspot_0`，点击后释放线索 `clue_001`。

## 8. 自测结果

- `python -m pytest backend -q`：128 passed，耗时 186.95 秒。
- `cd frontend; npm run build`：通过；Vite 仅提示 chunk 体积警告。
- `POST /api/scripts/generate` 拒绝 `dynasty_id=ming`：测试覆盖。
- 空关键词中文报错：测试覆盖。
- 线索断链、早期剧透、不可达结局、缺视觉字段阻塞：测试覆盖。
- 图片门禁拒绝 fallback、空文件、旧缓存、缺物件、错朝代元数据：测试覆盖。
- generated session 创建、首场景和 hotspot 调查：测试覆盖，并完成真实接口验证。

## 9. 中文化检查结果

新增用户可见文案为中文。按指定英文词清单扫描后，命中主要为 TypeScript 类型名、函数名、接口字段、历史报告、未挂载旧页或第三方内部方法，不属于当前新增用户可见英文文案。

## 10. AI 接入测试结果

真实 DeepSeek 调用成功。`job_5b69c108121a` 的 5 个 DeepSeek 调用均为 `success=true`、`fallback_used=false`：

- `DeepSeekScriptPitch`
- `DeepSeekScriptPackage`
- `DeepSeekScriptDoctor`
- `DeepSeekLogicQA`
- `DeepSeekScriptRepair`

中间曾遇到过上游超时、传输错误和模型结构不合规问题；已通过动态超时、重试、prompt/schema 加强和后端归一化修复。仍需注意 DeepSeek 上游偶发传输失败会使 job 明确 failed，不会伪造成功。

## 11. 图片生成测试结果

真实图片 provider 调用成功，15 张必需图片已下载保存到 `assets/generated/visuals/generated/p0_001_08121a/`，最终全部通过 `ImageQualityGate`。

中间曾遇到 provider 429，job 会停在 `visual_blocked` 或继续重试；现已增加续跑接口、节流和同 script 资产重校验。无法从像素层面证明语义完全正确的风险，仍建议强模型审查抽检图片内容与朝代风格。

## 12. 人工验收方法

1. `cd backend`
2. `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
3. `cd frontend`
4. `npm run dev -- --host 127.0.0.1 --port 5173`
5. 打开 `http://127.0.0.1:5173/`
6. 选择“明代”，确认直接进入固定 Demo。
7. 返回入口，选择“北宋”或“晚唐”，确认进入关键词页。
8. 输入 `驿站、军报、雨夜、粮草`，开始生成。
9. 观察流程图只随后端 job steps 推进。
10. 完成后进入概览页，选择生成身份并进入游戏。
11. 点击首场景热点，确认释放线索或调查反馈。

## 13. 未完成事项

- 需要继续做视觉语义强审查：当前门禁能阻塞占位、空文件、fallback、旧缓存和元数据不合规资产，但不能替代独立视觉理解模型。
- 旧的未挂载 `ScenarioGenerationPage` 和 `mock/entryFlow` 仍在代码库中，但当前入口已不再使用它们作为北宋/晚唐生成路径。
- 本次真实完成的 job 由早期 visual_blocked job 续跑而来，期间手动补正过该旧 job 的 `script_id` 元数据；代码已补上 visual_blocked 时持久化 `script_id`，后续新 job 不需要此手动步骤。

## 14. 阻塞问题

当前没有阻塞完整闭环的问题。剩余风险是上游 DeepSeek/图片 provider 偶发超时、传输错误或 429，这些会真实反映为 failed/visual_blocked，不会被标记为 completed。

## 15. 是否建议进入下一阶段

谨慎建议进入下一阶段。建议先做一次强模型审查和人工抽检，确认图片语义、热点坐标和生成剧本内容质量都符合验收标准。

## 16. 是否需要强模型审查

需要。建议重点检查：

- 明代是否仍为固定 Demo。
- 北宋/晚唐是否必须经过关键词生成。
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



CODEBUDDY.md



​stage_15_ai_script_generation_report.md



​   当前问题, 剧本生成完后场景没有人物， 违反了我说的原则人物和场景一起生成， 然后就是当前UI很丑，