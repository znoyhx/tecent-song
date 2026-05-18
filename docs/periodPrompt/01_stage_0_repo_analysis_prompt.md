# 阶段 0：仓库分析 Prompt

## 1. 你的角色

你是仓库分析执行模型。你的任务是只读分析当前仓库，输出真实状态报告，不开发业务功能。

## 2. 必须先阅读的文档

必须阅读：

- `CODEBUDDY.md`
- `docs/PRD.md`
- `docs/develop/00_project_overview.md`
- `docs/develop/01_mvp_scope.md`
- `docs/develop/03_directory_structure.md`
- `docs/develop/13_api_contracts.md`
- `docs/develop/20_development_roadmap.md`
- `docs/develop/22_risk_control.md`

必须检查但不得输出密钥内容：

- 是否存在 `docs/DeepseekAPIKey`
- 是否存在 `docs/ImageGenerateKey`
- 是否存在 `.env` 或 `.env.example`

## 3. 阶段目标

输出当前项目实际状态报告，确认：

- 前端是否存在。
- 后端是否存在。
- 依赖文件是否存在。
- 启动命令是否存在。
- 测试是否存在。
- DeepSeek 配置是否存在。
- 硅基流动图片生成配置是否存在。
- 当前结构与开发文档是否一致。

本阶段不开发游戏功能。

## 4. 当前阶段禁止事项

- 禁止修改业务代码。
- 禁止创建前端或后端工程。
- 禁止读取并输出 API Key。
- 禁止把 Key 写入报告。
- 禁止臆造不存在的启动命令。
- 禁止修改 `docs/PRD.md`、`CODEBUDDY.md`、`docs/develop/*.md`。

## 5. 允许修改的文件范围

允许新增一个只读分析报告：

- `docs/periodPrompt/reports/stage_0_repo_analysis_report.md`

如果目录不存在，可以创建目录。

## 6. 不允许修改的文件范围

不允许修改除上述报告外的任何文件。

## 7. 具体开发任务

### 任务 1：检查目录结构

- 任务目标：列出当前仓库目录。
- 参考文档：`03_directory_structure.md`。
- 涉及文件：全仓只读。
- 输入：当前文件系统。
- 输出：实际目录树摘要。
- 验收标准：明确指出是否存在 `frontend/`、`backend/`、`docs/develop/`。

### 任务 2：检查配置和密钥文件

- 任务目标：确认 Key 配置是否存在但不泄露。
- 参考文档：`15_real_ai_integration_plan.md`。
- 涉及文件：只检查路径存在和大小，不输出内容。
- 输入：文件系统。
- 输出：`DeepSeek Key 文件：存在/不存在`、`图片 Key 文件：存在/不存在`、`.env：存在/不存在`。
- 验收标准：报告中不包含任何 Key 字符串。

### 任务 3：检查启动和测试命令

- 任务目标：确认是否已有 `package.json`、`requirements.txt`、测试目录。
- 参考文档：`17_testing_and_acceptance.md`。
- 输出：当前能运行和不能运行的命令列表。
- 验收标准：不臆造已存在命令。

## 8. 数据与接口要求

本阶段不实现接口，只检查是否已有接口代码。若发现已有接口，列出路径和实际路由。

## 9. 中文化要求

报告必须中文。若发现已有前端/Mock/文案中有英文用户可见文本，列出文件和文本；若前端不存在，写明“前端尚不存在，无法检查 UI 文案”。

## 10. AI 接入要求

本阶段不调用真实 AI，不得伪造真实 AI 测试结论。只检查 Key 配置是否存在，不能输出 Key。

## 11. 模型必须执行的自测步骤

执行或等价完成：

- 列出仓库文件。
- 检查 `package.json` 是否存在。
- 检查 `requirements.txt` 是否存在。
- 检查 `.env*` 是否存在。
- 检查 Key 文件是否存在但不读取内容。
- 检查 `frontend/`、`backend/`、`tests/` 是否存在。

## 12. 人工验收方式

用户打开：

- `docs/periodPrompt/reports/stage_0_repo_analysis_report.md`

期望看到：

- 当前项目实际状态。
- 缺失项清单。
- 下一阶段可执行性判断。
- 没有任何 API Key 明文。

## 13. 完成后必须返回的报告格式

```md
# 阶段完成报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. 自测结果

## 4. 中文化检查结果

## 5. AI 接入测试结果
本阶段未调用真实 AI，只检查配置存在性。

## 6. 图片生成测试结果
本阶段未调用图片生成，只检查配置存在性。

## 7. 人工验收方法

## 8. 未完成事项

## 9. 阻塞问题

## 10. 是否建议进入下一阶段

## 11. 是否需要强模型审查
```
