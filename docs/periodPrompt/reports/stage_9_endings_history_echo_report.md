# 阶段 9 完成报告：多结局规则固化、历史回声生成与结局页可验收闭环

## 1. 已完成内容

- 梳理并复用当前真实结局链路：结局规则仍落在 `backend/app/services/game_engine.py`，接口仍为 `POST /api/ending/resolve`，未新增重复结局接口。
- 确认并保留明代书坊焚稿案 5 个结局：自保、秩序、真相、悲剧、隐藏。
- 保持 `ending_id` 完全由后端规则和状态决定，历史回声生成器只返回 `history_echo` 文本，不参与结局 ID 判定。
- 增强 `HistoryEchoGenerator`：真实模型返回文本必须为中文，并且至少引用最终选择、关键线索、人物命运或事件结构中的 2 类上下文；否则自动使用本地中文模板 fallback。
- 增强历史回声 Prompt，明确要求引用最终选择、关键线索或 NPC 命运信息，至少覆盖两类上下文。
- 增强前端结局页兜底展示：标题、摘要、正文、历史回声、NPC 命运在字段缺失或图片缺失时仍显示中文 fallback。
- 新增结局 API 专项测试，覆盖完整字段、规则锁定 `ending_id`、图片 fallback 不阻塞、密钥样式扫描。
- 补充历史回声测试，覆盖“模型返回泛泛中文但缺少上下文引用时必须 fallback”。

文档与代码差异说明：`CODEBUDDY.md` 仍保留“仓库偏文档优先”的旧描述，但当前真实仓库已有前后端、测试、视觉接口和结局链路；本阶段以真实代码结构为准。

## 2. 修改文件列表

- `backend/app/services/history_echo_generator.py`
- `backend/data/prompts/history_echo.md`
- `backend/tests/test_history_echo_generation.py`
- `backend/tests/test_ending_api.py`
- `frontend/src/components/ending/EndingPanel.tsx`
- `docs/periodPrompt/reports/stage_9_endings_history_echo_report.md`

## 3. 当前结局链路

- 结局判定接口：`POST /api/ending/resolve`
- 结局规则真实落点：`backend/app/services/game_engine.py` 的 `GameEngine._pick_ending()`
- 结局数据来源：`backend/data/endings/ming_bookshop_endings.json`
- 历史回声来源：优先 `HistoryEchoGenerator` 调用真实 DeepSeek；失败、Mock、无 Key 或返回内容不合格时使用 `backend/data/mock/history_echoes.json` 与结局数据拼接成本地中文 fallback。
- 前端结局展示位置：`frontend/src/components/ending/EndingPanel.tsx`
- fallback 机制：历史回声失败不影响接口返回；图片缺失时 `image_generation_service.attach_visual()` 提供视觉 fallback URL，前端继续展示中文结局内容。

## 4. 明代 Demo 结局清单

| ending_id | 中文标题 | 类型 | 触发条件摘要 | 是否可复现测试 |
| --- | --- | --- | --- | --- |
| `ending_survival` | 焚稿自保 | 自保结局 | `survival >= 4` 或最终选择 `choice_destroy_evidence` | 是 |
| `ending_order` | 误信告发 | 秩序结局 | `order >= 4` 或最终选择 `choice_give_to_lu` | 是 |
| `ending_truth` | 暗藏残页 | 真相结局 | `truth >= 5`、存在 `preserved_evidence`，且最终选择护送证据相关选项 | 是 |
| `ending_tragedy` | 身陷诏狱 | 悲剧结局 | `risk_level >= 6` 且关键人物信任不足 | 是 |
| `ending_hidden` | 引火反查 | 隐藏结局 | `found_hidden_chain`、`preserved_evidence`、陆峥与顾问信任达标、风险未过高、最终选择反查上游 | 是 |

## 5. 结局规则判定结果

- 是否由规则决定结局：是。`ending_id` 只由 `GameEngine._pick_ending()` 返回。
- 是否依赖 flags / scores / risk / trust / final choice：是。
  - flags：`found_hidden_chain`、`preserved_evidence` 等。
  - scores：`truth`、`order`、`survival`。
  - risk：悲剧与隐藏结局均读取 `risk_level`。
  - trust：悲剧、隐藏结局读取 `npc_jinyiwei`、`npc_scholar` 信任。
  - final choice：5 条结局路径均读取最终选择或受最终选择影响。
  - discovered clues：通过线索效果、组合 flags、分数与测试路径参与结局判定。
- 是否避免 AI 决定 ending_id：是。历史回声生成器 prompt 禁止输出或暗示新的 `ending_id`；后端只读取 `history_echo` 字段，即使模型返回额外 ID 字段也会忽略。

## 6. 历史回声接入结果

