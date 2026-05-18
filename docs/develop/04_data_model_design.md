# 04 数据模型设计

## 设计原则

所有核心模型先用 Pydantic 定义，再同步生成或手写 TypeScript 类型。字段名使用 `snake_case`，前端可在类型层保持一致，避免映射错误。

## 模型总表

| 模型 | 前端使用 | 后端使用 | 持久化 |
| --- | --- | --- | --- |
| `DynastyProfile` | 是 | 是 | JSON |
| `PlayerRole` | 是 | 是 | JSON |
| `EventTemplate` | 是 | 是 | JSON |
| `GameSessionState` | 是 | 是 | SQLite/JSON |
| `NPCProfile` | 是 | 是 | JSON |
| `NPCKnowledgePermission` | 否/调试用 | 是 | JSON |
| `Clue` | 是 | 是 | JSON + state |
| `Scene` | 是 | 是 | JSON |
| `DialogueTurn` | 是 | 是 | SQLite |
| `AIResponse` | 是 | 是 | SQLite/log |
| `SupervisorResult` | 调试用 | 是 | SQLite/log |
| `EndingRule` | 是 | 是 | JSON |
| `HistoryEcho` | 是 | 是 | SQLite |

## 字段定义

### DynastyProfile

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `dynasty_id` | string | 朝代 ID，如 `ming`。 |
| `name` | string | 展示名。 |
| `period_label` | string | 时期说明。 |
| `core_mood` | string | 朝代气质。 |
| `allowed_roles` | string[] | 可选身份 ID。 |
| `forbidden_terms` | string[] | 错朝代/现代禁词。 |
| `visual_keywords` | string[] | 视觉风格关键词。 |

示例：

```json
{"dynasty_id":"ming","name":"明代","period_label":"晚明城市书坊语境","core_mood":"皇权压力、文稿风险、书坊生计","allowed_roles":["role_ming_bookshop_apprentice"],"forbidden_terms":["互联网","手机","八旗"],"visual_keywords":["低饱和国风","雨夜","暗红线索"]}
```

### PlayerRole

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `role_id` | string | 身份 ID。 |
| `dynasty_id` | string | 所属朝代。 |
| `name` | string | 展示名。 |
| `social_position` | string | 社会位置。 |
| `permissions` | string[] | 玩家能做的行动边界。 |
| `limitations` | string[] | 不能做的事。 |

示例：

```json
{"role_id":"role_ming_bookshop_apprentice","dynasty_id":"ming","name":"书坊学徒","social_position":"低权力、熟悉书坊空间","permissions":["调查书坊","询问熟人","整理线索"],"limitations":["不能命令锦衣卫","不能直接调阅官府文书"]}
```

### EventTemplate

字段：`event_id:string`、`dynasty_id:string`、`title:string`、`surface_event:string`、`hidden_truth:string`、`stages:string[]`、`scene_ids:string[]`、`npc_ids:string[]`、`required_clue_ids:string[]`、`ending_rule_ids:string[]`。

示例：

```json
{"event_id":"ming_bookshop_fire","dynasty_id":"ming","title":"书坊焚稿案","surface_event":"夜间书坊失火，未刊文稿被烧。","hidden_truth":"有人借火销毁涉及边地粮册的抄录残页。","stages":["intro","investigation","reversal","choice","ending"],"scene_ids":["scene_front_hall","scene_fire_yard"],"npc_ids":["npc_owner","npc_worker","npc_scholar","npc_jinyiwei"],"required_clue_ids":["clue_burned_page"],"ending_rule_ids":["ending_truth","ending_order"]}
```

### GameSessionState

字段：`session_id:string`、`event_id:string`、`dynasty_id:string`、`player_role_id:string`、`current_stage:string`、`current_scene_id:string`、`discovered_clue_ids:string[]`、`npc_trust:object`、`flags:string[]`、`scores:object`、`risk_level:number`、`turn_count:number`、`status:string`。

示例：

```json
{"session_id":"s_001","event_id":"ming_bookshop_fire","dynasty_id":"ming","player_role_id":"role_ming_bookshop_apprentice","current_stage":"investigation","current_scene_id":"scene_fire_yard","discovered_clue_ids":["clue_burned_page"],"npc_trust":{"npc_worker":1},"flags":["found_liaodong_clue"],"scores":{"truth":1,"order":0,"survival":0,"sacrifice":0},"risk_level":1,"turn_count":3,"status":"active"}
```

