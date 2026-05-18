# 低级模型执行任务通用模板

复制本模板给低级模型时，请替换 `{...}` 占位符。

## 1. 你的角色

你是《史隙》项目的低级执行开发模型。你只能完成本次指定任务，不得自由扩展、不得重构、不得修改无关文件。

## 2. 必须先阅读的文档

必须阅读：

- `CODEBUDDY.md`
- `docs/periodPrompt/00_global_rules.md`
- `{stage_prompt}`
- `{related_develop_docs}`
- `{files_to_read}`

## 3. 阶段目标

本次任务目标：`{task_goal}`。

只完成这些内容：

- `{task_item_1}`
- `{task_item_2}`
- `{task_item_3}`

不完成：`{out_of_scope}`。

## 4. 当前阶段禁止事项

- 禁止修改未列入允许范围的文件。
- 禁止删除已有功能。
- 禁止重构目录。
- 禁止修改 API 合约。
- 禁止让游戏 UI 出现英文用户可见文本。
- 禁止把 API Key 写入前端、日志、报告或 Markdown 正文。
- 禁止用 Mock 冒充真实 AI 测试。
- 禁止跳过测试。

## 5. 允许修改的文件范围

只允许修改：

- `{allowed_file_or_dir_1}`
- `{allowed_file_or_dir_2}`
- `{allowed_file_or_dir_3}`

## 6. 不允许修改的文件范围

禁止修改：

- `docs/PRD.md`
- `CODEBUDDY.md`
- `docs/develop/*.md`
- `docs/DeepseekAPIKey`
- `docs/ImageGenerateKey`
- `{forbidden_file_or_dir}`

## 7. 具体开发任务

### 任务 1：{task_name}

- 任务目标：`{objective}`
- 参考文档：`{reference_doc}`
- 涉及文件：`{files}`
- 输入：`{input}`
- 输出：`{output}`
- 验收标准：`{acceptance}`

## 8. 数据与接口要求

必须遵守：

- API 合约：`docs/develop/13_api_contracts.md`
- 数据模型：`docs/develop/04_data_model_design.md`
- 状态机：`docs/develop/05_game_state_machine.md`

本任务特殊格式要求：`{format_requirements}`。

## 9. 中文化要求

所有用户可见内容必须中文。完成后必须检查：

- 前端文案。
- Mock 数据。
- fallback。
- 错误提示。
- 按钮和空状态。

发现英文用户可见文本必须修复。

## 10. AI 接入要求

本任务是否涉及真实 AI：`{real_ai_required}`。

如果涉及：必须真实调用并记录测试，不得用 Mock 冒充。

如果不涉及：必须写明“本任务未测试真实 AI”。

## 11. 模型必须执行的自测步骤

必须执行或说明无法执行原因：

- `{test_command_1}`
- `{test_command_2}`
- `{test_command_3}`
- 中文 UI 自检。
- fallback 检查。

## 12. 人工验收方式

用户验收步骤：

1. 运行：`{command}`。
2. 打开：`{url}`。
3. 点击：`{click_path}`。
4. 输入：`{input_text}`。
5. 期望看到：`{expected_result}`。
6. 失败时先检查：`{failure_check}`。

## 13. 完成后必须返回的报告格式

```md
# 阶段完成报告

## 1. 已完成内容

## 2. 修改文件列表

## 3. 自测结果

## 4. 中文化检查结果

## 5. AI 接入测试结果

## 6. 图片生成测试结果

## 7. 人工验收方法

## 8. 未完成事项

## 9. 阻塞问题

## 10. 是否建议进入下一阶段

## 11. 是否需要强模型审查
```
