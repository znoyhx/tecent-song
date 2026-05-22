# 23 DeepSeek AI 剧本生成需求

## 1. 需求定位

本阶段目标是把《史隙》从“固定主 Demo + 局部 AI 对话”推进到“由 DeepSeek 生成完整可玩的历史悬疑剧本包”。

这里的剧本生成不是给现有明代书坊焚稿案换几段文案，也不是只生成 NPC 台词。系统应允许 DeepSeek 根据用户选择或系统种子生成一个新的历史事件世界，包括故事内容、人物、地点、线索链、人物对话约束、关键抉择、结局、人物立绘 prompt、场景图 prompt、场景中的线索物件和线索图片 prompt。

当前明代书坊焚稿案只作为三类用途存在：

- 已有路演 Demo 和稳定 fallback；
- 生成数据格式、玩法闭环、导入流程的参考样例；
- 回归测试用的固定剧本。

它不应成为 AI 剧本生成器的内容边界。新的生成能力必须支持跨朝代、跨地点、跨职业身份、跨案件类型的剧本生产。

## 2. 产品目标

AI 剧本生成器要证明的能力是：

```text
玩家选择一个历史方向
  -> DeepSeek 生成一个完整历史悬疑事件世界
  -> 系统校验其历史可信、结构完整、玩法可执行
  -> 生成视觉资产需求
  -> 导入现有 React + Phaser + FastAPI 游戏框架
  -> 玩家能从开局调查到分支结局
```

最终体验应接近“AI 帮玩家即时开出一局历史剧本杀 / 推理视觉小说”，而不是“AI 讲一个故事给玩家看”。

核心要求：

- 每个剧本必须有强故事线、可调查空间、人物关系、误导线、反转、选择代价和多结局。
- 每条核心线索必须能进入玩法系统，影响阶段、对话、信任、推理或结局。
- 每个 NPC 必须有明确身份、动机、恐惧、信息边界和可变化态度。
- 每个地点必须有可视化场景、可点击热点和线索物件。
- 每局都应能被导入通用游戏引擎，而不是依赖硬编码的明代书坊案逻辑。

## 3. 生成范围

### 3.1 支持的历史方向

P0 不应限定为明代书坊案。当前阶段建议采用“兼容现有 Demo 的受控开放生成”：

```text
明代：继续进入现有固定路演 Demo，不走 AI 剧本生成流程
北宋：进入关键词填写页，再调用 DeepSeek 生成新剧本
晚唐 / 唐后期：进入关键词填写页，再调用 DeepSeek 生成新剧本
身份：从系统已有身份库中选择，或由 AI 在朝代约束内生成
案件类型：由系统提供类型池，DeepSeek 组合生成
地点：由 DeepSeek 根据朝代、身份、案件类型生成
人物：由 DeepSeek 生成，但必须通过身份、称谓、制度校验
线索：由 DeepSeek 生成，但必须通过线索图和规则图校验
```

这不是把 AI 生成器重新限制回明代书坊案，而是当前版本的兼容策略：明代已经有稳定可演示闭环，应继续作为固定 Demo 和 fallback；北宋、晚唐原本只是轻量预览入口，正适合承接“用户关键词 -> AI 生成剧本”的新能力。

P0 可以限制在已有朝代知识库内，避免完全任意历史时期带来的资料不足和监管困难。但在北宋和晚唐内，不应只做固定主线的变体。

### 3.2 当前入口兼容矩阵

| 用户选择 | 当前行为 | 是否进入 AI 剧本生成 | 说明 |
| --- | --- | --- | --- |
| 明代 | 直接启动现有书坊焚稿案 Demo | 否 | 保护路演稳定性，继续使用现有数据、场景、线索和结局 |
| 北宋 | 进入关键词填写页 | 是 | 根据关键词、朝代知识库和玩法结构生成新剧本 |
| 晚唐 / 唐后期 | 进入关键词填写页 | 是 | 根据关键词、朝代知识库和玩法结构生成新剧本 |

前端路由应表达清楚：

```text
选择明代
  -> 直接开始固定 Demo

选择北宋 / 晚唐
  -> 显示关键词输入
  -> 用户填写 1-8 个关键词
  -> 调用 /api/scripts/generate
  -> 等待多轮打磨、校验、视觉 prompt 和热点定位
  -> 进入生成剧本
```

后端也要做保护：P0 默认不接受 `dynasty_id=ming` 的 `/api/scripts/generate` 请求，除非显式开启开发用 feature flag。若误传明代，应返回清晰错误，例如 `AI_GENERATION_DISABLED_FOR_STABLE_DEMO`，而不是悄悄生成一个明代变体。

可选案件类型池：

- 文书异常；
- 火灾 / 失窃 / 失踪；
- 军报延误；
- 粮册亏空；
- 驿站换牒；
- 科举舞弊；
- 商税纠纷；
- 工匠事故；
- 私印伪造；
- 城门搜检；
- 船运沉货；
- 寺观藏物；
- 边地谣言。

### 3.3 P0 内容体量

每个可玩剧本包至少包含：

| 类型 | 最小数量 | 说明 |
| --- | ---: | --- |
| 剧情阶段 | 5 | `intro -> investigation -> reversal -> choice -> ending`，可扩展命名 |
| 地点 | 5 | 每个地点有描述、热点、视觉 prompt |
| NPC | 4 | 至少 3 个可对话，1 个可作为幕后压力源 |
| 线索 | 12 | 至少 6 条核心线索、3 条误导线索、3 条背景线索 |
| 线索组合 | 4 | 能推出阶段推进、人物矛盾或结局资格 |
| 关键选择 | 4 | 每个选择改变分数、风险、NPC 命运或结局 |
| 结局 | 4 | 至少覆盖自保、秩序、真相、悲剧，可含隐藏结局 |
| 场景图 prompt | 5 | 每个地点 1 条 |
| 人物图 prompt | 4 | 每个主要 NPC 1 条 |
| 线索图 prompt | 6 | 至少核心线索都有图片需求 |

## 4. 用户输入

