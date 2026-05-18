# 阶段 8 完成报告：AI 关键视觉、视觉资产落地与演示美术稳定化

## 1. 已完成内容

- 梳理并增强了现有后端视觉链路，保留并继续使用 `GET /api/visual/status`、`GET /api/visual/assets/{asset_id}`、`POST /api/visual/generate`、`POST /api/visual/bootstrap-demo-assets`。
- 固化阶段 8 明代书坊焚稿案视觉资产清单，接口返回 `asset_type`、`display_name`、`description`、`fallback_path`、`generated_path`、`status`、`generation_status`、`blocked` 等字段。
- 增加阶段 8 推荐资产 ID 与旧资产 ID 的兼容映射，保留既有已生成资源，不破坏旧入口。
- 后端图片生成服务改为显式区分“已生成 / fallback / blocked”，无 Key、服务关闭、接口异常或下载异常时只返回中文阻塞说明和 fallback，不伪造成功。
- 继续增强图片响应解析，兼容 `images` / `data`、`url` / `image_url`、base64 / data URL 等常见返回形态；仍不记录授权头、临时图片 URL 或原始响应正文。

- 前端场景、人物、线索详情均优先展示后端视觉资产接口返回的生成图或 SVG 占位图，图片缺失不阻断游戏流程。
- 移除前端人物区域自动触发图片生成的行为，避免浏览器侧间接制造不可控真实生图请求。
- 新增后端视觉状态、图片生成服务、fallback、真实图片生成 smoke 测试。
- 执行真实 SiliconFlow smoke：检测到图片生成凭据后已尝试真实接口；本次线索图生成未成功落盘，服务明确记录为 blocked 并使用 fallback。

文档与代码差异说明：`CODEBUDDY.md` 仍描述仓库偏文档优先，但当前实际仓库已有前后端、测试、视觉接口与已生成资源，本阶段以实际代码结构为准。

## 2. 修改文件列表

- `backend/app/services/image_generation_service.py`
- `backend/app/services/visual_prompt_agent.py`
- `backend/app/services/game_engine.py`
- `frontend/src/components/scene/CharacterPortrait.tsx`
- `frontend/src/components/scene/ScenePanel.tsx`
- `frontend/src/components/clue/ClueSidebar.tsx`
- `frontend/src/styles/global.css`
- `backend/tests/test_visual_asset_status.py`
- `backend/tests/test_image_generation_service.py`
- `backend/tests/test_visual_fallback.py`
- `backend/tests/test_image_generation_real_smoke.py`
- `docs/periodPrompt/reports/stage_8_visual_asset_ai_report.md`

额外说明：`backend/app/services/game_engine.py` 不在优先修改范围内，但会话快照原先没有把 `_scene_payload()` 注入当前场景和可前往场景，导致前端拿不到场景视觉 URL。本次只做视觉字段注入，不改状态机、线索释放或结局逻辑。

## 3. 当前视觉资产链路

- 视觉状态接口：`GET /api/visual/status`
- 视觉资产接口：`GET /api/visual/assets/{asset_id}`
- 图片生成接口：`POST /api/visual/generate`
- 批量准备接口：`POST /api/visual/bootstrap-demo-assets`
- fallback 机制：后端优先返回本地 PNG；本地文件不存在时返回中文 SVG 占位图；图片生成受阻时返回 `status=fallback`、`generation_status=blocked`、`blocked=true` 和中文说明。
- 前端展示位置：
  - 场景背景：`frontend/src/components/scene/ScenePanel.tsx`
  - 人物立绘：`frontend/src/components/scene/CharacterPortrait.tsx`
  - 线索物品图：`frontend/src/components/clue/ClueSidebar.tsx`
- 资产目录：`assets/generated/visuals/`
- 资产清单：`assets/generated/visuals/asset_manifest.json`

## 4. 明代 Demo 视觉资产清单

