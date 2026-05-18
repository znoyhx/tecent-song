# 阶段 11 修复报告

## 1. 已修复问题

- 收紧隐藏结局门槛：`ending_hidden` 不再只靠最终选择、封口链路和 NPC 信任触发，必须同时完成护证动机、焚毁目标、隐藏抄录等证据要求。
- 收紧最终抉择门槛：只发现锦衣卫封口令不会进入 `choice`，必须先确认“烧毁的不是普通诗稿”和“封口令背后另有链路”。
- 改造思维疑团玩法：`deductions` 不再自动完成，玩家必须主动选择证据并提交推理。
- 增加统一线索释放校验：所有线索入库统一经过 `unlock_conditions` 判断，避免对话或调查绕过前置条件。
- 修复前端用户可见英文残留：将英文后端服务名等提示改为中文表达。
- 完成密钥卫生修复：默认不读取公开文档目录中的本地密钥文件，新增忽略规则，报告不输出任何密钥内容。

## 2. 修改文件列表

- `.gitignore`
- `backend/app/core/config.py`
- `backend/app/models/game_models.py`
- `backend/app/routers/game.py`
- `backend/app/services/game_engine.py`
- `backend/app/services/image_generation_service.py`
- `backend/data/clues/ming_bookshop_clues.json`
- `backend/data/endings/ming_bookshop_endings.json`
- `backend/data/events/ming_bookshop_fire.json`
- `backend/tests/test_api.py`
- `backend/tests/test_chapter_script_volume.py`
- `backend/tests/test_deduction_and_unlock_rules.py`
- `backend/tests/test_demo_acceptance.py`
- `backend/tests/test_endings_paths.py`
- `backend/tests/test_logic.py`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/components/clue/ClueSidebar.tsx`
- `frontend/src/pages/GamePage.tsx`
- `frontend/src/pages/ScenarioGenerationPage.tsx`
- `frontend/src/types/game.ts`
- `docs/periodPrompt/reports/stage_11_story_volume_expansion_report.md`

## 3. 关键规则变化

- choice 阶段进入条件：`reversal -> choice` 现在必须同时满足焚毁目标成立与封口链路成立。焚毁目标可由 `combo_burned_text_is_ledger` 或 `deduced_burned_not_poem` 证明；封口链路可由 `combo_hidden_chain` 或 `deduced_hidden_chain` 证明。单独发现 `clue_jinyiwei_gag_order` 只推动调查，不再开放最终抉择。
- hidden ending 判定条件：隐藏结局必须满足 `preserved_evidence`、`choice_reverse_trace`、`found_hidden_chain`，并满足 `ledger_truth_exposed` 或 `deduced_burned_not_poem`；同时要求 `deduced_scholar_motive`、已发现 `clue_poem_hidden_copy`、顾闻信任 `>= 2`、陆峥信任 `>= 2`、风险 `<= 6`。
- deduction 主动提交逻辑：新增 `POST /api/deduction/submit`，请求包含 `session_id`、`deduction_id`、`selected_clue_ids`。错误提交返回中文 `wrong_feedback`，不应用 effects；正确提交才写入 `completed_deduction_ids` 并应用 flags、score、risk 等效果。`GET /api/session/{session_id}` 只向前端暴露未完成疑团的 `deduction_id` 和 `question`，不泄露正确证据 ID。
- unlock_conditions 中央校验逻辑：新增统一释放判断，支持 `required_clue_ids`、`required_flags`、`min_trust`、`max_risk`、`min_risk`。调查热点条件仍保留为场景提示，真正线索入库以中央校验为准。

## 4. 自测结果

- `python -m pytest backend/tests/test_chapter_script_volume.py -q --basetemp=.pytest_tmp_stage11_repair`：通过，4 passed。
- `python -m pytest backend/tests/test_api.py backend/tests/test_demo_acceptance.py backend/tests/test_endings_paths.py backend/tests/test_logic.py backend/tests/test_ai_fallback.py backend/tests/test_visual_fallback.py backend/tests/test_deduction_and_unlock_rules.py -q --basetemp=.pytest_tmp_stage11_repair_core`：通过，21 passed。
- `python -m pytest backend/tests/test_deduction_and_unlock_rules.py backend/tests/test_chapter_script_volume.py -q --basetemp=.pytest_tmp_stage11_repair_scope`：通过，9 passed。
- `python -m pytest backend/tests/test_api.py backend/tests/test_demo_acceptance.py backend/tests/test_endings_paths.py backend/tests/test_logic.py backend/tests/test_ai_fallback.py backend/tests/test_visual_fallback.py backend/tests/test_deduction_and_unlock_rules.py -q --basetemp=.pytest_tmp_stage11_repair_core_final`：通过，21 passed。
- `npm run build`：通过。直接在小写盘符映射工作目录运行时触发过 Vite/Rollup 的 Windows 盘符大小写路径问题；切换到规范路径 `D:\SomeFunnyProjFromGithub\HistoryGame\frontend` 后构建通过。
- Pytest 运行时仍提示无法写入 `.pytest_cache` 的 Windows 权限警告，不影响测试结果。

## 5. 中文化检查结果

- 已将前端用户可见的英文后端服务名提示改为“后端服务”。
- 已重点检查 `frontend/src/App.tsx`、`frontend/src/api/client.ts`、`frontend/src/pages/ScenarioGenerationPage.tsx`。
- 搜索 `Start`、`Loading`、`Error`、`Submit`、`Continue`、`Inventory`、`Clue`、`Session`、`Choice`、`Ending`、`Back`、`Next`、`backend` 后，剩余命中为代码标识、类型名、接口字段、文件路径或报告中的技术路径，不属于用户可见英文文案。

## 6. 密钥检查结果

- 发现本地密钥文件路径：`docs/DeepseekAPIKey`，未读取内容。
- 发现本地密钥文件路径：`docs/ImageGenerateKey`，未读取内容。
- 已新增忽略规则：`docs/DeepseekAPIKey`、`docs/ImageGenerateKey`、`backend/.env`、`.env`、`backend/logs/`。
- 运行时密钥读取已改为优先环境变量或 `backend/.env`；公开 `docs/*Key` 路径只在显式启用本机 fallback 开关时读取，默认不依赖。
- 搜索密钥形态时排除了两个本地密钥文件内容；未发现代码、Markdown、JSON、前端、日志或测试输出中包含完整 API Key。

## 7. Mock / AI fallback / 视觉 fallback 回归结果

- Mock Demo 相关路径已随核心测试回归，`test_demo_acceptance.py` 通过。
- AI fallback 已回归，`test_ai_fallback.py` 通过。
- 视觉 fallback 已回归，`test_visual_fallback.py` 通过。
- 新增主动推理与解锁条件测试已纳入核心回归，`test_deduction_and_unlock_rules.py` 通过。

## 8. 人工验收路线

- 普通真相路线：完成火因调查、账册焚毁目标链、封口链路链；在推理面板正确提交“烧毁的不是普通诗稿”和“封口链路”相关疑团；最终选择公开真相，应进入普通真相结局。
- 秩序路线：完成进入 `choice` 所需两条核心链路；保持对陆峥的较高信任；最终选择交由官府或维持秩序，应进入秩序结局。
- 自保路线：完成最低限度的焚毁目标与封口链路确认；最终选择自保或抽身，且未满足隐藏结局硬条件，应进入自保结局。
- 悲剧路线：调查中不断提高风险，或最终强推伙计承担罪责；进入最终抉择后选择高风险压迫路线，应进入悲剧结局。
- 隐藏路线：保存证据，选择反查；完成封口链路、焚毁目标、顾闻护证动机推理；发现 `clue_poem_hidden_copy`；顾闻和陆峥信任均达到 `>= 2`，风险保持 `<= 6`，应进入隐藏结局。
- 隐藏失败路线：选择反查但缺少 `clue_poem_hidden_copy`，或未完成焚毁目标证据链，或缺少 `deduced_scholar_motive`；应不能进入隐藏结局，并落入对应普通结局分支。

## 9. 阶段 11 UI 体验追加修复

- 默认隐藏调试面板：`DemoEvidencePanel` 改为受 `debugEnabled` 控制；普通入口不显示。开发者可通过 URL `?debug=1` 或 `localStorage.historyGameDebug = "1"` 开启，开发模式另有小型“调试”按钮切换，不删除原有安全摘要能力。
- 出示线索修复：前端继续传递 `presented_clue_ids`，并在出示后显示“已出示”、NPC 信任、分数、风险、状态更新、案卷新增等反馈摘要；后端补强了许掌柜火因/账册、阿沈后门、顾闻护证、陆峥封口链路的出示规则。
- 出示栏压缩方案：底部不再平铺全部“出示：xxx”按钮，改为“出示证据”浮层、最多 5 条最近线索快捷 chip、已选证据标签、搜索框与类型筛选；发送按钮在选中证据后显示“出示并追问”。
- 字体调整说明：`global.css` 新增 `--font-body`、`--font-ui`、`--font-story`、`--font-small`，正文默认 16px，剧情文本约 18px，按钮、chip、HUD、案卷与调试文本不低于 15px；移动端同步调整证据浮层和对话区布局。
- 背景图补齐清单：9 个明代书坊案地点均有独立视觉 asset 映射、`/api/visual/assets/{asset_id}` 加载路径和本地 PNG：书坊前厅、书坊后院火场、账房暗格、灯油架旁、刻版间、后门雨泥处、雨巷、城门搜检口、临时问话处。若图片生成服务不可用，中文 fallback 路由仍保留。
- 图片生成密钥卫生说明：未读取、打印或复制 `docs/DeepseekAPIKey`、`docs/ImageGenerateKey`。后端已切断公开文档目录 Key 兜底读取，DeepSeek 与硅基流动图片 Key 均只从运行环境变量或 `backend/.env` 读取；报告、测试和 manifest 不输出 Authorization、Bearer token 或完整密钥。
- 自测结果：`python -m pytest backend/tests/test_api.py backend/tests/test_visual_asset_status.py backend/tests/test_image_generation_service.py -q --basetemp=.pytest_tmp_stage11_ui_repair_assets` 通过，14 passed；指定核心回归 `python -m pytest backend/tests/test_api.py backend/tests/test_demo_acceptance.py backend/tests/test_endings_paths.py backend/tests/test_logic.py backend/tests/test_ai_fallback.py backend/tests/test_visual_fallback.py backend/tests/test_deduction_and_unlock_rules.py -q --basetemp=.pytest_tmp_stage11_ui_repair` 通过，23 passed；`npm run build` 通过。Pytest 仍有 `.pytest_cache` Windows 权限警告，不影响测试结果。
- 是否建议继续复审：建议继续做一次真实浏览器人工复审，重点检查证据浮层在不同屏宽下的遮挡、字号放大后的阅读节奏，以及 9 张场景背景在桌面和窄屏下的裁切、亮度与文字可读性。

## 10. 是否建议进入下一阶段

建议进入下一阶段。阶段 11 的可玩性、安全和回归验收项已经修复并通过自动化测试；后续可以继续做更细的剧情体验打磨，但不再阻塞阶段推进。

## 11. 是否仍需强模型复审

建议做一次轻量复审，重点看新主动推理 UI 的体验、六条人工路线的实际游玩手感，以及隐藏结局门槛是否既足够严格又不会过度卡玩家。

## 12. 阶段 11 UI 体验追加修复复核（2026-05-17）

- 调试面板：普通入口继续默认隐藏 `DemoEvidencePanel`，仅 `?debug=1`、`localStorage.historyGameDebug = "1"` 或开发模式小按钮可开启。
- 出示线索：证据选择器与右侧案卷新增持久“已出示”标记；顾闻收到 `clue_scholar_outer_wrapper` 后会释放护证反馈并写入 `scholar_motive_visible`，但不直接写入 `deduced_scholar_motive`，避免绕过主动推理。
- 出示栏压缩：底部仍采用“出示证据”浮层、最近 5 条快捷 chip、搜索与类型筛选、已选证据标签和“出示并追问”按钮，不回退到平铺按钮。
- 字体调整：保留全局 `--font-body: 16px`、`--font-story: 18px`、`--font-ui/--font-small: 15px`，并为新增“已出示”标签沿用不低于 15px 的 UI 字号。
- 背景图补齐：9 个明代书坊案地点均已生成可加载 PNG：`scene_bookshop_front_hall.png`、`scene_bookshop_backyard_fire.png`、`scene_account_room.png`、`scene_lamp_shelf.png`、`scene_burned_printing_room.png`、`scene_back_gate.png`、`scene_rain_alley.png`、`scene_city_gate.png`、`scene_jinyiwei_interrogation.png`。
- 图片生成密钥卫生：后端配置链路已支持运行环境变量、`backend/.env` 和项目根 `.env`；`docs/DeepseekAPIKey` 与 `docs/ImageGenerateKey` 仅确认路径存在，未读取内容。本次生成只输出资产状态和本地路径，没有输出 Authorization、Bearer token、临时图片 URL 或完整密钥。
- 图片生成兼容：硅基流动返回的图片下载体可能是 `application/octet-stream`，后端已改为用 PNG/JPEG/WebP 文件头二次确认，避免把有效 PNG 误判为 `invalid_image_content`。
- 自测结果：`python -m pytest backend/tests/test_api.py backend/tests/test_visual_asset_status.py backend/tests/test_image_generation_service.py -q --basetemp=.pytest_tmp_stage11_ui_repair_assets` 通过，14 passed；必跑后端 `python -m pytest backend/tests/test_api.py backend/tests/test_demo_acceptance.py backend/tests/test_endings_paths.py backend/tests/test_logic.py backend/tests/test_ai_fallback.py backend/tests/test_visual_fallback.py backend/tests/test_deduction_and_unlock_rules.py -q --basetemp=.pytest_tmp_stage11_ui_repair` 通过，23 passed；`npm run build` 通过。Pytest 仍有 `.pytest_cache` Windows 权限警告，不影响结果。
- 是否建议继续复审：建议做一次真实浏览器复审，重点看 9 张场景背景在桌面和窄屏下的裁切、亮度与文字可读性。
