from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from app.core.config import Settings
from app.services.music_generation_service import (
    DEFAULT_DURATION_SECONDS,
    GENERATION_API,
    QUERY_API,
    MusicGenerationService,
    MusicSelectionContext,
    select_bgm_id,
)


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


class FakeMusicHttpClient:
    posts: list[dict[str, Any]] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

    def __enter__(self) -> "FakeMusicHttpClient":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def post(self, url: str, *, json: dict[str, Any], headers: dict[str, str]) -> FakeResponse:  # noqa: A002
        payload = json
        FakeMusicHttpClient.posts.append({"url": url, "payload": payload, "headers": headers})
        if url.endswith("/generate"):
            return FakeResponse({"status": 200000, "message": "success", "request_id": "req_music_001", "data": {"item_ids": ["item_music_001"]}})
        if url.endswith("/query"):
            return FakeResponse(
                {
                    "status": 200000,
                    "message": "success",
                    "data": {
                        "instrumentals": [
                            {
                                "item_id": "item_music_001",
                                "status": "succeeded",
                                "audio_hi_status": "sub_succeeded",
                                "audio_url": "https://example.invalid/generated.mp3",
                                "duration": 80,
                            }
                        ]
                    }
                }
            )
        return FakeResponse({"status": 500000, "message": "unexpected"})

    def get(self, url: str) -> FakeResponse:
        assert url == "https://example.invalid/generated.mp3"
        return FakeResponse(content=b"ID3fake-audio", headers={"content-type": "audio/mpeg"})


def make_settings() -> Settings:
    return Settings(
        app_name="测试",
        version="0.11.0",
        use_mock_ai=True,
        ai_provider="mock",
        backend_port=8000,
        frontend_port=5173,
        deepseek_base_url="https://example.invalid",
        deepseek_model="mock",
        ai_timeout_seconds=1,
        ai_max_retries=0,
        deepseek_api_key=None,
        music_provider="tianpuyue",
        music_generate_endpoint="https://api.tianpuyue.cn/open-apis/v1/instrumental/generate",
        music_query_endpoint="https://api.tianpuyue.cn/open-apis/v1/instrumental/query",
        music_model="TemPolor i3.5",
        music_timeout_seconds=1,
        music_api_key="Tempo-unit-test-key",
        music_callback_url="https://example.invalid/api/music/callback",
    )


def make_service(tmp_path: Path) -> MusicGenerationService:
    service = MusicGenerationService(runtime_settings=make_settings())
    service.workspace_dir = tmp_path
    service.backend_dir = tmp_path / "backend"
    service.data_dir = tmp_path / "backend" / "data" / "music"
    service.generated_root = tmp_path / "assets" / "generated" / "music"
    service.manifest_path = service.data_dir / "music_manifest.json"
    service.tasks_path = service.data_dir / "music_tasks.json"
    service.data_dir.mkdir(parents=True, exist_ok=True)
    service.generated_root.mkdir(parents=True, exist_ok=True)
    return service


def test_music_manifest_schema_and_no_secret_leak(tmp_path: Path) -> None:
    service = make_service(tmp_path)

    manifest = service.ensure_manifest()

    assert manifest["provider"] == "tianpuyue"
    assert manifest["generation_api"] == GENERATION_API
    assert manifest["query_api"] == QUERY_API
    assert manifest["model"] == "TemPolor i3.5"
    assert len(manifest["tracks"]) == 14
    track_ids = {track["bgm_id"] for track in manifest["tracks"]}
    assert "pre_game_entry" in track_ids
    assert "ming_choice_evidence" in track_ids
    assert "ending_hidden" in track_ids
    for track in manifest["tracks"]:
        assert track["asset_url"].startswith("/api/music/assets/")
        assert track["fallback_url"] == "/api/music/fallback/silence.wav"
        assert 0.25 <= track["volume"] <= 0.4
        assert 1200 <= track["fade_ms"] <= 2500
        assert track["duration_seconds"] == DEFAULT_DURATION_SECONDS

    serialized = json.dumps(manifest, ensure_ascii=False)
    assert "Tempo-unit-test-key" not in serialized
    assert "Authorization" not in serialized


def test_music_status_only_reports_key_presence(tmp_path: Path) -> None:
    service = make_service(tmp_path)

    status = service.list_status()

    assert status["api_key_available"] is True
    assert status["callback_url_available"] is True
    assert status["completion_strategy"] == "query_polling"
    assert status["callback_required_for_completion"] is False
    serialized = json.dumps(status, ensure_ascii=False)
    assert "Tempo-unit-test-key" not in serialized
    assert "Authorization" not in serialized


