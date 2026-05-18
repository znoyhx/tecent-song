# 05 剧情状态机

## 核心原则

剧情阶段必须由后端状态机控制。AI 可以生成表达，但不能自行决定进入下一阶段、释放关键线索或判定结局。

## 五阶段结构

| 阶段 | 目的 | 进入条件 | 允许玩家行为 | 允许释放线索 | AI 禁止事项 |
| --- | --- | --- | --- | --- | --- |
| `intro` | 建立事件钩子 | 新建会话 | 查看场景、调查 1-2 个热点、首次对话 | 表层异常线索 | 不能说出纵火者、粮册完整真相、幕后压力 |
| `investigation` | 多 NPC 各执一词 | 发现至少 1 条异常线索 | 场景调查、NPC 追问、出示线索 | 核心物证、矛盾证言 | 不能直接进入结局，不能让 NPC 全盘交代 |
| `reversal` | 揭示表层解释不成立 | 发现至少 3 条关键线索或 1 组组合成立 | 深度追问、线索组合、进入新场景 | 粮册/封口令/命令矛盾类线索 | 不能直接给出最佳选择，不能替玩家推理完 |
| `choice` | 要求玩家承担代价 | 完成至少 1 组核心线索组合 | 做关键选择、最后对话 | 不再大量释放新线索，只允许补充解释 | 不能新增改变真相的大线索 |
| `ending` | 结局回收 | 玩家做出关键选择 | 查看结局、重开 | 不释放玩法线索 | 不能改变已判定结局 |

## 状态变量

```json
{
  "session_id": "s_001",
  "current_stage": "investigation",
  "current_scene_id": "scene_fire_yard",
  "discovered_clue_ids": ["clue_burned_page"],
  "completed_combo_ids": [],
  "npc_trust": {"npc_owner": -1, "npc_worker": 1, "npc_scholar": 0, "npc_jinyiwei": 0},
  "flags": ["found_liaodong_clue"],
  "scores": {"truth": 1, "order": 0, "survival": 0, "sacrifice": 0},
  "risk_level": 1,
  "available_scene_ids": ["scene_front_hall", "scene_fire_yard"],
  "available_choice_ids": [],
  "turn_count": 3
}
```

## 阶段跳转条件

```text
intro -> investigation
条件：discovered_clue_ids 包含任一 intro 异常线索。

investigation -> reversal
条件：关键线索数量 >= 3，或完成 combo_fire_is_arson，或 flags 包含 worker_contradiction_confirmed。

reversal -> choice
条件：完成 combo_burned_text_is_ledger 或发现 clue_jinyiwei_gag_order。

choice -> ending
条件：玩家提交 final_choice_id。
```

## 明代书坊焚稿案状态流转示例

1. 新建会话：`stage=intro`，场景为 `scene_front_hall`。
2. 玩家调查后院火场，发现 `clue_fire_origin_wrong` 与 `clue_burned_page`。
3. 状态机进入 `investigation`，开放前厅、后院、刻坊。
4. 玩家询问阿沈，若信任度达到 1，释放 `clue_worker_lie`。
5. 玩家发现 `clue_oil_smell`、`clue_owner_moved_box`，组合得到 `combo_fire_is_arson`。
6. 状态机进入 `reversal`，开放雨巷和临时审问处。
7. 玩家发现 `clue_jinyiwei_gag_order` 与 `clue_lu_order_conflict`。
8. 状态机进入 `choice`，开放最终选择。
9. 玩家选择交给陆峥 / 暗中交顾闻 / 销毁余稿 / 逼阿沈作证 / 反查命令。
10. 后端按分数、风险、信任和 flags 判定结局。

## 结局判定逻辑

判定按优先级执行：

1. 隐藏结局：`found_hidden_chain=true`、`npc_jinyiwei_trust>=2`、`npc_scholar_trust>=2`、`risk_level<7`。
2. 悲剧结局：`risk_level>=6` 且关键 NPC 信任不足。
3. 真相结局：`truth>=5` 且保存证据相关 flags 存在。
4. 秩序结局：`order>=4` 或最终选择为交给陆峥。
5. 自保结局：`survival>=4` 或最终选择为销毁/隐瞒证据。
6. 默认结局：证据残缺，事件被压下。

## 禁止 AI 的状态操作

AI 输出中即使包含以下字段，后端也必须忽略或二次校验：

- `current_stage`。
- `ending_id`。
- 不在 `allowed_released_clues` 内的 `released_clues`。
- 任意新增 NPC 知识。
- 任意新增最终真相。

## 测试方法

- 构造固定状态，调用 `StateMachineService.evaluate_transition()`。
- 确认未满足条件不会跳阶段。
- 确认 AI 返回非法阶段不会被采纳。
- 确认每个最终选择都能进入一个结局。
