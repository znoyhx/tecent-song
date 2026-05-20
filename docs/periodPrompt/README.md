# docs/periodPrompt 使用说明

`docs/periodPrompt/` 是《史隙》项目的分阶段 AI 协作开发指挥手册。这里的 Markdown 文件不是普通说明文，而是可以直接复制给低级模型或强模型执行的任务 Prompt。

## 推荐执行顺序

1. `00_global_rules.md`：每次任务都先附带。
2. `01_stage_0_repo_analysis_prompt.md`：先分析仓库真实状态。
3. `02_stage_1_mock_demo_prompt.md`：先跑通无真实 AI 的完整 Mock Demo。
4. `03_stage_2_frontend_base_prompt.md`：完善前端基础体验。
5. `04_stage_3_backend_base_prompt.md`：完善后端基础服务。
6. `05_stage_4_real_ai_npc_prompt.md`：接入真实 DeepSeek NPC。
7. `06_stage_5_state_and_clue_prompt.md`：完善状态机和线索系统。
8. `07_stage_6_consistency_supervisor_prompt.md`：实现一致性监管器。
9. `08_stage_7_rag_knowledge_prompt.md`：接入知识库和 RAG。
10. `09_stage_8_visual_asset_and_image_ai_prompt.md`：接入视觉资产和图片生成。
11. `10_stage_9_endings_and_history_echo_prompt.md`：完善多结局和历史回声。
12. `11_stage_10_testing_deployment_roadshow_prompt.md`：最终测试、部署和路演。
13. `19_story_volume_expansion_prompt.md`：可选增强阶段，在主 Demo 已跑通后扩写“明代 / 书坊学徒 / 书坊焚稿案”的章节级剧本体量。
14. `20_stage_12_phaser_stage_p0_prompt.md`：新增 Phaser 可交互舞台 P0，把现有 `ScenePanel` 升级为 React + Phaser 混合叙事舞台。

## Phaser 决策后的推荐开发流程

当前 PRD 和 CODEBUDDY 已明确：Phaser 只增强舞台层，不接管剧情系统。因此接下来推荐按以下顺序推进：

1. **阶段 12：Phaser 可交互舞台 P0**  
   执行 `20_stage_12_phaser_stage_p0_prompt.md`。目标是安装 Phaser、新增 `PhaserStage`、保留 `ScenePanel` 回退、渲染背景/NPC/热点、点击热点仍走 `/api/investigate`。

2. **阶段 12 完成审查**  
   使用 `12_code_review_prompt.md` 做一次强模型审查，重点看 React + Phaser 生命周期、事件清理、回退开关、前端构建和主流程回归。

3. **阶段 10 路演验收刷新**  
   重新执行或局部执行 `11_stage_10_testing_deployment_roadshow_prompt.md`，把路演脚本更新为“React + Phaser + FastAPI”架构，并验证 3 分钟演示路径。

4. **可选阶段：StageCue P1**  
   在 Phaser P0 稳定后，再考虑新增后端 `stage_cue` 字段，让 FastAPI 明确下发视觉反馈指令。不要在 Phaser P0 中提前做。

5. **可选阶段：章节体量或视觉打磨**  
   若路演时间允许，再用 `19_story_volume_expansion_prompt.md` 扩写剧本体量，或继续打磨 Phaser 特效与视觉资产。

## 哪些 Prompt 给低级模型

适合低级模型执行：

- `01_stage_0_repo_analysis_prompt.md`
- `02_stage_1_mock_demo_prompt.md` 中的单项任务
- `03_stage_2_frontend_base_prompt.md`
- `04_stage_3_backend_base_prompt.md` 中的简单路由和数据加载任务
- `13_bugfix_prompt.md`
- `14_chinese_only_audit_prompt.md`
- `17_low_level_model_execution_template.md`

给低级模型时必须同时附带：

- `00_global_rules.md`
- 当前阶段 Prompt
- 明确允许修改的文件列表

## 哪些 Prompt 给强模型

必须强模型执行或审查：

