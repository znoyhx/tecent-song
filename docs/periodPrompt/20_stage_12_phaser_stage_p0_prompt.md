# 阶段 12：Phaser 可交互舞台 P0 Prompt

## 1. 你的角色

你是《史隙》Phaser 舞台接入执行模型。你的任务不是重做游戏系统，而是把当前 React 视觉小说舞台升级为 React + Phaser 混合叙事舞台。

本阶段只增强现有 `ScenePanel` 舞台层，让当前场景背景、NPC、调查热点、线索高亮、火光雨雾和转场反馈更像游戏。剧情状态、线索释放、NPC 权限、AI 调用和结局判定仍然由现有 React + FastAPI 流程控制。

一句话边界：

> Phaser 是舞台，不是大脑；React 是界面，不是剧情裁判；FastAPI 是叙事中枢。

## 2. 必须先阅读的文档

必须阅读：

- `CODEBUDDY.md`
- `docs/PRD.md`
- `docs/develop/11_frontend_development_plan.md`
- `docs/develop/13_api_contracts.md`
- `docs/develop/16_visual_asset_plan.md`
- `docs/develop/17_testing_and_acceptance.md`
- `docs/periodPrompt/00_global_rules.md`
- 当前阶段 Prompt：`docs/periodPrompt/20_stage_12_phaser_stage_p0_prompt.md`
- 当前前端入口：`frontend/package.json`
- 当前主状态：`frontend/src/App.tsx`
- 当前游戏页：`frontend/src/pages/GamePage.tsx`
- 当前舞台：`frontend/src/components/scene/ScenePanel.tsx`
- 当前 NPC 立绘：`frontend/src/components/scene/CharacterPortrait.tsx`
- 当前类型：`frontend/src/types/game.ts`
- 当前 API helper：`frontend/src/api/client.ts`
- 当前样式：`frontend/src/styles/global.css`

如果文档、代码和当前数据结构冲突，先停止并报告冲突，不要自行重构目录。

## 3. 阶段目标

必须完成：

- 在 `frontend/` 安装并接入 `phaser`。
- 新增 `PhaserStage`，用于替换 / 增强现有 `ScenePanel`。
- 保留旧 `ScenePanel`，并提供回退开关。
- 新增最小 Phaser game / scene 结构。
- Phaser 舞台显示当前场景背景。
- Phaser 舞台显示当前 NPC 立绘或剪影。
- Phaser 舞台显示当前场景热点。
- 点击 Phaser 热点后仍走现有 `onInspect(sceneId, hotspotId, clueId)`。
- `DialoguePanel`、`ClueSidebar`、`EndingPanel` 功能不回退。
- `snapshot` 更新时刷新 Phaser 舞台，不重新创建 `Phaser.Game`。
- 场景变化时有淡入淡出或暗场转场。
- 新线索出现或热点点击后有轻量高亮 / 闪光 / 镜头推进反馈。
- 前端构建通过。

不完成：

- 不新增 `stage_cue` 后端字段。
- 不修改 FastAPI 接口合约。
- 不让 Phaser 直接请求 FastAPI。
- 不让 Phaser 直接请求 AI。
- 不把剧情状态迁移到 Phaser。
- 不引入 Zustand / Redux。
- 不重构 `App.tsx` 主状态。
- 不替换 `DialoguePanel`、`ClueSidebar`、`EndingPanel`。
- 不做角色行走、开放地图、复杂小游戏。
- 不做 Phaser 内长文本对话 UI。

## 4. 当前阶段禁止事项

- 禁止删除 `ScenePanel.tsx`。
- 禁止删除当前 React 对话、线索、结局逻辑。
- 禁止让 Phaser 保存权威剧情状态。
- 禁止让 Phaser 判断线索是否释放、阶段是否推进、结局是否触发。
- 禁止修改后端规则来迎合前端舞台。
- 禁止新增英文用户可见文本。
- 禁止把 API Key 写入前端、Markdown、日志或测试输出。
- 禁止为了接入 Phaser 大规模重写 CSS 和页面布局。
- 禁止破坏 Mock / fallback 可演示能力。
- 禁止在每次 React render 时重新创建 `Phaser.Game`。

