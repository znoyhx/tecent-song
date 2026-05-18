# 阶段 5 完成报告：RAG 上下文接入与 AI 监管修复闭环

## 1. 已完成内容

- 在现有 `/api/dialogue`、`DialogueOrchestrator`、`AIClient`、`SupervisorService` 基础上完成最小改动接入。
- 新增轻量 JSON RAG 检索服务，未接入 ChromaDB，不改变后端状态机。
- 为明代书坊焚稿案新增最小历史与剧情约束资料。
- NPC Prompt 已注入真实检索上下文，不再使用“暂未接入向量检索”占位。
- 新增 `RepairAgent` 与修复 Prompt。
- 对话链路改为：AI 输出 → Supervisor → RepairAgent 最多一次 → 再次 Supervisor → 失败 fallback。
- 增强监管器：现代词、错朝代、剧透、身份越权、非法线索、阶段跳跃、英文可见文本等均有规则检查。
- 扩展 AI 日志摘要字段，支持记录 RAG 命中数、修复尝试、修复结果和 RepairAgent 调用摘要。
- 新增 RAG、RepairAgent、监管修复闭环测试，并保持既有测试通过。

文档与代码差异说明：`CODEBUDDY.md` 的“文档优先、无实现文件”描述已滞后；当前实际仓库已存在 `backend/app/main.py`、前端与测试，本阶段以当前代码结构为准。

## 2. 修改文件列表

- `backend/app/services/rag_retriever.py`：新增轻量 RAG 检索器。
- `backend/data/rag_sources/ming_bookshop_context.json`：新增明代书坊案约束资料。
- `backend/app/services/repair_agent.py`：新增 RepairAgent。
- `backend/data/prompts/repair_dialogue.md`：新增修复 Prompt。
- `backend/app/services/dialogue_orchestrator.py`：接入 RAG、修复闭环与日志摘要。
- `backend/app/services/supervisor.py`：增强监管规则。
- `backend/app/services/ai_client.py`：保留解析失败原始文本，供修复链路使用。
- `backend/app/services/log_service.py`：支持附加日志字段并脱敏。
- `backend/data/prompts/npc_dialogue.md`：加入 RAG 使用规则。
- `backend/tests/test_rag_retriever.py`：新增 RAG 测试。
- `backend/tests/test_repair_agent.py`：新增 RepairAgent 测试。
- `backend/tests/test_supervisor_repair_flow.py`：新增监管修复闭环测试。
- `backend/tests/test_logic.py`：同步监管器问题类型断言。
- `docs/periodPrompt/reports/stage_5_rag_repair_supervisor_report.md`：本报告。

未修改：`docs/DeepseekAPIKey`、`docs/ImageGenerateKey`、`docs/PRD.md`、`docs/develop/*.md`、前端 Key 相关代码。

## 3. RAG 接入结果

- 数据来源：`backend/data/rag_sources/ming_bookshop_context.json`。
- 检索方式：按 `dynasty_id` 过滤，并对 `current_stage`、`npc_id`、玩家输入、出示线索、已发现线索、关键词、资料等级和严重度做轻量打分，返回 Top 3～5。
- 命中示例：
  - 阿沈 + `investigation` + “三更后”可命中 `ming_worker_third_watch_001`。
  - 陆峥 + “命令你撤走锦衣卫”可命中 `ming_jinyiwei_permission_001`。
- 是否影响后端规则：否。RAG 只进入 Prompt，线索入库、阶段跳转和结局仍由后端规则控制。

## 4. RepairAgent 接入结果

- 是否最多修复一次：是，`DialogueOrchestrator` 只调用一次 `RepairAgent`。
- 修复成功示例：测试中初始输出包含“手机”和非法线索，RepairAgent 修复为合规中文 JSON，最终未 fallback。
- 修复失败 fallback 示例：测试中 RepairAgent 仍返回违规内容，二次监管失败后使用本地中文 fallback。
- 是否保留中文：是，修复 Prompt 要求所有玩家可见文本必须为中文，测试覆盖中文 JSON 输出。

## 5. Supervisor 增强结果

