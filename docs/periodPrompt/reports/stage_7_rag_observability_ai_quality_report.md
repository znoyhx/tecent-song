# 阶段 7 完成报告：RAG 可观测性、真实 AI 对话质感评估与演示稳定化

## 1. 已完成内容

- 新增安全 RAG 调试预览接口 `POST /api/debug/rag/preview`，可查看某次 NPC 对话输入会命中的 RAG 资料摘要。
- `RAGRetriever` 新增 `preview()`，返回 `hit_count`、`source_ids`、`material_types`、`hits`、`grouped`，并限制 `content` 摘要长度。
- AI 日志摘要增强：记录 `ai_mode`、`rag_hit_count`、`rag_source_ids`、`rag_material_types`、`supervisor_issue_types`、`repair_attempted`、`repair_success`、`fallback_used`。
- `LogService` 脱敏增强为递归处理嵌套 `dict/list`，覆盖授权头、`sk-` 样式字符串与当前运行环境中的 DeepSeek Key。
- 新增 RAG 调试接口测试、AI 日志可观测性测试、真实 AI RAG 质感冒烟测试。
- 微调 NPC 与修复 Prompt，明确不向玩家复述 `source_id` 等内部 RAG 字段，且 RAG 不控制线索、阶段和结局。
- 固化阿沈、陆峥、许掌柜三条人工验收路径。

文档与代码差异说明：`CODEBUDDY.md` 中“文档优先、无实现文件”的描述仍已滞后；当前实际仓库已有 `backend/app/main.py`、前端、测试与真实 AI/RAG 链路，本阶段以实际代码结构为准。当前目录不是 Git 仓库，`git status` 不可用。

## 2. 修改文件列表

- `backend/app/routers/game.py`
- `backend/app/services/rag_retriever.py`
- `backend/app/services/dialogue_orchestrator.py`
- `backend/app/services/log_service.py`
- `backend/data/prompts/npc_dialogue.md`
- `backend/data/prompts/repair_dialogue.md`
- `backend/tests/test_rag_debug_preview.py`
- `backend/tests/test_ai_log_observability.py`
- `backend/tests/test_real_ai_rag_enrichment_smoke.py`
- `docs/periodPrompt/reports/stage_7_rag_observability_ai_quality_report.md`

未修改：`frontend/` 源码、`docs/PRD.md`、`CODEBUDDY.md`、`docs/develop/*.md`、`docs/DeepseekAPIKey`、`docs/ImageGenerateKey`、既有视觉资源缓存。

## 3. RAG 调试预览能力

- 是否新增调试接口：是。
- 接口路径：`POST /api/debug/rag/preview`。
- 是否不改变 GameState：是，测试覆盖已有 session 调用前后 `state` 完全一致。
- 是否不调用真实 AI：是，只调用 `RAGRetriever.preview()`，不进入 `AIClient`。
- 是否返回 source_ids：是。
- 是否返回 material_types：是。
- 是否返回 grouped：是，按 `material_type` 分组。
- 是否限制 content 长度：是，默认最多 100 字，内部上限 120 字。
- 是否避免 Prompt 暴露：是，不返回完整 Prompt、API Key 或授权头。

## 4. 日志可观测性增强

- 是否记录 ai_mode：是，支持 `mock`、`real`、`unavailable` 摘要。
- 是否记录 rag_hit_count：是。
- 是否记录 rag_source_ids：是。
- 是否记录 rag_material_types：是。
- 是否记录 supervisor_issue_types：是。
- 是否记录 repair_attempted：是。
- 是否记录 repair_success：是。
- 是否记录 fallback_used：是。
- 是否脱敏 Key 与授权头：是，测试覆盖 `Bearer xxx`、`sk-xxxxxxxx`、当前运行环境 Key、嵌套 extra fields。

## 5. Prompt 微调结果

- 是否保留结构化 RAG 块：是，`npc_dialogue.md` 继续保留结构化 RAG 注入。
- 是否限制最多吸收 1～2 个细节：是。
- 是否禁止向玩家复述 source_id：是，已明确禁止复述 `source_id`、`material_type`、`source_level`、`severity` 等内部字段。
- 是否声明 RAG 不控制线索：是。
- 是否声明 RAG 不控制阶段：是。
- 是否声明 RAG 不控制结局：是。

## 6. 真实 AI 质感冒烟测试

- 测试文件：`backend/tests/test_real_ai_rag_enrichment_smoke.py`。
- 是否无 Key 时 skip：是。
- 是否真实调用：是，运行时设置 `USE_MOCK_AI=false` 且 `AI_PROVIDER=deepseek`，本机结果 `1 passed`。
- 阿沈测试结果：通过；断言中文可见文本、无现代词/剧透词、`rag_hit_count > 0`。
- 陆峥测试结果：通过；断言不服从“撤走锦衣卫”越权命令、中文可见文本、`rag_hit_count > 0`。
- 许掌柜测试结果：通过；断言中文可见文本、无剧透、`rag_hit_count > 0`。
- 是否无现代词：是，测试断言覆盖常见现代词。
- 是否无剧透：是，测试断言覆盖“幕后上级”“完整真相”“纵火主谋”等。
- 是否无非法线索：是，测试断言释放线索必须属于对应 NPC 白名单。
- 是否日志有 RAG 命中：是，三条 smoke 路径均断言 `rag_hit_count > 0`。

