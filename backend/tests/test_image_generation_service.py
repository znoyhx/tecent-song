from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import httpx

from app.services.image_generation_service import ImageGenerationService


class FakeResponse:
    def __init__(self, payload: dict[str, Any] | None = None, *, content: bytes = b"", headers: dict[str, str] | None = None) -> None:
        self._payload = payload or {}
        self.content = content
        self.headers = headers or {}
        self.status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeHttpClient:
    posted_headers: dict[str, str] = {}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

    def __enter__(self) -> "FakeHttpClient":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def post(self, url: str, *, headers: dict[str, str], json: dict[str, Any]) -> FakeResponse:  # noqa: A002
        FakeHttpClient.posted_headers = headers
        assert url.endswith("/v1/images/generations")
        assert json["model"] == "Kwai-Kolors/Kolors"
        assert "Authorization" in headers
        return FakeResponse({"images": [{"url": "https://example.invalid/generated.png"}], "seed": 123})

    def get(self, url: str) -> FakeResponse:
        assert url == "https://example.invalid/generated.png"
        return FakeResponse(content=b"\x89PNG\r\n\x1a\nfake", headers={"content-type": "application/octet-stream"})


def make_service(tmp_path: Path) -> ImageGenerationService:
    service = ImageGenerationService()
    service.workspace_dir = tmp_path
    service.backend_dir = tmp_path / "backend"
    service.assets_root = tmp_path / "assets" / "generated" / "visuals"
    service.manifest_path = service.assets_root / "asset_manifest.json"
    service._manifest = {"version": 1, "assets": {}}
    return service



def test_generate_without_key_returns_blocked_fallback(tmp_path, monkeypatch) -> None:
    service = make_service(tmp_path)
    monkeypatch.setattr(service, "_load_api_key", lambda: None)

    result = service.generate_asset("clue_red_seal", force=True)

    assert result["status"] == "fallback"
    assert result["generation_status"] == "blocked"
    assert result["blocked"] is True
    assert "未检测到图片生成 Key" in result["message"]
    assert result["generated_path"] is None

    manifest = service.manifest_path.read_text(encoding="utf-8")
    assert "Authorization" not in manifest
    assert "Bearer " not in manifest
    assert not re.search(r"sk-[A-Za-z0-9_\-]{8,}", manifest)


def test_image_key_can_be_loaded_from_workspace_env_without_status_leak(tmp_path, monkeypatch) -> None:
    service = make_service(tmp_path)
    monkeypatch.delenv("SILICONFLOW_API_KEY", raising=False)
    monkeypatch.delenv("IMAGE_GENERATION_API_KEY", raising=False)
    (tmp_path / ".env").write_text("SILICONFLOW_API_KEY=unit-test-root-image-key\n", encoding="utf-8")

    assert service._load_api_key() == "unit-test-root-image-key"
    assert service._has_api_key() is True

    serialized = json.dumps(service.list_status(), ensure_ascii=False)
    assert "unit-test-root-image-key" not in serialized
    assert "Authorization" not in serialized
    assert "Bearer " not in serialized


def test_generate_success_saves_local_file_without_leaking_headers(tmp_path, monkeypatch) -> None:
    service = make_service(tmp_path)
    monkeypatch.setattr(service, "_load_api_key", lambda: "unit-test-image-key")
    monkeypatch.setattr(httpx, "Client", FakeHttpClient)

    result = service.generate_asset("clue_burned_page", force=True)

    assert result["status"] == "generated"
    assert result["blocked"] is False
    assert result["generated_path"]
    saved_path = service.workspace_dir / result["generated_path"]
    assert saved_path.exists()
    assert saved_path.read_bytes().startswith(b"\x89PNG")
    assert FakeHttpClient.posted_headers["Authorization"].startswith("Bearer ")

    manifest_payload = json.loads(service.manifest_path.read_text(encoding="utf-8"))
    serialized = json.dumps(manifest_payload, ensure_ascii=False)
    assert "Authorization" not in serialized
    assert "Bearer " not in serialized
    assert "unit-test-image-key" not in serialized


def test_octet_stream_png_download_is_accepted(tmp_path) -> None:
    service = make_service(tmp_path)
    image_bytes = service._extract_image_bytes(
        {"images": [{"url": "https://example.invalid/generated.png"}]},
        FakeHttpClient(),
    )

    assert image_bytes.startswith(b"\x89PNG")
