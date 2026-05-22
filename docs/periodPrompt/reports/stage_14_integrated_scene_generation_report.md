# Stage 14 Integrated Scene Generation Report

## Direction Change

主场景生成方式改为“场景、人物、线索物件一起生成”。每个地点的主图 prompt 同时描述朝代、地点、当前 NPC、人物身份与姿态，以及可点击线索物件。

例子：书坊前厅应把许掌柜、柜台、书柜、架子、旧书箱、缺失稿单、半枚朱红纸角和门柱刻痕放进同一张图的空间关系里，而不是先生成空背景，再把人物立绘贴上去。

## Implemented

- `backend/app/services/visual_prompt_agent.py`: 场景 prompt 改为 integrated scene prompt，显式要求人物与地点同透视、同光源、同色温，不能像后期贴上去的半身立绘。
- `backend/app/services/image_generation_service.py`: 场景资产新增 prompt version，旧 scene 图不能再被当成当前版本复用。
- `frontend/src/game/scenes/MainScene.ts` 和 `frontend/src/game/objects/NPCSprite.ts`: Phaser 主舞台不再加载大 NPC 立绘叠在背景上，改为在合成图上放轻量 NPC 点击区域和选中反馈。
- `frontend/src/components/scene/ScenePanel.tsx` 和 `frontend/src/styles/global.css`: React fallback 同步改为集成场景点击标记，避免人物贴图重复。
- `CODEBUDDY.md`: 记录新的主场景视觉决策，后续阶段按 integrated scene 方向继续。

## Actual Regeneration Result

2026-05-21 21:34-21:42 已使用真实 SiliconFlow provider `siliconflow` / `Kwai-Kolors/Kolors` 重新生成全部 9 张主场景图。`/api/visual/status` 当前返回 `generated_count=18`、`fallback_count=0`、`blocked_count=0`，其中 9 个 scene asset 全部为 `generated`。

| scene asset | generated path | updated_at |
| --- | --- | --- |
| `scene_bookshop_front_hall` | `assets/generated/visuals/scenes/scene_bookshop_front_hall.png` | `2026-05-21T21:34:38` |
| `scene_bookshop_fire_yard` | `assets/generated/visuals/scenes/scene_bookshop_backyard_fire.png` | `2026-05-21T21:34:46` |
| `scene_account_room` | `assets/generated/visuals/scenes/scene_account_room.png` | `2026-05-21T21:34:53` |
| `scene_lamp_shelf` | `assets/generated/visuals/scenes/scene_lamp_shelf.png` | `2026-05-21T21:35:02` |
| `scene_bookshop_engraving_room` | `assets/generated/visuals/scenes/scene_burned_printing_room.png` | `2026-05-21T21:35:09` |
| `scene_back_gate` | `assets/generated/visuals/scenes/scene_back_gate.png` | `2026-05-21T21:35:17` |
| `scene_rain_alley` | `assets/generated/visuals/scenes/scene_rain_alley.png` | `2026-05-21T21:35:26` |
| `scene_city_gate` | `assets/generated/visuals/scenes/scene_city_gate.png` | `2026-05-21T21:41:29` |
| `scene_interrogation_room` | `assets/generated/visuals/scenes/scene_jinyiwei_interrogation.png` | `2026-05-21T21:42:43` |

## Manual Image Check

- `scene_bookshop_front_hall` now includes Xu the bookshop owner inside the bookshop, beside the counter and bookshelves. The old book box and papers are indoors, not outside in the rain.
- `scene_account_room`, `scene_bookshop_engraving_room`, `scene_back_gate`, `scene_rain_alley`, `scene_city_gate`, and `scene_interrogation_room` include their scene NPCs as part of the generated scene image.
- `scene_bookshop_fire_yard` and `scene_lamp_shelf` have no major NPC in source scene data, so they remain clue-object investigation scenes.

## Verification

- `python -m py_compile backend/app/services/visual_prompt_agent.py backend/app/services/image_generation_service.py`: passed.
- `python -m pytest backend/tests/test_visual_asset_status.py -q`: `6 passed`.