剧本生成入口只在北宋和晚唐 / 唐后期入口出现。明代入口不展示关键词生成表单，仍然直接进入现有固定 Demo。

AI 生成表单应接受一组轻量输入，而不是要求用户写复杂 prompt。关键词是当前阶段的核心输入，用户用它表达想看的历史事件、地点、人物关系、悬疑气质或关键物件。

建议输入：

```json
{
  "dynasty_id": "song",
  "player_identity_id": "auto",
  "keywords": ["驿站", "军报", "雨夜", "粮草"],
  "case_type": "auto",
  "tone": "historical_suspense",
  "difficulty": "normal",
  "session_length": "roadshow",
  "visual_style": "low_saturation_chinese_historical_suspense",
  "seed": "optional-user-seed"
}
```

字段说明：

- `dynasty_id`：P0 只允许 `song` 或 `late_tang` 进入 AI 生成；`ming` 走固定 Demo。
- `player_identity_id`：可由用户选择，也可设为 `auto` 让系统生成。
- `keywords`：用户填写的生成关键词，建议 1-8 个，不能为空。关键词可以是地点、事件、物件、人物关系或氛围，例如“驿站 / 军报 / 雨夜 / 粮草”。
- `case_type`：案件类型，不是固定剧情；可设为 `auto`，由 DeepSeek 根据关键词和朝代知识库选择。
- `tone`：叙事气质，例如悬疑、压迫、诡谲、悲凉。
- `difficulty`：影响线索数量、误导强度、结局门槛。
- `session_length`：影响剧本体量，路演版应控制在 10-15 分钟可通关。
- `visual_style`：传给视觉 prompt 生成。
- `seed`：用于生成可复现剧本。

关键词约束：

- 关键词必须经过后端清洗和长度限制，避免把长 prompt 直接透传给 DeepSeek。
- 关键词不能覆盖朝代边界；例如选择北宋时，关键词里出现“锦衣卫”应被监管器纠正或拒绝。
- 关键词可以影响题材方向，但不能绕过玩法结构、监管器和历史知识库。
- 如果关键词过于空泛，例如“好玩”“刺激”，系统应提示用户补充至少一个具体地点、物件、职业或事件。

## 5. 剧本包数据结构

DeepSeek 最终输出应被解析为 `ScriptPackage`。所有字段必须结构化，后端不得直接相信模型散文。

```json
{
  "script_id": "song_relay_clerk_001",
  "title": "夜驿迟报",
  "version": "1.0",
  "dynasty": {},
  "player_identity": {},
  "playable_identities": [],
  "script_overview": {},
  "world": {},
  "story": {},
  "stages": [],
  "locations": [],
  "npcs": [],
  "relationships": [],
  "clues": [],
  "clue_graph": [],
  "dialogue_rules": [],
  "choices": [],
  "endings": [],
  "visual_assets": [],
  "visual_style_guide": {},
  "hotspot_positioning": [],
  "rules": {},
  "historical_anchors": [],
  "supervision_constraints": []
}
```

### 5.1 World

```json
{
  "world_summary": "北宋边地驿站一封军报延误，表面是雨夜马匹失蹄，实际牵出驿券、边防虚报与地方官的互相遮掩。",
  "historical_pressure": ["边报时限", "驿站劳役", "地方官考课", "军粮调拨"],
  "public_explanation": "军报因暴雨延误",
  "hidden_truth": "有人调换驿券并压下前线缺粮消息",
  "central_question": "玩家要保住驿站众人，还是让一封可能引发清算的军报继续上达？"
}
```

### 5.2 Script Overview

剧本生成完成后，前端必须展示从 `ScriptPackage` 读取的剧本概览，而不是继续使用北宋 / 晚唐的静态占位文案。概览内容用于让玩家确认本局主题、风险和可选身份，但不能剧透最终真相。

```json
{
  "script_overview": {
    "title": "夜驿迟报",
    "dynasty_label": "北宋",
    "generated_from_keywords": ["驿站", "军报", "雨夜", "粮草"],
    "one_sentence_hook": "雨夜里，驿马空鞍而归，一封边地军报却迟迟不见。",
    "public_case": "军报延误被解释为雨夜事故。",
    "player_goal": "查清军报为何延误，并决定是否让危险文书继续上达。",
    "tone_tags": ["历史悬疑", "雨夜", "文书疑案", "边地压力"],
    "estimated_play_time": "10-15 分钟",
    "difficulty_label": "普通",
    "non_spoiler_location_preview": ["驿站前院", "文书房", "马厩", "雨夜官道", "临时问询处"],
    "non_spoiler_npc_preview": ["驿丞", "马夫", "过路商人", "押送小吏"]
  }
}
```

概览约束：

- 只能展示表层案件、玩家目标、氛围、地点预览和人物身份预览。
- 不展示幕后主使、最终真相、隐藏线索和结局条件。
- 所有内容必须来自生成后的 `ScriptPackage`。
- 若图片已通过门禁，可以展示 approved 主场景缩略图；未通过时不能用占位图冒充概览主图。

### 5.3 Playable Identities

北宋 / 晚唐 AI 生成剧本完成后，应进入选人界面。可选身份必须来自生成好的剧本包，并且每个身份都要与本局案件有合理行动权限。

```json
{
  "playable_identities": [
    {
      "identity_id": "player_relay_clerk",
      "display_name": "驿站文书",
      "identity_summary": "负责登记驿券和封套，能接触文书房与驿站账册。",
      "starting_location_id": "loc_relay_document_room",
      "starting_trust": {
        "npc_station_master": 1,
        "npc_groom": 1
      },
      "permissions": ["inspect_documents", "question_station_staff", "access_relay_records"],
      "limitations": ["不能直接调阅军报正文", "不能命令官兵"],
      "difficulty_modifier": "normal",
      "recommended": true
    }
  ]
}
```

选人要求：

- 至少生成 2 个可选身份，P0 可以推荐其中 1 个。
- 每个身份要改变起始地点、NPC 初始信任、可调查权限或对话入口。
- 如果用户在生成前选择了具体身份，则完成页可以预选该身份；如果输入为 `auto`，必须让用户在生成后选择。
- 不能展示与剧本无关的静态身份卡。
- 选择身份后才调用 `POST /api/session/start-generated`。

