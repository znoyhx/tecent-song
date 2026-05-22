# 阶段完成报告

## 1. 已完成内容

- 重构主游戏页面为“顶部状态栏 + 左侧功能栏 + 中央 Phaser 舞台 + 右侧调查栏 + 底部对话框”的视觉小说调查界面。
- 新增场景九宫格弹窗、人物信息弹窗、任务摘要弹窗、DeepSeek 智能助手面板。
- 右侧调查栏改为“线索 / 推理 / 笔记 / 助手”Tab，线索图仅在真实生成图存在时展示，缺图显示“线索图待生成”。
- 底部对话框补齐 NPC 身份、信任度、推荐追问、自由输入、出示线索联动。
- 后端新增 `/api/assistant/hint`，由后端读取权威 session 状态后调用真实 DeepSeek，并做未发现线索 / 剧透拦截。
- 视觉 prompt 目录改为从明代书坊案场景、人物、线索数据动态生成：场景 prompt 包含本场景热点与线索，线索 prompt 包含线索名、描述、朝代、所属场景与材质状态。
- `/api/visual/status` 合并返回全量 prompt 目录资产，`/api/visual/bootstrap-demo-assets?include_clues=true` 可覆盖全量场景、人物和线索。

## 2. 修改文件列表

- `frontend/src/pages/GamePage.tsx`
- `frontend/src/components/assistant/AssistantPanel.tsx`
- `frontend/src/components/clue/ClueSidebar.tsx`
- `frontend/src/components/dialogue/DialoguePanel.tsx`
- `frontend/src/components/scene/ScenePanel.tsx`
- `frontend/src/components/scene/PhaserStage.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/styles/global.css`
- `frontend/vite.config.ts`
- `backend/app/routers/game.py`
- `backend/app/routers/visual.py`
- `backend/app/services/visual_prompt_agent.py`
- `assets/generated/visuals/asset_manifest.json`
- `assets/generated/visuals/clues/*.png`

## 3. 主页面 UI 重构说明

主页面由 `GamePage.tsx` 统一编排：中央仍渲染 `PhaserStage`，`VITE_USE_PHASER_STAGE=0` 时回退到 `ScenePanel`。顶栏、左栏、右栏和底部对话框都是 React 壳层，不接管剧情状态。视觉风格使用深色半透明面板、暗金边线、宣纸/古籍纹理、克制朱红强调，并移除了通用 RPG 资源栏语义。

## 4. 顶部状态栏数据来源

- 朝代：`snapshot.dynasty.name`、`snapshot.dynasty.period_label`
- 地点：`snapshot.scene.name`
- 身份：`snapshot.player_identity?.display_name ?? snapshot.player_role.name`
- 当前目标：`snapshot.current_goal`
- 调查进度：前端根据当前阶段权重、已发现线索数、可用场景热点线索池计算

未写死“大唐 · 长安”，未展示金币、铜币、体力、商城、成就等资源项。

## 5. 左侧功能栏说明

左侧仅保留：场景、人物、任务、智能助手。没有“线索”入口，线索只在右侧调查栏显示。

## 6. 场景九宫格说明

场景卡片来自 `snapshot.available_scenes`，不硬编码隐藏场景。卡片展示场景名、描述、当前地点状态、未发现线索提示和场景背景图。背景图来自后端注入的 `scene.visual_asset_id / visual_asset_url / visual_status`。

## 7. 人物信息弹窗说明

人物面板展示当前场景可盘问 NPC 的半身像、姓名、身份、信任度、关系、已知信息、可疑点、相关线索和最近对话摘要。人物资料来自 `snapshot.scene_npcs` 与 `snapshot.state.npc_trust`；头像 / 半身像来自后端视觉资产路由。

## 8. 线索图生成结果

真实图片生成服务：SiliconFlow / `Kwai-Kolors/Kolors`。本轮真实生成 20 条案卷线索图；15 条因上游 `http_429` 限流未完成，前端会显示“线索图待生成”，不会显示无关占位图。

