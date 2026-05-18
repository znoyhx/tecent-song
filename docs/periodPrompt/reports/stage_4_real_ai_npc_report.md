# 阶段 4 完成报告：真实 AI NPC 接入

## 1. 已完成内容

- 在现有 FastAPI 入口 `backend/app/main.py` 与现有 Mock Demo 基础上完成真实 AI NPC 接入，没有重写后端或首页流程。
- 按当前仓库实际路径完善 `backend/app/core/config.py`；旧阶段 Prompt 中的 `backend/config.py` 与当前代码不符，未新建重复配置入口。
- 新增 DeepSeek JSON 客户端 `AIClient`，支持 `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`、`USE_MOCK_AI`、`AI_PROVIDER`、超时和重试配置。
- 新增 NPC 对话 Prompt 模板，包含朝代、阶段、场景、玩家身份、NPC 角色信息、知识权限、已发现线索、出示线索、玩家输入和 RAG 预留上下文。
- 新增 `DialogueOrchestrator`，将 `/api/dialogue` 链路接入真实 AI，并保留现有 Mock/fallback 对话。
- 扩展监管器，检查 JSON 转换结果、中文可见文本、现代词、错朝代词、剧透、阶段跳跃、身份越权和非法线索释放。
- 新增 AI 调用日志服务，记录调用摘要、模型名、耗时、成功状态、fallback 状态、监管结果和日志文件路径，不记录 Key。
- 新增真实连通性、NPC JSON 结构和 fallback 测试。
- 确认 AI 不直接推进阶段、不直接判定结局；AI 建议的线索释放仍受 NPC 权限、阶段和后端规则控制。

## 2. 修改文件列表

- `backend/app/core/config.py`
- `backend/app/services/ai_client.py`
- `backend/app/services/dialogue_orchestrator.py`
- `backend/app/services/log_service.py`
- `backend/app/services/game_engine.py`
- `backend/app/services/supervisor.py`
- `backend/data/prompts/npc_dialogue.md`
- `backend/tests/test_deepseek_connection.py`
- `backend/tests/test_ai_dialogue_json.py`
- `backend/tests/test_ai_fallback.py`
- `docs/periodPrompt/reports/stage_4_real_ai_npc_report.md`

未修改：`docs/DeepseekAPIKey`、`docs/ImageGenerateKey`、`docs/PRD.md`、`docs/develop/*.md`、前端 Key 相关代码。

## 3. 自测结果

- Mock 模式测试：`cd backend; python -m pytest tests -q --color=no --basetemp ../.pytest_tmp`，结果 `8 passed, 1 skipped`。跳过项为真实 DeepSeek 连通性测试在 Mock 模式下按预期跳过。
- 真实 AI 连通性测试：`USE_MOCK_AI=false; AI_PROVIDER=deepseek; python -m pytest tests/test_deepseek_connection.py -q --color=no --basetemp ../.pytest_tmp_real`，结果 `1 passed`。
- NPC JSON 测试：`USE_MOCK_AI=false; AI_PROVIDER=deepseek; python -m pytest tests/test_ai_dialogue_json.py -q --color=no --basetemp ../.pytest_tmp_real_json`，结果 `1 passed`。
- fallback 测试：`python -m pytest tests/test_ai_fallback.py -q --color=no --basetemp ../.pytest_tmp_fallback`，结果 `1 passed`。
- 后端完整测试：`python -m pytest tests -q --color=no --basetemp ../.pytest_tmp`，结果 `8 passed, 1 skipped`。
- 前端构建或人工联调：`cd frontend; npm run build`，结果通过，Vite 构建成功。

## 4. 中文化检查结果

- 新增 NPC Prompt、fallback 文案、错误提示和测试用玩家可见文本均为中文。
- 监管器会拦截 `npc_dialogue`、`npc_action`、`suggested_questions` 中的英文可见文本。
- 已对后端新增日志执行密钥格式与授权头明文检查，未发现 Key 或授权头明文。

- 搜索后端代码与数据时仍可见既有代码字段名、类名、资源 ID、内部视觉提示词中的英文；这些不属于本阶段新增用户可见文案，且本阶段未改动前端展示文案。

## 5. AI 接入测试结果

- 测试时间：2026-05-15 23:24 左右
- 测试接口：后端 `/api/dialogue` 等价链路，通过 `GameEngine.dialogue()` 真实模式联调
- 输入摘要：`NPC=阿沈，阶段=investigation，玩家问题=你昨夜三更后到底听见了什么？`
- 是否调用真实 API：是
- 是否成功：是
- JSON 格式是否正确：是，已解析为 NPC 对话结构
- 是否 fallback：否
- 日志路径：`backend/logs/ai_calls.jsonl`，对应 `backend/logs/prompts/` 与 `backend/logs/responses/`
- 是否确认无 Key 泄露：是；日志只记录摘要、模型名、耗时和状态，不包含 Key；密钥正则与授权头搜索结果为 0。
- 问题：真实模式依赖本机 Key 与网络；如环境无 Key，`test_deepseek_connection.py` 会中文 skip，不会冒充成功。
- 下一步建议：接入更完整的 RAG 上下文与修复 Agent，但仍保持状态机、线索和结局由后端规则控制。

真实联调摘要：

```json
{"fallback_used": false, "supervisor_pass": true, "module": "NPCDialogueAgent", "success": true}
```

## 6. 图片生成测试结果

本阶段不新增图片生成；保留现有视觉 fallback 与已生成资产。

## 7. 人工验收方法

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

3. 打开 `http://127.0.0.1:5173/`。
4. 选择“明代”，生成本局剧本并进入正式剧情。
5. 调查火场使阶段进入“调查”，进入刻版间，与“阿沈”对话。
6. 输入：`你昨夜三更后到底听见了什么？`
7. 期望看到自然中文回复、中文推荐追问、无现代词、无幕后上级身份剧透。
8. 查看 `backend/logs/ai_calls.jsonl`，确认存在 `module=NPCDialogueAgent`、`success=true`、`fallback_used=false` 的记录。
9. 临时移除 Key 或设置 `USE_MOCK_AI=true` 后重复对话，应回退到中文 Mock 回复且游戏不崩溃。

## 8. 未完成事项

- 本阶段未实现完整 RAG 检索，只在 Prompt 中保留 RAG 上下文字段。
- 本阶段未实现 RepairAgent；监管失败时直接回退到现有 Mock/fallback。
- 本阶段未扩展北宋、晚唐完整剧情。

## 9. 阻塞问题

无当前阻塞。真实 AI 能力依赖本机安全 Key 与网络可用性；缺失时会自动 fallback，并在真实连通性测试中中文跳过。

## 10. 是否建议进入下一阶段

建议进入下一阶段，但进入前建议先做一次强模型审查，重点检查 AI 输出监管覆盖率、日志脱敏和线索释放白名单。

## 11. 是否需要强模型审查

本阶段涉及真实 AI、输出监管和 Key 安全，建议强模型审查。