### 5.4 Story

```json
{
  "hook": "雨夜中，驿马空鞍而归，封套破损的军报却迟迟不见。",
  "truth_layers": [
    "军报不是自然延误",
    "驿券被人调换",
    "延误掩盖了边地粮册问题",
    "玩家的身份使其既能查到文书，也最容易被推为替罪者"
  ],
  "misdirections": [
    "马夫看似失职",
    "过路商人看似偷走军报",
    "驿丞看似主谋"
  ],
  "emotional_core": "小吏是否要为一封自己没有资格过问的军报承担风险"
}
```

### 5.5 Location

```json
{
  "location_id": "loc_relay_courtyard",
  "name": "驿站前院",
  "stage_availability": ["intro", "investigation"],
  "description": "雨水冲散马蹄印，檐下挂着未干的驿牌。",
  "present_npc_ids": ["npc_station_master", "npc_groom"],
  "hotspots": [
    {
      "hotspot_id": "hotspot_empty_saddle",
      "label": "空鞍",
      "linked_clue_id": "clue_cut_saddle_strap",
      "visual_anchor": "画面左下角的湿马鞍，皮带边缘有整齐割痕",
      "expected_position": { "x": 0.22, "y": 0.72 }
    }
  ],
  "visual_asset_id": "scene_relay_courtyard",
  "scene_prompt_id": "prompt_scene_relay_courtyard"
}
```

### 5.6 NPC

```json
{
  "npc_id": "npc_station_master",
  "name": "周驿丞",
  "identity": "北宋边地驿站驿丞",
  "surface_goal": "把军报延误解释为雨夜事故",
  "hidden_motive": "害怕驿站被问责，也害怕上级查到旧账",
  "knows": ["驿券昨夜被重新登记", "马夫没有按原路线出发"],
  "does_not_know": ["军报内的完整内容", "幕后调换驿券者的真实身份"],
  "can_reveal_by_stage": {
    "intro": ["事故说法"],
    "investigation": ["驿券登记异常"],
    "reversal": ["上级来信压力"]
  },
  "trust_rules": {
    "gain": ["玩家出示非公开羞辱类证据", "玩家保护驿站杂役"],
    "lose": ["玩家直接威胁上报", "玩家向外人泄露驿站内情"]
  },
  "portrait_prompt_id": "prompt_npc_station_master"
}
```

### 5.7 Clue

```json
{
  "clue_id": "clue_cut_saddle_strap",
  "name": "被割开的鞍带",
  "category": "physical",
  "discoverable_at": {
    "location_id": "loc_relay_courtyard",
    "hotspot_id": "hotspot_empty_saddle",
    "stage": "intro"
  },
  "description": "鞍带断口平整，不像雨夜奔逃时自然磨断。",
  "gameplay_effect": {
    "flags_added": ["sabotage_suspected"],
    "truth_score": 1,
    "risk_score": 0
  },
  "unlocks": ["question_groom_about_route"],
  "misleading": false,
  "core": true,
  "image_prompt_id": "prompt_clue_cut_saddle_strap"
}
```

### 5.8 Clue Graph

```json
{
  "deduction_id": "deduction_report_delay_not_accident",
  "required_clue_ids": [
    "clue_cut_saddle_strap",
    "clue_wrong_relay_ticket",
    "clue_rain_sheltered_hoofprints"
  ],
  "conclusion": "军报延误不是单纯雨夜事故，而是有人预先制造路线中断。",
  "effects": {
    "stage_transition": "reversal",
    "flags_added": ["delay_is_planned"],
    "unlocked_location_ids": ["loc_document_room"]
  }
}
```

### 5.9 Dialogue Rules

对话规则不是完整逐字剧本，而是运行时 NPC 对话的边界。

```json
{
  "npc_id": "npc_groom",
  "stage": "investigation",
  "allowed_topics": ["马匹状态", "出发时辰", "驿券登记", "雨夜路线"],
  "forbidden_reveals": ["幕后主使身份", "军报完整内容", "最终结局条件"],
  "tone": "害怕、急于自保、对玩家仍有同僚信任",
  "evidence_responses": [
    {
      "clue_id": "clue_cut_saddle_strap",
      "response_intent": "承认鞍带不是自然断裂，但不敢说看见谁动手"
    }
  ]
}
```

### 5.10 Visual Assets

视觉资产需求由 DeepSeek 生成 prompt，生图服务负责真正出图并落盘。

```json
{
  "asset_id": "scene_relay_courtyard",
  "asset_type": "integrated_scene",
  "target_ref": "loc_relay_courtyard",
  "prompt": "北宋边地驿站雨夜后的前院，低饱和中国历史悬疑视觉小说场景，湿泥地、空马鞍、檐下驿牌、周驿丞站在廊下，马夫低头躲在一旁，画面左下角湿马鞍皮带有整齐割痕，可作为可点击线索物件，同一透视、同一光源、暗色雨雾、细腻火灯光",
  "negative_prompt": "现代建筑，电灯，汽车，手机，清代辫发，日式盔甲，赛博朋克，英文文字，卡通夸张"
}
```

### 5.11 Visual Style Guide

每个剧本包必须生成一份统一视觉风格指南。它不是展示文案，而是后续场景图、人物立绘、线索图、UI 缩略图 prompt 的共同约束。之前遇到过人物风格不统一、人物像从不同游戏里来的问题，因此 DeepSeek 不能只给每张图单独写 prompt。

