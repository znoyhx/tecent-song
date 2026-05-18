# 阶段 1 Mock Demo 完成报告

## 1. 已完成内容

已完成一个**可运行的最小中文 Mock Demo**，从 0 搭建了 `frontend/` 与 `backend/` 工程，并跑通了“明代 / 书坊学徒 / 书坊焚稿案”的完整闭环。

当前浏览器内可完成：

- 进入开始页
- 选择“明代 / 书坊学徒”
- 进入书坊焚稿案
- 依次经历 `intro → investigation → reversal → choice → ending`
- 与 4 个 NPC 进行 Mock 对话
- 获取并查看 15 条中文线索中的已发现部分
- 点击关键线索查看详情
- 向 NPC 出示线索并触发至少 1 次中文回复变化
- 在抉择阶段选择关键行动
- 进入 5 个中文结局之一

同时已完成：

- FastAPI 后端最小工程与中文错误返回
- React + TypeScript + Vite 前端最小工程
- 明代书坊焚稿案固定数据包
- 后端状态机、线索释放、线索组合、结局判定
- Mock 对话与最小监管器
- 环境变量示例 `.env.example`
- 后端测试与前端构建自测
- 中文化检查
- 人工验收说明

本阶段**未接入真实 DeepSeek**，**未接入真实硅基流动图片生成**，仅保留后续接入接口与提示词文件位置。

## 2. 创建或修改的文件列表

### 根目录

- `.env.example`

### 前端

- `frontend/package.json`
- `frontend/tsconfig.json`
- `frontend/vite.config.ts`
- `frontend/index.html`
- `frontend/README.md`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/mock/demoNotes.ts`
- `frontend/src/store/gameStore.ts`
- `frontend/src/types/game.ts`
- `frontend/src/pages/StartPage.tsx`
- `frontend/src/pages/GamePage.tsx`
- `frontend/src/components/layout/GameShell.tsx`
- `frontend/src/components/scene/ScenePanel.tsx`
- `frontend/src/components/dialogue/DialoguePanel.tsx`
- `frontend/src/components/clue/ClueSidebar.tsx`
- `frontend/src/components/ending/EndingPanel.tsx`
- `frontend/src/styles/global.css`

### 后端

- `backend/requirements.txt`
- `backend/README.md`
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/models/game_models.py`
- `backend/app/routers/game.py`
- `backend/app/services/game_engine.py`
- `backend/app/services/supervisor.py`
- `backend/tests/test_api.py`
- `backend/tests/test_logic.py`

### 后端数据

- `backend/data/dynasties/dynasties.json`
- `backend/data/roles/roles.json`
- `backend/data/events/ming_bookshop_fire.json`
- `backend/data/scenes/ming_bookshop_scenes.json`
- `backend/data/npcs/ming_bookshop_npcs.json`
- `backend/data/clues/ming_bookshop_clues.json`
- `backend/data/endings/ming_bookshop_endings.json`
- `backend/data/mock/scene_responses.json`
- `backend/data/mock/history_echoes.json`
- `backend/data/mock/dialogues/npc_owner.json`
- `backend/data/mock/dialogues/npc_worker.json`
- `backend/data/mock/dialogues/npc_scholar.json`
- `backend/data/mock/dialogues/npc_jinyiwei.json`

### 后续 AI 接口占位

- `backend/data/prompts/npc_dialogue.md`
- `backend/data/prompts/supervisor.md`
- `backend/data/prompts/repair.md`
- `backend/data/prompts/history_echo.md`
- `backend/data/prompts/visual_prompt.md`

### 资源占位说明

- `assets/placeholders/README.md`

### 报告

- `docs/periodPrompt/reports/stage_1_mock_demo_report.md`

## 3. 前端实现说明

前端采用 **React + TypeScript + Vite**。

已实现：

- 中文开始页
  - 中文标题“明代书坊焚稿案”
  - 中文按钮“进入明代书坊焚稿案”
  - 朝代与身份入口卡片
  - 中文状态说明与演示边界说明

