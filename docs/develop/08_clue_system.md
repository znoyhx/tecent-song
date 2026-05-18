# 08 线索系统

## 目标

线索是本项目的核心玩法，不是收藏文本。每条线索至少影响一种内容：NPC 对话、剧情阶段、信任度、风险、结局、线索组合或可进入场景。

## 线索字段定义

```json
{
  "clue_id": "clue_burned_page",
  "title": "烧焦残页",
  "type": "document",
  "is_key": true,
  "source_scene_id": "scene_fire_yard",
  "source_npc_id": null,
  "highlight_text": "辽东粮册",
  "display_text": "灰烬中残留一角纸页，上有辽东粮册四字。",
  "detail": "这不像普通诗稿，更像边地粮册抄录的一部分。",
  "stage_available": ["intro", "investigation"],
  "unlock_conditions": {},
  "effects": {"truth": 1, "risk": 1, "flags": ["found_liaodong_clue"]},
  "related_clue_ids": ["clue_red_seal", "clue_poem_hidden_copy"]
}
```

## 普通线索与关键线索

- 普通线索：提供氛围、辅助推理、改变小幅信任或风险。
- 关键线索：能推进阶段、解锁关键对话、影响结局或触发组合。

关键线索必须有 `is_key=true`，并在测试中验证其至少影响一个阶段或结局。

## 释放方式

1. 场景热点调查释放。
2. NPC 对话释放。
3. 出示证据后释放。
4. 线索组合后释放推理结论。
5. 关键选择前补充说明释放。

## 前端展示

场景文本中可点击部分使用结构化数据，不要直接信任 AI HTML：

```json
{
  "text": "灰烬里露出一角残纸，上面残留着辽东粮册四字。",
  "highlights": [{"text":"辽东粮册","clue_id":"clue_burned_page"}]
}
```

前端渲染为红色高亮；点击后调用 `POST /api/investigate` 或本地打开详情。

## 线索如何影响剧情

- `clue_fire_origin_wrong` + `clue_oil_smell` + `clue_backdoor_latch` 组合为 `combo_fire_is_arson`。
- `clue_burned_page` + `clue_red_seal` + `clue_poem_hidden_copy` 组合为 `combo_burned_text_is_ledger`。
- 发现 `clue_jinyiwei_gag_order` 后可进入 `choice`。

## 明代书坊焚稿案 15 条线索

| ID | 标题 | 类型 | 来源 | 关键 | 作用 |
| --- | --- | --- | --- | --- | --- |
| `clue_fire_origin_wrong` | 火起点异常 | 环境 | 后院火场 | 是 | 证明灯油走水说法可疑 |
| `clue_burned_page` | 烧焦残页 | 文书 | 后院灰烬 | 是 | 引出“辽东粮册” |
| `clue_red_seal` | 半枚红印纸角 | 文书 | 旧书箱 | 是 | 连接官府文书 |
| `clue_oil_smell` | 异常火油味 | 环境 | 灯油架旁 | 是 | 支持人为纵火 |
| `clue_backdoor_latch` | 后门门闩松动 | 环境 | 后门 | 否 | 支持有人夜间进出 |
| `clue_worker_lie` | 刻工矛盾证言 | 证言 | 阿沈 | 是 | 推翻“整夜在刻坊” |
| `clue_ink_on_sleeve` | 袖口旧墨 | 物证 | 阿沈 | 否 | 说明阿沈接触过旧稿 |
| `clue_box_before_dawn` | 三更搬箱 | 证言 | 阿沈 | 是 | 推进至反转线索链 |
| `clue_owner_moved_box` | 掌柜提前清箱 | 证言/行为 | 许掌柜 | 是 | 掌柜隐瞒动作 |
| `clue_missing_manuscript_list` | 缺失稿单 | 文书 | 前厅账册 | 否 | 指向顾闻诗稿不普通 |
| `clue_scholar_searches_manuscript` | 士子急寻旧稿 | 证言 | 顾闻 | 否 | 说明顾闻另有所求 |
| `clue_poem_hidden_copy` | 诗稿夹带抄录 | 文书 | 顾闻 | 是 | 证明烧的不是普通诗 |
| `clue_jinyiwei_gag_order` | 锦衣卫封口令 | 文书 | 临时审问处 | 是 | 进入 choice 的关键线索 |
| `clue_lu_order_conflict` | 陆峥命令矛盾 | 证言 | 陆峥 | 是 | 说明陆峥也未掌握全局 |
| `clue_city_gate_search` | 城门搜检加严 | 环境/传闻 | 雨巷 | 否 | 提升风险并支持外部压力 |

## 线索与 NPC 绑定

| NPC | 可释放线索 |
| --- | --- |
| 许掌柜 | `clue_owner_moved_box`, `clue_missing_manuscript_list` |
| 阿沈 | `clue_worker_lie`, `clue_ink_on_sleeve`, `clue_box_before_dawn` |
| 顾闻 | `clue_scholar_searches_manuscript`, `clue_poem_hidden_copy`, `clue_city_gate_search` |
| 陆峥 | `clue_jinyiwei_gag_order`, `clue_lu_order_conflict` |

## 线索组合

```json
{
  "combo_id": "combo_fire_is_arson",
  "required_clue_ids": ["clue_fire_origin_wrong", "clue_oil_smell", "clue_backdoor_latch"],
  "result_title": "火灾并非意外",
  "result_text": "火起位置、火油气味和门闩异常共同说明失火更可能是人为。",
  "effects": {"truth": 2, "risk": 1, "flags": ["fire_is_arson"]}
}
```

## 测试要求

- 每条线索能被获得且不重复加入。
- 未满足阶段/条件时不能释放关键线索。
- 红色高亮点击后线索进入侧栏。
- 线索组合必须检查所有 required clues。
- 结局判定能读取线索和 flags。
