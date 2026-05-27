# gpt-image-2 接口文档
发布时间：2026-05-17 18:32:16

## 接口基础信息
- 接口名称：gpt-image-2 图像生成接口
- 请求方式：POST
- 请求地址：`https://{base_url}/v1/api/generate`
- 节点地址
  - 全球节点：`https://grsaiapi.com`
  - 国内节点：`https://grsai.dakka.com.cn`
- 完整示例地址
  - 全球：`https://grsaiapi.com/v1/api/generate`
  - 国内：`https://grsai.dakka.com.cn/v1/api/generate`
- 异步结果查询接口：https://qmy27nhsd9.apifox.cn/452409577e0

> 史隙项目默认优先使用国内节点 `https://grsai.dakka.com.cn/v1/api/generate`，全球节点 `https://grsaiapi.com/v1/api/generate` 只作为失败后的备用节点。

## 请求参数
### Path 参数
| 参数名 | 类型 | 是否必需 | 说明 |
|--------|------|----------|------|
| base_url | string | 必需 | 基础节点地址 |

### Header 参数
| 参数名 | 类型 | 是否必需 | 说明 |
|--------|------|----------|------|
| Authorization | string | 可选 | 身份认证；APIKEY获取地址：https://grsai.ai/zh/dashboard/api-keys<br>示例：`Bearer sk-xxxxxxxxxxx` |

### Body 参数（Content-Type：application/json）
| 参数名 | 类型 | 是否必需 | 说明 |
|--------|------|----------|------|
| model | string | 必需 | 模型名称，可选：`gpt-image-2`、`gpt-image-2-vip` |
| prompt | string | 必需 | 生成提示词 |
| images | array[string] | 可选 | 参考图，支持base64格式、url链接 |
| aspectRatio | string | 可选 | 图片比例/分辨率 |
| replyType | string | 可选 | 回复类型：`json`、`stream`、`async`（异步轮询） |

## 分辨率参数说明
### gpt-image-2 普通版
1. 支持比例格式（如 `16:9`）或1K像素值（如 `1024x1024`）
2. 固定尺寸参考
| 比例 | 分辨率 |
|------|--------|
| 1:1 | 1024x1024 |
| 16:9 | 1672 x941 |
| 9:16 | 941x1672 |
| 4:3 | 1443x1090 |
| 3:4 | 1090x1443 |
| 3:2 | 1536x1024 |
| 2:3 | 1024x1536 |
| 5:4 | 1408x1120 |
| 4:5 | 1120x1408 |
| 21:9 | 1920x832 |
| 9:21 | 832x1920 |
| 1:2 | 896x1792 |
| 2:1 | 1792x896 |

### gpt-image-2-vip 尊享版
1. 支持1K/2K/4K像素值，**不支持比例格式**
2. 自定义像素约束规则
   - 最大边长 ≤ 3840px
   - 两边均为16的倍数
   - 长边/短边之比不超过 3:1
   - 总像素：655,360 ~ 8,294,400
3. 固定尺寸参考
| 比例 | 1K | 2K | 4K |
|------|----|----|----|
| 1:1 | 1024x1024 | 2048x2048 | 2880x2880 |
| 16:9 | 1280x720 | 2048x1152 | 3840x2160 |
| 9:16 | 720x1280 | 1152x2048 | 2160x3840 |
| 4:3 | 1152x864 | 2304x1728 | 3264x2448 |
| 3:4 | 864x1152 | 1728x2304 | 2448x3264 |
| 3:2 | 1536x1024 | 2048x1360 | 3504x2336 |
| 2:3 | 1024x1536 | 1360x2048 | 2336x3504 |
| 5:4 | 1120x896 | 2240x1792 | 3200x2560 |
| 4:5 | 896x1120 | 1792x2240 | 2560x3200 |
| 21:9 | 1456x624 | 2912x1248 | 3840x1648 |
| 9:21 | 624x1456 | 1248x2912 | 1648x3840 |
| 1:3 | 688x2048 | 1280x3840 | - |
| 3:1 | 2048x688 | 3840x1280 | - |
| 2:1 | 1536x768 | 3072x1536 | 3840x1920 |
| 1:2 | 768x1536 | 1536x3072 | 1920x3840 |

