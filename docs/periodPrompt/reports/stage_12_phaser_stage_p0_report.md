# 阶段完成报告

## 1. 已完成内容

- 已在 `frontend` 安装并接入 `phaser`，`package.json` 和 `package-lock.json` 已更新。
- 已新增默认启用的 `PhaserStage`，并通过 `VITE_USE_PHASER_STAGE=0` 保留旧 `ScenePanel` 回退路径。
- 已新增最小 Phaser 目录结构，Phaser 只负责舞台渲染、热点点击事件、NPC 点击事件和视觉反馈。
- 已实现当前场景背景、NPC 立绘或中文剪影 fallback、场景热点中文标签。
- 已实现热点点击后回到 React 的 `onInspect(sceneId, hotspotId, clueId)`，NPC 点击后回到 React 的 `onSelectNpc(npcId)`。
- 已实现 `snapshot` 更新时通过 `game.events.emit("snapshot:update", payload)` 刷新舞台，不在每次 React render 重新创建 `Phaser.Game`。
- 已实现场景暗场转场、热点闪光与轻微镜头推进、新线索闪光反馈，并加入轻量雨线、烟雾和火光氛围。
- 已保留 `DialoguePanel`、`ClueSidebar`、`EndingPanel` 的 React 流程，未修改后端接口合约。
- 当前结构确认：`snapshot.scene` 提供场景 id、名称、描述、`visual_asset_url`、`visual_asset_id` 和 `hotspots`；`snapshot.scene_npcs` 提供当前场景 NPC；`scene.hotspots` 提供 `id`、`label`、`clue_ids`，当前无坐标字段，Phaser 使用稳定预设位置；图片 URL 继续通过 `resolveApiUrl` 处理 `/api/visual/assets/*`。

## 2. 修改文件列表

- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/pages/GamePage.tsx`
- `frontend/src/components/scene/PhaserStage.tsx`
- `frontend/src/game/phaserGame.ts`
- `frontend/src/game/events.ts`
- `frontend/src/game/scenes/MainScene.ts`
- `frontend/src/game/objects/Hotspot.ts`
- `frontend/src/game/objects/NPCSprite.ts`
- `frontend/src/styles/global.css`
- `docs/periodPrompt/reports/stage_12_phaser_stage_p0_report.md`

未修改 `backend/`、API 合约、对话组件、线索组件、结局组件，也未删除旧 `ScenePanel.tsx`。

## 3. Phaser 接入结构

- `phaserGame.ts` 只负责创建 `Phaser.Game`，使用传入 DOM 容器作为 parent，启用 `RESIZE` 缩放，并把初始 payload 放入 registry。
- `events.ts` 定义内部事件：`snapshot:update`、`hotspot:clicked`、`npc:clicked`。
- `PhaserStage.tsx` 在挂载时创建一次 `Phaser.Game`，卸载时移除监听并 `game.destroy(true)`；React props 变化时只向 `game.events` 发送 `snapshot:update`。
- `MainScene.ts` 监听 `snapshot:update` 后重绘背景、NPC、热点和反馈；仅保存上一帧场景 id 和线索 id 用于视觉 diff，不保存权威剧情状态。
- `Hotspot.ts` 点击后通过 `game.events.emit("hotspot:clicked", payload)` 把 `sceneId`、`hotspotId`、`clueId` 交还 React。
- `NPCSprite.ts` 点击后通过 `game.events.emit("npc:clicked", payload)` 把 `npcId` 交还 React。

事件流为：React `snapshot` / 选中 NPC / busy 状态变化 -> `PhaserStage` 发 `snapshot:update` -> `MainScene` 刷新舞台；玩家点击热点或 NPC -> Phaser 发事件 -> `PhaserStage` 调用现有 React handler -> 现有 API helper 和主状态继续处理。

## 4. 自测结果

- 已执行 `cd frontend; npm install phaser`。首次沙箱内执行因本机 `D:\node_cache` 权限失败；经授权后执行成功。
- 已执行 `cd frontend; npm run build`，构建通过。Vite 对 Phaser 大体积 chunk 给出体积提示，但不是构建失败。
- 已执行 `VITE_USE_PHASER_STAGE=0` 回退构建，旧 `ScenePanel` 路径构建通过。
- 已做新增前端源码的英文用户可见文本搜索，命中均为 TypeScript 类型名、组件名、文件名或 Phaser 内部值，例如 `SessionSnapshot`、`ClueSidebar`、`NPCSprite`、`Back.easeOut`，未发现新增用户可见英文文案。
- 已做新增 Phaser 代码的业务 API 搜索，未发现 `fetch`、调查接口、对话接口、AI 调用、`stage_cue`、Zustand 或 Redux；仅复用 `/api/visual/assets/*` 视觉资产 URL。
- 已做后端 API 辅助 smoke：创建明代书坊焚稿案会话并调用 `/api/investigate`，现有调查流程可返回新线索。
- 浏览器 smoke 已进入首页，选择“明代”，进入“书坊焚稿案”生成页并看到“开始游戏”。继续点击时浏览器自动化工具因额度限制拒绝执行，因此未能在工具内完成 Phaser 舞台可见性、热点点击、线索栏和对话面板的完整人工链路验证。
- 未执行后端 pytest，因为本阶段未修改后端或共享数据。

## 5. 中文化检查结果

- Phaser 热点标签来自 `scene.hotspots[].label`，沿用中文数据。
- Phaser fallback 文案使用中文，例如“案场影像未就绪”“暂无可查之处”。
- React 叠加 HUD 使用中文场景名、阶段名和“调查中”状态。
- 新增前端源码未发现新增用户可见英文文本。

## 6. AI 接入测试结果

本阶段不新增 AI 接入，不读取、不打印、不复制任何 API Key。Phaser 不调用 AI，也不调用对话、调查、结局等业务 API；既有 Mock / 真实 AI fallback 路径未被本阶段修改。

## 7. 图片生成测试结果

本阶段不新增图片生成。Phaser 复用既有 `visual_asset_url`、`visual_asset_id`、NPC 立绘字段和 `/api/visual/assets/*` 资源；资源缺失或加载失败时使用中文暗场 fallback 和 NPC 中文姓名剪影。

## 8. 人工验收方法

1. `cd frontend`
2. `npm install`
3. 启动后端：`cd backend; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
4. 启动前端：`cd frontend; npm run dev -- --host 127.0.0.1 --port 5173`
5. 打开 `http://127.0.0.1:5173/`。
6. 选择“明代”，进入“书坊焚稿案”。
7. 确认主舞台为 Phaser canvas，背景、NPC 和中文热点可见。
8. 点击至少一个中文热点，确认仍触发现有调查流程并在底部对话或右侧线索栏看到中文反馈。
9. 切换 NPC，确认 Phaser 舞台 NPC 高亮变化。
10. 切换场景，确认有暗场淡入淡出。
11. 设置 `VITE_USE_PHASER_STAGE=0` 后重启前端，确认旧 React `ScenePanel` 可回退。

## 9. 未完成事项

- 受浏览器自动化工具额度限制，未能在工具内完成点击“开始游戏”后的完整 Phaser 舞台人工 smoke。源码、构建、回退构建和 API 辅助 smoke 已完成。
- 运行构建和开发服务产生了本地 `dist`、`.vite`、`.playwright-mcp`、`node_modules` 相关缓存/产物变更；这些不属于本阶段源码设计内容，后续提交前建议按项目习惯清理或忽略。

## 10. 阻塞问题

- 浏览器自动化工具在继续点击“开始游戏”时触发额度限制，阻止完整 UI smoke。
- 停止本次 smoke 启动的后端开发服务时，`taskkill` 被本机权限拒绝；再次提权停止时也被额度限制拒绝。需要人工确认本机 `127.0.0.1:8000` 开发服务是否仍在运行并手动停止。

## 11. 是否建议进入下一阶段

建议先完成一次人工浏览器 smoke 和强模型审查，通过后再进入下一阶段。当前代码层面的 P0 接入、构建和回退路径已完成。

## 12. 是否需要强模型审查

建议需要。重点审查：

- 是否不会每次 render 重复创建 `Phaser.Game`。
- 是否完整清理 `game.events` 监听和 `game.destroy(true)`。
- 是否保留旧 `ScenePanel` 回退。
- 是否无后端越权和业务 API 越权。
- 是否没有把剧情状态迁移到 Phaser。
- 是否热点点击仍回到现有 React `/api/investigate` 流程。
- 是否保持全中文用户可见文本。
- 是否没有 API Key 泄露风险。
- 是否前端构建通过。
