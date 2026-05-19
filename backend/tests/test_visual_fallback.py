from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.image_generation_service import image_generation_service

client = TestClient(app)


def test_visual_asset_endpoint_returns_image_or_chinese_fallback() -> None:
    response = client.get("/api/visual/assets/unknown_demo_asset")
    assert response.status_code == 200
    content_type = response.headers["content-type"]
    assert "image/png" in content_type or "image/svg+xml" in content_type
    if "image/svg+xml" in content_type:
        text = response.text
        assert "<text" not in text
        assert "?" not in text
        assert "fallback" not in text.lower()


def test_generate_endpoint_reports_blocked_when_key_is_absent(tmp_path, monkeypatch) -> None:
    original_workspace_dir = image_generation_service.workspace_dir
    original_backend_dir = image_generation_service.backend_dir
    original_assets_root = image_generation_service.assets_root
    original_manifest_path = image_generation_service.manifest_path
    original_manifest = image_generation_service._manifest

    image_generation_service.workspace_dir = tmp_path
    image_generation_service.backend_dir = tmp_path / "backend"
    image_generation_service.assets_root = tmp_path / "assets" / "generated" / "visuals"
    image_generation_service.manifest_path = image_generation_service.assets_root / "asset_manifest.json"
    image_generation_service._manifest = {"version": 1, "assets": {}}
    monkeypatch.setattr(image_generation_service, "_load_api_key", lambda: None)

    try:
        response = client.post("/api/visual/generate", json={"asset_id": "clue_jinyiwei_gag_order", "force": True})
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "fallback"
        assert payload["generation_status"] == "blocked"
        assert payload["blocked"] is True
        assert "未检测到图片生成 Key" in payload["message"]
    finally:
        image_generation_service.workspace_dir = original_workspace_dir
        image_generation_service.backend_dir = original_backend_dir
        image_generation_service.assets_root = original_assets_root
        image_generation_service.manifest_path = original_manifest_path
        image_generation_service._manifest = original_manifest

