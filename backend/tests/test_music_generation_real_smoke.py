from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from app.services.music_generation_service import music_generation_service


def test_real_tianpuyue_music_generation_or_explicit_blocked() -> None:
    if not music_generation_service.settings.music_api_key_available:
        pytest.skip("未检测到音乐生成 Key")

    poll_seconds = int(os.getenv("MUSIC_REAL_SMOKE_POLL_SECONDS", "0") or "0")
    result = music_generation_service.generate_track(
        "pre_game_entry",
        force=True,
        wait_for_audio=True,
        poll_seconds=max(0, min(poll_seconds, 180)),
    )

    serialized = json.dumps(result, ensure_ascii=False)
    assert "Authorization" not in serialized
    assert "Tempo-" not in serialized

    assert result["status"] in {
        "submitted",
        "succeeded",
        "main_succeeded",
        "running",
        "unknown",
        "failed",
        "part_failed",
        "blocked",
    }

    if result.get("asset_available"):
        generated_path = result.get("generated_path")
        assert generated_path
        assert (Path(music_generation_service.workspace_dir) / generated_path).exists()
        return

    if result["status"] == "submitted":
        assert result.get("item_id")
    if result["status"] == "blocked":
        assert result.get("error_code")
