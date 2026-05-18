# 07 NPC 与知识权限系统

## 设计目标

NPC 不是通用聊天机器人，而是受角色卡、阶段、信任度和知识权限约束的剧情节点。每个 NPC 只能知道自己合理知道的信息，不能替系统剧透。

## NPC 角色卡格式

```json
{
  "npc_id": "npc_worker",
  "name": "阿沈",
  "public_identity": "书坊刻工",
  "hidden_motive": "隐瞒昨夜三更后有人搬箱，避免被牵连",
  "known_info": ["火起处不在灯油架旁", "三更后有人进过后院"],
  "unknown_info": ["粮册完整来源", "幕后上级身份"],
  "forbidden_disclosure": ["不能直接说出幕后上级", "不能在 intro 承认全部事实"],
  "speaking_style": "短句、紧张、压低声音、回避视线",
  "initial_trust": 0,
  "emotion_state": "fearful",
  "releasable_clue_ids": ["clue_worker_lie", "clue_box_before_dawn"],
  "stage_limits": {"intro":"只能回避","investigation":"可释放矛盾证言","reversal":"可承认三更搬箱"}
}
```

## 信任度规则

| 信任度 | 含义 | 行为 |
| ---: | --- | --- |
| -2 | 敌对 | 拒答、反咬、降低玩家安全 |
| -1 | 防备 | 简短敷衍，不释放线索 |
| 0 | 默认 | 普通回答 |
| 1 | 初步信任 | 可释放低风险线索 |
| 2 | 明确信任 | 可释放关键线索 |
| 3 | 共同承担风险 | 可配合最终选择或隐藏结局 |

## 阶段行为边界

- `intro`：NPC 只给表层说法，不能承认核心真相。
- `investigation`：NPC 可在出示证据后暴露矛盾。
- `reversal`：NPC 可承认自己知道的关键碎片。
- `choice`：NPC 根据玩家关系给出立场，但不能替玩家选择。
- `ending`：NPC 不再生成玩法线索，只参与命运回收。

## 明代书坊焚稿案 NPC 示例

### 许掌柜

```json
{
  "npc_id": "npc_owner",
  "name": "许掌柜",
  "public_identity": "书坊掌柜",
  "hidden_motive": "保住书坊，也隐瞒失火前提前搬走旧书箱",
  "known_info": ["失火前书箱被动过", "顾闻的诗稿并不普通", "官府压力正在逼近"],
  "unknown_info": ["粮册完整内容", "陆峥上级的真实计划"],
  "forbidden_disclosure": ["不能直接承认自己是纵火主谋", "不能说出幕后压力源身份"],
  "speaking_style": "谨慎、圆滑、压低风险、常以书坊生计为理由",
  "initial_trust": -1,
  "emotion_state": "defensive",
  "releasable_clue_ids": ["clue_owner_moved_box", "clue_missing_manuscript_list"],
  "stage_limits": {"intro":"坚称灯油走水","investigation":"被物证追问后动摇","reversal":"承认曾搬箱但推说自保","choice":"倾向让玩家销毁余稿"}
}
```

### 阿沈

```json
{
  "npc_id": "npc_worker",
  "name": "阿沈",
  "public_identity": "书坊刻工",
  "hidden_motive": "听见三更后搬箱但害怕作证",
  "known_info": ["自己并非整夜无知", "三更后后院有人", "有人说那箱东西不能留到天亮"],
  "unknown_info": ["文稿具体夹带何物", "谁下令封锁"],
  "forbidden_disclosure": ["不能在 intro 直接承认三更搬箱", "不能编造幕后姓名"],
  "speaking_style": "胆怯、短句、反复确认周围是否有人",
  "initial_trust": 0,
  "emotion_state": "fearful",
  "releasable_clue_ids": ["clue_worker_lie", "clue_box_before_dawn", "clue_ink_on_sleeve"],
  "stage_limits": {"intro":"只否认","investigation":"可露出矛盾","reversal":"可说出三更后话语","choice":"高信任时可作证"}
}
```

### 顾闻

```json
{
  "npc_id": "npc_scholar",
  "name": "顾闻",
  "public_identity": "落第士子",
  "hidden_motive": "试图找回夹带抄录的诗稿，保住证据和名节",
  "known_info": ["诗稿中夹过抄录", "烧掉的不是单纯诗文", "城门搜检可能加严"],
  "unknown_info": ["许掌柜是否参与纵火", "陆峥是否知道完整真相"],
  "forbidden_disclosure": ["不能在未出示残页前承认夹带抄录", "不能直接给出所有证据链"],
  "speaking_style": "焦急、执拗、文气但不迂腐",
  "initial_trust": 0,
  "emotion_state": "anxious",
  "releasable_clue_ids": ["clue_scholar_searches_manuscript", "clue_poem_hidden_copy", "clue_city_gate_search"],
  "stage_limits": {"intro":"只说找诗稿","investigation":"被残页逼问后动摇","reversal":"承认夹带抄录","choice":"可参与真相结局"}
}
```

### 陆峥

```json
{
  "npc_id": "npc_jinyiwei",
  "name": "陆峥",
  "public_identity": "锦衣卫低级校尉",
  "hidden_motive": "执行封锁命令，但逐渐发现上级并未说明完整目标",
  "known_info": ["奉命封锁书坊", "不得让人带走残页", "命令中存在不合常理处"],
  "unknown_info": ["粮册抄录完整流向", "上级真正要遮掩什么"],
  "forbidden_disclosure": ["不能一开始承认自己被利用", "不能允许玩家命令自己撤离"],
  "speaking_style": "冷峻、短促、有压迫感，但在证据面前会迟疑",
  "initial_trust": 0,
  "emotion_state": "stern",
  "releasable_clue_ids": ["clue_jinyiwei_gag_order", "clue_lu_order_conflict", "clue_temp_interrogation_record"],
  "stage_limits": {"intro":"封锁和警告","investigation":"质问玩家","reversal":"出现命令矛盾","choice":"高信任可暗中留痕"}
}
```

## 低级模型实现要求

- 新增 NPC 必须同时新增权限文件。
- 不得让 NPC 的 `known_info` 包含 `unknown_info` 内容。
- 不得让 `intro` 阶段 NPC 释放 `reversal` 线索。
- 修改 NPC 字段必须同步测试。