- 中文游戏主页面
  - 当前朝代：明代
  - 当前身份：书坊学徒
  - 当前地点
  - 当前剧情阶段
  - 当前目标提示
  - 场景描述与剧情文本
  - 红色高亮调查按钮
  - NPC 对话区
  - 推荐追问按钮
  - 自由输入框
  - 出示线索下拉框
  - 右侧线索栏
  - 推理组合展示
  - 演示状态面板

- 线索栏
  - 只显示已发现线索
  - 支持关键线索红色高亮
  - 点击线索查看详情
  - 空状态显示“尚未发现线索”

- 抉择阶段
  - 关键选择卡片
  - 选择后提交到后端
  - 不允许前端自行决定结局

- 结局页
  - 中文结局标题
  - 中文结局摘要
  - 中文结局正文
  - 中文历史回声
  - 众人去向
  - 本案 5 个结局目录展示

视觉上使用 **深色悬疑国风氛围** 和 CSS 渐变占位，没有伪造图片资源；`background_asset` 字段和 `assets/placeholders/` 已为后续本地图或真实生成图预留。

## 4. 后端实现说明

后端采用 **FastAPI**。

已实现接口：

- `GET /api/health`
- `GET /api/dynasties`
- `GET /api/roles`
- `POST /api/session/start`
- `GET /api/session/{session_id}`
- `POST /api/dialogue`
- `POST /api/investigate`
- `POST /api/choice`
- `POST /api/ending/resolve`

实现特点：

- 后端维护会话状态，前端不能绕过状态机跳阶段
- 对话返回结构为未来真实 AI 可复用的结构化 schema
- 监管器会检查：
  - 现代词
  - 非法线索释放
  - 越阶段线索释放
  - 人物禁止披露内容
- 当前对话为固定 Mock 规则，不调用真实 AI
- 中文错误响应已经统一，例如：
  - 未找到会话
  - 当前阶段不能执行该动作
  - 线索未发现不可出示

## 5. Mock 数据说明

### 4 个 NPC

- 许掌柜：书坊掌柜
- 阿沈：书坊刻工
- 顾闻：落第士子
- 陆峥：锦衣卫低级校尉

### 5 个场景

- 书坊前厅
- 书坊后院火场
- 烧毁的刻版间
- 雨巷
- 锦衣卫临时问话处

### 15 条线索

- 火起点异常
- 烧焦残页
- 半枚红印纸角
- 异常火油味
- 后门门闩松动
- 刻工矛盾证言
- 袖口旧墨
- 三更搬箱
- 掌柜提前清箱
- 缺失稿单
- 士子急寻旧稿
- 诗稿夹带抄录
- 锦衣卫封口令
- 陆峥命令矛盾
- 城门搜检加严

### 5 个结局

- 焚稿自保
- 误信告发
- 暗藏残页
- 身陷诏狱
- 引火反查

补充说明：

- 一局流程中可稳定获得至少 8 条线索
- 关键线索可推进阶段、触发组合、改变 NPC 回复或影响结局
- 阿沈在收到 `刻工矛盾证言` 或 `袖口旧墨` 后，会改口并释放 `三更搬箱`

## 6. 状态机实现说明

状态机由后端 `GameEngine` 控制。

实现规则：

- 初始阶段固定为 `intro`
- `intro -> investigation`
  - 发现任一引子异常线索后进入
- `investigation -> reversal`
  - 关键线索数量达到阈值，或完成纵火组合，或确认刻工矛盾后进入
- `reversal -> choice`
  - 完成“焚毁的不是普通诗稿”组合，或发现 `锦衣卫封口令`
- `choice -> ending`
  - 玩家提交最终选择后进入
- 结局由规则判定，不使用随机数

结局判定优先级：

1. 隐藏结局
2. 悲剧结局
3. 真相结局
4. 秩序结局
5. 自保结局
6. 默认回落到真相结局分支

## 7. 线索系统实现说明

线索系统不是展示装饰，而是实际驱动玩法。

