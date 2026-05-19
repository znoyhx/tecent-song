# 天谱乐 纯音乐生成 API 文档（提取版）
## 接口信息
- **请求方式**：POST
- **接口地址**：`https://api.tianpuyue.cn/open-apis/v1/instrumental/generate`
- **功能**：输入关键词生成纯音乐，支持通过 prompt 精准控制时长、节奏、调性、和弦等

---

## 请求参数
### Header 参数
| 参数名 | 类型 | 是否必填 | 说明 | 示例 |
| --- | --- | --- | --- | --- |
| Authorization | string | 是 | API 密钥 | Tempo-********************************-3w |
| Content-Type | string | 是 | 固定为 | application/json |

### Body 参数（application/json）
| 参数名 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| prompt | string | 是 | 音乐生成提示词，可控制：曲风、风格、情绪、节奏BPM、调性、和弦、时长 |
| model | string | 是 | 使用的模型名称 |
| callback_url | string | 是 | 任务完成回调地址，需自行开发接收接口 |

### prompt 示例写法
```
Genre: Electronic Dance Music (EDM), House, Techno
Style: Instrumental, Beat-driven, Club-oriented
Mood: Energetic, Vibrant, Hypnotic
BPM 85, Cmajor, C,Am,F,G, 时长100秒
```

---

## 请求示例（curl）
```bash
curl --location --globoff 'https://api.tianpuyue.cn/open-apis/v1/instrumental/generate' \
--header 'Authorization: Tempo-********************************-3w' \
--header 'Content-Type: application/json' \
--data '{
    "prompt": "Genre: Electronic Dance Music (EDM), House, Techno  Style: Instrumental, Beat-driven, Club-oriented  Mood: Energetic, Vibrant, Hypnotic ",
    "model": "TemPolor i3.5",
    "callback_url": "https://**************/callback"
}'
```

---

## 成功响应（200）
```json
{
    "status": 200000,
    "message": "success",
    "request_id": "b072a68c-4c1b-41be-bdd1-0a0309754de7",
    "data": {
        "item_ids": [
            "123"
        ]
    }
}
```

### 响应字段说明
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| status | integer | 业务状态码 |
| message | string | 结果描述 |
| request_id | string | 请求唯一 ID，用于排查问题 |
| data.item_ids | array[string] | 生成任务的作品 ID 列表 |

---

# 天谱乐 纯音乐回调接口文档（完整提取）
## 接口基础信息
- 请求方式：**POST**
- 回调地址：**你的域名/instrumental/callback**（自行开发）
- 回调要求：接口处理成功必须返回字符串：**success**
- 回调次数：一次纯音乐生成会触发**两次回调**
  - 第一次：mp3 音频回调
  - 第二次：wav 无损音频回调

---

## 请求参数（Body：application/json）
### 顶层结构
| 字段 | 类型 | 是否必填 | 说明 |
| :--- | :--- | :--- | :--- |
| instrumentals | array[object] | 是 | 作品信息列表（数组，单元素） |

### instrumentals 子字段详情
| 字段 | 类型 | 可选 | 说明 |
| :--- | :--- | :--- | :--- |
| item_id | string | 可选 | 作品唯一 ID |
| status | string | 可选 | 整体任务状态 |
| audio_hi_status | string | 可选 | 无损音频（wav）生成状态 |
| model | string | 可选 | 生成使用的模型 |
| title | string | 可选 | 音乐标题 |
| prompt | string | 可选 | 生成提示词 |
| duration | integer | 可选 | 音频时长（秒） |
| created_at | integer | 可选 | 创建时间戳（秒） |
| finished_at | integer | 可选 | 完成时间戳（秒） |
| audio_url | string | 可选 | mp3 音频地址（有效期3天） |
| audio_hi_url | string | 可选 | wav 无损音频地址（有效期3天） |
| style | string | 可选 | 音乐风格 |
| event | string | 可选 | 回调事件类型 |

### 枚举值说明
1. **status（整体状态）**
   - running：生成中
   - main_succeeded：主功能成功
   - failed：主功能失败
   - succeeded：全部成功
   - part_failed：部分子功能失败
2. **audio_hi_status（无损状态）**
   - waiting：等待中
   - running：生成中
   - sub_succeeded：成功
   - sub_failed：失败
3. **event（回调事件）**
   - audio_complete：mp3 完成
   - wav_complete：wav 完成
   - lrcsections_complete：歌词段落完成

---