- 现代词：拦截手机、互联网、电话、电灯、汽车、枪、现代警察、公司、电脑、摄像头、网络、系统后台等。
- 错朝代：拦截清代辫发、八旗、民国、洋枪、现代法律等。
- 剧透：拦截“幕后上级”“完整真相是”“纵火主谋就是”等提前揭示。
- 身份越权：拦截书坊学徒命令锦衣卫并被服从；拦截同意调阅官府密档。
- 非法线索：拦截不存在、非 NPC 可释放、当前阶段不允许释放的线索。
- 阶段跳跃：拦截“进入结局”“可以结案”“已经通关”等。
- 英文可见文本：拦截 `npc_dialogue`、`npc_action`、`suggested_questions` 中的英文可见短语。

## 6. 自测结果

- RAG 测试：已覆盖阿沈三更后、陆峥越权命令、空查询、返回字段。
- RepairAgent 测试：已覆盖现代词移除、非法线索移除、JSON 字段完整、中文输出。
- Supervisor 修复闭环测试：已覆盖初始违规、监管拦截、RepairAgent 调用一次、修复后通过。
- fallback 测试：已覆盖修复失败后 fallback，且违规线索未污染状态。
- 后端完整测试：`cd backend; python -m pytest tests -q --basetemp ../.pytest_tmp`，结果 `25 passed, 1 skipped`。
- 真实 AI 冒烟测试：`USE_MOCK_AI=false; AI_PROVIDER=deepseek; python -m pytest tests/test_deepseek_connection.py -q --basetemp ../.pytest_tmp_real`，结果 `1 passed`。
- 前端构建或人工联调：`cd frontend; npm run build`，结果通过，Vite 构建成功。

## 7. 中文化检查结果

- 新增 fallback 展示文本、测试中的用户可见文本均为中文。
- Prompt、RAG 内容和 RepairAgent 约束均要求玩家可见文本为中文。
- 本阶段未改动首页三段式流程和前端用户可见文案。
- 代码变量名、字段名、测试类名保留英文，仅作为内部实现。

## 8. AI 日志检查结果

- 日志路径：`backend/logs/ai_calls.jsonl`，Prompt 与响应分别落盘到 `backend/logs/prompts/`、`backend/logs/responses/`。
- 是否记录 RAG 命中：是，`NPCDialogueAgent` 日志支持 `rag_hit_count`。
- 是否记录修复尝试：是，`NPCDialogueAgent` 日志支持 `repair_attempted`、`repair_success`、`repair_call_id`；RepairAgent 会单独记录 `module=RepairAgent` 摘要。
- 是否确认无 Key 泄露：是；对 `backend/logs` 执行 `Bearer` 与 `sk-` 样式搜索，结果 0；日志写入会递归脱敏附加字段。

## 9. 图片生成测试结果

本阶段不新增图片生成；保留现有视觉 fallback 与已生成资产。

## 10. 人工验收方法

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
4. 调查火场，使剧情进入调查阶段，进入刻版间，与“阿沈”对话。
5. 输入：`你昨夜三更后到底听见了什么？`
6. 期望：回复为自然中文；阿沈保持胆怯回避；不剧透幕后身份；不出现现代词；日志可见 `rag_hit_count`。
7. 与“陆峥”对话，输入：`我命令你立刻撤走锦衣卫。`
8. 期望：陆峥不服从；监管或修复链路阻止身份越权；状态不跳阶段、不进入结局。
9. 设置 Mock：`$env:USE_MOCK_AI="true"` 后重复对话，期望中文 fallback 可用且游戏不崩溃。

## 11. 未完成事项

- 本阶段未接入 ChromaDB，仅实现 JSON 轻量检索。
- 本阶段未扩展北宋、晚唐完整剧情。
- 未新增图片生成能力。

## 12. 阻塞问题

无当前阻塞。真实 DeepSeek 冒烟测试在本机环境通过；如其他环境缺少 Key 或网络不可达，真实测试会跳过或失败，不应使用 Mock 冒充成功。

## 13. 是否建议进入下一阶段

建议进入下一阶段。下一阶段可考虑将 RAG 数据扩展为可维护资料包，并为更多 NPC 对话路径加入真实 AI 冒烟样例。

## 14. 是否需要强模型审查

本阶段涉及 RAG 上下文、AI 修复、输出监管和 Key 安全，建议强模型审查。
