# 史隙阶段 1 后端

本目录提供《史隙》阶段 1 的 FastAPI Mock Demo 后端。

## 启动

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

启动后默认监听 `http://127.0.0.1:8000`。

## 测试

```powershell
cd backend
python -m pytest
```

## 说明

- 当前只实现**中文 Mock Demo**。
- 未接入真实 DeepSeek。
- 未接入真实图片生成。
- 已为后续真实 AI 接入预留接口字段与监管器入口。
