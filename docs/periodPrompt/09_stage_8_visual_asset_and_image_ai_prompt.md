# 阶段 8：视觉资产与图片 AI Prompt

## 1. 你的角色

你是视觉资产和硅基流动图片生成接入执行模型。你的任务是在后端安全调用图片生成 API，生成并保存最小视觉资产，同时保证失败时占位图可用。

## 2. 必须先阅读的文档

- `CODEBUDDY.md`
- `docs/develop/16_visual_asset_plan.md`
- `docs/develop/15_real_ai_integration_plan.md`
- `docs/help/Imagegenerate.md`
- `docs/periodPrompt/00_global_rules.md`
- 当前资源目录和前端图片展示代码

## 3. 阶段目标

必须完成真实图片生成测试，至少生成：

- 1 张明代书坊背景图。
- 1 张明代 NPC 剪影或立绘图。
- 1 张线索物品图。

必须完成：

- 从环境变量读取硅基流动图片生成 API Key。
- 前端不接触 Key。
- 图片保存到清晰目录。
- 前端可展示生成图。
- 生成失败使用占位图。
- 输出图片生成测试记录。

## 4. 当前阶段禁止事项

- 禁止前端直接调用硅基流动 API。
- 禁止打印完整图片生成 Key。
- 禁止把 Key 写入 Markdown、日志、前端。
- 禁止生成不符合历史悬疑氛围的现代画面。
- 禁止因图片失败导致游戏无法运行。
- 禁止英文用户可见 UI。

## 5. 允许修改的文件范围

- `backend/services/image_generation_client.*`
- `backend/services/visual_asset_service.*`
- `backend/config.py`
- `backend/tests/test_image_generation.*`
- `assets/`
- `frontend/src/components/scene/*`
- `frontend/src/components/npc/*`
- `frontend/src/components/clue/*`
- `docs/periodPrompt/reports/stage_8_visual_asset_report.md`

## 6. 不允许修改的文件范围

- `docs/ImageGenerateKey`
- `docs/DeepseekAPIKey`
- `docs/PRD.md`
- `docs/develop/*.md`
- 状态机和线索判定逻辑

## 7. 具体开发任务

### 任务 1：图片生成客户端

- 任务目标：封装硅基流动图片生成 API。
- 参考文档：`docs/help/Imagegenerate.md`。
- 输入：prompt、negative_prompt、image_size。
- 输出：图片 URL 或错误。
- 验收标准：Key 不泄露，失败有中文错误。

### 任务 2：生成并保存资产

- 任务目标：生成 3 张最小资产并下载保存。
- 输出路径：`assets/scenes/`、`assets/npcs/`、`assets/clues/`。
- 验收标准：本地文件存在，命名规范英文，展示文案中文。

### 任务 3：前端展示与 fallback

- 任务目标：前端优先显示生成图，缺失时显示占位图。
- 输出：AssetResolver 或等价逻辑。
- 验收标准：删图后页面仍能显示占位图。

### 任务 4：测试记录

- 任务目标：记录真实图片生成。
- 输出：测试时间、接口、输入摘要、真实 API、成功、保存路径、fallback、问题、建议。
- 验收标准：不含 Key。

## 8. 数据与接口要求

图片生成请求由后端发起。前端只拿本地静态资源路径或后端返回的已保存图片路径。

## 9. 中文化要求

页面上的图片标题、说明、失败提示必须中文。图片 prompt 内容可以包含必要模型风格词，但最终用户可见描述必须中文。

## 10. AI 接入要求

本阶段必须真实调用硅基流动图片生成 API。判断不是 Mock：

- 测试记录 `是否调用真实 API：是`。
- 返回过图片 URL 或明确 API 错误。
- 成功时本地保存图片。
- 失败时记录 fallback。

## 11. 模型必须执行的自测步骤

- 检查图片 API Key 是否存在但不打印。
- 调用生成明代书坊背景图。
- 调用生成 NPC 图。
- 调用生成线索物品图。
- 下载保存图片。
- 启动前端查看图片。
- 模拟图片缺失，确认占位图生效。
- 执行中文 UI 检查。

## 12. 人工验收方式

1. 启动后端。
2. 运行图片生成测试脚本。
3. 查看 `assets/scenes/` 是否有明代书坊背景图。
4. 查看 `assets/npcs/` 是否有 NPC 图。
5. 查看 `assets/clues/` 是否有线索图。
6. 启动前端，进入书坊场景。
7. 期望看到背景图、NPC 图或占位图。
8. 删除一张测试图或改名，刷新页面，期望出现中文占位状态且游戏不崩溃。

## 13. 完成后必须返回的报告格式

```md
# 阶段完成报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. 自测结果

## 4. 中文化检查结果

## 5. AI 接入测试结果
本阶段不涉及 DeepSeek 文本生成，除非同时测试视觉提示词。

## 6. 图片生成测试结果
- 测试时间：
- 测试接口：
- 输入摘要：
- 是否调用真实 API：
- 是否成功：
- 保存路径：
- 是否 fallback：
- 问题：
- 下一步建议：

## 7. 人工验收方法

## 8. 未完成事项

## 9. 阻塞问题

## 10. 是否建议进入下一阶段

## 11. 是否需要强模型审查
```
