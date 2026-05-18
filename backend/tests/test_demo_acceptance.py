from __future__ import annotations

import json
import re
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from app.services.game_engine import engine

client = TestClient(app)

SECRET_PATTERN = re.compile(r"Bearer\s+|Authorization|sk-[A-Za-z0-9_\-]{8,}")


def setup_function() -> None:
    engine.sessions.clear()


def _assert_has_chinese(value: str) -> None:
    assert any("\u4e00" <= char <= "\u9fff" for char in value)


def _assert_no_secret_payload(payload: Any) -> None:
    serialized = json.dumps(payload, ensure_ascii=False)
    assert SECRET_PATTERN.search(serialized) is None


def _post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post(path, json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    _assert_no_secret_payload(data)
    return data


def _start_demo_session() -> str:
    payload = _post_json(
        "/api/session/start",
        {
            "dynasty_id": "ming",
            "role_id": "role_ming_bookshop_apprentice",
            "event_id": "ming_bookshop_fire",
        },
    )
    assert payload["state"]["current_stage"] == "intro"
    assert payload["scene"]["name"] == "书坊前厅"
    _assert_has_chinese(payload["current_goal"])
    return payload["session_id"]


def _reach_choice_stage(session_id: str) -> dict[str, Any]:
    steps = [
        ("/api/dialogue", {"session_id": session_id, "npc_id": "npc_owner", "message": "昨夜第一眼看见什么？", "action_type": "question", "presented_clue_ids": []}),
        ("/api/investigate", {"session_id": session_id, "scene_id": "scene_fire_yard", "hotspot_id": "ash_pile"}),
        ("/api/investigate", {"session_id": session_id, "scene_id": "scene_engraving_room"}),
        ("/api/dialogue", {"session_id": session_id, "npc_id": "npc_worker", "message": "你昨夜一直在刻坊吗？", "action_type": "question", "presented_clue_ids": []}),
        ("/api/dialogue", {"session_id": session_id, "npc_id": "npc_worker", "message": "你这话前后对不上。", "action_type": "question", "presented_clue_ids": ["clue_worker_lie"]}),
        ("/api/investigate", {"session_id": session_id, "scene_id": "scene_front_hall", "hotspot_id": "old_box"}),
        ("/api/investigate", {"session_id": session_id, "scene_id": "scene_rain_alley"}),
        ("/api/dialogue", {"session_id": session_id, "npc_id": "npc_scholar", "message": "你回书坊究竟是为了什么？", "action_type": "question", "presented_clue_ids": []}),
        ("/api/dialogue", {"session_id": session_id, "npc_id": "npc_scholar", "message": "这张残页你总该认识。", "action_type": "question", "presented_clue_ids": ["clue_burned_page"]}),
        ("/api/investigate", {"session_id": session_id, "scene_id": "scene_rain_alley", "hotspot_id": "search_notice"}),
        ("/api/investigate", {"session_id": session_id, "scene_id": "scene_city_gate", "hotspot_id": "second_notice"}),
        ("/api/investigate", {"session_id": session_id, "scene_id": "scene_interrogation_room", "hotspot_id": "sealed_desk"}),
        ("/api/investigate", {"session_id": session_id, "scene_id": "scene_interrogation_room", "hotspot_id": "temp_record"}),
    ]
    seen_clue_ids: set[str] = set()
    saw_dialogue = False
    saw_state_change = False

    for path, payload in steps:
        before_stage = client.get(f"/api/session/{session_id}").json()["state"]["current_stage"]
        result = _post_json(path, payload)
        seen_clue_ids.update(clue["clue_id"] for clue in result.get("new_clues", []))
        saw_dialogue = saw_dialogue or path == "/api/dialogue"
        saw_state_change = saw_state_change or result.get("state", {}).get("current_stage") != before_stage

    snapshot_response = client.get(f"/api/session/{session_id}")
    assert snapshot_response.status_code == 200
    snapshot = snapshot_response.json()
    _assert_no_secret_payload(snapshot)

    assert snapshot["state"]["current_stage"] == "choice"
    assert "clue_burned_page" in seen_clue_ids
    assert "clue_red_seal" in seen_clue_ids
    assert saw_dialogue is True
    assert saw_state_change is True
    assert len(snapshot["available_choices"]) >= 3
    return snapshot


def test_stage_10_demo_smoke_reaches_truth_ending_with_safe_payload() -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    health_payload = health.json()
    assert health_payload["status"] == "ok"
    assert health_payload["display_text"] == "服务运行中"
    _assert_no_secret_payload(health_payload)

    session_id = _start_demo_session()
    choice_snapshot = _reach_choice_stage(session_id)
    assert any(choice["choice_id"] == "choice_help_scholar" for choice in choice_snapshot["available_choices"])

    choice_result = _post_json("/api/choice", {"session_id": session_id, "choice_id": "choice_help_scholar"})
    assert choice_result["state"]["current_stage"] == "ending"

    ending = _post_json("/api/ending/resolve", {"session_id": session_id})
    for field in [
        "ending_id",
        "title",
        "summary",
        "ending_text",
        "history_echo",
        "npc_fates",
        "history_echo_ai_used",
        "history_echo_fallback_used",
    ]:
        assert field in ending

    assert ending["ending_id"] == "ending_truth"
    assert isinstance(ending["npc_fates"], dict)
    assert ending["npc_fates"]
    for field in ["title", "summary", "ending_text", "history_echo"]:
        _assert_has_chinese(str(ending[field]))
    assert isinstance(ending["history_echo_ai_used"], bool)
    assert isinstance(ending["history_echo_fallback_used"], bool)
    _assert_no_secret_payload(ending)
