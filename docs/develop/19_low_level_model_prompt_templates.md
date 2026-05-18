# 19 低级模型 Prompt 模板

## 通用开发任务 Prompt

```text
你是本项目的执行开发模型。请只完成当前任务，不要扩展功能。

任务目标：{task_goal}
允许修改文件：{allowed_files}
禁止修改文件：{forbidden_files}
参考文档：{reference_docs}
输入数据：{input_data}
预期输出：{expected_output}
验收标准：{acceptance_criteria}

约束：
1. 修改前先阅读允许修改文件和参考文档。
2. 不要修改无关文件。
3. 不要删除已有逻辑。
4. 不要重构目录结构。
5. 不要改变 API 字段名。
6. 不要引入新技术栈。
7. 完成后列出修改文件。
8. 完成后说明如何测试。
```

## 前端组件开发 Prompt

```text
请实现前端组件：{component_name}。

只允许修改：{allowed_files}
禁止修改：API client、后端文件、状态机文档。
组件输入 props：{props}
组件输出/行为：{behavior}
样式要求：暗色历史悬疑风格，红色只用于关键线索或风险。

必须做到：
- TypeScript 类型明确。
- loading/error/empty 状态可处理。
- 不在组件中硬编码后端业务规则。
- 不读取任何 API Key。
- 不新增全局状态，除非任务明确要求。

验收：{acceptance_criteria}
```

## 后端 API 开发 Prompt

```text
请实现后端 API：{api_name}。

只允许修改：{allowed_files}
参考合约：docs/develop/13_api_contracts.md
请求模型：{request_model}
响应模型：{response_model}
调用服务：{services}

约束：
- 使用 FastAPI + Pydantic。
- 返回结构化 JSON。
- 错误使用统一 error 格式。
- 不在路由中写复杂业务逻辑，业务放 services。
- 不读取或暴露前端 API Key。
- 不改变已有 API 合约字段。

验收：{acceptance_criteria}
测试方法：{test_method}
```

## 数据 JSON 编写 Prompt

```text
请按既有 schema 编写或补充 JSON 数据。

只允许修改：{json_files}
参考 schema：{schema_doc}
数据主题：{data_topic}
数量要求：{count}

约束：
- JSON 必须可解析。
- ID 使用英文 snake_case。
- 不要新增未被引用的孤立 ID。
- 线索、NPC、场景之间的引用必须一致。
- 不要写入任何真实 API Key。
- 不要修改代码文件。

验收：运行 JSON 校验，且所有引用 ID 能互相找到。
```

## Bug 修复 Prompt

```text
请修复以下 bug，不要做额外优化。

Bug 描述：{bug_description}
复现步骤：{reproduction_steps}
期望行为：{expected_behavior}
实际行为：{actual_behavior}
允许修改文件：{allowed_files}
禁止修改文件：{forbidden_files}

要求：
- 先定位原因，再做最小修改。
- 不要重构。
- 不要修改测试期望来掩盖问题。
- 修复后补充或更新必要测试。
- 说明根因和修改文件。
```

## 样式调整 Prompt

```text
请只调整样式，不要修改业务逻辑。

目标组件：{component}
允许修改：{allowed_style_files}
视觉目标：低饱和国风、暗色历史悬疑、视觉小说 UI。
具体问题：{style_issue}

禁止：
- 修改 API 调用。
- 修改状态管理。
- 修改数据模型。
- 删除交互逻辑。

验收：页面在主流程中显示正常，红色高亮仍可点击。
```

## 测试编写 Prompt

```text
请为以下模块编写测试。

模块：{module}
允许修改：{test_files}
参考行为：{behavior_doc}
必须覆盖：{cases}

约束：
- 不修改业务代码，除非发现无法测试的明显 bug 并先说明。
- 测试名称要描述行为。
- 包含成功和失败路径。
- 不依赖真实 AI API。

验收：测试可运行且失败时能定位问题。
```

## 禁止重构约束模板

```text
本任务禁止重构。你只能在指定文件中做最小增量修改。

禁止行为：
- 移动目录。
- 重命名公共函数或字段。
- 删除已有逻辑。
- 合并多个服务。
- 新增替代性架构。
- 修改 API 合约。
- 修改 docs/PRD.md、CODEBUDDY.md、docs/develop/*.md。

如果你认为必须重构，请停止并说明原因，不要自行执行。
```

## 代码审查修复 Prompt

```text
请根据代码审查意见修复问题。

审查意见：{review_comments}
允许修改文件：{allowed_files}
禁止修改文件：{forbidden_files}
验收标准：{acceptance_criteria}

要求：
- 逐条对应审查意见修复。
- 不引入新功能。
- 不改变未被提及的行为。
- 修复后列出每条意见对应的修改。
- 说明运行了哪些测试。
```