def test_generate_track_uses_tianpuyue_payload(tmp_path: Path, monkeypatch) -> None:
    service = make_service(tmp_path)
    FakeMusicHttpClient.posts = []
    monkeypatch.setattr(httpx, "Client", FakeMusicHttpClient)

    result = service.generate_track("pre_game_entry", force=True)

    assert result["status"] == "submitted"
    assert result["item_id"] == "item_music_001"
    posted = FakeMusicHttpClient.posts[0]
    assert posted["url"].endswith("/instrumental/generate")
    assert posted["payload"]["model"] == "TemPolor i3.5"
    assert posted["payload"]["callback_url"] == "https://example.invalid/api/music/callback"
    assert "Instrumental" in posted["payload"]["prompt"]
    assert "no vocal" in posted["payload"]["prompt"]
    assert "no lyrics" in posted["payload"]["prompt"]
    assert "duration 80 seconds" in posted["payload"]["prompt"]
    assert posted["headers"]["Authorization"] == "Tempo-unit-test-key"

    manifest_text = service.manifest_path.read_text(encoding="utf-8")
    assert "Tempo-unit-test-key" not in manifest_text
    assert "Authorization" not in manifest_text


def test_query_task_downloads_audio_without_storing_remote_url(tmp_path: Path, monkeypatch) -> None:
    service = make_service(tmp_path)
    FakeMusicHttpClient.posts = []
    monkeypatch.setattr(httpx, "Client", FakeMusicHttpClient)

    result = service.query_task("item_music_001", bgm_id="pre_game_entry", download_on_success=True)

    assert result["status"] == "succeeded"
    assert result["asset_available"] is True
    saved_path = tmp_path / result["generated_path"]
    assert saved_path.exists()
    assert saved_path.read_bytes().startswith(b"ID3")
    assert FakeMusicHttpClient.posts[0]["url"].endswith("/instrumental/query")
    assert FakeMusicHttpClient.posts[0]["payload"] == {"item_ids": ["item_music_001"]}

    tasks_text = service.tasks_path.read_text(encoding="utf-8")
    assert "https://example.invalid/generated.mp3" not in tasks_text


def test_callback_downloads_audio_and_accepts_item_id(tmp_path: Path, monkeypatch) -> None:
    service = make_service(tmp_path)
    monkeypatch.setattr(httpx, "Client", FakeMusicHttpClient)
    service._record_task({"task_id": "item_music_001", "item_id": "item_music_001", "bgm_id": "pre_game_entry"})

    result = service.handle_callback(
        {
            "instrumentals": [
                {
                    "item_id": "item_music_001",
                    "status": "succeeded",
                    "audio_hi_status": "sub_succeeded",
                    "audio_hi_url": "https://example.invalid/generated.mp3",
                    "event": "wav_complete",
                }
            ]
        }
    )

    assert result["accepted"] is True
    assert result["asset_available"] is True
    assert (service.generated_root / "pre_game_entry.mp3").exists()


def test_missing_generated_audio_falls_back_in_manifest(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    generated = service.generated_root / "pre_game_entry.mp3"
    generated.write_bytes(b"ID3fake-audio")

    first_manifest = service.ensure_manifest()
    first_track = next(track for track in first_manifest["tracks"] if track["bgm_id"] == "pre_game_entry")
    assert first_track["asset_available"] is True

    generated.rename(service.generated_root / "pre_game_entry.missing")
    second_manifest = service.ensure_manifest()
    second_track = next(track for track in second_manifest["tracks"] if track["bgm_id"] == "pre_game_entry")

    assert second_track["asset_available"] is False
    assert second_track["fallback_url"] == "/api/music/fallback/silence.wav"
    assert second_track["generated_path"] is None


def test_bgm_selection_priority() -> None:
    assert select_bgm_id(MusicSelectionContext(current_stage="choice", current_npc_id="npc_owner")) == "ming_choice_evidence"
    assert select_bgm_id(MusicSelectionContext(current_stage="reversal", current_npc_id="npc_worker")) == "ming_reversal_grain_record"
    assert select_bgm_id(MusicSelectionContext(current_stage="investigation", current_scene_id="scene_fire_yard", current_npc_id="npc_worker")) == "ming_npc_worker_ashen"
    assert select_bgm_id(MusicSelectionContext(current_stage="investigation", current_scene_id="scene_lamp_shelf")) == "ming_investigation_threads"
    assert select_bgm_id(MusicSelectionContext(current_stage="investigation", risk_level=6)) == "ming_reversal_grain_record"
    assert select_bgm_id(MusicSelectionContext(current_stage="intro")) == "ming_intro_night_fire"
    assert select_bgm_id(MusicSelectionContext(ending_id="ending_hidden", current_stage="choice")) == "ending_hidden"
    assert select_bgm_id(MusicSelectionContext()) == "pre_game_entry"