- 是否中文：是，后端校验含中文且过滤长英文片段。
- 是否真实调用 AI：是。本阶段执行真实 DeepSeek 历史回声 smoke，结果 `ai_success=True`、`fallback_used=False`。
- 无 Key 时行为：测试会 skip；运行时 `AIClient` 返回失败结果，`HistoryEchoGenerator` 使用中文 fallback。
- AI 失败时行为：使用中文 fallback，不影响 `/api/ending/resolve` 返回。
- 是否至少引用 2 类上下文信息：是。新增后端校验要求模型文本至少命中最终选择、关键线索、人物命运或事件结构中的 2 类；本地 fallback 固定引用最终选择、至少 2 条线索和至少 2 名人物命运。

## 7. 前端结局页结果

- 结局标题：显示后端标题，缺失时显示“结局已定”。
- 结局摘要：显示后端摘要，缺失时显示中文 fallback。
- 结局正文：显示 `ending_text`，缺失时显示中文 fallback。
- 历史回声：显示后端历史回声，缺失时显示中文 fallback。
- NPC 命运：显示“众人去向”列表，缺失时显示“众人去向已随结局落定。”
- 图片缺失 fallback：继续使用后端视觉资产 fallback，不阻断结局内容展示。
- 用户可见中文检查：结局页新增/修改可见文案均为中文，已将旧的英文缩写提示改为“真实智能模型润色”。


## 8. 自测结果

- 结局路径测试：`cd backend; python -m pytest tests/test_endings_paths.py tests/test_history_echo_generation.py tests/test_ending_api.py -q --basetemp ../.pytest_tmp_endings`，结果 `11 passed`。
- 后端完整测试：`cd backend; python -m pytest tests -q --basetemp ../.pytest_tmp`，结果 `64 passed, 3 skipped`。
- 真实 AI 历史回声 smoke：`cd backend; $env:USE_MOCK_AI="false"; $env:AI_PROVIDER="deepseek"; python -m pytest tests/test_history_echo_real_smoke.py -q --basetemp ../.pytest_tmp_history_echo_real`，结果 `1 passed`。
- 前端构建：`cd frontend; npm run build`，结果通过。
- Key 泄露扫描：扫描 `backend/logs` 与 `docs/periodPrompt/reports`，未发现真实 Key；命中项来自旧报告中的接口认证方式说明和脱敏占位描述，不是完整凭据。本阶段报告未新增真实凭据或完整授权头。

## 9. 中文化检查结果

- 结局数据中文：标题、摘要、正文、历史回声模板、NPC 命运均为中文。
- 结局页用户可见文案中文：是。
- 本阶段新增用户可见英文：无。
- 代码变量、接口字段、类型名仍保留英文，仅用于内部实现。

## 10. 人工验收方法

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

3. 打开 `http://127.0.0.1:5173/`，选择“明代 / 书坊学徒”，进入主流程。
4. 路线一：最终选择“将残页交给陆峥”，期望进入“误信告发”。
5. 路线二：最终选择“暗助顾闻护出残页”，期望进入“暗藏残页”。
6. 路线三：最终选择“焚尽余稿，先保书坊”，期望进入“焚稿自保”。
7. 路线四：最终选择“逼阿沈作证换路”，期望进入“身陷诏狱”。
8. 隐藏路线：发现封口令、陆峥命令矛盾、城门搜检加严并使陆峥/顾问信任达标后，选择“顺着封口令反查上游”，期望进入“引火反查”。
9. 每个结局页应展示中文标题、摘要、正文、历史回声、众人去向和“重新开始”按钮。
10. 若图片缺失，页面仍应展示文字结局内容。
11. 判断真实模型是否参与：查看接口返回的 `history_echo_ai_used`；为真时表示历史回声由真实模型生成或润色，但结局 ID 仍由后端规则决定。

## 11. AI 历史回声测试结果

- 测试时间：2026-05-16
- 测试接口：后端 `HistoryEchoGenerator` 通过 DeepSeek 聊天补全接口生成结构化 JSON。
- 输入摘要：明代书坊焚稿案真相结局；最终选择为“暗助顾闻护出残页”；关键线索包含“烧焦残页”“半枚红印纸角”“诗稿夹带抄录”；NPC 命运包含顾闻、阿沈等。
- 是否调用真实 API：是。
- 是否成功：是，安全布尔结果为 `ai_success=True`。
- 是否 fallback：否，安全布尔结果为 `fallback_used=False`。
- 问题：未发现影响阶段 9 的问题。
- 下一步建议：路演时只说明“智能模型参与历史回声生成或润色”，不要声称模型决定结局 ID。

## 12. 未完成事项

- 未继续修复 SiliconFlow 线索图真实落盘问题；该问题属于阶段 8 视觉链路遗留，不影响阶段 9。
- 未新增北宋、晚唐完整多结局线，符合本阶段范围限制。

## 13. 阻塞问题

- 当前阶段无阻塞。

## 14. 是否建议进入下一阶段

建议进入下一阶段。阶段 9 已满足：5 个结局存在且可判定、至少 3 条路径有测试、结局由规则决定、历史回声中文且可真实模型生成/失败回退、前端结局页可展示、前后端测试通过。

## 15. 是否需要强模型审查

本阶段涉及真实 AI 历史回声、结局规则可控性和路演收束质量，建议强模型审查。
