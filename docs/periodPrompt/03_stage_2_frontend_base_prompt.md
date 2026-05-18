# 阶段 2：前端基础体验 Prompt

## 1. 你的角色

你是前端体验执行开发模型。你的任务是在 Mock Demo 基础上完善中文视觉小说式游戏体验，不改变后端业务规则。

## 2. 必须先阅读的文档

- `CODEBUDDY.md`
- `docs/develop/02_technical_architecture.md`
- `docs/develop/03_directory_structure.md`
- `docs/develop/11_frontend_development_plan.md`
- `docs/develop/13_api_contracts.md`
- `docs/develop/16_visual_asset_plan.md`
- `docs/develop/17_testing_and_acceptance.md`
- `docs/periodPrompt/00_global_rules.md`
- 当前 `frontend/` 代码

## 3. 阶段目标

完善前端基础体验：

- 视觉小说 / 对话游戏布局。
- 顶部状态栏。
- 场景区域。
- NPC 区域。
- 底部对话框。
- 右侧线索栏。
- 推荐追问按钮。
- 自由输入框。
- 出示线索入口。
- 选择卡片。
- 结局页面。
- 全中文 Loading / Error / Empty 文案。
- 支持 Mock/API 模式切换。

不实现：真实 AI、RAG、图片生成 API。

## 4. 当前阶段禁止事项

- 禁止修改后端状态机规则。
- 禁止新增英文用户可见文本。
- 禁止把 API Key 放进前端。
- 禁止在前端硬编码结局判定。
- 禁止删除 Mock 模式。
- 禁止重构无关目录。

## 5. 允许修改的文件范围

- `frontend/src/`
- `frontend/package.json`（仅限必要脚本/依赖）
- `assets/placeholders/`
- `docs/periodPrompt/reports/stage_2_frontend_base_report.md`

## 6. 不允许修改的文件范围

- `backend/services/state_machine.py` 或等价状态机文件
- `backend/data/` 剧情数据，除非为修复前端展示字段缺失且先说明
- `docs/PRD.md`
- `docs/develop/*.md`
- 密钥文件

## 7. 具体开发任务

### 任务 1：游戏主布局

- 任务目标：实现视觉小说式主界面。
- 参考文档：`11_frontend_development_plan.md`。
- 涉及文件：`GameShell`、`TopStatusBar`、`SceneStage`。
- 输入：session state、scene。
- 输出：中文状态栏和场景。
- 验收标准：显示朝代、身份、场景、阶段、风险。

### 任务 2：对话体验

- 任务目标：实现 NPC 对话框、推荐追问、自由输入。
- 涉及文件：`DialoguePanel`、`NPCSprite`。
- 输入：dialogue response。
- 输出：中文 NPC 回复和中文按钮。
- 验收标准：可提交中文问题并展示中文回复。

### 任务 3：线索栏和高亮

- 任务目标：支持红色关键线索点击查看。
- 涉及文件：`HighlightedText`、`ClueSidebar`。
- 输入：scene highlights、clues。
- 输出：右侧线索栏。
- 验收标准：点击红色线索后线索栏出现对应中文线索详情。

### 任务 4：选择与结局页

- 任务目标：实现关键选择卡片和结局展示。
- 涉及文件：`ChoiceCards`、`EndingView`。
- 输出：中文结局标题、结局正文、历史回声。
- 验收标准：5 类结局都可正常展示。

## 8. 数据与接口要求

前端只能调用 `13_api_contracts.md` 定义的 API。前端不得自行构造隐藏线索或阶段。所有请求和响应类型应在 `frontend/src/types/` 维护。

## 9. 中文化要求

所有 UI 文案必须中文：按钮、标题、占位、错误、Loading、空状态、调试提示。完成后搜索前端源码中用户可见字符串，列出英文残留并修复。

## 10. AI 接入要求

本阶段不接入真实 AI。若页面展示“AI 正在思考”等文案，必须只是中文 Loading，不得声称真实 AI 已调用。

## 11. 模型必须执行的自测步骤

- 安装前端依赖。
- 运行类型检查或构建。
- 启动前端。
- 联调后端 Mock API。
- 点击开始游戏。
- 点击红色线索。
- 发送中文对话。
- 出示线索。
- 进入结局页。
- 检查浏览器控制台错误。
- 执行中文 UI 自检。

## 12. 人工验收方式

1. 启动后端 Mock。
2. 启动前端。
3. 打开前端地址。
4. 选择“明代 / 书坊学徒”。
5. 观察是否是暗色视觉小说布局。
6. 点击红色线索，右侧线索栏应出现中文线索。
7. 在输入框输入：“你昨夜到底听见了什么？”
8. 点击中文提交按钮。
9. 期望 NPC 用中文回答。
10. 进入选择阶段，点击中文选择卡。
11. 期望出现中文结局页。

## 13. 完成后必须返回的报告格式

```md
# 阶段完成报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. 自测结果

## 4. 中文化检查结果

## 5. AI 接入测试结果
本阶段不接入真实 AI。

## 6. 图片生成测试结果
本阶段不接入图片生成。

## 7. 人工验收方法

## 8. 未完成事项

## 9. 阻塞问题

## 10. 是否建议进入下一阶段

## 11. 是否需要强模型审查
```
