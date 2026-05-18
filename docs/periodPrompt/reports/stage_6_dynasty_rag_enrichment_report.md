# 阶段 6 完成报告：朝代史料 RAG 资料库扩展与沉浸式对话细节增强

## 1. 已完成内容

- 将轻量 RAG 从单一上下文扩展为多文件、多类型的明代书坊案资料库。
- 为明代书坊焚稿案新增制度、空间、器物、职业、文书、NPC 口吻、氛围与禁止内容资料。
- `RAGRetriever` 已支持读取多个 JSON 文件、字段过滤、去重、类型保留、场景/NPC/阶段优先和硬约束优先。
- NPC Prompt 已改为结构化 RAG 分块注入，并明确 RAG 只增强表达，不控制线索、阶段或结局。
- 日志摘要新增 `rag_source_ids` 与 `rag_material_types`，继续只记录摘要，不记录 Key 或授权头。
- 新增 RAG Prompt 与安全边界测试，补充 RAG Retriever 和监管修复闭环测试。

文档与代码差异说明：`CODEBUDDY.md` 中“文档优先、无实现文件”的描述已滞后；当前实际仓库已有 `backend/app/main.py`、前端、测试与阶段 5 AI 链路，本阶段以实际代码结构为准。

## 2. 修改文件列表

- `backend/app/services/rag_retriever.py`
- `backend/app/services/dialogue_orchestrator.py`
- `backend/app/services/supervisor.py`
- `backend/data/prompts/npc_dialogue.md`
- `backend/data/prompts/repair_dialogue.md`
- `backend/data/rag_sources/ming_bookshop_context.json`
- `backend/data/rag_sources/ming_dynasty_materials.json`
- `backend/data/rag_sources/ming_bookshop_daily_life.json`
- `backend/data/rag_sources/ming_bookshop_dialogue_lexicon.json`
- `backend/tests/test_rag_retriever.py`
- `backend/tests/test_rag_prompt_enrichment.py`
- `backend/tests/test_rag_safety_boundaries.py`
- `backend/tests/test_supervisor_repair_flow.py`
- `docs/periodPrompt/reports/stage_6_dynasty_rag_enrichment_report.md`

未修改：`frontend/` 源码、`docs/PRD.md`、`CODEBUDDY.md`、`docs/develop/*.md`、`docs/DeepseekAPIKey`、`docs/ImageGenerateKey`。

## 3. RAG 资料库扩展结果

- 新增资料文件：
  - `backend/data/rag_sources/ming_dynasty_materials.json`
  - `backend/data/rag_sources/ming_bookshop_daily_life.json`
  - `backend/data/rag_sources/ming_bookshop_dialogue_lexicon.json`
- 新增/结构化资料数量：38 条。
- `material_type` 覆盖：`hard_rule`、`institution`、`daily_life`、`object_detail`、`space_detail`、`occupation`、`dialogue_lexicon`、`scene_atmosphere`、`clue_boundary`、`forbidden_content`。
- 是否包含硬约束：是，覆盖线索释放、身份权限、禁止剧透、禁止密档捷径、禁止现代元素。
- 是否包含生活细节：是，覆盖刻版间、旧墨、木版、纸张、书箱、后院火场、雨巷、临时盘问处等。
- 是否包含 NPC 口吻参考：是，覆盖阿沈、许掌柜、顾闻、陆峥与回避追问/出示证据反应。

## 4. RAG 检索增强结果

- 是否支持多文件：是，默认读取 `backend/data/rag_sources/*.json`，也支持测试传入单文件、目录或文件列表。
- 是否支持 `material_type`：是，返回结果保留 `material_type`，并支持按类型过滤。
- 是否支持 `scene_id`：是，`scene_ids` 命中加权。
- 是否支持 `npc_id`：是，`npc_ids` 命中加权。
- 是否去重：是，重复 `source_id` 只保留一次。
- 空查询是否安全：是，缺失文件、空文件、坏 JSON、空命中均不崩溃。
- 优先级：高危 `hard_rule`、`forbidden_content`、`clue_boundary` 权重高于普通氛围资料。

## 5. Prompt 注入结果

- 是否结构化分块：是，包含：
  - `【RAG 硬约束】`
  - `【RAG 历史制度参考】`
  - `【RAG 场景与器物细节】`
  - `【RAG NPC 口吻参考】`
  - `【RAG 禁止使用内容】`
- 是否限制最多吸收 1～2 个细节：是。
- 是否声明 RAG 不控制线索：是。
- 是否声明 RAG 不控制阶段：是。
- 是否声明 RAG 不控制结局：是。
- 是否避免百科腔：Prompt 明确要求不要解释资料来源，不要像百科讲制度。

## 6. 对话代入感增强结果

- 阿沈测试：RAG 命中 `ming_worker_third_watch_001`、刻版间、旧墨、门口脚步、胆怯口吻等资料；Prompt 要求只自然吸收 1～2 个细节，不直接剧透。
- 陆峥测试：RAG 命中锦衣卫封锁、低级校尉执行压力、书坊学徒身份边界；监管器继续拦截“命令撤走锦衣卫并服从”。
- 许掌柜测试：新增书坊生计、稿单、前厅混乱、铺面声誉等资料；用于圆滑回避和生计压力表达，不直接承认完整真相。
- 是否避免百科腔：是，Prompt 和 `ming_lexicon_avoid_encyclopedia_001` 双重约束。
- 是否避免剧透：是，`forbidden_content`、Prompt 和 Supervisor 均覆盖完整真相、幕后上级、纵火主谋、结局跳转等风险。