## 回调请求示例
```json
{
    "instrumentals": [
        {
            "audio_hi_status": "sub_succeeded",
            "audio_hi_url": "https://****",
            "created_at": 1747278096,
            "duration": 262,
            "event": "wav_complete",
            "finished_at": 1747278158,
            "item_id": "123",
            "model": "TemPolor i3.5",
            "prompt": "Genre: Electronic Dance Music (EDM), House, Techno  Style: Instrumental, Beat-driven, Club-oriented  Mood: Energetic, Vibrant, Hypnotic  Tempo: Typically ranges from 120 to 130 BPM  Structure: Build-ups, Drops, Breakdowns  Instruments/Sounds: Synthesizers, Drum Machines, Basslines, Hi-hats, Pads",
            "status": "succeeded",
            "style": "electronic,house,techno",
            "title": "Neon Pulse Drive"
        }
    ]
}
```

---

## cURL 调用示例
```bash
curl --location --request POST '你的域名/instrumental/callback' \
--header 'Content-Type: application/json' \
--data-raw '{
    "instrumentals": [
        {
            "audio_hi_status": "sub_succeeded",
            "audio_hi_url": "https://****",
            "created_at": 1747278096,
            "duration": 262,
            "event": "wav_complete",
            "finished_at": 1747278158,
            "item_id": "123",
            "model": "TemPolor i3.5",
            "prompt": "Genre: Electronic Dance Music (EDM), House, Techno",
            "status": "succeeded",
            "style": "electronic,house,techno",
            "title": "Neon Pulse Drive"
        }
    ]
}'
```

---

## 响应要求
- 成功响应：HTTP 200，返回纯文本 **success**
- 示例：
  ```
  success
  ```

---


# 天谱乐 纯音乐任务状态查询 API 文档（完整提取）
## 接口基础信息
- 请求方式：**POST**
- 接口地址：`https://api.tianpuyue.cn/open-apis/v1/instrumental/query`
- 功能：根据作品 ID 查询纯音乐生成任务状态与音频结果

---

## 请求参数
### Header 参数
| 参数名 | 类型 | 是否必填 | 说明 | 示例 |
| --- | --- | --- | --- | --- |
| Authorization | string | 是 | API 密钥 | Tempo-********************************-3w |
| Content-Type | string | 是 | 固定为 | application/json; charset=utf-8 |

### Body 参数（application/json）
| 参数名 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| item_ids | array[string] | 是 | 待查询的作品 ID 列表，**最多支持 10 个** |

---

## 请求示例（curl）
```bash
curl --location --request POST 'https://api.tianpuyue.cn/open-apis/v1/instrumental/query' \
--header 'Authorization: Tempo-********************************-3w' \
--header 'Content-Type: application/json; charset=utf-8' \
--data-raw '{
    "item_ids": [
        "123"
    ]
}'
```

---

## 成功响应（200）
```json
{
    "status": 200000,
    "message": "success",
    "request_id": "1165b1fc-e56d-4b55-a5d9-dbae434cd47d",
    "data": {
        "instrumentals": [
            {
                "item_id": "123",
                "status": "succeeded",
                "audio_hi_status": "sub_succeeded",
                "model": "TemPolor i3.5",
                "title": "Neon Pulse Groove",
                "prompt": "Genre: Electronic Dance Music (EDM), House, Techno  Style: Instrumental, Beat-driven, Club-oriented  Mood: Energetic, Vibrant, Hypnotic  Tempo: Typically ranges from 120 to 130 BPM  Structure: Build-ups, Drops, Breakdowns  Instruments/Sounds: Synthesizers, Drum Machines, Basslines, Hi-hats, Pads",
                "duration": 266,
                "created_at": 1747276813,
                "finished_at": 1747277627,
                "audio_url": "https://****",
                "audio_hi_url": "https://****",
                "style": "electronic,house,techno"
            }
        ]
    }
}
```

---

## 响应字段说明
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| status | integer | 业务状态码，200000 为成功 |
| message | string | 结果描述 |
| request_id | string | 请求唯一 ID，用于问题排查 |
| data.instrumentals | array[object] | 任务结果列表 |
| ├─ item_id | string | 作品 ID |
| ├─ status | string | 整体任务状态 |
| ├─ audio_hi_status | string | 无损音频（wav）状态 |
| ├─ model | string | 使用模型 |
| ├─ title | string | 音乐标题 |
| ├─ prompt | string | 生成提示词 |
| ├─ duration | integer | 时长（秒） |
| ├─ created_at | integer | 创建时间戳（秒） |
| ├─ finished_at | integer | 完成时间戳（秒） |
| ├─ audio_url | string | MP3 音频地址（有效期3天） |
| ├─ audio_hi_url | string | WAV 无损音频地址（有效期3天） |
| └─ style | string | 音乐风格 |

---