已实现：

- 场景调查释放线索
- NPC 对话释放线索
- 出示线索改变 NPC 回复
- 线索不会重复加入
- 关键线索支持红色高亮展示
- 线索详情面板可查看标题、正文、细节与关键文本
- 线索组合会产生推理结论与状态影响

当前已实现 3 组组合：

- 火灾并非意外
- 焚毁的不是普通诗稿
- 封口令背后另有链路

线索影响范围：

- 推动阶段
- 增减真相 / 秩序 / 自保 / 牺牲分数
- 增减风险
- 增减 NPC 信任
- 影响最终结局

## 8. 中文化检查结果

已执行中文化检查。

### 检查范围

- 前端 `pages/`
- 前端 `components/`
- 前端 `mock/`
- 后端 `data/`
- 错误提示文案
- 结局、线索、NPC、场景文本

### 结果

- **未发现玩家可见英文 UI 文本残留**。
- 搜索中出现的 `health`、`choice`、`ending`、`clue`、`stage` 等命中，均属于：
  - 类型名
  - 组件名
  - CSS 类名
  - 内部字段名
  - 内部阶段枚举值
- 这些内容**不会直接展示给玩家**，因此不构成中文化违规。

### 已确认中文化覆盖的玩家可见区域

- 页面标题
- 开始按钮
- 空状态
- 对话按钮
- 推荐追问
- 线索栏
- 线索详情
- 抉择卡片
- 结局页
- 接口报错展示文案
- 加载文案“正在准备书坊夜案……”

## 9. 自测结果

### 后端依赖安装

已执行：

```powershell
cd backend
pip install -r requirements.txt
```

结果：成功。

### 后端接口测试

已执行：

```powershell
cd backend
python -m pytest
```

结果：**5 个测试全部通过**。

覆盖内容：

- `GET /api/health`
- `GET /api/dynasties`
- `GET /api/roles`
- `POST /api/session/start`
- `GET /api/session/{session_id}`
- `POST /api/dialogue`
- `POST /api/investigate`
- `POST /api/choice`
- `POST /api/ending/resolve`
- 五类结局确定性判定
- 监管器现代词拦截

### 后端启动测试

已执行：

```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

结果：成功启动。

已确认：

- `http://127.0.0.1:8000/api/health` 返回正常
- 日志显示服务运行中

### 前端依赖安装

已执行：

```powershell
cd frontend
npm install
```

结果：成功。

### 前端构建测试

已执行：

```powershell
cd frontend
npm run build
```

结果：成功。

### 前端启动测试

已执行：

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

结果：成功。

Vite 日志显示：

- 本地地址 `http://127.0.0.1:5173/`
- 服务已就绪

### 完整流程测试

已通过真实运行中的后端服务执行一条完整 Mock 路径，结果如下：

- 健康状态：服务运行中
- 朝代列表：明代 / 北宋 / 晚唐
- 可玩身份：书坊学徒
- 进入抉择前阶段：抉择
- 进入抉择前线索数：8
- 最终结局：暗藏残页

该链路证明：

- 可从开局进入抉择与结局
- 至少获得 8 条线索
- 至少一条出示线索改变 NPC 回复
- 结局由规则确定，不依赖随机

## 10. 人工验收方法

### 1. 如何启动后端

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. 如何启动前端

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

### 3. 浏览器打开什么地址

打开：`http://127.0.0.1:5173/`

### 4. 点击哪个中文按钮进入游戏

点击：**进入明代书坊焚稿案**

### 5. 第一轮应该看到什么中文场景

进入后默认看到：**书坊前厅**

并能看到：

- 当前朝代：明代
- 当前身份：书坊学徒
- 当前阶段：引子
- 当前目标提示
- 前厅场景描述
- 许掌柜对话区

### 6. 如何触发第一条线索

有两种稳定方式：

- 直接点击前厅高亮或调查点“查看账册桌”，获得“缺失稿单”
- 或先向许掌柜发问，得到第一批前厅线索

### 7. 如何打开线索栏