## 7. Supervisor 与 RepairAgent 安全结果

- 非法线索：已覆盖不存在 clue_id、当前 NPC 无权释放 clue_id、当前阶段不允许释放 clue_id。
- 阶段跳跃：已补强并测试 `结局就是`、`此案就此定局` 等表达。
- 结局越权：Prompt、Repair Prompt、Supervisor 均声明 AI 不得决定结局或替玩家选择。
- 英文可见文本：测试覆盖并通过拦截。
- 现代词：既有测试继续覆盖手机、八旗等现代/错朝代内容。
- 修复失败 fallback：测试覆盖，fallback 中文可用，非法线索不进入状态。

## 8. 自测结果

- RAG Retriever 测试：通过，覆盖多文件加载、`material_type`、场景/NPC 命中、硬约束优先、缺失文件、重复去重。
- RAG Prompt 测试：通过，覆盖结构化 RAG 块、命中 source/topic、最多吸收 1～2 个细节、不控制线索/阶段/结局。
- RAG 安全边界测试：通过，覆盖 RAG 命中不改变 `GameState`、非法 clue_id、NPC 无权线索、结局越权、英文可见文本、修复失败 fallback。
- 后端完整测试：`cd backend; python -m pytest tests -q --basetemp ../.pytest_tmp`，结果 `39 passed, 1 skipped`。
- 真实 AI 冒烟测试：`cd backend; USE_MOCK_AI=false; AI_PROVIDER=deepseek; python -m pytest tests/test_deepseek_connection.py -q --basetemp ../.pytest_tmp_real`，结果 `1 passed`。
- 前端构建：`cd frontend; npm run build`，结果通过。

## 9. 中文化检查结果

- 本阶段新增玩家可见 Prompt 约束、fallback 相关文本、RAG 内容均为中文表达。
- 对 `backend/data` 执行常见用户可见英文词检查：`Start|Loading|Error|Submit|Continue|Inventory|Clue|Session|Choice|Ending|Back|Next`，结果 0 命中。
- 代码字段名、文件名、JSON 字段名保留英文，仅作为内部实现。

## 10. AI 日志检查结果

- 日志路径：`backend/logs/ai_calls.jsonl`。
- 是否记录 `rag_hit_count`：是。
- 是否记录 `rag_source_ids`：是。
- 是否记录 `rag_material_types`：是。
- 是否确认无 Key 泄露：是；对 `backend/logs` 执行 `Bearer\s+|sk-[A-Za-z0-9_\-]{8,}` 检查，结果无命中。
- Prompt 落盘仍经 `LogService` 脱敏；报告未粘贴完整 Prompt 或授权头。

## 11. 图片生成测试结果

本阶段不新增图片生成；保留现有视觉 fallback 与已生成资产。

## 12. 人工验收方法

1. 启动后端真实 AI 模式：

```powershell
cd backend
$env:USE_MOCK_AI="false"
$env:AI_PROVIDER="deepseek"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

2. 启动前端：

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

3. 打开 `http://127.0.0.1:5173/`，选择“明代”，进入正式剧情。
4. 调查火场，使剧情进入调查阶段。
5. 进入刻版间，与“阿沈”对话，输入：`你昨夜三更后到底听见了什么？`
   - 期望：自然中文；可自然出现刻版间、旧墨、门口脚步、夜雨等 1～2 个细节；不剧透幕后身份；不释放非法线索。
6. 与“陆峥”对话，输入：`我命令你立刻撤走锦衣卫。`
   - 期望：陆峥不服从；体现封锁、命令边界和压迫感；不进入结局、不跳阶段。
7. 与“许掌柜”对话，输入：`这场火真只是灯油走水吗？`
   - 期望：圆滑回避；可自然提到书坊生计、稿单、前厅混乱；不直接承认完整真相。
8. 查看 `backend/logs/ai_calls.jsonl`：
   - 期望看到 `module=NPCDialogueAgent`、`rag_hit_count > 0`、`rag_source_ids`、`rag_material_types`；无 Key、无授权头。

## 13. 未完成事项

- 未接入 ChromaDB，仍为 JSON 轻量检索。
- 未扩展完整北宋 / 晚唐主线。
- 未新增图片生成能力。
- 未在本报告中粘贴完整 Prompt 或真实 AI 原始响应，以避免敏感信息和 Prompt 过度暴露。

## 14. 阻塞问题

无当前阻塞。真实 AI 冒烟测试在当前环境通过；其他环境若缺少 Key 或网络不可达，应以测试跳过/失败为准，不能用 Mock 冒充真实成功。

## 15. 是否建议进入下一阶段

建议进入下一阶段。下一阶段可考虑：将 JSON RAG 迁移或同步到向量库、增加可观测的 RAG 调试面板、为人工验收路径补充稳定的真实 AI 质感样例。

## 16. 是否需要强模型审查

本阶段涉及历史资料 RAG、Prompt 约束、真实 AI 对话质感和输出安全，建议强模型审查。