```json
{
  "visual_style_guide": {
    "style_name": "低饱和中国历史悬疑视觉小说",
    "dynasty_id": "song",
    "palette": ["湿青灰", "旧纸黄", "暗朱", "灯火暖金"],
    "lighting": "雨夜冷环境光与油灯暖光混合，低对比但关键线索有可见边缘光",
    "line_and_texture": "写实偏绘本质感，细腻布料、木器、纸张和泥水纹理",
    "camera": "电影式中景，人物和线索物件同一透视，不使用夸张漫画镜头",
    "character_style": "人物五官写实克制，服饰层次符合朝代身份，避免现代妆发和网游盔甲",
    "scene_style": "建筑、家具、器物、文字材料符合所选朝代和地点等级",
    "clue_image_style": "线索特写仍保持同一光源、材质和色调，不像独立商品图",
    "global_negative_prompt": "现代城市，电灯，汽车，手机，玻璃幕墙，清代辫发，日式武士，欧洲中世纪盔甲，赛博朋克，英文招牌，现代印刷字体"
  }
}
```

人物视觉还需要稳定描述。每个主要 NPC 都要有 `appearance_lock`，用于人物弹窗立绘、场景融合图、关系图头像保持一致。

```json
{
  "npc_id": "npc_station_master",
  "appearance_lock": {
    "age_range": "四十岁上下",
    "body_shape": "清瘦微驼",
    "face_features": "长脸、眉骨低、眼下有疲态",
    "hair_and_hat": "北宋小吏幞头，发髻不外露",
    "costume": "旧青灰圆领公服，袖口有雨痕",
    "signature_prop": "磨旧驿牌和账册袋",
    "do_not_change": ["年龄段", "帽式", "青灰公服", "疲惫神态"]
  }
}
```

### 5.12 Era Feature Checklist

每张场景图必须附带朝代特征检查表。视觉 prompt 不能只写“古风”，必须写清楚建筑、衣冠、器物、文书、照明和空间等级。生图后也要用这张表做人工或模型复核。

```json
{
  "asset_id": "scene_relay_courtyard",
  "era_feature_checklist": {
    "architecture": ["驿站院落", "木构廊檐", "泥地", "马厩"],
    "costume": ["北宋小吏幞头", "短褐杂役服", "无清代辫发"],
    "props": ["驿牌", "马鞍", "封套", "油灯", "木质文书柜"],
    "writing_materials": ["纸质封套", "手写墨迹", "无现代印刷字体"],
    "lighting": ["油灯", "天光", "无电灯"],
    "forbidden_elements": ["玻璃窗", "水泥路", "霓虹", "现代雨衣", "清代官帽"]
  }
}
```

### 5.13 Hotspot Positioning

线索互动位置必须通过定位数据确定，不能只依赖自然语言描述。DeepSeek 可以给出初始视觉锚点，但最终进入 Phaser 的坐标必须是结构化坐标，并且与生成后的图片对应。

推荐坐标格式：

```json
{
  "asset_id": "scene_relay_courtyard",
  "hotspot_id": "hotspot_empty_saddle",
  "linked_clue_id": "clue_cut_saddle_strap",
  "visual_anchor": "画面左下角的湿马鞍，皮带边缘有整齐割痕",
  "position": {
    "coordinate_space": "normalized_image",
    "anchor_point": { "x": 0.22, "y": 0.72 },
    "bbox": { "x": 0.15, "y": 0.63, "width": 0.18, "height": 0.15 },
    "polygon": [
      { "x": 0.14, "y": 0.64 },
      { "x": 0.34, "y": 0.65 },
      { "x": 0.32, "y": 0.78 },
      { "x": 0.16, "y": 0.80 }
    ]
  },
  "position_source": "ai_estimate",
  "calibration_status": "needs_review",
  "confidence": 0.68
}
```

定位规则：

- 坐标使用 `0-1` 归一化图片坐标，不直接写像素，避免不同分辨率错位。
- P0 至少支持 `anchor_point` 和 `bbox`；P1 支持 `polygon`。
- DeepSeek 只能提供 `ai_estimate` 初始位置。
- 图片生成后必须经过 `manual_review`、`vision_model_review` 或 `debug_tool_calibrated` 之一，才能标记为 `approved`。
- `approved` 之前前端可以显示热点，但调试面板必须标记“待校准”。
- 如果生图结果中没有出现线索物件，必须重新生成图片或修改 prompt，不能把热点放在不存在的物件上。
- 同一场景的 NPC 点击区域也使用同一套定位格式。

### 5.14 Image Quality Gate

AI 生成图片是本功能的阻塞项。生成剧本不能只停留在 prompt 层，也不能用占位图、空白图或风格错误的图片冒充完成。每张进入正式剧本的场景图、人物图和核心线索图都必须通过 `ImageQualityGate`。

图片状态建议：

```json
{
  "asset_id": "scene_relay_courtyard",
  "asset_type": "integrated_scene",
  "generation_status": "approved",
  "quality_gate": {
    "blank_check": "pass",
    "style_check": "pass",
    "era_check": "pass",
    "content_check": "pass",
    "character_consistency_check": "pass",
    "clue_visibility_check": "pass",
    "hotspot_alignment_check": "pass",
    "review_method": "vision_model_review",
    "retry_count": 1,
    "last_rejection_reason": "第一版缺少空马鞍线索物件，已重生。"
  }
}
```

必须拒绝并重新请求的情况：

- 图片为空白、纯色、严重模糊、损坏、加载失败；
- 图片是占位图、默认 fallback、旧缓存或与本剧本无关的历史资产；
- 场景图没有体现所选朝代的建筑、服饰、器物或照明特征；
- 出现现代物品、错朝代服饰、错制度符号、现代文字或明显异世界风格；
- 人物图与 `appearance_lock` 冲突，或同一 NPC 在不同图中像不同人物；
- 场景图中的人物风格与人物立绘明显不一致；
- 核心线索图没有表现线索本体，或像无关装饰图；
- 集成场景图没有包含可点击核心线索物件；
- 线索物件太小、被遮挡、无法定位，导致 Phaser 热点无法可靠点击；
- 整体风格与 `visual_style_guide` 不一致，例如过亮、过卡通、网游感、现代商业插画感过强。

重试规则：

