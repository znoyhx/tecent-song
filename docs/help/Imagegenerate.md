# SiliconFlow 图片生成接口文档整理

基于 SiliconFlow 官方文档页面整理。该接口用于根据 `prompt` 创建图片生成请求，生成结果中的图片 URL 有效期为 **1 小时**，需要及时下载保存。([SiliconFlow][1])

---

## 1. 接口基本信息

```http
POST https://api.siliconflow.cn/v1/images/generations
```

用途：创建图片生成请求，即 Text-to-Image / Image Generation。

请求方式：`POST`

认证方式：在请求头中携带 API Key。

```http
Authorization: Bearer YOUR-API-KEY
Content-Type: application/json
```

---

## 2. cURL 示例

```bash
curl --request POST \
  --url https://api.siliconflow.cn/v1/images/generations \
  --header 'Authorization: Bearer YOUR-API-KEY' \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "Kwai-Kolors/Kolors",
    "prompt": "an island near sea, with seagulls, moon shining over the sea, light house, boats in the background, fish flying over the sea",
    "image_size": "1024x1024",
    "batch_size": 1,
    "num_inference_steps": 20,
    "guidance_scale": 7.5
  }'
```

---

## 3. 请求体参数

### `model`

类型：`string`

是否必填：是

说明：指定使用的图片生成模型。SiliconFlow 说明模型列表可能会随服务调整而变化，完整可用模型需要以平台模型列表为准。([SiliconFlow][1])

示例：

```json
"model": "Kwai-Kolors/Kolors"
```

也可以使用页面中给出的示例模型：

```json
"model": "Qwen/Qwen-Image-Edit-2509"
```

---

### `prompt`

类型：`string`

是否必填：是

说明：图片生成提示词，用于描述希望生成的画面内容。

示例：

```json
"prompt": "an island near sea, with seagulls, moon shining over the sea, light house, boats in the background"
```

---

### `negative_prompt`

类型：`string`

是否必填：否

说明：负向提示词，用于描述不希望出现在图片中的元素。

示例：

```json
"negative_prompt": "low quality, blurry, distorted"
```

---

### `image_size`

类型：`string`

是否必填：通常必填

说明：图片分辨率，格式为：

```text
宽度x高度
```

例如：

```json
"image_size": "1024x1024"
```

注意：文档中特别说明，`Qwen/Qwen-Image-Edit-2509` 和 `Qwen/Qwen-Image-Edit` 不支持该字段。([SiliconFlow][1])

#### Kolors 推荐尺寸

```text
1024x1024  1:1
960x1280   3:4
768x1024   3:4
720x1440   1:2
720x1280   9:16
```

#### Qwen-Image 推荐尺寸

```text
1328x1328  1:1
1664x928   16:9
928x1664   9:16
1472x1140  4:3
1140x1472  3:4
1584x1056  3:2
1056x1584  2:3
```

---

### `batch_size`

类型：`integer`

默认值：`1`

取值范围：

```text
1 <= batch_size <= 4
```

说明：一次请求生成的图片数量。文档说明该参数仅适用于 `Kwai-Kolors/Kolors`。([SiliconFlow][1])

示例：

```json
"batch_size": 1
```

---

### `seed`

类型：`integer`

取值范围：

```text
0 <= seed <= 9999999999
```

说明：随机种子。通常用于控制生成结果的可复现性。

示例：

```json
"seed": 123456
```

---

### `num_inference_steps`

类型：`integer`

默认值：`20`

取值范围：

```text
1 <= num_inference_steps <= 100
```

说明：推理步数。一般来说，步数越高，生成过程越充分，但耗时可能更长。([SiliconFlow][1])

示例：

```json
"num_inference_steps": 20
```

---

### `guidance_scale`

类型：`number`

默认值：`7.5`

取值范围：

```text
0 <= guidance_scale <= 20
```

