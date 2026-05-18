from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.services.dialogue_orchestrator import DialogueOrchestrator
from app.services.game_engine import engine
from app.services.log_service import LogService


client = TestClient(app)


def setup_function() -> None:
    engine.sessions.clear()


def test_dialogue_falls_back_to_chinese_mock_when_key_missing(monkeypatch, tmp_path) -> None:
    runtime_settings = Settings(
        app_name="测试",
        version="0.4.0",
        use_mock_ai=False,
        ai_provider="deepseek",
        backend_port=8000,
        frontend_port=5173,
        deepseek_base_url="https://example.invalid",
        deepseek_model="deepseek-chat",
        ai_timeout_seconds=1,
        ai_max_retries=0,
        deepseek_api_key=None,
    )
    monkeypatch.setattr(
        engine,
        "dialogue_orchestrator",
        DialogueOrchestrator(runtime_settings=runtime_settings, logs=LogService(tmp_path)),
    )

    start = client.post(
        "/api/session/start",
        json={
            "dynasty_id": "ming",
            "role_id": "role_ming_bookshop_apprentice",
            "event_id": "ming_bookshop_fire",
        },
    )
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    result = client.post(
        "/api/dialogue",
        json={
            "session_id": session_id,
            "npc_id": "npc_owner",
            "message": "昨夜第一眼看见什么？",
            "action_type": "question",
            "presented_clue_ids": [],
        },
    )

    assert result.status_code == 200
    payload = result.json()
    assert payload["fallback_used"] is True
    dialogue = payload["dialogue"]["npc_dialogue"]
    assert re.search(r"[\u4e00-\u9fff]", dialogue)
    assert not re.search(r"[A-Za-z]{2,}", dialogue)
    assert any(clue["clue_id"] == "clue_missing_manuscript_list" for clue in payload["new_clues"])
    assert payload["state"]["current_stage"] == "investigation"