- 每个必需资产生成后立即进入 `ImageQualityGate`。
- 未通过时应根据拒绝原因改写 prompt，再重新请求生图。
- P0 每个资产至少允许 3 次自动重试。
- 3 次仍失败时，该剧本 job 标记为 `visual_blocked` 或 `failed`，不得作为已完成剧本进入正式游玩。
- 开发调试模式可以临时显示占位图，但 UI 和日志必须明确标记“图片未通过验收”；该状态不能通过 P0 验收。
- 如果场景图重生导致物件位置变化，必须重新执行热点坐标校准。
- 只有 `generation_status=approved` 的图片才能计入路演完成度。

## 6. 生成流程

推荐采用“先生成剧本包，再运行游戏”的流程，避免一边游玩一边临时生成导致线索断链。

```text
1. 用户选择朝代、身份、案件类型和风格
2. 若选择明代，直接启动现有固定 Demo，不进入本流程
3. 若选择北宋 / 晚唐，用户填写关键词
4. 后端读取朝代知识库、身份库、关键词和案件类型约束
5. DeepSeek 生成 2-3 个剧本 pitch
6. 系统选择或用户选择一个 pitch
7. DeepSeek 生成初版 ScriptPackage JSON
8. DeepSeek 多轮打磨剧本，检查缺漏、逻辑 BUG、人物薄弱和视觉问题
9. SchemaValidator 做结构校验
10. ScriptSupervisor 做历史、玩法、剧透、线索链校验
11. RepairAgent 修复不合格字段
12. VisualPromptAgent 补齐或规范化视觉 prompt、风格指南和朝代特征检查表
13. VisualAssetService 排队生成场景、人物、线索图片
14. ImageQualityGate 审查图片，拒绝空白、占位、错风格、错朝代和缺线索物件的图片
15. 未通过图片质量门禁时，改写 prompt 并重新请求生图
16. HotspotCalibrationService 基于通过门禁的图片生成或校准 Phaser 热点坐标
17. ScriptImportService 转换为游戏引擎可读取的数据
18. 玩家从生成剧本启动 session
```

P0 可以暂时跳过用户选择 pitch，直接使用系统评分最高的 pitch。

### 6.1 生成进度流程图

北宋 / 晚唐进入 AI 生成后，前端必须展示生成流程图。这个流程图不是装饰性 loading，而是严格绑定后端 job 的真实进度。

流程节点建议：

```text
关键词校验
  -> 剧本方向生成
  -> 剧本初稿
  -> 编剧审稿
  -> 逻辑 QA
  -> NPC 权限审查
  -> 游玩模拟
  -> 视觉连续性审查
  -> 图片生成
  -> 图片质量门禁
  -> 热点定位校准
  -> 剧本导入
  -> 剧本概览与选人
```

每个节点只能使用后端返回的状态：

```json
{
  "step_key": "image_quality_gate",
  "label": "图片质量门禁",
  "status": "running",
  "started_at": "2026-05-22T20:12:00+08:00",
  "finished_at": null,
  "progress": 0.46,
  "summary": "已通过 7 / 15 张图片，2 张因缺少线索物件正在重试。",
  "blocking_issue_count": 0
}
```

状态规则：

- 前端不能用定时器假装推进流程。
- 后端没有进入某阶段时，流程图必须停在上一阶段或显示等待。
- `running`、`passed`、`failed`、`blocked`、`retrying` 要有清晰区分。
- 图片重试、剧本修复、热点重校准都要反映在流程图中。
- 如果 job 失败，流程图停在失败节点并展示失败原因，不自动跳到完成页。

### 6.2 等待过渡名句

生成期间可以展示历史相关名人名句作为过渡内容，但它们不能替代真实进度，也不能暗示生成阶段已经完成。

名句要求：

- 从本地 curated quote pool 读取，优先匹配当前朝代或主题。
- 每条包含 `quote_text`、`author`、`dynasty_label`、`source_label`、`theme_tags`。
- 只做等待页氛围和文化表达，不进入剧本事实、不影响 AI 生成。
- 不展示未经校验的现代伪名言。
- 不展示与当前朝代明显冲突的句子，除非明确标注为跨时代引用。
- 轮播频率建议 6-10 秒，不推动进度条。

示例：

```json
{
  "quote_text": "纸上得来终觉浅，绝知此事要躬行。",
  "author": "陆游",
  "dynasty_label": "南宋",
  "source_label": "《冬夜读书示子聿》",
  "theme_tags": ["求证", "调查", "纸本文书"]
}
```

### 6.3 生成完成后的剧本概览与选人

当 job 完成且必需图片通过质量门禁后，前端进入“剧本概览 + 选人”页面。

该页面必须读取生成后的 `ScriptPackage`：

- 剧本标题、朝代、关键词、表层案件、玩家目标来自 `script_overview`。
- 地点预览来自 `locations` 的非剧透字段。
- 人物预览来自 `npcs` 的公开身份字段。
- 可选身份来自 `playable_identities`。
- 主视觉或场景缩略图只能使用 `generation_status=approved` 的图片。
- 选定身份后，再创建生成剧本 session。

该页面不能展示：

- 静态北宋 / 晚唐预览卡；
- 明代书坊案人物或线索；
- 未通过质量门禁的图片；
- 最终真相、隐藏线索、结局条件；
- 与当前生成剧本无关的身份。

进入游戏流程：

```text
AI 生成 job 完成
  -> 展示剧本概览
  -> 玩家选择生成身份
  -> POST /api/session/start-generated
  -> 后端按 script_id + identity_id 创建 session
  -> React + Phaser 加载生成剧本首场景
```

## 7. DeepSeek 多轮打磨要求

初版剧本包不能直接进入导入流程。历史悬疑剧本的风险不只在文笔，而在暗层结构：线索可能断链，NPC 可能知道了自己不该知道的事，结局条件可能不可达，地点可能没有有效调查对象，视觉 prompt 也可能没有把线索物件放进画面。因此，生成器必须把 DeepSeek 用作多轮编剧和审稿工具，而不是一次性文本生成器。

P0 至少需要 4 轮 DeepSeek 对话：

