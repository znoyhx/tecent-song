# 09 RAG 与知识库方案

## MVP 是否必须上向量数据库

首个可运行 Mock Demo 不必须上向量数据库。MVP 推荐两步走：

1. 阶段 1：使用 JSON / Markdown + 关键词检索，快速给 AI prompt 提供历史约束。
2. 阶段 2：替换为 `ChromaDB` 或腾讯云向量数据库，但保持 `RAGService.retrieve()` 接口不变。

## 不上向量数据库时的替代方案

使用结构化知识片段：

```json
{
  "chunk_id": "ming_jinyiwei_rule_001",
  "dynasty_id": "ming",
  "topics": ["锦衣卫", "封锁", "身份权限"],
  "source_level": "C",
  "content": "锦衣卫在本游戏中代表侦缉压力；书坊学徒不能命令其撤离，只能请求、试探或出示线索。",
  "forbidden_terms": ["手机", "互联网", "八旗"]
}
```

检索逻辑：

1. 按 `dynasty_id` 过滤。
2. 按 query 分词或关键词匹配 `topics`、`content`。
3. 按 `source_level`、匹配次数、当前阶段排序。
4. 返回 top 3。

## 上向量数据库时的切片建议

- 每个 chunk 150-300 中文字。
- 一个 chunk 只讲一个制度、空间、器物、身份边界或禁忌。
- metadata 必须包含 `dynasty_id`、`topic`、`source_level`、`rule_type`、`severity`。
- 禁止把大段 PRD 整体塞入向量库。

## 知识库包含内容

| 类型 | 内容 | 用途 |
| --- | --- | --- |
| 朝代概况 | 明代、北宋、晚唐气质 | 世界生成与 UI 展示 |
| 身份边界 | 书坊学徒、刻工、校尉能做什么 | 防越权 |
| 场景常识 | 书坊、刻坊、驿站、粮仓 | 场景描述 |
| 文书制度 | 粮册、封口令、路引 | 线索解释 |
| 错朝代禁项 | 现代词、清代元素等 | 监管器规则 |
| 视觉规则 | 低饱和国风、暗色悬疑 | 视觉提示词 |

## 朝代知识组织

```text
backend/data/rag_sources/
├── ming/
│   ├── institutions.json
│   ├── daily_life.json
│   ├── documents.json
│   ├── forbidden_terms.json
│   └── visual_style.json
├── song/
└── tang/
```

## 错朝代禁止项组织

```json
{
  "dynasty_id": "ming",
  "forbidden_terms": [
    {"term":"手机","reason":"现代物品"},
    {"term":"互联网","reason":"现代概念"},
    {"term":"八旗","reason":"不属于明代语境"},
    {"term":"电灯","reason":"现代物品"}
  ]
}
```

## RAG 如何进入 Prompt

只放短上下文，不要堆满：

```text
【历史参考，仅供约束】
1. 书坊学徒不能命令侦缉人员，只能请求、试探或出示线索。
2. 明代文稿、刊刻和官府文书风险可作为剧情压力。
3. 当前场景禁止出现现代物品和清代制度词。
```

## 避免召回无关内容

- 必须先按 `dynasty_id` 过滤。
- 当前事件只取 `ming_bookshop_fire` 或 `common` 内容。
- 当前阶段只取可用规则。
- top K 不超过 3-5。
- RAG 内容不得覆盖状态机结论。

## 为腾讯云向量数据库预留接口

定义统一接口：

```python
class RAGService:
    def retrieve(self, query: str, dynasty_id: str, stage: str, top_k: int = 3) -> list[RAGChunk]:
        ...
```

后续实现：

- `KeywordRAGService`：MVP 默认。
- `ChromaRAGService`：本地向量库。
- `CloudVectorRAGService`：腾讯云或其他云向量库。

调用方只依赖接口，不依赖具体实现。

## 测试方法

- 查询“锦衣卫 书坊 文稿”，必须返回明代规则。
- 查询“手机”，监管器必须命中现代禁词。
- 查询北宋词时不得返回明代专属线索。
- RAG 返回为空时 AI 仍可用 fallback 规则运行。
