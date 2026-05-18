# 06 AI NPC 对话链路

## 目标

让 NPC 回复既像角色，又受状态机、线索、知识权限和历史规则约束。AI 只负责生成表达，后端负责合法性。

## 完整链路

1. 前端调用 `POST /api/dialogue`。
2. 后端读取 `GameSessionState`。
3. 后端读取 `NPCProfile`。
4. 后端读取 `NPCKnowledgePermission`。
5. 后端检查 `presented_clue_ids` 是否已发现。
6. 后端用 `dynasty_id`、`npc_id`、`current_stage`、玩家输入、线索标题检索 RAG。
7. 后端构造 prompt。
8. `AIClient` 调用模型；Mock 模式则读取固定回复。
9. 解析模型返回 JSON。
10. `ConsistencySupervisor` 审查。
11. 如失败，调用 `RepairAgent`；仍失败则 fallback。
12. `ClueService` 过滤可释放线索。
13. `GameStateService` 更新状态。
14. 返回前端。

## API 输入示例

```json
{
  "session_id": "s_001",
  "npc_id": "npc_worker",
  "message": "你昨夜三更后到底听见了什么？",
  "action_type": "question",
  "presented_clue_ids": ["clue_worker_lie"]
}
```

## Prompt 模板

```text
你是历史悬疑游戏《史隙》的 NPC 对话生成器。

必须只输出合法 JSON，不要输出 Markdown。

【朝代】{dynasty_name}
【当前阶段】{current_stage}
【当前场景】{current_scene}
【玩家身份】{player_role}
【NPC 角色卡】{npc_profile_json}
【NPC 知识权限】{npc_permission_json}
【已发现线索】{discovered_clues_json}
【玩家出示线索】{presented_clues_json}
【NPC 当前信任度】{npc_trust}
【历史/RAG 参考】{rag_context}
【玩家输入】{player_message}

规则：
1. NPC 只能说自己知道的信息。
2. 不得透露 forbidden_disclosure 中的信息。
3. 不得释放当前阶段不允许的线索。
4. 不得让玩家身份越权。
5. 不得出现现代词或错朝代元素。
6. 回复要符合 NPC 说话风格。
7. 如果玩家问题超出 NPC 知识，只能回避、怀疑或表达不知道。

输出 JSON Schema：
{
  "npc_dialogue": "string",
  "npc_action": "string",
  "emotion": "fearful|calm|angry|hesitant|defensive",
  "released_clue_ids": ["string"],
  "highlight_clues": [{"clue_id":"string","highlight_text":"string","display_text":"string"}],
  "suggested_questions": ["string"],
  "state_update_suggestion": {
    "npc_trust_delta": 0,
    "truth_score_delta": 0,
    "order_score_delta": 0,
    "survival_score_delta": 0,
    "risk_level_delta": 0,
    "new_flags": ["string"]
  }
}
```

## AI 输出示例

```json
{
  "npc_dialogue": "阿沈攥着袖口，声音低得像怕被雨声也带出去：我只听见有人说，那箱东西不能留到天亮。别再问了，问多了你我都活不成。",
  "npc_action": "他避开火场方向，指尖还沾着旧墨。",
  "emotion": "fearful",
  "released_clue_ids": ["clue_box_before_dawn"],
  "highlight_clues": [{"clue_id":"clue_box_before_dawn","highlight_text":"那箱东西不能留到天亮","display_text":"阿沈称三更后有人说那箱东西不能留到天亮。"}],
  "suggested_questions": ["那箱东西是谁搬的？","掌柜昨夜在哪里？","你为什么现在才说？"],
  "state_update_suggestion": {"npc_trust_delta":1,"truth_score_delta":1,"order_score_delta":0,"survival_score_delta":0,"risk_level_delta":1,"new_flags":["worker_heard_box"]}
}
```

## 格式错误处理

处理顺序：

1. 尝试 `json.loads(raw_text)`。
2. 若失败，提取第一个 `{...}` JSON 块再解析。
3. 若仍失败，调用 `RepairAgent`，输入 raw_text 和目标 schema。
4. 若修复失败，使用 fallback。

Fallback 示例：

```json
{
  "npc_dialogue": "阿沈张了张口，又把话咽了回去：我现在不能说。你若真想查，就先看看火场那边。",
  "npc_action": "他往后退了半步，不再看你。",
  "emotion": "fearful",
  "released_clue_ids": [],
  "highlight_clues": [],
  "suggested_questions": ["你在害怕谁？", "火场哪里不对？"],
  "state_update_suggestion": {"npc_trust_delta":0,"truth_score_delta":0,"order_score_delta":0,"survival_score_delta":0,"risk_level_delta":0,"new_flags":[]}
}
```

## 状态更新规则

- AI 建议的 `released_clue_ids` 必须经过 `ClueService.can_release()`。
- AI 建议的分数变化必须限制在 `-1` 到 `+1`，关键选择除外。
- 信任度范围建议 `-2` 到 `3`。
- 风险值范围建议 `0` 到 `8`。
- 阶段跳转只由状态机计算。

## 返回给前端示例

```json
{
  "session_id": "s_001",
  "dialogue": {...},
  "new_clues": [{"clue_id":"clue_box_before_dawn","title":"三更搬箱"}],
  "state": {"current_stage":"investigation","risk_level":2},
  "supervisor": {"pass":true,"issues":[]},
  "fallback_used": false
}
```

## 测试方法

- Mock 模式测试：固定输入返回固定 JSON。
- 非 JSON 测试：模拟模型返回散文，确认 fallback。
- 非法线索测试：AI 返回未授权线索，确认被过滤。
- 剧透测试：AI 直接说出幕后压力源，确认监管器拦截。