| 轮次 | 目标 | 输入 | 输出 |
| --- | --- | --- | --- |
| 1. 剧本初稿 | 生成完整 `ScriptPackage` | 用户选择、朝代知识、案件类型约束 | 初版故事、人物、地点、线索、结局、视觉 prompt |
| 2. 编剧审稿 | 找故事薄弱点 | 初版 `ScriptPackage` | 人物动机、情感核心、反转支撑、选择代价的修改建议 |
| 3. 逻辑 QA | 查玩法 BUG | 初版剧本和审稿建议 | 线索断链、阶段不可达、结局不可达、NPC 越权、剧透风险列表 |
| 4. 修复合并 | 输出可验证版本 | 初版剧本、审稿建议、QA 问题列表 | 修复后的 `ScriptPackage` 和变更摘要 |

推荐完整流程为 8 轮：

| 轮次 | DeepSeek 角色 | 重点检查 |
| --- | --- | --- |
| 1. Pitch Writer | 生成多个剧本方向，比较历史冲突、悬疑强度和可玩性 |
| 2. Script Writer | 写出完整结构化剧本包 |
| 3. Script Doctor | 强化人物动机、人物关系、误导线、反转和选择代价 |
| 4. Logic QA | 查找线索断链、循环依赖、无法发现的核心线索、不可达结局 |
| 5. NPC Permission Auditor | 检查每个 NPC 知道什么、不知道什么、何时能透露什么 |
| 6. Playthrough Simulator | 模拟普通玩家、激进玩家、真相导向玩家各走一遍，找死路和剧透 |
| 7. Visual Continuity Auditor | 检查场景图、人物图、线索图 prompt 是否可生成、可点击、同朝代、同风格，并检查热点定位是否有结构化坐标 |
| 8. Image Quality Auditor | 检查实际生成图片是否为空白、占位、错风格、错朝代、缺人物、缺线索物件或无法定位 |

每一轮都必须输出结构化结果，而不是散文建议。建议统一为：

```json
{
  "round": "logic_qa",
  "pass": false,
  "issues": [
    {
      "severity": "blocking",
      "code": "ENDING_UNREACHABLE",
      "path": "endings[hidden]",
      "message": "隐藏结局要求 clue_secret_order，但该线索没有任何 discoverable_at。",
      "suggested_fix": "把 clue_secret_order 放入 loc_document_room 的 locked_drawer 热点，并设置 reversal 阶段可发现。"
    }
  ],
  "recommended_changes": [],
  "summary": "当前剧本存在 1 个阻塞问题和 3 个非阻塞问题。"
}
```

多轮打磨的硬性规则：

- 有 `blocking` 问题时不得导入游戏。
- 同一阻塞问题修复两次仍失败时，job 应标记为 failed，并返回问题列表。
- 打磨轮次不能修改用户明确选择的朝代、身份和案件类型，除非返回需要用户确认的冲突说明。
- 修复轮必须输出完整 `ScriptPackage`，不能只输出 patch 描述。
- 每轮必须记录 prompt、输入摘要、输出摘要、问题数量、是否通过、是否使用 fallback。
- 打磨不能绕过 `SchemaValidator` 和 `ScriptSupervisor`；DeepSeek 自称“已修复”不等于通过。
- 若成本或时间限制开启 roadshow 快速模式，也至少要保留“初稿 -> 逻辑 QA -> 修复合并”三步。

## 8. DeepSeek 职责边界

DeepSeek 可以决定：

- 本局故事主题；
- 案件表层解释和深层真相；
- 人物身份、动机和关系；
- 地点、热点和线索物件；
- 线索之间的推理关系；
- NPC 对话种子和语气；
- 关键选择及其叙事后果；
- 结局文本草稿；
- 视觉 prompt 草稿；
- 人物外观锁定描述、视觉风格指南和热点初始位置估计。

DeepSeek 不可以直接决定：

- 当前玩家是否已经获得某条线索；
- 某个 NPC 在运行时是否允许剧透；
- 阶段是否可以跳转；
- 结局是否达成；
- 真实图片是否生成成功；
- 热点坐标是否最终通过；
- API Key、文件路径、服务配置；
- 绕过监管器或要求前端直接调用模型。

运行时仍由后端游戏引擎掌控状态。区别在于：游戏引擎读取的是生成出来的通用规则配置，而不是写死的明代书坊案配置。

## 9. 监管要求

AI 剧本生成必须新增 `ScriptSupervisor`，它与现有 NPC 输出监管器职责不同。它校验的是整局剧本能不能玩。

必须检查：

- JSON 可解析，字段完整；
- 朝代、称谓、官制、器物、空间符合所选历史语境；
- 没有现代物品、现代组织、现代词汇误入；
- 玩家身份有调查动机和行动权限；
- 每个地点至少有一个可调查对象；
- 核心线索能串成真相链；
- 误导线索不会把玩家导向无法回收的假结论；
- 每个 NPC 都有信息边界；
- 没有 NPC 在早期直接说出最终真相；
- 阶段推进条件可达成；
- 每个结局都有明确条件；
- 至少一个普通结局不依赖隐藏线索；
- 视觉 prompt 不含错朝代元素；
- 人物立绘、场景人物、关系图头像使用同一份 `appearance_lock`，不能出现同一 NPC 风格漂移；
- 场景图包含所选朝代的建筑、服饰、器物、照明和文书特征检查表；
- 场景图 prompt 明确排除错朝代和现代元素；
- 每个 Phaser 热点都有归一化 `anchor_point` 和 `bbox`；
- 核心线索热点的坐标已通过校准，且对应物件确实出现在生成图中；
- 必需场景图、人物图和核心线索图均通过 `ImageQualityGate`；
- 没有占位图、空白图、fallback 图或风格不合格图片被标记为完成；
- 所有玩家可见文本为中文；
- 生图 prompt 不要求生成血腥、露骨或不适合路演的画面。
- 多轮打磨中发现的阻塞问题已经被修复，且没有被后续修复重新引入。

校验结果应输出：

```json
{
  "pass": false,
  "severity": "blocking",
  "issues": [
    {
      "code": "CLUE_CHAIN_BROKEN",
      "path": "clue_graph[2]",
      "message": "该推理需要 clue_missing_ticket，但 clues 中不存在此线索。",
      "suggested_fix": "补充线索或修改 required_clue_ids。"
    }
  ]
}
```

