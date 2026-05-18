from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.models.game_models import GameScores, GameState
from app.services.game_engine import engine

client = TestClient(app)


def setup_function() -> None:
    engine.sessions.clear()


def start_session() -> str:
    response = client.post(
        "/api/session/start",
        json={
            "dynasty_id": "ming",
            "role_id": "role_ming_bookshop_apprentice",
            "event_id": "ming_bookshop_fire",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["session_id"]


def test_deductions_require_player_submission_and_return_chinese_feedback() -> None:
    session_id = start_session()
    state = engine.sessions[session_id]["state"]
    state.current_stage = "reversal"
    state.discovered_clue_ids = ["clue_burned_page", "clue_red_seal", "clue_grain_term_mismatch"]
    engine._refresh_state_metadata(state)

    snapshot = client.get(f"/api/session/{session_id}")
    assert snapshot.status_code == 200
    available = snapshot.json()["available_deductions"]
    assert any(item["deduction_id"] == "deduce_burned_not_poem" for item in available)
    assert all("correct_clue_ids" not in item for item in available)

    assert engine._evaluate_deductions(state) == []
    assert "deduced_burned_not_poem" not in state.flags

    wrong = client.post(
        "/api/deduction/submit",
        json={
            "session_id": session_id,
            "deduction_id": "deduce_burned_not_poem",
            "selected_clue_ids": ["clue_burned_page"],
        },
    )
    assert wrong.status_code == 200, wrong.text
    wrong_payload = wrong.json()
    assert wrong_payload["correct"] is False
    assert "必须找到粮册字样和官式纸角" in wrong_payload["feedback"]
    assert "deduced_burned_not_poem" not in wrong_payload["state"]["flags"]
    assert wrong_payload["state"]["scores"]["truth"] == 0

    correct = client.post(
        "/api/deduction/submit",
        json={
            "session_id": session_id,
            "deduction_id": "deduce_burned_not_poem",
            "selected_clue_ids": ["clue_burned_page", "clue_red_seal", "clue_grain_term_mismatch"],
        },
    )
    assert correct.status_code == 200, correct.text
    correct_payload = correct.json()
    assert correct_payload["correct"] is True
    assert "被烧毁的是夹在诗稿里的账册抄录" in correct_payload["feedback"]
    assert "deduced_burned_not_poem" in correct_payload["state"]["flags"]
    assert "deduce_burned_not_poem" in correct_payload["state"]["completed_deduction_ids"]
    assert correct_payload["state"]["scores"]["truth"] == 1
    assert correct_payload["state"]["risk_level"] == 1


def test_gag_order_alone_does_not_open_choice_stage() -> None:
    session_id = start_session()
    state = engine.sessions[session_id]["state"]
    state.current_stage = "reversal"
    state.discovered_clue_ids = ["clue_jinyiwei_gag_order"]
    engine._refresh_state_metadata(state)

    engine._evaluate_transitions(state)

    assert state.current_stage == "reversal"


def test_choice_stage_requires_burned_target_and_hidden_chain() -> None:
    session_id = start_session()
    state = engine.sessions[session_id]["state"]
    state.current_stage = "reversal"
    state.discovered_clue_ids = [
        "clue_burned_page",
        "clue_red_seal",
        "clue_poem_hidden_copy",
        "clue_gag_order_wording",
        "clue_temp_interrogation_record",
        "clue_city_gate_second_notice",
    ]
    state.completed_combo_ids = ["combo_burned_text_is_ledger"]
    state.flags = ["ledger_truth_exposed"]
    engine._refresh_state_metadata(state)

    engine._evaluate_transitions(state)
    assert state.current_stage == "reversal"

    state.completed_combo_ids.append("combo_hidden_chain")
    state.flags.append("found_hidden_chain")
    engine._evaluate_transitions(state)
    assert state.current_stage == "choice"


def test_clue_unlock_conditions_block_dialogue_release_until_ready() -> None:
    session_id = start_session()
    state = engine.sessions[session_id]["state"]
    state.current_stage = "reversal"
    state.current_scene_id = "scene_interrogation_room"
    state.discovered_clue_ids = []
    engine._refresh_state_metadata(state)

    blocked = client.post(
        "/api/dialogue",
        json={
            "session_id": session_id,
            "npc_id": "npc_jinyiwei",
            "message": "你为何不问火因？",
            "action_type": "question",
            "presented_clue_ids": [],
        },
    )
    assert blocked.status_code == 200, blocked.text
    assert blocked.json()["new_clues"] == []

    state.discovered_clue_ids = ["clue_red_seal", "clue_jinyiwei_gag_order"]
    released = client.post(
        "/api/dialogue",
        json={
            "session_id": session_id,
            "npc_id": "npc_jinyiwei",
            "message": "你为何不问火因？",
            "action_type": "question",
            "presented_clue_ids": [],
        },
    )
    assert released.status_code == 200, released.text
    assert any(clue["clue_id"] == "clue_lu_order_conflict" for clue in released.json()["new_clues"])


def build_ending_state() -> GameState:
    return GameState(
        session_id="s_test",
        event_id="ming_bookshop_fire",
        dynasty_id="ming",
        player_role_id="role_ming_bookshop_apprentice",
        current_stage="ending",
        current_scene_id="scene_front_hall",
        discovered_clue_ids=[],
        completed_combo_ids=[],
        completed_deduction_ids=[],
        npc_trust={"npc_owner": 0, "npc_worker": 0, "npc_scholar": 0, "npc_jinyiwei": 0},
        flags=[],
        scores=GameScores(),
        risk_level=0,
        available_scene_ids=["scene_front_hall"],
        available_choice_ids=[],
        turn_count=0,
        status="ending_ready",
        final_choice_id="choice_reverse_trace",
    )


def test_hidden_ending_requires_hidden_copy_and_burned_target_chain() -> None:
    missing_chain = build_ending_state()
    missing_chain.flags = ["found_hidden_chain", "preserved_evidence"]
    missing_chain.npc_trust["npc_scholar"] = 2
    missing_chain.npc_trust["npc_jinyiwei"] = 2
    missing_chain.scores.truth = 6
    assert engine._pick_ending(missing_chain).ending_id != "ending_hidden"

    complete = build_ending_state()
    complete.discovered_clue_ids = ["clue_poem_hidden_copy"]
    complete.flags = [
        "found_hidden_chain",
        "preserved_evidence",
        "ledger_truth_exposed",
        "deduced_scholar_motive",
    ]
    complete.npc_trust["npc_scholar"] = 2
    complete.npc_trust["npc_jinyiwei"] = 2
    complete.scores.truth = 6
    complete.risk_level = 6
    assert engine._pick_ending(complete).ending_id == "ending_hidden"
