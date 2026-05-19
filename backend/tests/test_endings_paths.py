from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.game_engine import engine

client = TestClient(app)


def setup_function() -> None:
    engine.sessions.clear()


def reach_choice_stage() -> str:
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

    steps = [
        ("dialogue", {"session_id": session_id, "npc_id": "npc_owner", "message": "昨夜第一眼看见什么？", "action_type": "question", "presented_clue_ids": []}),
        ("investigate", {"session_id": session_id, "scene_id": "scene_fire_yard", "hotspot_id": "ash_pile"}),
        ("investigate", {"session_id": session_id, "scene_id": "scene_engraving_room"}),
        ("dialogue", {"session_id": session_id, "npc_id": "npc_worker", "message": "你昨夜一直在刻坊吗？", "action_type": "question", "presented_clue_ids": []}),
        ("dialogue", {"session_id": session_id, "npc_id": "npc_worker", "message": "你这话前后对不上。", "action_type": "question", "presented_clue_ids": ["clue_worker_lie"]}),
        ("investigate", {"session_id": session_id, "scene_id": "scene_front_hall", "hotspot_id": "old_box"}),
        ("investigate", {"session_id": session_id, "scene_id": "scene_rain_alley"}),
        ("dialogue", {"session_id": session_id, "npc_id": "npc_scholar", "message": "你回书坊究竟是为了什么？", "action_type": "question", "presented_clue_ids": []}),
        ("dialogue", {"session_id": session_id, "npc_id": "npc_scholar", "message": "这张残页你总该认识。", "action_type": "question", "presented_clue_ids": ["clue_burned_page"]}),
        ("investigate", {"session_id": session_id, "scene_id": "scene_rain_alley", "hotspot_id": "search_notice"}),
        ("investigate", {"session_id": session_id, "scene_id": "scene_city_gate", "hotspot_id": "second_notice"}),
        ("investigate", {"session_id": session_id, "scene_id": "scene_interrogation_room", "hotspot_id": "sealed_desk"}),
        ("investigate", {"session_id": session_id, "scene_id": "scene_interrogation_room", "hotspot_id": "temp_record"}),
    ]
    for endpoint, payload in steps:
        response = client.post(f"/api/{endpoint}", json=payload)
        assert response.status_code == 200, response.text

    snapshot = client.get(f"/api/session/{session_id}")
    assert snapshot.status_code == 200
    assert snapshot.json()["state"]["current_stage"] == "choice"
    return session_id


@pytest.mark.parametrize(
    ("choice_id", "expected_ending_id", "expected_title"),
    [
        ("choice_destroy_evidence", "ending_survival", "焚稿自保"),
        ("choice_give_to_lu", "ending_order", "误信告发"),
        ("choice_help_scholar", "ending_truth", "暗藏残页"),
        ("choice_force_worker", "ending_tragedy", "身陷诏狱"),
    ],
)
def test_api_paths_resolve_distinct_endings(choice_id: str, expected_ending_id: str, expected_title: str) -> None:
    session_id = reach_choice_stage()

    choose = client.post("/api/choice", json={"session_id": session_id, "choice_id": choice_id})
    assert choose.status_code == 200
    assert choose.json()["state"]["current_stage"] == "ending"

    ending = client.post("/api/ending/resolve", json={"session_id": session_id})
    assert ending.status_code == 200
    payload = ending.json()

    assert payload["ending_id"] == expected_ending_id
    assert payload["title"] == expected_title
    assert payload["history_echo"]
    assert any("\u4e00" <= char <= "\u9fff" for char in payload["history_echo"])
    assert len(payload["history_echo_sources"]) >= 3
    assert isinstance(payload["history_echo_fallback_used"], bool)
    assert isinstance(payload["history_echo_ai_used"], bool)
    assert payload["history_echo_ai_used"] is not payload["history_echo_fallback_used"]


def test_hidden_ending_is_deterministic_from_state_rules() -> None:
    state = engine.sessions.setdefault("s_hidden", {})
    session_state = engine.start_session(
        type("Request", (), {"dynasty_id": "ming", "role_id": "role_ming_bookshop_apprentice", "event_id": "ming_bookshop_fire"})()
    )["state"]
    real_session_id = session_state["session_id"]
    record = engine.sessions[real_session_id]
    game_state = record["state"]
    game_state.current_stage = "ending"
    game_state.status = "ending_ready"
    game_state.final_choice_id = "choice_reverse_trace"
    game_state.discovered_clue_ids = ["clue_poem_hidden_copy"]
    game_state.flags = ["found_hidden_chain", "preserved_evidence", "ledger_truth_exposed", "deduced_scholar_motive"]
    game_state.npc_trust["npc_scholar"] = 2
    game_state.npc_trust["npc_jinyiwei"] = 2
    game_state.scores.truth = 6
    game_state.risk_level = 1
    state.clear()

    ending = client.post("/api/ending/resolve", json={"session_id": real_session_id})
    assert ending.status_code == 200
    assert ending.json()["ending_id"] == "ending_hidden"
    assert ending.json()["title"] == "引火反查"