## 10. 导入现有游戏框架

生成剧本包必须转换为现有前后端能理解的 session snapshot，而不是另起一套游戏。

导入后的基本映射：

| ScriptPackage | 现有游戏概念 |
| --- | --- |
| `dynasty` | `snapshot.dynasty` |
| `player_identity` | `snapshot.player_identity` |
| `script_overview` | generated script overview page |
| `playable_identities` | generated role selection page |
| `locations` | `snapshot.available_scenes` / `snapshot.scene` |
| `npcs` | `snapshot.scene_npcs` |
| `clues` | clue sidebar / investigation result |
| `hotspots` | Phaser hotspot |
| `dialogue_rules` | NPC dialogue orchestration |
| `choices` | choice endpoint |
| `endings` | ending resolver |
| `visual_assets` | visual asset manifest |
| `visual_style_guide` | visual prompt shared constraints |
| `hotspot_positioning` | Phaser hotspot coordinates |

现有明代数据可以继续保留，但新的导入层不应依赖 `npc_owner`、`scene_front_hall`、`clue_burned_page` 这类固定 ID。所有 ID 应从生成剧本包读取。

## 11. API 需求草案

新增 API 可以按异步 job 设计，因为完整剧本和图片生成都可能耗时。

```text
POST /api/scripts/generate
GET  /api/scripts/jobs/{job_id}
GET  /api/scripts/{script_id}
POST /api/scripts/{script_id}/validate
POST /api/scripts/{script_id}/visuals/generate
POST /api/session/start-generated
```

`POST /api/scripts/generate` 输入：

```json
{
  "dynasty_id": "song",
  "player_identity_id": "auto",
  "keywords": ["驿站", "军报", "雨夜", "粮草"],
  "case_type": "auto",
  "tone": "historical_suspense",
  "difficulty": "normal",
  "session_length": "roadshow"
}
```

API 兼容规则：

- `POST /api/session/start` 保留现有明代固定 Demo 启动能力。
- `POST /api/scripts/generate` P0 只接受 `song` 和 `late_tang`。
- 若 `POST /api/scripts/generate` 收到 `dynasty_id=ming`，默认返回 `AI_GENERATION_DISABLED_FOR_STABLE_DEMO`。
- 若 `keywords` 为空或全部无效，返回 `KEYWORDS_REQUIRED`，前端要求用户补充关键词。
- 若关键词与朝代明显冲突，返回 `KEYWORDS_CONFLICT_WITH_DYNASTY` 或进入修复建议。

`GET /api/scripts/jobs/{job_id}` 输出：

```json
{
  "job_id": "job_001",
  "status": "running",
  "script_id": "song_relay_clerk_001",
  "progress": 0.72,
  "current_step": "image_quality_gate",
  "current_step_label": "图片质量门禁",
  "blocking_issues": [],
  "steps": [
    {
      "step_key": "script_package_generation",
      "label": "剧本初稿",
      "status": "passed",
      "progress": 1.0,
      "summary": "已生成完整 ScriptPackage。"
    },
    {
      "step_key": "image_quality_gate",
      "label": "图片质量门禁",
      "status": "running",
      "progress": 0.46,
      "summary": "已通过 7 / 15 张图片，2 张因缺少线索物件正在重试。"
    }
  ],
  "transitional_quote": {
    "quote_text": "纸上得来终觉浅，绝知此事要躬行。",
    "author": "陆游",
    "dynasty_label": "南宋",
    "source_label": "《冬夜读书示子聿》"
  },
  "ready_for_overview": false,
  "ai_mode": "real",
  "fallback_used": false
}
```

`POST /api/session/start-generated` 输入：

```json
{
  "script_id": "song_relay_clerk_001",
  "identity_id": "player_relay_clerk"
}
```

启动规则：

- 只有 `GET /api/scripts/jobs/{job_id}` 返回 `status=completed` 且 `ready_for_overview=true` 后，前端才能进入剧本概览与选人页。
- `start-generated` 必须校验 `identity_id` 属于该 `script_id` 的 `playable_identities`。
- 若 `script_id` 的必需图片未全部 approved，`start-generated` 应拒绝启动正式 session。
- 若玩家刷新页面，前端应能通过 `script_id` 重新加载同一个剧本概览和身份列表。

## 12. 失败与回退

必须避免“生成失败导致现有 Demo 不能玩”。

失败策略：

- DeepSeek 不可用：返回明确生成失败状态，不冒充真实生成。
- 明代入口误入生成流程：中止生成并提示使用固定 Demo。
- 北宋 / 晚唐生成入口未填写关键词：不创建生成任务，要求用户补充关键词。
- JSON 不可解析：进入一次 repair，仍失败则 job failed。
- 多轮打磨发现阻塞问题：进入修复轮，修复失败则 job failed。
- 剧本监管不通过：返回问题列表，允许重新生成或修复。
- 图片生成失败、空白、占位、错风格、错朝代或缺核心线索物件：改写 prompt 并重新请求生图。
- 必需图片重试后仍无法通过质量门禁：job 标记为 `visual_blocked` 或 `failed`，不得作为完成剧本进入正式游玩。
- 导入失败：不得污染现有固定数据。
- 运行时 NPC 生成失败：使用 `dialogue_rules` 中的 fallback intent 生成安全回复。

当前明代书坊案可以作为 fallback playable script，但前端必须标明这是“固定示例剧本”，不能伪装成刚刚 AI 生成。

## 13. 日志与路演证明

每次剧本生成都要保留可展示日志，用于证明真实 DeepSeek 参与。

日志记录：