说明：控制生成图片与提示词的匹配程度。值越高，模型越倾向于严格遵循提示词；值越低，生成结果越自由，可能出现更多变化。文档说明该参数仅适用于 `Kwai-Kolors/Kolors`。([SiliconFlow][1])

示例：

```json
"guidance_scale": 7.5
```

---

### `image`

类型：`string`

是否必填：否

说明：上传参考图片，可以使用 Base64 或图片 URL。

支持形式：

```text
data:image/png;base64, XXX
```

或：

```text
图片 URL
```

示例：

```json
"image": "https://example.com/image.png"
```

---

### `image2`

类型：`string`

是否必填：否

说明：第二张输入图片。文档说明该字段仅适用于 `Qwen/Qwen-Image-Edit-2509`。([SiliconFlow][1])

支持形式同 `image`：

```text
data:image/png;base64, XXX
```

或：

```text
图片 URL
```

---

### `image3`

类型：`string`

是否必填：否

说明：第三张输入图片。文档说明该字段仅适用于 `Qwen/Qwen-Image-Edit-2509`。([SiliconFlow][1])

支持形式同 `image`：

```text
data:image/png;base64, XXX
```

或：

```text
图片 URL
```

---

## 4. 返回结果

成功请求返回 `200`，响应格式为 JSON。

```json
{
  "images": [
    {
      "url": "<string>"
    }
  ],
  "timings": {
    "inference": 123
  },
  "seed": 123
}
```

字段说明：

### `images`

类型：`object[]`

说明：生成图片列表。每个对象中包含图片 URL。

```json
"images": [
  {
    "url": "<string>"
  }
]
```

注意：生成图片的 URL 有效期为 1 小时，需要及时下载保存。([SiliconFlow][1])

---

### `timings`

类型：`object`

说明：推理耗时信息。

示例：

```json
"timings": {
  "inference": 123
}
```

---

### `seed`

类型：`integer`

说明：本次生成使用的随机种子。

示例：

```json
"seed": 123
```

---

## 5. 可能的状态码

页面列出的状态码包括：

```text
200  请求成功
400  请求参数错误
401  未认证或 API Key 错误
403  无权限
404  资源不存在
429  请求过于频繁
503  服务不可用
504  请求超时
```

---

## 6. Python 请求示例

```python
import requests

url = "https://api.siliconflow.cn/v1/images/generations"

headers = {
    "Authorization": "Bearer YOUR-API-KEY",
    "Content-Type": "application/json"
}

payload = {
    "model": "Kwai-Kolors/Kolors",
    "prompt": "an island near sea, with seagulls, moon shining over the sea, light house, boats in the background",
    "image_size": "1024x1024",
    "batch_size": 1,
    "num_inference_steps": 20,
    "guidance_scale": 7.5
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

---

## 7. JavaScript 请求示例

```javascript
const response = await fetch("https://api.siliconflow.cn/v1/images/generations", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR-API-KEY",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "Kwai-Kolors/Kolors",
    prompt: "an island near sea, with seagulls, moon shining over the sea, light house, boats in the background",
    image_size: "1024x1024",
    batch_size: 1,
    num_inference_steps: 20,
    guidance_scale: 7.5
  })
});

const data = await response.json();
console.log(data);
```

---

## 8. 使用时的关键注意事项

1. `Authorization` 必须使用 `Bearer YOUR-API-KEY` 格式。
2. 图片 URL 只保留 1 小时，生成后要立即下载或转存。
3. 不同模型支持的参数不同，例如 `guidance_scale` 和 `batch_size` 只适用于 `Kwai-Kolors/Kolors`。
4. `Qwen/Qwen-Image-Edit-2509` 支持多图输入字段，如 `image`、`image2`、`image3`。
5. `image_size` 需要使用模型推荐尺寸，不同模型推荐分辨率不同。
6. 实际可用模型应以 SiliconFlow 模型列表为准。

[1]: https://docs.siliconflow.cn/cn/api-reference/images/images-generations "创建图片生成请求 - SiliconFlow"