| asset_id | 类型 | 中文名称 | 状态 | fallback | generated_path |
| --- | --- | --- | --- | --- | --- |
| `scene_bookshop_front_hall` | scene_background | 书坊前厅 | generated | `/api/visual/assets/scene_bookshop_front_hall` | `assets/generated/visuals/scenes/scene_bookshop_front_hall.png` |
| `scene_bookshop_fire_yard` | scene_background | 书坊后院火场 | fallback | `/api/visual/assets/scene_bookshop_fire_yard` | 无 |
| `scene_bookshop_engraving_room` | scene_background | 烧毁的刻版间 | fallback | `/api/visual/assets/scene_bookshop_engraving_room` | 无 |
| `scene_interrogation_room` | scene_background | 锦衣卫临时问话处 | fallback | `/api/visual/assets/scene_interrogation_room` | 无 |
| `npc_owner_xu` | npc_portrait | 许掌柜 | generated | `/api/visual/assets/npc_owner_xu` | `assets/generated/visuals/npcs/npc_xu_owner.png` |
| `npc_worker_ashen` | npc_portrait | 阿沈 | generated | `/api/visual/assets/npc_worker_ashen` | `assets/generated/visuals/npcs/npc_ashen_worker.png` |
| `npc_jinyiwei_lu` | npc_portrait | 陆峥 | generated | `/api/visual/assets/npc_jinyiwei_lu` | `assets/generated/visuals/npcs/npc_luzheng_jinyiwei.png` |
| `clue_burned_page` | clue_item | 烧焦残页 | fallback / blocked | `/api/visual/assets/clue_burned_page` | 无 |
| `clue_red_seal` | clue_item | 半枚红印纸角 | fallback | `/api/visual/assets/clue_red_seal` | 无 |
| `clue_jinyiwei_gag_order` | clue_item | 锦衣卫封口令 | fallback | `/api/visual/assets/clue_jinyiwei_gag_order` | 无 |

补充资产：`scene_rain_alley`、`npc_scholar_guwen`、`clue_missing_manuscript_list`、`clue_oil_smell` 仍保留在状态接口中；其中顾闻已有本地生成图，其余走 fallback。

## 5. 图片生成 Prompt 结果

- 是否统一风格：是。继续使用低饱和国风、暗色历史悬疑、雨夜、火光、烟气、明代书坊、视觉小说风格。
- 是否包含负面约束：是。已补充现代城市、现代服饰、电灯、霓虹、汽车、枪械、手机、清代辫发、八旗、日式武士、现代警察、民国服饰、英文标牌、血腥和色情等负面项。
- 是否避免现代元素：是，Prompt 与负面约束均覆盖。
- 是否避免错朝代元素：是，Prompt 明确 Ming dynasty，负面约束覆盖清代、民国、日式武士等错代元素。
- 是否未暴露 Key：是。Prompt、manifest、报告均不包含凭据内容或完整认证头。

## 6. 图片生成接入结果

- Provider：`siliconflow`
- 是否后端读取 Key：是。优先读环境变量，其次读 `backend/.env`，再按既有本机开发兜底读取本地 Key 文件；只返回“是否存在”的布尔状态。
- 是否前端不接触 Key：是。前端只请求本项目后端 `/api/visual/*`。
- 是否真实调用：是。本次真实 smoke 检测到凭据后尝试调用真实 SiliconFlow 图片接口。
- 无 Key 时行为：返回 `status=fallback`、`generation_status=blocked`、`blocked=true`，中文提示“未检测到图片生成 Key，已使用本地视觉占位。”
- API 失败时行为：返回 `status=fallback`、`generation_status=blocked`、`blocked=true`，不阻断主流程，不写入凭据。
- 是否保存本地图片：已有场景图和人物图已在本地；本次线索图真实生成未成功保存。
- 保存路径：
  - `assets/generated/visuals/scenes/scene_bookshop_front_hall.png`
  - `assets/generated/visuals/npcs/npc_xu_owner.png`
  - `assets/generated/visuals/npcs/npc_ashen_worker.png`
  - `assets/generated/visuals/npcs/npc_luzheng_jinyiwei.png`
  - `assets/generated/visuals/npcs/npc_guwen_scholar.png`

## 7. 前端展示结果

- 场景背景：`ScenePanel` 使用 `visual_asset_url` 或 `/api/visual/assets/{asset_id}`，优先展示生成图，缺失时显示后端 SVG 占位图。
- NPC 图：`CharacterPortrait` 使用后端视觉资产 URL；不再由前端自动触发生图；图片加载失败时回到 CSS 剪影。
- 线索图：`ClueSidebar` 的线索详情新增线索图区域，存在视觉资产 URL 时展示图片；加载失败时显示中文提示。
- 图片缺失 fallback：后端 SVG 占位 + 前端 CSS 剪影/中文提示双保险。
- 用户可见中文检查：本阶段新增用户可见文案均为中文；代码变量名和内部类型名仍使用英文。

## 8. 自测结果

- 后端视觉测试：`cd backend; python -m pytest tests/test_visual_asset_status.py tests/test_image_generation_service.py tests/test_visual_fallback.py -q --basetemp ../.pytest_tmp_visual`，结果 `6 passed`。
- 后端完整测试：`cd backend; python -m pytest tests -q --basetemp ../.pytest_tmp`，结果 `52 passed, 2 skipped`。
- 真实图片生成 smoke：`cd backend; $env:IMAGE_PROVIDER="siliconflow"; python -m pytest tests/test_image_generation_real_smoke.py -q --basetemp ../.pytest_tmp_image_real`，结果 `1 passed`；继续增强解析后重跑 `tests/test_image_generation_real_smoke.py`，结果仍为 `1 passed`。测试通过表示真实调用路径被执行且失败时显式 blocked，不表示线索图成功落盘。
- 图片解析增强回归：`cd backend; python -m pytest tests/test_image_generation_service.py tests/test_visual_fallback.py -q --basetemp ../.pytest_tmp_image_service`，结果 `4 passed`。