| clue_id | 线索名 | 是否生成 AI 图 | 图片路径 / asset_id | 是否与内容匹配 |
| --- | --- | --- | --- | --- |
| clue_fire_origin_wrong | 火起点异常 | 是 | `assets/generated/visuals/clues/clue_fire_origin_wrong.png` | 是 |
| clue_burned_page | 烧焦残页 | 是 | `assets/generated/visuals/clues/clue_burned_page.png` | 是 |
| clue_red_seal | 半枚红印纸角 | 是 | `assets/generated/visuals/clues/clue_red_seal.png` | 是 |
| clue_oil_smell | 异常火油味 | 是 | `assets/generated/visuals/clues/clue_oil_smell.png` | 是 |
| clue_backdoor_latch | 后门门闩松动 | 是 | `assets/generated/visuals/clues/clue_backdoor_latch.png` | 是 |
| clue_worker_lie | 刻工矛盾证言 | 是 | `assets/generated/visuals/clues/clue_worker_lie.png` | 是 |
| clue_ink_on_sleeve | 袖口旧墨 | 是 | `assets/generated/visuals/clues/clue_ink_on_sleeve.png` | 是 |
| clue_box_before_dawn | 三更搬箱 | 是 | `assets/generated/visuals/clues/clue_box_before_dawn.png` | 是 |
| clue_owner_moved_box | 掌柜提前清箱 | 是 | `assets/generated/visuals/clues/clue_owner_moved_box.png` | 是 |
| clue_missing_manuscript_list | 缺失稿单 | 是 | `assets/generated/visuals/clues/clue_missing_manuscript_list.png` | 是 |
| clue_scholar_searches_manuscript | 士子急寻旧稿 | 是 | `assets/generated/visuals/clues/clue_scholar_searches_manuscript.png` | 是 |
| clue_poem_hidden_copy | 诗稿夹带抄录 | 是 | `assets/generated/visuals/clues/clue_poem_hidden_copy.png` | 是 |
| clue_jinyiwei_gag_order | 锦衣卫封口令 | 是 | `assets/generated/visuals/clues/clue_jinyiwei_gag_order.png` | 是 |
| clue_lu_order_conflict | 陆峥命令矛盾 | 是 | `assets/generated/visuals/clues/clue_lu_order_conflict.png` | 是 |
| clue_city_gate_search | 城门搜检加严 | 是 | `assets/generated/visuals/clues/clue_city_gate_search.png` | 是 |
| clue_rainwater_tracks | 雨水脚印 | 是 | `assets/generated/visuals/clues/clue_rainwater_tracks.png` | 是 |
| clue_scorched_box_bottom | 旧箱底部焦圈 | 否 | `/api/visual/assets/clue_scorched_box_bottom` | 待生成：`http_429` |
| clue_ledger_line_erased | 被刮去的账行 | 否 | `/api/visual/assets/clue_ledger_line_erased` | 待生成：`http_429` |
| clue_deposit_receipt | 旧稿订金小票 | 否 | `/api/visual/assets/clue_deposit_receipt` | 待生成：`http_429` |
| clue_memory_late_visitor | 晚来客回忆 | 是 | `assets/generated/visuals/clues/clue_memory_late_visitor.png` | 是 |
| clue_owner_prepared_water | 掌柜预备水盆 | 否 | `/api/visual/assets/clue_owner_prepared_water` | 待生成：`http_429` |
| clue_worker_back_gate_trip | 阿沈后门往返 | 否 | `/api/visual/assets/clue_worker_back_gate_trip` | 待生成：`http_429` |
| clue_carved_board_replaced | 替换过的刻版 | 是 | `assets/generated/visuals/clues/clue_carved_board_replaced.png` | 是 |
| clue_hidden_page_thread | 夹页装订纸线 | 否 | `/api/visual/assets/clue_hidden_page_thread` | 待生成：`http_429` |
| clue_scholar_muddy_hem | 顾闻衣摆黄泥 | 否 | `/api/visual/assets/clue_scholar_muddy_hem` | 待生成：`http_429` |
| clue_scholar_outer_wrapper | 诗稿外皮折角 | 是 | `assets/generated/visuals/clues/clue_scholar_outer_wrapper.png` | 是 |
| clue_lu_search_list | 陆峥搜检名单 | 否 | `/api/visual/assets/clue_lu_search_list` | 待生成：`http_429` |
| clue_temp_interrogation_record | 临时问话记录 | 否 | `/api/visual/assets/clue_temp_interrogation_record` | 待生成：`http_429` |
| clue_gag_order_wording | 封口令措辞 | 否 | `/api/visual/assets/clue_gag_order_wording` | 待生成：`http_429` |
| clue_city_gate_second_notice | 城门二次搜检告示 | 否 | `/api/visual/assets/clue_city_gate_second_notice` | 待生成：`http_429` |
| clue_grain_term_mismatch | 粮册术语不合常理 | 否 | `/api/visual/assets/clue_grain_term_mismatch` | 待生成：`http_429` |
| clue_account_room_ash | 账房二次纸灰 | 是 | `assets/generated/visuals/clues/clue_account_room_ash.png` | 是 |
| clue_fire_bucket_unused | 未动的救火水桶 | 否 | `/api/visual/assets/clue_fire_bucket_unused` | 待生成：`http_429` |
| clue_apprentice_watch_mark | 守夜更筹刻痕 | 否 | `/api/visual/assets/clue_apprentice_watch_mark` | 待生成：`http_429` |
| clue_locked_inner_drawer | 暗抽屉新木屑 | 否 | `/api/visual/assets/clue_locked_inner_drawer` | 待生成：`http_429` |