## 7. Supervisor / Repair / fallback 结果

- 非法线索：既有测试继续覆盖不存在 clue_id、当前 NPC 无权 clue_id、当前阶段不允许 clue_id。
- 身份越权：既有测试覆盖书坊学徒命令锦衣卫、调阅官府密档越权。
- 阶段跳跃：既有测试覆盖 `结局就是`、`此案就此定局`、`通关` 等。
- 结局越权：Prompt、Repair Prompt、Supervisor 均要求 AI 不决定结局。
- 英文可见文本：既有测试覆盖并通过。
- 修复失败 fallback：既有测试覆盖，fallback 中文可用，非法线索不进入状态。

## 8. 自测结果

- 后端完整测试：`cd backend; python -m pytest tests -q --basetemp ../.pytest_tmp`，结果 `45 passed, 2 skipped`。
- RAG 调试接口测试：`cd backend; python -m pytest tests/test_rag_debug_preview.py -q --basetemp ../.pytest_tmp_debug`，结果 `5 passed`。
- 日志可观测性测试：`cd backend; python -m pytest tests/test_ai_log_observability.py -q --basetemp ../.pytest_tmp_log`，结果 `1 passed`。
- 真实 AI RAG 冒烟测试：`cd backend; $env:USE_MOCK_AI="false"; $env:AI_PROVIDER="deepseek"; python -m pytest tests/test_real_ai_rag_enrichment_smoke.py -q --basetemp ../.pytest_tmp_real_rag`，结果 `1 passed`。
- 前端构建：`cd frontend; npm run build`，结果通过。
- 日志脱敏检查：`Get-ChildItem -Path backend/logs -Recurse -File | Select-String -Pattern "Bearer\s+|sk-[A-Za-z0-9_\-]{8,}"`，结果无命中。

## 9. 中文化检查结果

- 新增后端错误提示、Prompt 规则、测试输入和报告均为中文。
- 执行常见用户可见英文词抽查：`Start|Loading|Error|Submit|Continue|Inventory|Clue|Session|Choice|Ending|Back|Next`，本阶段新增用户可见文案未发现英文残留。
- 代码变量名、接口字段名、文件名保留英文，仅作为内部实现。

## 10. 人工验收方法

### 启动真实 AI 模式

```powershell
cd backend
$env:USE_MOCK_AI="false"
$env:AI_PROVIDER="deepseek"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

另开终端：

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

打开 `http://127.0.0.1:5173/`，选择“明代 / 书坊学徒”，进入主线。

### RAG 调试预览

可直接调用：

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/debug/rag/preview -ContentType "application/json" -Body '{"dynasty_id":"ming","current_stage":"investigation","current_scene_id":"scene_engraving_room","npc_id":"npc_worker","player_message":"你昨夜三更后到底听见了什么？","presented_clue_ids":[],"discovered_clue_ids":["clue_burned_page"],"top_k":8}'
```

期望：返回 `hit_count > 0`、`source_ids` 包含 `ming_worker_third_watch_001`、包含 `material_types` 与 `grouped`，不出现 Key、授权头或完整 Prompt。

### 阿沈

输入：

```text
你昨夜三更后到底听见了什么？
```

期望：

- 自然中文；
- 可能出现旧墨、刻版间、门口脚步、夜雨等 1～2 个细节；
- 阿沈胆怯、吞吐、回避；
- 不说完整真相；
- 不说幕后上级；
- 不释放非法线索；
- 日志中 `rag_hit_count > 0`。

### 陆峥

输入：

```text
我命令你立刻撤走锦衣卫。
```

期望：

- 陆峥不服从；
- 有封锁、命令边界、压迫感；
- 不让玩家越权；
- 不调阅密档；
- 不进入结局；
- 如 AI 违规，Supervisor/Repair/fallback 生效。

### 许掌柜

输入：

```text
这场火真只是灯油走水吗？
```

期望：

- 许掌柜圆滑回避；
- 可自然提到书坊生计、稿单、前厅混乱；
- 不直接承认完整真相；
- 不释放未授权关键线索。

## 11. 图片生成测试结果

本阶段不新增图片生成；保留现有视觉 fallback 与已生成资产。

## 12. 未完成事项

- 未接入 ChromaDB，仍使用 JSON 轻量 RAG 检索。
- 未新增前端 RAG 调试面板，本阶段仅提供后端调试接口。
- 未扩展完整北宋 / 晚唐主线。
- 未新增图片生成能力。

## 13. 阻塞问题

无当前阻塞。真实 AI RAG 冒烟测试在当前环境通过；其他环境若缺少 Key 或网络不可达，应以测试跳过/失败为准，不能用 Mock 冒充真实成功。

## 14. 是否建议进入下一阶段

建议进入下一阶段。下一阶段可考虑将 RAG 调试结果做成仅开发者可见面板，或继续完善路演用日志查看页。

## 15. 是否需要强模型审查

本阶段涉及真实 AI 对话质感、RAG 命中可观测性、日志脱敏和演示稳定性，建议强模型审查。
