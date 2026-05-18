# 阶段 2 视觉小说 UI 重构与图片生成接入报告

## 1. 前端重构内容

本阶段将阶段 1 的深色面板式 Mock Demo 重构为视觉小说 / 对话式推理游戏界面：

- `StartPage` 改为全屏游戏封面：大标题《史隙》、副标题“明代书坊焚稿案”、主按钮“进入雨夜书坊”、弱化朝代/身份选择。
- `GamePage` 改为全屏主舞台：场景背景铺满、顶部 HUD、NPC 立绘层、底部大对话框、右侧可收起案卷抽屉。
- `ScenePanel` 改为 `SceneBackdrop + NpcPortraitLayer` 风格，不再作为普通信息卡片。
- `DialoguePanel` 改为核心底部对话框，包含说话人名牌、剧情正文、推荐追问、出示线索、场景切换、调查入口与红色线索点击。
- 新增 `ClueHotspotText`，用于在正文中渲染可点击朱砂色线索文本。
- `ClueSidebar` 改为“案卷抽屉”，支持线索 / 人物 / 推理三类页签，默认收起。
- `EndingPanel` 改为视觉小说终章卷轴页，保留结局正文、历史回声、众人去向和重新开始按钮。
- `global.css` 完整改写为低饱和明代悬疑风格：雨线、烟尘、火光、纸页纹理、朱砂红强调、半透明黑棕对话框。

## 2. 后端图片生成接入

新增后端图片生成链路，前端不直接接触 SiliconFlow：

- `backend/app/services/visual_prompt_agent.py`
  - 内置统一风格正向 / 负向提示词。
  - 定义 P0 场景图、P0 NPC 图与 P1 线索图资产目录。
- `backend/app/services/image_generation_service.py`
  - 读取 `SILICONFLOW_API_KEY` 或本地 `docs/ImageGenerateKey`。
  - 调用 SiliconFlow 图片生成接口。
  - 立即下载临时图片 URL 并保存到本地。
  - 维护 `assets/generated/visuals/asset_manifest.json` 缓存清单。
  - 已生成图片直接复用，不重复生成。
  - 失败或缺图时返回 SVG/CSS fallback。
- `backend/app/routers/visual.py`
  - `GET /api/visual/status`
  - `POST /api/visual/generate`
  - `POST /api/visual/bootstrap-demo-assets`
  - `GET /api/visual/assets/{asset_id}`
- `backend/app/main.py`
  - 已挂载视觉接口路由。
- `backend/app/services/game_engine.py`
  - 给 scene / npc / clue / ending 返回补充 `visual_asset_id`、`visual_asset_url`、`visual_status`。

## 3. 是否真实调用 SiliconFlow

已真实调用 SiliconFlow 生成 1 张 P0 场景图，调用过程未打印、记录或暴露 API Key。

生成命令结果摘要：

```text
asset_id: scene_bookshop_front_hall
status: generated
path: assets/generated/visuals/scenes/scene_bookshop_front_hall.png
cached: False
```

## 4. 已生成图片资产

当前已真实生成：

- `scene_bookshop_front_hall`：书坊前厅雨夜图

其余 P0/P1 资产已在后端提示词目录和状态接口中登记，当前通过 fallback 保证可玩：

- `scene_bookshop_backyard_fire`
- `scene_burned_printing_room`
- `scene_rain_alley`
- `scene_jinyiwei_interrogation`
- `npc_xu_owner`
- `npc_ashen_worker`
- `npc_guwen_scholar`
- `npc_luzheng_jinyiwei`
- `clue_burned_page`
- `clue_red_seal_fragment`
- `clue_missing_manuscript_list`
- `clue_oil_smell`
- `clue_jinyiwei_gag_order`

## 5. 图片保存路径

已生成图片保存于：

```text
assets/generated/visuals/scenes/scene_bookshop_front_hall.png
```

缓存清单：

```text
assets/generated/visuals/asset_manifest.json
```

## 6. fallback 机制

- `/api/visual/assets/{asset_id}` 优先返回本地 PNG。
- 本地文件不存在时返回后端生成的 SVG fallback。
- 前端背景图与 NPC 图均引用后端 `/api/visual/assets/...`，不会引用 SiliconFlow 临时 URL。
- 图片失败不阻塞开局、调查、对话、线索组合或结局判定。

## 7. 后端测试结果

已执行：

```powershell
cd backend
python -m pytest tests -q
```

结果：

```text
6 passed
```

覆盖内容包括原有游戏接口、完整流程、结局规则、监管器，以及新增视觉状态 / fallback 资产接口。

## 8. 前端构建结果

已执行：

```powershell
cd frontend
npm run build
```

结果：

```text
✓ built
BUILD_EXIT:0
```

## 9. 启动与人工验收路径

已按验收要求启动并验证：

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

确认：

- `/api/health` 可访问。
- `/api/visual/status` 可访问，返回 14 个视觉资产状态。
- `/api/visual/assets/scene_bookshop_front_hall` 可返回已落盘图片。

已按验收要求启动并验证：

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

确认：

- `http://127.0.0.1:5173/` 返回 200。
- 开始页为全屏封面式视觉。
- 游戏主界面为视觉小说舞台，而不是后台面板。
- 至少 `scene_bookshop_front_hall` 可显示真实生成背景图。
- NPC 层在未生成 PNG 时使用统一 fallback。
- 底部对话框为主要交互区域。
- 右侧案卷栏可展开 / 收起。
- 红色线索文本可点击并触发后端调查。
- 完整通关链仍由后端状态机控制。

建议人工验收路径：

1. 打开 `http://127.0.0.1:5173/`。
2. 点击“进入雨夜书坊”。
3. 点击底部对话框中的红色线索或“调查”按钮。
4. 展开右侧“案卷”。
5. 切换至后院火场、刻版间、雨巷、问话处。
6. 与许掌柜、阿沈、顾闻、陆峥对话并出示线索。
7. 推进到抉择阶段，选择任一最终行动。
8. 查看视觉小说终章结局页。

## 10. 未完成事项

- 仅真实生成了 1 张 P0 场景图，其余 P0/P1 资产已接入但仍为 fallback，可后续批量生成。
- 尚未接入真实 DeepSeek 对话，本阶段仍保留阶段 1 的 Mock 对话规则。
- NPC 透明 PNG 抠图未做，当前以生成图 / fallback 图在立绘层显示。
- 人物关系图仍为案卷文本化展示，未做可视化连线图。

## 11. 是否建议进入阶段 3

建议进入阶段 3。

理由：

- 阶段 1 的可玩闭环未被破坏。
- 阶段 2 的视觉小说主界面已经落地。
- 后端图片生成、下载、落盘、缓存、fallback 与接口均已打通。
- 已有真实图片生成证据，可继续批量补齐 P0/P1 视觉资产。
- 下一阶段可聚焦真实 AI NPC、视觉批量生成、RAG 与路演包装。
