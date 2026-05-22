from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.routers import scripts as scripts_router
from app.services.script_job_store import script_job_store


client = TestClient(app)


def test_generate_api_rejects_ming() -> None:
    response = client.post("/api/scripts/generate", json={"dynasty_id": "ming", "keywords": ["书坊"]})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "AI_GENERATION_DISABLED_FOR_STABLE_DEMO"
    assert "固定 Demo" in response.json()["error"]["message"]


def test_generate_api_rejects_empty_keywords() -> None:
    response = client.post("/api/scripts/generate", json={"dynasty_id": "song", "keywords": []})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "KEYWORDS_REQUIRED"
    assert "关键词" in response.json()["error"]["message"]


def test_generate_api_creates_failed_job_when_deepseek_unavailable(monkeypatch) -> None:
    def fake_run_job(job_id: str) -> None:
        job = script_job_store.get_job(job_id)
        assert job is not None
        script_job_store.set_running(job, "pitch_generation", "正在检查 DeepSeek 配置。")
        script_job_store.fail_job(job, "pitch_generation", "AI_UNAVAILABLE", "AI 服务不可用，生成已失败。")

    monkeypatch.setattr(scripts_router.script_generation_service, "run_job", fake_run_job)

    response = client.post("/api/scripts/generate", json={"dynasty_id": "song", "keywords": ["驿站"]})

    assert response.status_code == 200
    job_id = response.json()["job_id"]
    job_response = client.get(f"/api/scripts/jobs/{job_id}")

    assert job_response.status_code == 200
    job_payload = job_response.json()
    assert job_payload["status"] == "failed"
    assert job_payload["blocking_issues"][0]["code"] == "AI_UNAVAILABLE"
