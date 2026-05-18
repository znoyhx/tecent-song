# 14 Mock Demo 计划

## 为什么先做 Mock Demo

真实 AI 接入存在不确定性：密钥、网络、模型输出格式、成本、延迟和监管器误判都可能阻塞开发。Mock Demo 先验证游戏闭环、状态机、线索系统、UI 和 API 合约，保证即使 AI 暂时不可用也能路演。

## Mock Demo 必须跑通的流程

1. 选择明代和书坊学徒。
2. 创建会话进入 `intro`。
3. 调查前厅和后院火场。
4. 点击红色高亮获得线索。
5. 与 4 个 NPC 至少各对话一次。
6. 向至少 2 个 NPC 出示线索。
7. 完成至少 2 组线索组合。
8. 进入 `choice`。
9. 选择任一关键行动。
10. 进入 5 个结局之一。

## Mock 数据位置

```text
backend/data/mock/
├── sessions/
├── dialogues/
│   ├── npc_owner.json
│   ├── npc_worker.json
│   ├── npc_scholar.json
│   └── npc_jinyiwei.json
├── scene_responses.json
└── history_echoes.json
```

## Mock NPC 回复格式

```json
{
  "npc_id": "npc_worker",
  "stage": "investigation",
  "trigger": {"presented_clue_ids": ["clue_worker_lie"]},
  "response": {
    "npc_dialogue": "我只听见有人说那箱东西不能留到天亮。",
    "npc_action": "阿沈低下头，手指发抖。",
    "emotion": "fearful",
    "released_clue_ids": ["clue_box_before_dawn"],
    "suggested_questions": ["那箱东西是谁搬的？"]
  }
}
```

## Mock 线索释放规则

- 场景热点固定释放场景线索。
- NPC 默认回复不释放关键线索。
- 出示指定线索或信任度达标才释放关键线索。
- Mock 不允许释放不在当前阶段的线索。

## Mock 结局判定规则

与真实版本共用 `EndingService`：

- `choice_destroy_evidence` → 自保倾向。
- `choice_give_to_lu` → 秩序倾向。
- `choice_help_scholar` → 真相倾向。
- `risk_level >= 6` → 悲剧倾向。
- 隐藏线索 + 双 NPC 高信任 → 隐藏结局。

## Mock Demo 验收标准

- 不配置任何 API Key 也可完整通关。
- 首屏到结局不出现 500 错误。
- 至少获得 8 条线索。
- 线索栏显示详情。
- 出示线索改变 NPC 回复。
- 关键选择改变结局分数。
- 调试面板显示 `USE_MOCK_AI=true`。
- 监管器仍会检查 Mock 输出，保证真实 AI 接入前规则可用。

## 低级模型执行提示

低级模型只应按 Mock 数据和固定规则实现，不要自行接入真实 AI，不要修改真实 AI 接口设计，不要扩展新朝代。
