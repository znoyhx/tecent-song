# 阶段完成报告：背景音乐 BGM

## 1. 已完成内容

- 后端新增天谱乐纯音乐生成服务，支持生成任务提交、任务查询、回调接收、音频下载保存与静音 fallback。
- 后端新增 `/api/music/manifest`、`/api/music/status`、`/api/music/generate`、`/api/music/tasks/{task_id}`、`/api/music/callback`、`/api/music/assets/{bgm_id}`、`/api/music/fallback/silence.wav`。
- 完成策略改为 query 轮询优先；callback 入口保留为兼容能力，不作为生成闭环的前置条件。
- 未显式配置 `MUSIC_CALLBACK_URL` 时，后端会基于自身地址推导 `/api/music/callback`，仍可用 `MUSIC_PUBLIC_BASE_URL`、`BACKEND_PUBLIC_URL` 或 `MUSIC_CALLBACK_URL` 覆盖。
- 已维护 14 首最小 BGM 曲目 manifest，前端只读取可播放路径和元数据，不接触 Key。
- 已完成 1 首真实生成闭环，`pre_game_entry` 保存为本地 WAV 音频。
- 前端新增 `AudioDirector`，根据剧情阶段、场景、当前人物、风险值与结局自动选择 BGM。
- 前端音乐控制栏已完全隐藏；默认开启音乐，固定轻音量播放，保留循环播放与淡入淡出。
- 当前目标曲目未生成时，优先回落到已生成的 `pre_game_entry`，而不是直接静音。
- 浏览器自动播放限制已处理：未发生玩家交互前不强行播放有声音乐。
- 音频不可用时切换后端静音 WAV，游戏流程不被阻断。
- 根据当前开发方向，将原火山音乐记录修正为天谱乐接口记录。

## 2. 修改文件列表

- `backend/app/core/config.py`
- `backend/app/services/music_generation_service.py`
- `backend/app/routers/music.py`
- `backend/app/main.py`
- `backend/data/music/music_manifest.json`
- `backend/tests/test_music_generation_service.py`
- `backend/tests/test_music_generation_real_smoke.py`
- `assets/generated/music/pre_game_entry.wav`
- `frontend/src/components/audio/AudioDirector.tsx`
- `frontend/src/store/musicSelector.ts`
- `frontend/src/types/music.ts`
- `frontend/src/pages/StartPage.tsx`
- `frontend/src/pages/ScenarioGenerationPage.tsx`
- `frontend/src/App.tsx`
- `docs/periodPrompt/reports/stage_11_music_bgm_report.md`

## 3. BGM 曲目与映射表

| bgm_id | 使用场景 | 映射 |
| --- | --- | --- |
| `pre_game_entry` | 进入游戏前 | 默认入口，已真实生成 |
| `ming_intro_night_fire` | 引子 / 夜火 | `intro`、前厅、后院火场 |
| `ming_investigation_threads` | 调查 | 账房、灯油架、刻坊、后门 |
| `ming_npc_owner_xu` | 许掌柜对话 | `npc_owner` |
| `ming_npc_worker_ashen` | 阿沈对话 | `npc_worker` |
| `ming_npc_scholar_guwen` | 顾闻对话 | `npc_scholar` |
| `ming_npc_jinyiwei_luzheng` | 陆峥对话 | `npc_jinyiwei` |
| `ming_reversal_grain_record` | 粮册真相 | `reversal`、高风险兜底 |
| `ming_choice_evidence` | 关键抉择 | `choice` |
| `ending_truth` | 真相结局 | `ending_truth` |
| `ending_order` | 秩序结局 | `ending_order` |
| `ending_survival` | 自保结局 | `ending_survival` |
| `ending_tragedy` | 悲剧结局 | `ending_tragedy` |
| `ending_hidden` | 隐藏结局 | `ending_hidden` |

## 4. 自测结果

- 后端音乐配置存在性检查：通过，仅输出 `completion_strategy=query_polling`、`callback_required_for_completion=False`、`api_key_available=True`，未输出 Key。
- 音乐 manifest schema 测试：通过。
- BGM 选择优先级测试：通过。
- 天谱乐 API 客户端单元测试：通过，覆盖 generate、query、callback、下载保存、远端 URL 不入任务记录。
- fallback 测试：通过，改名本地音频后 manifest 切到静音 fallback。
- 后端音乐单测：`python -m pytest backend/tests/test_music_generation_service.py -q`，7 passed。
- 真实 smoke：`python -m pytest backend/tests/test_music_generation_real_smoke.py -q -rs`，1 passed。
- 前端构建：`npm.cmd run build -- --outDir D:/tmp/historygame-build-stage11 --emptyOutDir`，通过。

## 5. 中文化检查结果

- 音乐入口和游戏内音乐控件已完全隐藏，不再遮挡视野。
- 音乐失败不显示打断式 UI；游戏继续运行，必要时静默回落。
- 本轮顺手修正入口页/剧本页可见英文残留：`NPC` 改为“人物”，`Demo` 改为“演示”。
- 搜索结果中剩余匹配主要是代码类型名、组件名和内部变量名，不属于用户可见文案。

## 6. 音乐生成 API 测试结果

- 测试时间：2026-05-19
- 接口：天谱乐纯音乐接口 `instrumental.generate` / `instrumental.query`
- 是否后付费 GenBGMForTime：否，本轮按用户确认方向转为天谱乐接口
- 是否调用真实 API：是
- 是否成功：是
- TaskID：`t2m_WPnZjVKkKiLweowiz`
- 是否获得可播放音频：是
- 保存路径：`assets/generated/music/pre_game_entry.wav`
- 是否 fallback：否；其他未生成曲目仍使用 `/api/music/fallback/silence.wav`
- 是否打印 Key：否

## 7. 人工验收方法

1. 后端工作目录 `backend`，运行 `python -m uvicorn app.main:app --reload`。
2. 前端工作目录 `frontend`，运行 `npm run dev`。
3. 打开前端页面后，音乐栏目不应出现。
4. 点击选择朝代或进入游戏后，浏览器获得用户手势，已生成的入口曲会从 `assets/generated/music/pre_game_entry.wav` 自动播放。
5. 调查、对话、进入抉择或结局时，如果目标曲尚未生成，会继续播放入口曲；目标曲已生成后再切换。
6. 当前建议继续使用 query 轮询完成下载；若以后要让天谱乐主动回调本机后端，再将 `MUSIC_PUBLIC_BASE_URL` 或 `MUSIC_CALLBACK_URL` 配置为公网可访问地址。

## 8. 未完成事项

- 当前只真实生成了 1 首 `pre_game_entry`，尚未批量生成剩余 13 首，以避免后付费失控。
- 其他曲目仍配置了 manifest 和静音 fallback，可按需逐首生成。

## 9. 阻塞问题

- 本地默认回调地址可以用于提交参数，但天谱乐服务器通常无法访问 `127.0.0.1`。本轮真实闭环依赖 query 轮询拿到音频 URL 并下载成功。
- 文档未提供单独下载接口；当前实现按 query/callback 返回的 `audio_url` / `audio_hi_url` 下载保存，已通过真实任务验证。

## 10. 是否建议进入下一阶段

建议进入下一阶段。BGM manifest、前端动态播放、控制 UI、fallback、天谱乐真实提交、query 轮询与本地保存均已跑通；剩余曲目建议按展示需要逐首生成。

## 11. 是否需要强模型审查

是。建议重点审查天谱乐回调公网地址配置、真实任务回调安全性、音频 URL 下载校验，以及是否需要限制真实批量生成数量。