## 5. 允许修改的文件范围

可创建/修改：

- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/pages/GamePage.tsx`
- `frontend/src/components/scene/PhaserStage.tsx`
- `frontend/src/components/scene/ScenePanel.tsx`（仅为导出、复用或轻量兼容，不删除旧逻辑）
- `frontend/src/game/phaserGame.ts`
- `frontend/src/game/events.ts`
- `frontend/src/game/scenes/MainScene.ts`
- `frontend/src/game/objects/Hotspot.ts`
- `frontend/src/game/objects/NPCSprite.ts`
- `frontend/src/styles/global.css`
- `frontend/src/types/game.ts`（仅当需要补充前端舞台类型，不能改 API 合约）
- 可新增前端测试或 smoke 辅助文件
- `docs/periodPrompt/reports/stage_12_phaser_stage_p0_report.md`

## 6. 不允许修改的文件范围

默认不允许修改：

- `docs/PRD.md`
- `CODEBUDDY.md`
- `docs/develop/*.md`
- `docs/DeepseekAPIKey`
- `docs/ImageGenerateKey`
- `backend/` 所有文件
- `frontend/src/components/dialogue/*`
- `frontend/src/components/clue/*`
- `frontend/src/components/ending/*`
- 无关页面、无关 Mock 数据、无关视觉资源

如果确实必须修改禁止范围内的文件，先报告原因、风险和最小改动方案，等待用户或上层模型确认。

## 7. 具体开发任务

### 任务 1：确认当前前端结构和依赖

- 任务目标：确认当前 `frontend/package.json`、`GamePage.tsx`、`ScenePanel.tsx`、`types/game.ts` 的真实状态。
- 输出：在报告中记录当前舞台组件、数据字段、热点字段、图片 URL 处理方式。
- 验收标准：明确 `snapshot.scene`、`snapshot.scene_npcs`、`scene.hotspots` 如何进入 Phaser。

### 任务 2：安装 Phaser

- 任务目标：把 `phaser` 加入 `frontend` 依赖。
- 命令建议：

```powershell
cd frontend
npm install phaser
```

- 验收标准：`frontend/package.json` 和 lockfile 更新，`npm run build` 能解析 `phaser`。
- 如果网络或权限导致安装失败，必须停止并报告，不得手写伪依赖或复制库代码。

### 任务 3：新增 Phaser 基础结构

- 任务目标：建立可维护的 Phaser 目录，不污染 React 组件。
- 推荐文件：

```text
frontend/src/game/phaserGame.ts
frontend/src/game/events.ts
frontend/src/game/scenes/MainScene.ts
frontend/src/game/objects/Hotspot.ts
frontend/src/game/objects/NPCSprite.ts
```

- 验收标准：
  - `createPhaserGame(container, initialSnapshot)` 或等价函数只负责创建 game。
  - `MainScene` 能接收 `snapshot:update`。
  - `Hotspot` 能发出 `hotspot:clicked`。
  - `NPCSprite` 能显示图片或稳定剪影 fallback。

### 任务 4：新增 PhaserStage React 桥

- 任务目标：用 React 管理 Phaser 生命周期和事件桥。
- 涉及文件：`frontend/src/components/scene/PhaserStage.tsx`。
- 必须实现：

```text
挂载时创建 Phaser.Game
卸载时 game.destroy(true)
snapshot 更新时 game.events.emit("snapshot:update", payload)
监听 game.events.on("hotspot:clicked", handler)
清理所有监听
```

- `PhaserStage` props 应复用现有 `ScenePanel` 的核心 props：

```ts
snapshot: SessionSnapshot;
selectedNpcId: string | null;
busy: boolean;
onSelectNpc: (npcId: string) => void;
onInspect: (sceneId: string, hotspotId: string, clueId?: string | null) => void;
```

- 验收标准：切换场景、切换 NPC、点击热点后 React 状态仍能正常更新。

### 任务 5：在 GamePage 中接入并保留回退

- 任务目标：将现有 `ScenePanel` 替换为可回退的 `PhaserStage`。
- 推荐开关：

```ts
const usePhaserStage = import.meta.env.VITE_USE_PHASER_STAGE !== '0';
```

- 默认使用 Phaser；当环境变量 `VITE_USE_PHASER_STAGE=0` 时回退到旧 `ScenePanel`。
- 验收标准：两种模式都可构建；回退模式不依赖 Phaser 运行时舞台事件。

### 任务 6：渲染背景、NPC 和热点

- 任务目标：Phaser 主舞台能表达当前 `snapshot`。
- 背景要求：
  - 优先使用 `scene.visual_asset_url`。
  - 其次使用 `/api/visual/assets/{visual_asset_id}`。
  - 图片加载失败时显示暗色历史悬疑 fallback，不出现英文。
- NPC 要求：
  - 使用现有 NPC 视觉字段：`visual_asset_url`、`visual_asset_id`、`portraitUrl`、`fallbackPortraitUrl` 等。
  - 缺图时用剪影或中文姓名印记。
  - 当前 `selectedNpcId` 有明显高亮。
  - 点击 NPC 可调用 `onSelectNpc(npcId)` 或通过事件桥触发。
- 热点要求：
  - 从 `scene.hotspots` 生成可点击区域。
  - 如果没有坐标，按热点 index 使用稳定预设位置。
  - 热点标签必须中文，来自数据字段 `label`。
  - 点击后使用第一个 `clue_ids[0]` 作为候选 clueId。

### 任务 7：舞台反馈与转场

- 任务目标：让舞台有最小游戏感。
- 必须实现至少三类反馈：
  - 场景变化：淡入淡出或暗场转场。
  - 热点点击：热点闪光或短暂高亮。
  - 新线索 / 当前热点：镜头推进、描边、闪光或轻微震动之一。
- 可实现轻量循环特效：
  - 雨线。
  - 烟雾。
  - 火光或灰烬。
- 验收标准：反馈不遮挡 React 对话框和线索栏，不造成文字难读。

### 任务 8：样式与响应式

- 任务目标：保持原有视觉小说布局，不因 Phaser canvas 挤压 UI。
- 涉及文件：`frontend/src/styles/global.css`。
- 要求：
  - Phaser canvas 铺满主舞台。
  - React 顶部 HUD、底部对话框、右侧线索栏仍在可读层级。
  - 移动端不出现明显重叠。
  - 不新增英文 UI 文本。

### 任务 9：验证与报告

- 任务目标：证明 Phaser P0 接入没有破坏主流程。
- 必须执行或说明无法执行原因：

```powershell
cd frontend
npm run build
```

如修改后端或共享数据，另执行：

```powershell
cd backend
python -m pytest
```

- 必须人工或浏览器 smoke：
  1. 启动后端。
  2. 启动前端。
  3. 进入明代书坊焚稿案。
  4. 确认看到 Phaser 舞台。
  5. 点击至少一个舞台热点。
  6. 确认仍调用现有调查流程并新增线索或显示中文反馈。
  7. 打开右侧线索栏，确认线索正常。
  8. 切换 `VITE_USE_PHASER_STAGE=0` 或等价开关，确认旧 `ScenePanel` 可回退。

## 8. 数据与接口要求

- 不得修改现有 API 合约。
- 不得新增后端必需字段。
- 不得要求后端返回 `stage_cue` 才能运行。
- `stage_cue` 只作为后续 P1 设计，不在本阶段实现。
- 本阶段 Phaser 反馈可以从现有前端状态推导：

| 条件 | 舞台反馈 |
| --- | --- |
| 点击热点 | 热点闪光 / 轻微镜头推进 |
| `scene_id` 变化 | 淡入淡出 |
| `selectedNpcId` 变化 | NPC 高亮变化 |
| 发现新线索 | 线索高亮 / 闪光 |
| 进入结局 | 淡出到 React 结局页 |

## 9. 中文化要求

所有用户可见文本必须中文，包括：

- Phaser 热点标签。
- Phaser fallback 文案。
- HUD 文案。
- 空状态。
- 加载失败提示。
- 按钮或提示。

允许保留英文：

- 文件名。
- 变量名。
- TypeScript 类型名。
- Phaser 内部事件名，如 `hotspot:clicked`、`snapshot:update`。

完成后必须检查新增前端代码中是否出现用户可见英文：`Start`、`Loading`、`Error`、`Submit`、`Continue`、`Inventory`、`Clue`、`NPC`、`Session`、`Choice`、`Ending`、`Back`、`Next`。

## 10. AI 接入要求

- 本阶段不新增真实 AI 能力。
- 本阶段不新增真实图片生成能力。
- 不读取、不打印、不复制任何 API Key。
- 如启动项目时真实 AI 不可用，必须确认 Mock / fallback 仍可演示。
- 不得声称本阶段完成了新的 AI 接入。

## 11. 模型必须执行的自测步骤

必须执行或说明无法执行原因：

- `cd frontend; npm install phaser`，如果依赖不存在。
- `cd frontend; npm run build`
- 搜索新增用户可见英文文本。
- 验证 `VITE_USE_PHASER_STAGE` 回退路径。
- 浏览器 smoke：进入明代主 Demo，点击至少一个 Phaser 热点。
- 确认 `DialoguePanel` 可继续追问。
- 确认 `ClueSidebar` 可继续打开、查看线索、提交推理。
- 确认 `EndingPanel` 仍可显示或未被本阶段破坏。
- 如无法执行浏览器 smoke，必须说明缺少什么环境和剩余风险。

## 12. 人工验收方式

用户可按以下步骤验收：

1. 安装依赖：

```powershell
cd frontend
npm install
```

2. 启动后端：

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

3. 启动前端：

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

4. 打开 `http://127.0.0.1:5173/`。
5. 选择“明代”，进入“书坊焚稿案”。
6. 确认主舞台是 Phaser 渲染，背景、NPC 和热点可见。
7. 点击舞台上的一个中文热点。
8. 确认底部对话 / 叙事反馈变更，右侧线索栏可看到新增线索或调查结果。
9. 切换 NPC，确认舞台 NPC 高亮变化。
10. 切换场景，确认有淡入淡出或暗场转场。
11. 设置 `VITE_USE_PHASER_STAGE=0` 后重启前端，确认旧 React `ScenePanel` 可回退。

本阶段不通过的情况：

- 点击 Phaser 热点没有进入现有调查流程。
- Phaser 直接请求后端或 AI。
- `DialoguePanel`、`ClueSidebar` 或 `EndingPanel` 功能消失。
- 旧 `ScenePanel` 无法回退。
- 前端构建失败。
- 页面出现英文用户可见文本。
- 需要后端新增字段才能运行。

## 13. 完成后必须返回的报告格式

```md
# 阶段完成报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. Phaser 接入结构

说明新增了哪些 Phaser 文件、React 如何创建和销毁 Phaser、事件如何流转。

## 4. 自测结果

## 5. 中文化检查结果

## 6. AI 接入测试结果

本阶段不新增 AI；说明是否保持既有 Mock / 真实 AI fallback。

## 7. 图片生成测试结果

本阶段不新增图片生成；说明是否复用现有视觉资产和 fallback。

## 8. 人工验收方法

## 9. 未完成事项

## 10. 阻塞问题

## 11. 是否建议进入下一阶段

## 12. 是否需要强模型审查
```

## 14. 强模型审查要求

本阶段涉及 React + Phaser 生命周期、前端事件桥和主流程稳定性，完成后建议强模型审查，重点检查：

- 是否每次 render 都重复创建 Phaser.Game。
- 是否清理 game events 监听。
- 是否保留 `ScenePanel` 回退。
- 是否无后端越权。
- 是否没有把剧情状态搬进 Phaser。
- 是否热点点击仍走现有 `/api/investigate`。
- 是否保持全中文用户可见文本。
- 是否没有引入 API Key 泄露风险。
- 是否前端构建通过。