- `05_stage_4_real_ai_npc_prompt.md`
- `06_stage_5_state_and_clue_prompt.md` 的核心规则部分
- `07_stage_6_consistency_supervisor_prompt.md`
- `08_stage_7_rag_knowledge_prompt.md` 的知识和召回策略审查
- `10_stage_9_endings_and_history_echo_prompt.md` 的结局规则审查
- `11_stage_10_testing_deployment_roadshow_prompt.md`
- `12_code_review_prompt.md`
- `15_real_ai_integration_test_prompt.md`
- `16_image_generation_test_prompt.md`
- `19_story_volume_expansion_prompt.md`：用于章节级剧本结构、线索链、推理节点和结局条件扩写，建议强模型执行或审查。
- `20_stage_12_phaser_stage_p0_prompt.md`：涉及 React + Phaser 生命周期、事件桥和主流程回归，建议强模型执行或审查。

## 每个阶段完成后如何汇报

每个阶段 Prompt 都要求输出固定报告：

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

没有报告，不允许进入下一阶段。

## 如何避免低级模型乱改

给低级模型任务时必须明确：

- 只完成当前任务。
- 只能改指定文件。
- 不能删除已有逻辑。
- 不能重构目录。
- 不能修改 API 合约。
- 不能让 UI 出现英文。
- 不能接触或打印 API Key。
- 必须执行自测。
- 缺少依赖、Key、脚本、文档时必须反馈。

推荐把 `17_low_level_model_execution_template.md` 作为包装模板，把具体任务填入后再交给低级模型。

## 如何保证全中文游戏界面

所有阶段 Prompt 都包含中文化要求：

- 用户可见文本必须中文。
- 英文变量名和接口字段允许保留。
- 前端、Mock、fallback、错误、结局、线索都要检查。
- `14_chinese_only_audit_prompt.md` 可作为专项审计。

## 如何保证真实 AI 接入测试

真实 AI 阶段必须使用：

- `05_stage_4_real_ai_npc_prompt.md`
- `15_real_ai_integration_test_prompt.md`
- `16_image_generation_test_prompt.md`

这些 Prompt 明确要求：

- 只能检查 Key 是否存在，不能打印 Key。
- 必须真实调用 API。
- 不能用 Mock 冒充真实测试。
- 必须记录测试时间、接口、输入摘要、是否成功、是否 fallback。

## 如何保证缺东西及时反馈

所有 Prompt 都要求遇到以下情况停止反馈：

- 文档缺失。
- 依赖无法安装。
- 启动脚本缺失。
- API Key 不存在或变量名不明。
- DeepSeek 或硅基流动不可访问。
- 接口文档与代码冲突。
- 低级模型无法判断是否会破坏架构。

反馈必须包含：缺少什么、为什么阻塞、怎么补、还能先做什么、是否需要强模型。

## 如何保证人工可验收

每个阶段 Prompt 都有“人工验收方式”，要求写明：

- 运行命令。
- 打开地址。
- 点击路径。
- 输入中文测试文本。
- 预期中文结果。
- 如何判断线索、AI、图片、fallback 是否生效。
- 是否可以进入下一阶段。

## 文件清单

- `00_global_rules.md`
- `01_stage_0_repo_analysis_prompt.md`
- `02_stage_1_mock_demo_prompt.md`
- `03_stage_2_frontend_base_prompt.md`
- `04_stage_3_backend_base_prompt.md`
- `05_stage_4_real_ai_npc_prompt.md`
- `06_stage_5_state_and_clue_prompt.md`
- `07_stage_6_consistency_supervisor_prompt.md`
- `08_stage_7_rag_knowledge_prompt.md`
- `09_stage_8_visual_asset_and_image_ai_prompt.md`
- `10_stage_9_endings_and_history_echo_prompt.md`
- `11_stage_10_testing_deployment_roadshow_prompt.md`
- `12_code_review_prompt.md`
- `13_bugfix_prompt.md`
- `14_chinese_only_audit_prompt.md`
- `15_real_ai_integration_test_prompt.md`
- `16_image_generation_test_prompt.md`
- `17_low_level_model_execution_template.md`
- `18_stage_transition_checklist.md`
- `19_story_volume_expansion_prompt.md`
- `20_stage_12_phaser_stage_p0_prompt.md`
- `README.md`