- 前端构建：`cd frontend; npm run build`，结果通过。
- Key 泄露扫描：扫描 `backend/logs`、`assets`、`docs/periodPrompt/reports` 后未发现真实凭据；命中项均为旧报告中的占位描述或文档说明，不是实际密钥或完整认证头。

## 9. 中文化检查结果

- 后端新增响应文案：中文。
- 前端新增状态文案：中文，包括“已生成场景”“视觉占位场景”“已生成线索图”“线索占位图”“线索图暂不可用，已保留文字证据。”
- SVG fallback 可见文案：中文，已去掉可见英文 fallback。
- 代码内部变量、类型名、CSS 类名仍使用英文，仅作为内部实现。

## 10. 人工验收方法

1. 启动后端：

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

2. 查看视觉状态：

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/visual/status
```

期望：返回阶段 8 资产清单，`display_name` 与 `description` 为中文，`generated_path` 或 `fallback_path` 可见，不出现凭据内容。

3. 查看单个图片或占位图：

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/api/visual/assets/scene_bookshop_front_hall -OutFile .\front_hall_check.png
```

期望：已生成图可下载；若请求缺失资产，则浏览器中显示中文 SVG 占位图。

4. 启动前端：

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

5. 打开 `http://127.0.0.1:5173/`，选择“明代 / 书坊学徒”，进入主线。

期望：

- 主舞台显示书坊前厅生成图或视觉占位图；
- 人物区域显示许掌柜、阿沈、陆峥等生成图或剪影；
- 调查获得线索后，在右侧“线索”详情中看到线索图或中文占位提示；
- 图片缺失不影响调查、对话、线索组合和结局。

6. 验证真实生图：

```powershell
cd backend
$env:IMAGE_PROVIDER="siliconflow"
python -m pytest tests/test_image_generation_real_smoke.py -q --basetemp ../.pytest_tmp_image_real
```

判断方式：无凭据则跳过；有凭据则尝试真实接口；成功时本地保存图片；失败时必须显示 blocked/fallback，不能写真实成功。

## 11. 图片生成测试结果

- 测试时间：2026-05-16 01:00 左右
- 测试接口：`POST https://api.siliconflow.cn/v1/images/generations`
- 输入摘要：生成 `clue_burned_page`，中文名“烧焦残页”，类型 `clue_item`，风格为明代书坊悬疑线索物品图。
- 是否调用真实 API：是。测试未使用本地 Mock 冒充成功。
- 是否成功：否。本次未得到可保存的本地线索图片。
- 保存路径：无新增线索图保存路径。
- 是否 fallback：是，`clue_burned_page` 当前为 `fallback / blocked`。
- 问题：继续增强解析后，服务记录安全错误码 `invalid_image_content`，表示下载到的内容未被后端识别为图片内容；为避免泄露临时 URL、响应正文和授权信息，manifest 只保留安全错误码。
- 下一步建议：确认 SiliconFlow 图片模型权限、参数兼容性、返回结构和图片下载地址可访问性；必要时切换到平台当前推荐的图片模型或调整尺寸参数后重跑 smoke。


## 12. 未完成事项

- 本次真实 smoke 未成功落盘线索图，因此线索图仍由 SVG fallback 支撑演示。
- 后院火场、刻版间、问话处等场景仍主要走 fallback，后续可在接口恢复稳定后逐张生成。
- 未制作静态 PNG 占位图；当前 fallback 为后端 SVG 与前端 CSS 剪影。

## 13. 阻塞问题

- 真实图片生成链路已尝试，但 `clue_burned_page` 未成功保存本地图片，当前阻塞点为 SiliconFlow 下载结果未被识别为图片内容，安全错误码为 `invalid_image_content`。

- 该阻塞不影响游戏主流程；场景图、人物图已有本地生成资源，线索图使用中文 fallback。

## 14. 是否建议进入下一阶段

建议在修复真实线索图生成阻塞后再进入下一阶段。如果路演时间紧，可先使用当前“场景 + 人物生成图 + 线索 fallback”的稳定闭环进行演示，但不要宣称线索图真实生成成功。

## 15. 是否需要强模型审查

本阶段涉及真实图片生成、视觉资产展示、Key 安全和路演体验，建议强模型审查。