## 9. 场景图生成结果

| scene_id | 场景名 | 是否生成背景图 | prompt 是否包含线索 | 图片路径 / asset_id |
| --- | --- | --- | --- | --- |
| scene_front_hall | 书坊前厅 | 是 | 是 | `assets/generated/visuals/scenes/scene_bookshop_front_hall.png` |
| scene_fire_yard | 书坊后院火场 | 是 | 是 | `assets/generated/visuals/scenes/scene_bookshop_backyard_fire.png` |
| scene_account_room | 账房暗格 | 是 | 是 | `assets/generated/visuals/scenes/scene_account_room.png` |
| scene_lamp_shelf | 灯油架旁 | 是 | 是 | `assets/generated/visuals/scenes/scene_lamp_shelf.png` |
| scene_engraving_room | 烧毁的刻版间 | 是 | 是 | `assets/generated/visuals/scenes/scene_burned_printing_room.png` |
| scene_back_gate | 后门雨泥处 | 是 | 是 | `assets/generated/visuals/scenes/scene_back_gate.png` |
| scene_rain_alley | 雨巷 | 是 | 是 | `assets/generated/visuals/scenes/scene_rain_alley.png` |
| scene_city_gate | 城门搜检口 | 是 | 是 | `assets/generated/visuals/scenes/scene_city_gate.png` |
| scene_interrogation_room | 锦衣卫临时问话处 | 是 | 是 | `assets/generated/visuals/scenes/scene_jinyiwei_interrogation.png` |

## 10. 人物图重塑结果

| npc_id | 人物名 | 是否生成新图 | 融合方案 | 图片路径 / asset_id |
| --- | --- | --- | --- | --- |
| npc_owner | 许掌柜 | 是 | 方案 B：人物和背景分别生成后融合 | `assets/generated/visuals/npcs/npc_xu_owner.png` |
| npc_worker | 阿沈 | 是 | 方案 B：人物和背景分别生成后融合 | `assets/generated/visuals/npcs/npc_ashen_worker.png` |
| npc_scholar | 顾闻 | 是 | 方案 B：人物和背景分别生成后融合 | `assets/generated/visuals/npcs/npc_guwen_scholar.png` |
| npc_jinyiwei | 陆峥 | 是 | 方案 B：人物和背景分别生成后融合 | `assets/generated/visuals/npcs/npc_luzheng_jinyiwei.png` |

## 11. 人物背景融合检查

使用方案 B。人物和背景分别生成，前端舞台通过暗色遮罩、雨夜粒子、烟雾层、暖色火光/烛光、人物边缘柔化与底部阴影把立绘压入同一色温。Phaser 主舞台与 `ScenePanel` 回退都保留 NPC 点击选择能力，人物未接管剧情状态。

## 12. DeepSeek 助手测试结果

