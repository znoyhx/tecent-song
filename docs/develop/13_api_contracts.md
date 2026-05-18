# 13 前后端 API 合约

## 通用响应约定

错误响应：

```json
{"error":{"code":"SESSION_NOT_FOUND","message":"Session not found","details":{}}}
```

通用错误码：`BAD_REQUEST`、`SESSION_NOT_FOUND`、`INVALID_STAGE_ACTION`、`CLUE_NOT_DISCOVERED`、`AI_UNAVAILABLE`、`INTERNAL_ERROR`。

## GET /api/health

用途：健康检查。

请求：无。

响应示例：

```json
{"status":"ok","version":"0.1.0","mock_ai":true}
```

前端调用时机：启动时。

后端逻辑：返回服务状态，不检查外部 AI。

## GET /api/dynasties

用途：获取朝代入口。

响应示例：

```json
{"dynasties":[{"dynasty_id":"ming","name":"明代","enabled":true},{"dynasty_id":"song","name":"北宋","enabled":false},{"dynasty_id":"tang","name":"晚唐","enabled":false}]}
```

错误码：`INTERNAL_ERROR`。

前端调用时机：开始页加载。

后端逻辑：读取 `DynastyProfile`。

## GET /api/roles

用途：按朝代获取身份。

请求参数：`dynasty_id=ming`。

响应示例：

```json
{"roles":[{"role_id":"role_ming_bookshop_apprentice","name":"书坊学徒","enabled":true}]}
```

错误码：`BAD_REQUEST`。

前端调用时机：玩家选择朝代后。

后端逻辑：过滤 role JSON。

## GET /api/player-identities

用途：根据当前剧本返回 4-6 个玩家自我身份推荐，包含默认身份和背景预览。

请求参数：`dynasty_id=ming&event_id=ming_bookshop_fire`。

响应示例：

```json
{
  "default_identity":"bookshop_apprentice",
  "options":[
    {
      "identity_id":"bookshop_apprentice",
      "display_name":"书坊学徒",
      "description":"熟悉书坊日常，也最容易被卷入嫌疑。",
      "social_rank":"low",
      "relation_to_case":"你本就在书坊守夜，能接触纸稿、账册和后院火场。",
      "attitude_hint":"多数 NPC 会把你当作可驱使的小人物，轻慢中带着试探。",
      "background":"你是书坊里打杂守夜的学徒，熟悉纸张、刻版和前后院动线。",
      "tags":["书坊","守夜","低身份"],
      "is_default":true
    }
  ]
}
```

错误码：`BAD_REQUEST`。

前端调用时机：剧本生成完成页加载“你的身份”区域。

后端逻辑：按朝代、事件和核心 NPC 生成推荐身份；AI 不可用时返回本地中文推荐。

## POST /api/player-identity/validate

用途：校验自定义玩家身份是否适合当前剧本，并生成身份背景。

请求示例：

```json
{"dynasty_id":"ming","event_id":"ming_bookshop_fire","custom_identity_text":"爱喝水的侦探"}
```

合法响应示例：

```json
{
  "is_valid":true,
  "identity":{
    "identity_id":"custom_123",
    "source":"custom",
    "display_name":"爱喝水的侦探",
    "normalized_name":"爱喝水的探事人",
    "description":"爱喝水的侦探能自然查访人情，但仍需要靠证据逐步取信。",
    "background":"你自称是爱喝水的侦探，以探事人的名头在城中行走。",
    "social_rank":"middle",
    "era_fit_score":0.76,
    "story_fit_score":0.82,
    "tags":["中身份","可查访","查案"],
    "is_valid":true,
    "rejection_reason":""
  },
  "rejection_reason":"",
  "suggestions":[],
  "warnings":[]
}
```

非法响应示例：

```json
{"is_valid":false,"identity":null,"rejection_reason":"这个身份暂时不适合当前剧本，请换成时代内可存在、不会压过主线的身份，例如书生、樵夫、游方探事人。","suggestions":["书生","樵夫","游方探事人"],"warnings":[]}
```

错误码：`BAD_REQUEST`。

后端逻辑：先规则拦截现代政治身份、现代职业/科技身份、真实历史大人物、超自然/穿越破坏身份、Prompt 注入和无效文本；再在真实 AI 可用时做语义校验；AI 不可用时使用中文 fallback 校验和背景。