```json
{
  "job_id": "job_001",
  "script_id": "song_relay_clerk_001",
  "provider": "deepseek",
  "model": "configured_model",
  "input_summary": "北宋 / 自动身份 / 军报延误 / 历史悬疑",
  "steps": [
    "pitch_generation",
    "script_package_generation",
    "script_doctor_review",
    "logic_qa_review",
    "npc_permission_audit",
    "playthrough_simulation",
    "visual_continuity_audit",
    "image_quality_gate",
    "image_regeneration",
    "hotspot_calibration",
    "refinement_repair",
    "schema_validation",
    "script_supervision",
    "visual_prompt_generation",
    "import"
  ],
  "refinement_rounds": [
    {
      "round": "logic_qa",
      "pass": false,
      "blocking_issue_count": 1,
      "fixed_by_round": "refinement_repair"
    }
  ],
  "visual_quality": {
    "required_asset_count": 15,
    "approved_asset_count": 15,
    "rejected_asset_count": 3,
    "regeneration_count": 3,
    "visual_blocked": false
  },
  "ready_for_overview": true,
  "latency_ms": 185000,
  "supervisor_pass": true,
  "fallback_used": false
}
```

日志不得包含 API Key。可在路演 DebugPanel 展示：

- 本局剧本是否由真实 DeepSeek 生成；
- 生成耗时；
- 生成流程图当前停在哪个真实 job 节点；
- DeepSeek 进行了几轮剧本打磨；
- 每轮发现了哪些阻塞问题和非阻塞问题；
- 监管器发现并修复了哪些问题；
- 生成了哪些场景 / 人物 / 线索视觉 prompt；
- 人物风格锁定、朝代特征检查和热点坐标校准是否通过；
- 图片质量门禁拒绝了哪些图片、为什么拒绝、重试了几次、最终是否通过；
- 完成后展示的剧本概览和可选身份是否来自生成后的 `ScriptPackage`；
- 哪些图片已生成，哪些仍在队列中。

## 14. 验收标准

P0 验收必须满足：

- 可以在非明代书坊案框架下生成一个新剧本。
- 明代选择后仍直接进入现有书坊焚稿案固定 Demo。
- 北宋和晚唐 / 唐后期选择后进入关键词填写页，而不是直接进入固定预览。
- 北宋和晚唐 / 唐后期填写有效关键词后，才调用 AI 剧本生成流程。
- `/api/scripts/generate` 在 P0 不会为明代生成新剧本，除非开启开发 feature flag。
- 生成剧本至少包含 5 个地点、4 名 NPC、12 条线索、4 个结局。
- 每个剧本至少经过“初稿、编剧审稿、逻辑 QA、修复合并”4 轮 DeepSeek 打磨。
- 多轮打磨日志能展示发现的问题、修复结果和最终通过状态。
- 生成剧本能通过 schema 校验和剧本监管器。
- 生成剧本可以导入现有游戏 session。
- 生成等待页有流程图，并且流程图节点严格使用后端 job 的真实 `steps` 状态，不允许前端假进度。
- 生成等待期间可以轮播历史名人名句，但名句不能推动进度，也不能替代真实 job 状态。
- job 未完成或图片未全部 approved 时，前端不能进入剧本概览与选人页。
- 生成完成后必须展示由 `script_overview` 驱动的剧本概览。
- 生成完成后的选人界面必须使用 `playable_identities`，不能使用静态占位身份。
- `POST /api/session/start-generated` 必须带 `script_id + identity_id`，并校验身份属于该剧本。
- 玩家能从开局调查到至少一个结局。
- 线索不是展示文本，至少 6 条线索能影响阶段、对话、推理或结局。
- 每个主要 NPC 都有可执行的信息边界和证据回应规则。
- 每个地点都有场景 prompt 和 Phaser 可点击热点。
- 每个剧本包都有 `visual_style_guide`，主要 NPC 有 `appearance_lock`。
- 场景图 prompt 有朝代特征检查表，并明确排除错朝代和现代元素。
- 必需图片全部通过 `ImageQualityGate`，包括 5 张场景图、4 张主要 NPC 人物图、至少 6 张核心线索图。
- 占位图、空白图、fallback 图、旧缓存图、错风格图、错朝代图一律不能计入验收。
- 未通过质量门禁的图片必须自动改写 prompt 并重新请求生图。
- 必需图片未全部通过时，生成剧本不能标记为完成，不能进入正式路演游玩。
- 每个可点击线索热点都有归一化 `anchor_point` 和 `bbox`。
- 至少 6 个核心热点完成坐标校准，且坐标对应生成图中的真实物件。
- 只有图片通过质量门禁后，热点校准结果才有效；图片重生后必须重新校准热点。
- DeepSeek 失败、图片生成失败、监管失败时，系统不破坏现有固定 Demo。

P1 验收可以扩展为：

- 用户可在 2-3 个 pitch 中选择一个剧本方向；
- 支持保存、复玩和分享生成剧本；
- 支持人工编辑生成剧本后再导入；
- 支持不同难度下自动调整线索密度和结局门槛；
- 支持同一朝代下多案件类型连续生成。
- 支持完整 8 轮 DeepSeek 打磨，并在 DebugPanel 中展示每轮摘要。
- 支持在调试界面拖拽校准热点，并把校准后的 `bbox` / `polygon` 回写到剧本包。
- 支持图片质量门禁的人工复核界面，可查看拒绝原因、重试历史和最终 approved 图片。

## 15. 非目标

本阶段不做：

- 完全无约束的任意历史时期生成；
- 前端直接调用 DeepSeek；
- 前端直接调用生图服务；
- 让 Phaser 接管剧情规则；
- 让 AI 在运行时临时发明关键线索；
- P0 用 AI 替换当前明代稳定 Demo；
- 生成长篇小说式全文剧本后由玩家被动阅读；
- 把当前明代书坊案改造成唯一模板。

## 16. 核心决策

本需求最重要的产品决策如下：

```text
AI 剧本生成器的目标不是“明代书坊案变体生成器”，
而是“受历史知识库和玩法结构约束的通用历史悬疑剧本生成器”。
```

因此，后续实现时应优先建设：

- 通用 `ScriptPackage` schema；
- 通用剧本监管器；
- 通用剧本导入层；
- 通用线索图 / 场景图 / 人物图 prompt 生成；
- 可配置状态机和结局规则。

明代书坊案继续承担稳定演示职责，但不再定义 AI 剧本生成能力的上限。