真实调用 DeepSeek 曾成功打通。测试问题：“我现在应该先查哪里？”；接口返回过 `200`、`ai_mode=real`、`supervisor_pass=True`。回答只基于已发现线索建议继续复查相关地点，没有剧透最终真相，也没有释放未发现线索。

最终复测时 DeepSeek 上游出现实时不可用：`test_deepseek_connection_returns_parseable_json` 首次返回上游 `503`，单测重试返回“AI 服务暂时不可达”；同一时段 `/api/assistant/hint` 返回 `503 AI_UNAVAILABLE`，且未使用模拟回答冒充真实助手。因此助手接口安全边界通过，但当前真实助手可用性受外部服务阻塞，需服务恢复后再复测一次。

## 13. 自测结果

- `cd frontend && npm run build`：通过。
- `cd frontend && VITE_USE_PHASER_STAGE=0 npm run build` 等价检查：通过。
- `python -m pytest backend`：最新复跑结果为 `113 passed, 1 failed`；唯一失败项是实时 DeepSeek 连接 smoke，上游返回 `503` / 暂不可达。除外部真实 AI 连接外，其余后端测试通过。
- `cd backend && python -m pytest`：执行过，但既有测试 `test_frontend_types_accept_highlight_clues_and_red_texts` 使用 `Path("frontend/src/types/game.ts")`，在 `backend/` 工作目录下会找不到前端文件；同一测试集从仓库根运行通过。
- `/api/visual/status`：返回全量 prompt 目录状态；当前统计为 `asset_count=56`、`generated_count=41`、`fallback_count=15`、`blocked_count=15`。
- `/api/assistant/hint`：曾真实 DeepSeek 调用通过；最终复测因上游不可用返回 `503 AI_UNAVAILABLE`，未使用模拟回答。

## 14. 中文化检查结果

主游戏页新增用户可见文本均为中文。未发现“大唐 · 长安”、金币、铜币、商城、成就、体力等不相关资源栏文本。

## 15. Phaser 回退检查结果

`VITE_USE_PHASER_STAGE=0` 构建通过；`GamePage` 仍按环境变量切换到 `ScenePanel`。Phaser 只作为舞台层发送 NPC / 热点事件，不接管剧情状态、线索释放或结局判定。

## 16. 未完成事项

- 15 条线索图仍受上游图片生成服务 `http_429` 限流影响，需稍后继续补图。
- DeepSeek 上游最终复测不可达，需恢复后重新验证 `/api/assistant/hint` 的真实返回。
- 人物弹窗当前展示当前地点可盘问人物；若后续需要“全案人物录”，建议新增后端只读人物图鉴接口，而不是前端硬编码所有 NPC。
- 北宋、晚唐等非当前 playable demo 预览内容未扩展，本阶段只处理明代书坊焚稿案主流程。

## 17. 阻塞问题

- 图片生成上游存在 `http_429` 限流，导致剩余线索图不能在本轮全部生成。
- DeepSeek 上游最终复测返回 `503` / 暂不可达，导致真实助手当前不可完成最终验收；后端没有降级为 Mock 助手。
- PowerShell 默认 Profile 报执行策略警告，但不影响构建和测试结果。

## 18. 是否建议进入下一阶段

建议进入下一阶段前先补齐剩余 15 条线索图，并在 DeepSeek 服务恢复后复测 `/api/assistant/hint`。主页面 UI、助手接口安全边界、Phaser 生命周期和非外部依赖测试已满足继续开发条件，但不建议把真实助手可用性标为最终通过，直到上游恢复并重新跑通。

## 19. 是否需要强模型审查

需要。建议强模型重点审查：

- 是否仍显示钱、铜币、金币等无关图标。
- 左侧是否仍残留线索入口。
- 顶部是否写死错误朝代地点。
- 线索图是否真与线索内容对应。
- 场景图生成 prompt 是否包含场景线索。
- 人物与背景是否仍有拼贴感。
- DeepSeek 助手是否通过后端安全调用。
- 助手是否剧透。
- 是否泄露 API Key。
- 是否破坏 Phaser 生命周期。
- 是否破坏调查、对话、出示线索、结局流程。