## POST /api/session/start

用途：创建一局游戏。

请求示例：

```json
{"dynasty_id":"ming","role_id":"role_ming_bookshop_apprentice","event_id":"ming_bookshop_fire","identity_id":"bookshop_apprentice"}
```

自定义身份开局示例：

```json
{"dynasty_id":"ming","role_id":"role_ming_bookshop_apprentice","event_id":"ming_bookshop_fire","custom_identity_text":"爱喝水的侦探"}
```

兼容说明：`identity_id` 与 `custom_identity_text` 均可省略；省略时后端使用当前剧本默认身份。若传入自定义身份，后端会重新校验，不信任前端重复传入的身份对象。

响应示例：

```json
{
  "session_id":"s_001",
  "state":{"current_stage":"intro","current_scene_id":"scene_front_hall","risk_level":0},
  "player_identity":{"display_name":"书坊学徒","social_rank":"low","background":"..."},
  "scene":{"scene_id":"scene_front_hall","name":"书坊前厅"},
  "available_actions":["investigate","dialogue"]
}
```

错误码：`BAD_REQUEST`。

前端调用时机：点击开始游戏。

后端逻辑：校验 dynasty/role/event，创建初始 state。

## GET /api/session/{session_id}

用途：读取会话状态。

响应示例：

```json
{"session_id":"s_001","state":{},"scene":{},"clues":[],"dialogue_turns":[]}
```

错误码：`SESSION_NOT_FOUND`。

前端调用时机：刷新页面或调试。

后端逻辑：查询持久化会话并组装展示数据。

## POST /api/dialogue

用途：与 NPC 对话。

请求示例：

```json
{"session_id":"s_001","npc_id":"npc_worker","message":"你昨夜听见了什么？","action_type":"question","presented_clue_ids":["clue_worker_lie"]}
```

响应字段：`dialogue`、`new_clues`、`state`、`supervisor`、`fallback_used`。

响应示例：

```json
{"dialogue":{"npc_id":"npc_worker","npc_dialogue":"我只听见有人说那箱东西不能留到天亮。","emotion":"fearful"},"new_clues":[{"clue_id":"clue_box_before_dawn","title":"三更搬箱"}],"state":{"current_stage":"investigation","risk_level":2},"supervisor":{"pass":true,"issues":[]},"fallback_used":false}
```

错误码：`SESSION_NOT_FOUND`、`CLUE_NOT_DISCOVERED`、`AI_UNAVAILABLE`。

前端调用时机：玩家提交输入或推荐追问。

后端逻辑：执行 NPC 对话链路。

## POST /api/investigate

用途：调查场景热点或点击高亮线索。

请求示例：

```json
{"session_id":"s_001","scene_id":"scene_fire_yard","hotspot_id":"ash_pile","clue_id":"clue_burned_page"}
```

响应示例：

```json
{"text":"灰烬里露出一角残纸。","new_clues":[{"clue_id":"clue_burned_page","title":"烧焦残页"}],"state":{"current_stage":"investigation"}}
```

错误码：`INVALID_STAGE_ACTION`、`BAD_REQUEST`。

前端调用时机：点击热点/高亮。

后端逻辑：检查场景和阶段，释放合法线索，评估状态机。

## POST /api/choice

用途：提交关键选择。

请求示例：

```json
{"session_id":"s_001","choice_id":"choice_give_to_lu"}
```

响应示例：

```json
{"state":{"current_stage":"ending","scores":{"order":5}},"next":"resolve_ending"}
```

错误码：`INVALID_STAGE_ACTION`。

前端调用时机：`choice` 阶段点击选择卡。

后端逻辑：更新分数、flags、risk，进入 ending 阶段。

## POST /api/ending/resolve

用途：判定并返回结局。

请求示例：

```json
{"session_id":"s_001"}
```

响应示例：

```json
{"ending_id":"ending_order","title":"交还官府","summary":"陆峥带走残页，事件被定为普通失火。","history_echo":"你选择相信秩序，但秩序未必选择真相。","npc_fates":{"npc_worker":"继续沉默","npc_scholar":"被迫离城"}}
```

错误码：`SESSION_NOT_FOUND`、`INVALID_STAGE_ACTION`。

前端调用时机：提交 choice 后。

后端逻辑：按 EndingRule 判定，生成或读取历史回声。