页面右侧就是**线索栏**，无需额外打开按钮。

### 8. 如何确认关键线索红色高亮

在场景中点击：

- “辽东粮册”
- “偏离灯油架的焦痕”
- “不合时宜的火油味”

这些会以红色按钮样式显示；线索栏中的关键线索卡片也会有红色强调。

### 9. 如何向 NPC 出示线索

在人物对话区：

- 先选择当前场景中的 NPC
- 在“出示线索”下拉框选择一条已发现线索
- 输入问题或点击推荐追问
- 点击“发问”

### 10. 如何触发反转阶段

推荐路径：

1. 去书坊后院火场，获取“烧焦残页”
2. 去刻版间，与阿沈对话，拿到“刻工矛盾证言”和“袖口旧墨”
3. 再把“刻工矛盾证言”或“袖口旧墨”出示给阿沈
4. 获取“三更搬箱”后，阶段会进一步推进
5. 再去雨巷与顾闻对话，并出示“烧焦残页”得到“诗稿夹带抄录”

此时会从调查推进到异变，再进入抉择前条件。

### 11. 如何进入选择阶段

完成以下任一关键链：

- 获得“烧焦残页” + “半枚红印纸角” + “诗稿夹带抄录”
- 或拿到“锦衣卫封口令”

进入后页面会出现**关键抉择**卡片区。

### 12. 如何进入至少 1 个结局

在抉择区点击任一选择卡，例如：

- “暗助顾闻护出残页”

提交后会自动进入结局页。

### 13. 如何验证至少 5 个结局存在

进入任一结局页后，查看“本案收录结局”区域，可见：

- 焚稿自保
- 误信告发
- 暗藏残页
- 身陷诏狱
- 引火反查

### 14. 如何确认没有英文 UI

人工检查页面以下位置：

- 开始页按钮
- 对话按钮
- 当前目标
- 空状态
- 线索栏
- 结局页
- 错误提示
- 加载提示

当前页面展示文案均为中文。

### 15. 如何判断阶段 1 可以进入阶段 2

满足以下条件即可判断阶段 1 达标：

- 前后端可按命令启动
- 从开始页可以一路玩到结局
- 至少获得 8 条线索
- 可向 NPC 出示线索并改变回复
- 后端控制状态机，不靠前端乱跳
- 未接入真实 AI 但已保留接口与 prompt 位置
- 所有玩家可见 UI 文案为中文

## 11. 未完成事项

以下内容**按阶段规划故意未完成**：

- 真实 DeepSeek 接入
- 真实硅基流动图片生成
- 真正的 RAG 检索
- 真实 AI 日志链路
- 自动修复 Agent
- 本地场景图 / NPC 图素材
- 北宋、晚唐完整剧情

另外：

- `assets/placeholders/` 目前只提供说明文件，未放入伪造图片资源
- 原因是阶段 1 重点是跑通 Mock 闭环，不应制造假图片完成感

## 12. 阻塞问题

当前**无阻塞问题**。

在开发过程中遇到的主要问题是：

- 阿沈在测试路径中会因状态推进过快，导致部分证据反馈只在调查阶段触发

已修复：

- 将阿沈对 `刻工矛盾证言` / `袖口旧墨` 的关键反馈补到 `reversal` 阶段，使完整流程更稳

## 13. 是否建议进入阶段 2

**建议进入阶段 2。**

原因：

- 阶段 1 的核心目标已达成
- 工程骨架已建立
- 中文 Mock 闭环已跑通
- 后端状态机已落地
- 线索系统已具备真实玩法意义
- 已为后续真实 AI 提前预留结构和提示词位置

## 14. 是否需要强模型审查

**建议需要一次强模型审查。**

建议审查重点：

- 真实 AI 接入前的数据契约是否稳定
- 监管器规则是否足以承接真实模型输出
- Prompt 模板与服务职责是否适合后续扩展
- 状态机与线索系统是否还有可抽象空间
- 结局与人物行为边界是否满足后续增强需求
