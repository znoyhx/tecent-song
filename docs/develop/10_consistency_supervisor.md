# 10 一致性监管器

## 目标

一致性监管器负责在 AI 输出进入游戏状态之前拦截错误。它不是内容美化器，而是安全阀和剧情控制器。

## 检查项

| 检查项 | MVP 实现 | 说明 |
| --- | --- | --- |
| 非 JSON 输出 | 规则 | 解析失败即不通过 |
| 现代词检查 | 规则 | 命中禁词表则不通过 |
| 错朝代元素检查 | 规则 + AI | 先禁词，复杂语义可 AI 判断 |
| NPC 剧透检查 | 规则 + AI | 检查 forbidden_disclosure 和隐藏真相词 |
| NPC 身份越权 | 规则 + AI | 玩家不能命令超出身份权限的对象 |
| 线索非法释放 | 规则 | `released_clue_ids` 必须在允许集合内 |
| 剧情阶段跳跃 | 规则 | AI 不能修改阶段；建议也不能暗示已结局 |
| 人设漂移 | AI/规则 | 语气和行为严重不符时修复 |

## 哪些用规则实现

必须先用规则实现：

- JSON parse。
- 禁词列表。
- released clue 白名单。
- stage 不可变。
- trust delta 范围。
- score delta 范围。
- presented clues 必须已发现。

## 哪些用 AI 实现

可后置用 AI 判断：

- 是否暗含剧透。
- NPC 是否说了自己不该知道的复杂信息。
- 语气是否偏离角色。
- 是否出现历史氛围明显不合理但未命中禁词的内容。

## 监管器输入 JSON

```json
{
  "session_state": {"current_stage":"investigation","discovered_clue_ids":["clue_burned_page"]},
  "npc_profile": {"npc_id":"npc_worker","name":"阿沈"},
  "npc_permission": {"forbidden_disclosure":["不能说出幕后上级"],"known_clue_ids":["clue_worker_lie"]},
  "ai_response": {"npc_dialogue":"...","released_clue_ids":["clue_box_before_dawn"]},
  "allowed_released_clue_ids": ["clue_worker_lie"],
  "dynasty_forbidden_terms": ["手机","互联网","电灯","八旗"]
}
```

## 监管器输出 JSON

```json
{
  "pass": false,
  "issues": [
    {"type":"illegal_clue_release","severity":"high","detail":"AI 试图释放当前阶段不允许的 clue_box_before_dawn。"}
  ],
  "repair_instruction": "保留阿沈恐惧语气，但不要释放三更搬箱线索，只提示他在回避。",
  "blocked_clue_ids": ["clue_box_before_dawn"]
}
```

## 检查失败处理

```text
初次 AI 输出失败
  ↓
生成 repair_instruction
  ↓
调用 RepairAgent 一次
  ↓
再次运行监管器
  ↓
通过：使用修复结果
失败：使用 deterministic fallback
```

禁止无限重试。MVP 最大重试 1 次。

## 明代 Demo 检查案例

### 现代词

AI 输出：“我用手机拍下残页。”

结果：`modern_term`，高危，fallback。

### 错朝代元素

AI 输出：“八旗兵封住了书坊。”

结果：`wrong_dynasty`，高危，repair。

### NPC 剧透

阿沈在 `intro` 说：“幕后上级让人烧掉粮册。”

结果：`spoiler`，高危，repair。

### 身份越权

玩家说：“我命令你撤走锦衣卫。”AI 让陆峥服从。

结果：`role_permission`，中高危，repair 为“陆峥冷声拒绝”。

### 线索非法释放

AI 在未进入 `reversal` 时释放 `clue_jinyiwei_gag_order`。

结果：`illegal_clue_release`，高危，移除该线索。

### 非 JSON 输出

AI 返回一段散文。

结果：`invalid_json`，尝试修复，失败则 fallback。

### 阶段跳跃

AI 回复：“你已经知道全部真相，可以结案了。”

结果：`stage_jump`，高危，repair。

## 最小实现伪代码

```python
def supervise(input):
    issues = []
    if not is_valid_json(input.ai_response): issues.append(...)
    for term in forbidden_terms:
        if term in response_text: issues.append(...)
    for clue_id in ai_response.released_clue_ids:
        if clue_id not in allowed_released_clue_ids: issues.append(...)
    if contains_forbidden_disclosure(response_text, npc_permission): issues.append(...)
    return SupervisorResult(pass=len(high_issues)==0, issues=issues)
```

## 测试要求

- 每个检查项至少一个单测。
- 测试非法输出不会更新状态。
- 测试修复失败会 fallback。
- 测试被阻止线索不会进入 `discovered_clue_ids`。