## 请求体示例
```json
{
    "model": "gpt-image-2",
    "prompt": "生成一张边牧与古牧正在抖音直播间直播带货截图",
    "images": [],
    "aspectRatio": "1024x1024",
    "replyType": "json"
}
```

## cURL 请求示例
```bash
curl --location 'https://v1/api/generate' \
--header 'Authorization: Bearer sk-xxxxxxxxxxx' \
--header 'Content-Type: application/json' \
--data '{
    "model": "gpt-image-2",
    "prompt": "生成一张边牧与古牧正在抖音直播间直播带货截图",
    "images": [],
    "aspectRatio": "1024x1024",
    "replyType": "json"
}'
```
支持语言：Shell、JavaScript、Java、Swift、Go、PHP、Python、HTTP、C、C#、Objective-C、Ruby、OCaml、Dart、R

## 接口返回
### 成功状态码：200
#### 通用返回字段
| 字段名 | 类型 | 是否必需 | 说明 |
|--------|------|----------|------|
| id | string | 必需 | 任务ID |
| status | string | 必需 | 任务状态：running(进行中)、violation(违规)、succeeded(生成成功)、failed(任务失败) |
| progress | integer | 可选 | 生成进度 0~100 |
| results | array[object] | 可选 | 结果数组 |
| error | string | 可选 | 报错信息 |

#### results 对象字段
| 字段名 | 类型 | 说明 |
|--------|------|------|
| url | string | 图片/视频链接 |

#### 成功响应示例
```json
{
    "id": "14-5f3cf761-a4bb-486a-8016-77f490998f80",
    "status": "succeeded",
    "results": [
        {
            "url": "https://file1.aitohumanize.com/file/fcdd2d07449d438d9d69d450f5626976.png"
        }
    ]
}
```

### 状态码说明
- 200：请求成功（同步/异步均返回）
- 400：请求参数错误/业务报错

## 史隙项目使用规范

- 后端图片生成服务必须统一接入本 API，密钥只读取环境变量 `NEW_IMAGE_API_KEY`。
- 默认调用国内节点：`POST https://grsai.dakka.com.cn/v1/api/generate`。
- 全球节点：`POST https://grsaiapi.com/v1/api/generate` 仅作为国内节点网络失败、API 失败或服务不可用后的 fallback。
- 默认模型使用 `gpt-image-2`；只有需要 2K/4K 或严格自定义像素尺寸时，才使用 `gpt-image-2-vip`，且必须满足 VIP 尺寸约束。
- 场景图使用 `16:9` 或等价宽屏尺寸；NPC 图可使用 `1:1` 或竖向尺寸；线索图优先使用 `1:1` 近景。
- 生成剧本的场景 prompt 必须同时包含朝代、具体地点、镜头视角、当前 NPC、全部关键线索物件和大致位置。有尸体就必须出现尸体，有空盒子就必须出现盒子，不允许只生成空背景。
- 建议使用简洁英文优先或中英双语 prompt。因为接口没有独立 negative prompt 字段，负面约束必须写进同一个 `prompt`：禁止山景、湖泊、木屋、鹿、西式风景、现代物品、可读文字、水印，除非剧本明确需要。
- 仅当 API 返回 `status=succeeded` 且 `results[0].url` 可下载时，图片才允许进入本地保存与 `ImageQualityGate`。
- 视觉门禁必须检查图片是否空白/损坏/占位、是否错朝代/错风格、是否缺少线索物件、线索是否能与热点大致定位匹配。不通过时进入 prompt repair 和重新生成；多次失败后标记 `visual_blocked` 或 failed。
- 不得把 `NEW_IMAGE_API_KEY` 写入前端代码、日志、生成任务 JSON、提交记录或公开文档。
