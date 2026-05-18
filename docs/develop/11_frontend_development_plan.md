# 11 前端开发计划

## 页面结构

MVP 前端只需要 4 个页面状态，不必引入复杂路由：

1. `StartPage`：选择朝代和身份。
2. `GamePage`：主游戏界面。
3. `EndingPage`：结局展示和历史回声。
4. `DebugPanel`：开发模式显示状态、线索、AI 日志。

## UI 布局

```text
┌──────────────────────────────────────┐
│ TopStatusBar：朝代/身份/场景/阶段/风险 │
├──────────────────────────────────────┤
│ SceneStage：背景图 + NPC + 热点        │
│                         ClueSidebar  │
├──────────────────────────────────────┤
│ DialoguePanel：文本/高亮线索/输入/按钮 │
└──────────────────────────────────────┘
```

## 组件拆分

| 组件 | 职责 |
| --- | --- |
| `GameShell` | 游戏整体布局。 |
| `TopStatusBar` | 展示当前状态。 |
| `SceneStage` | 背景、场景描述、热点。 |
| `NPCSprite` | NPC 剪影、姓名、情绪。 |
| `DialoguePanel` | 对话内容、输入框、推荐追问。 |
| `HighlightedText` | 渲染红色高亮并处理点击。 |
| `ClueSidebar` | 线索列表、详情、组合入口。 |
| `ChoiceCards` | 关键选择卡片。 |
| `EndingView` | 结局和历史回声。 |
| `LoadingOverlay` | AI 调用和场景切换 loading。 |
| `ErrorBanner` | 错误提示和重试。 |
| `DebugPanel` | 开发调试状态。 |

## 状态管理

建议 `Zustand` store：

```ts
type GameStore = {
  session: GameSessionState | null;
  currentScene: Scene | null;
  clues: Clue[];
  dialogueTurns: DialogueTurn[];
  loading: boolean;
  error: string | null;
}
```

后端是权威状态。前端不自行推进阶段，只使用 API 返回的 `state`。

## Mock 数据接入方式

- `frontend/src/mock/` 放前端视觉调试用数据。
- 真正剧情 Mock 由后端提供，避免前后端逻辑分叉。
- 开发前端时可用 `VITE_USE_FRONTEND_MOCK=true` 暂时渲染页面，但最终验收必须接后端。

## 真实 API 切换

`frontend/src/api/client.ts` 读取：

- `VITE_API_BASE_URL`。
- `VITE_USE_FRONTEND_MOCK`。

不得读取任何模型 API Key。

## 前端开发任务列表

### F1 初始化前端工程

- 任务目标：创建 `frontend/` Vite React TS 工程并配置 Tailwind。
- 涉及文件：`frontend/package.json`、`src/main.tsx`、`src/App.tsx`、`tailwind.config.*`。
- 输入数据：无。
- 输出结果：`npm run dev` 可打开空页面。
- 禁止改动：`docs/PRD.md`、`CODEBUDDY.md`。
- 验收标准：无 TS 错误，首页显示项目名。
- 模型等级：低级模型可做，普通模型审查。

### F2 实现 API Client 与类型

- 任务目标：封装 API 请求和 TypeScript 类型。
- 涉及文件：`src/api/client.ts`、`src/types/game.ts`。
- 输入数据：`13_api_contracts.md`。
- 输出结果：所有 API 方法有类型定义。
- 禁止改动：后端合约字段名。
- 验收标准：Mock 调用能编译。
- 模型等级：普通模型。

### F3 实现游戏布局

- 任务目标：完成视觉小说式主界面。
- 涉及文件：`GameShell.tsx`、`TopStatusBar.tsx`、`SceneStage.tsx`。
- 输入数据：会话 state、scene。
- 输出结果：能显示场景、阶段、风险。
- 禁止改动：API client。
- 验收标准：不同场景能正确渲染。
- 模型等级：低级模型可做。

### F4 实现对话框

- 任务目标：展示 NPC 回复、玩家输入、推荐追问、出示线索。
- 涉及文件：`DialoguePanel.tsx`、`NPCSprite.tsx`。
- 输入数据：`DialogueTurn`、`Clue[]`。
- 输出结果：可发起 `POST /api/dialogue`。
- 禁止改动：状态机逻辑。
- 验收标准：loading、成功、失败三态可见。
- 模型等级：普通模型。

### F5 实现线索栏和红色高亮

- 任务目标：点击高亮获得/查看线索，线索栏展示详情。
- 涉及文件：`HighlightedText.tsx`、`ClueSidebar.tsx`。
- 输入数据：scene text highlights、clues。
- 输出结果：已发现线索不重复加入。
- 禁止改动：后端线索释放规则。
- 验收标准：点击 `辽东粮册` 后侧栏出现烧焦残页。
- 模型等级：普通模型。

### F6 实现关键选择和结局页

- 任务目标：展示选择卡片，提交后进入结局页。
- 涉及文件：`ChoiceCards.tsx`、`EndingView.tsx`。
- 输入数据：available choices、ending response。
- 输出结果：显示结局标题、NPC 命运、历史回声。
- 禁止改动：结局判定逻辑。
- 验收标准：5 个结局响应均能展示。
- 模型等级：低级模型可做。

### F7 实现调试面板

- 任务目标：开发模式展示 state、flags、scores、AI 监管结果。
- 涉及文件：`DebugPanel.tsx`。
- 输入数据：API 返回的 debug 字段。
- 输出结果：路演前可隐藏。
- 禁止改动：生产 UI 主流程。
- 验收标准：能定位阶段和线索问题。
- 模型等级：低级模型可做。
