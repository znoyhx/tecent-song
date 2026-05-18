# 16 视觉资产方案

## 视觉目标

统一风格：低饱和国风剪影 + 暗色历史悬疑 + 视觉小说 UI。视觉用于增强叙事，不要先做复杂动画系统。

## 人物剪影方案

MVP 先用剪影或半身占位图：

- 许掌柜：疲惫、精明、微躬身。
- 阿沈：胆怯、低头、袖口有墨。
- 顾闻：清瘦、焦急、抱旧稿。
- 陆峥：冷峻、直立、腰牌/佩刀剪影。

若无图片，用 CSS 渐变卡片 + 角色名 + 情绪色条代替。

## 背景图方案

5 个最小场景：

1. `scene_front_hall`：书坊前厅。
2. `scene_fire_yard`：后院火场。
3. `scene_printing_room`：刻坊。
4. `scene_rain_alley`：雨巷。
5. `scene_interrogation_room`：临时审问处。

## 线索物品图方案

首版可不为每条线索配图。最小 3 个线索图：

- 烧焦残页。
- 半枚红印纸角。
- 锦衣卫封口令。

## UI 风格

- 背景：深灰、黑、暗红、米白。
- 红色只用于关键线索和风险提示。
- 对话框：底部半透明深色面板。
- 线索栏：右侧抽屉，纸张质感或暗色卡片。
- 字体：正文清晰优先，标题可偏宋体气质。

## 图片资源目录

```text
assets/
├── placeholders/
│   ├── scene_placeholder.png
│   └── npc_placeholder.png
├── scenes/
│   ├── ming_front_hall.png
│   └── ming_fire_yard.png
├── npcs/
│   ├── npc_owner.png
│   └── npc_worker.png
└── clues/
    ├── clue_burned_page.png
    └── clue_gag_order.png
```

## 资源命名规范

- 场景：`ming_<scene_name>.png`。
- NPC：`npc_<npc_id>.png`。
- 线索：`clue_<clue_id>.png`。
- 不使用中文文件名，避免部署路径问题。

## 没有图片时如何占位

前端 `AssetResolver`：

```text
指定图片存在 -> 使用指定图片
不存在 -> 使用同类型 placeholder
placeholder 不存在 -> CSS 渐变背景
```

不得因为图片缺失导致页面崩溃。

## AI 生图接入

`docs/help/Imagegenerate.md` 记录 SiliconFlow：

- `POST https://api.siliconflow.cn/v1/images/generations`。
- Bearer Auth。
- 图片 URL 有效期 1 小时，生成后必须下载保存。
- 不同模型参数不同。

后续由后端 `VisualAssetService` 调用，不由前端直接调用。

## 最小视觉资产列表

| 类型 | 数量 | 说明 |
| --- | ---: | --- |
| 主视觉 | 1 | 雨夜书坊、火光、锦衣卫剪影、残页 |
| 场景背景 | 5 | 对应 5 场景 |
| NPC 剪影 | 4 | 许掌柜、阿沈、顾闻、陆峥 |
| 线索图 | 3 | 残页、红印纸角、封口令 |
| 占位图 | 3 | scene/npc/clue 通用占位 |

## 视觉提示词示例

```json
{
  "asset_type":"scene_background",
  "asset_name":"明代书坊后院火场",
  "prompt":"雨夜后的明代书坊后院，旧书箱烧毁，灰烬与积水，远处有侦缉人员剪影，低饱和国风，暗色历史悬疑，视觉小说背景，细腻光影",
  "negative_prompt":"现代建筑，电灯，手机，霓虹，清代服饰，日式武士，赛博朋克"
}
```