### NPCProfile

字段：`npc_id:string`、`name:string`、`public_identity:string`、`hidden_motive:string`、`speaking_style:string`、`initial_emotion:string`、`stage_behavior:object`、`releasable_clue_ids:string[]`。

示例：

```json
{"npc_id":"npc_worker","name":"阿沈","public_identity":"书坊刻工","hidden_motive":"隐瞒三更搬箱，避免被牵连","speaking_style":"短句、紧张、压低声音","initial_emotion":"fearful","stage_behavior":{"intro":"回避","investigation":"可被追问"},"releasable_clue_ids":["clue_box_before_dawn"]}
```

### NPCKnowledgePermission

字段：`npc_id:string`、`known_clue_ids:string[]`、`unknown_topics:string[]`、`forbidden_disclosure:string[]`、`trust_unlocks:object`、`stage_unlocks:object`。

示例：

```json
{"npc_id":"npc_worker","known_clue_ids":["clue_box_before_dawn","clue_worker_lie"],"unknown_topics":["幕后上级姓名"],"forbidden_disclosure":["不能直接说出粮册完整来源"],"trust_unlocks":{"1":["clue_worker_lie"],"2":["clue_box_before_dawn"]},"stage_unlocks":{"investigation":["clue_worker_lie"],"reversal":["clue_box_before_dawn"]}}
```

### Clue

字段：`clue_id:string`、`title:string`、`type:string`、`is_key:boolean`、`source_scene_id:string|null`、`source_npc_id:string|null`、`highlight_text:string`、`display_text:string`、`detail:string`、`stage_available:string[]`、`unlock_conditions:object`、`effects:object`、`related_clue_ids:string[]`。

示例：

```json
{"clue_id":"clue_burned_page","title":"烧焦残页","type":"document","is_key":true,"source_scene_id":"scene_fire_yard","source_npc_id":null,"highlight_text":"辽东粮册","display_text":"灰烬里露出残纸，上有辽东粮册四字。","detail":"不是普通诗稿，可能牵涉边地文书。","stage_available":["intro","investigation"],"unlock_conditions":{},"effects":{"truth":1,"risk":1,"flags":["found_liaodong_clue"]},"related_clue_ids":["clue_red_seal"]}
```

### Scene

字段：`scene_id:string`、`name:string`、`description:string`、`background_asset:string`、`available_stage:string[]`、`npc_ids:string[]`、`hotspots:object[]`。

示例：

```json
{"scene_id":"scene_fire_yard","name":"后院火场","description":"雨后灰烬未冷，旧书箱烧得最重。","background_asset":"scene_fire_yard.png","available_stage":["intro","investigation"],"npc_ids":["npc_worker"],"hotspots":[{"hotspot_id":"ash_pile","label":"灰烬","clue_ids":["clue_burned_page"]}]}
```

### DialogueTurn

字段：`turn_id:string`、`session_id:string`、`npc_id:string`、`player_message:string`、`presented_clue_ids:string[]`、`npc_response:string`、`released_clue_ids:string[]`、`created_at:string`。

### AIResponse

字段：`call_id:string`、`module:string`、`raw_text:string`、`parsed_json:object|null`、`success:boolean`、`latency_ms:number`、`fallback_used:boolean`。

### SupervisorResult

字段：`pass:boolean`、`issues:object[]`、`repair_instruction:string|null`、`blocked_clue_ids:string[]`。

示例：

```json
{"pass":false,"issues":[{"type":"spoiler","severity":"high","detail":"提前说出幕后上级"}],"repair_instruction":"改为暗示上级压力，不给出身份。","blocked_clue_ids":["clue_hidden_superior"]}
```

### EndingRule

字段：`ending_id:string`、`title:string`、`priority:number`、`conditions:object`、`required_flags:string[]`、`blocked_flags:string[]`、`result_summary:string`。

### HistoryEcho

字段：`session_id:string`、`ending_id:string`、`text:string`、`referenced_clue_ids:string[]`、`referenced_choice_ids:string[]`、`npc_fates:object`。
