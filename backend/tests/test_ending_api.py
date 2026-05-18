from __future__ import annotations

import json
import re
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from app.models.game_models import GameScores, SessionStartRequest
from app.services.game_engine import engine
from app.services.history_echo_generator import HistoryEchoResult

client = TestClient(app)

SECRET_PATTERN = re.compile(r"Bearer\s+|sk-[A-Za-z0-9_\-]{8,}|Authorization")


def setup_function() -> None:
    engine.sessions.clear()


def _seed_ending_state(
    *,
    final_choice_id: str,
    scores: GameScores,
    flags: list[str] | None = None,
    discovered_clue_ids: list[str] | None = None,
    completed_combo_ids: list[str] | None = None,
    npc_trust: dict[str, int] | None = None,
    risk_level: int = 0,
) -> str:
    snapshot = engine.start_session(
        SessionStartRequest(
            dynasty_id="ming",
            role_id="role_ming_bookshop_apprentice",
            event_id="ming_bookshop_fire",
        )
    )
    session_id = snapshot["session_id"]
    state = engine.sessions[session_id]["state"]
    state.current_stage = "ending"
    state.current_scene_id = "scene_interrogation_room"
    state.status = "ending_ready"
    state.final_choice_id = final_choice_id
    state.scores = scores
    state.flags = flags or []
    state.discovered_clue_ids = discovered_clue_ids or []
    state.completed_combo_ids = completed_combo_ids or []
    state.risk_level = risk_level
    if npc_trust:
        state.npc_trust.update(npc_trust)
    return session_id


def test_resolve_ending_api_returns_complete_chinese_payload_without_image_dependency() -> None:
    session_id = _seed_ending_state(
        final_choice_id="choice_give_to_lu",
        scores=GameScores(order=4, truth=3),
        flags=["surrendered_to_lu", "seal_order_found"],
        discovered_clue_ids=["clue_burned_page", "clue_red_seal", "clue_jinyiwei_gag_order"],
        npc_trust={"npc_jinyiwei": 1},
        risk_level=2,
    )

    response = client.post("/api/ending/resolve", json={"session_id": session_id})
    assert response.status_code == 200
    payload = response.json()

    assert payload["ending_id"] == "ending_order"
    assert payload["title"] == "误信告发"
    for field in ["summary", "ending_text", "history_echo"]:
        assert payload[field]
        assert any("\u4e00" <= char <= "\u9fff" for char in payload[field])
    assert isinstance(payload["npc_fates"], dict)
    assert len(payload["npc_fates"]) >= 2
    assert len(payload["history_echo_sources"]) >= 3
    assert "visual_asset_url" in payload
    assert payload["visual_asset_url"]


def test_ending_id_is_kept_by_rules_even_when_history_echo_uses_ai(monkeypatch: Any) -> None:
    class FakeHistoryEchoGenerator:
        def generate(self, **kwargs: Any) -> HistoryEchoResult:
            assert kwargs["ending"].ending_id == "ending_truth"
            return HistoryEchoResult(
                text="你选择暗助顾闻护出残页，使烧焦残页和半枚红印纸角继续指向粮册背后的时代压力，顾闻与阿沈的命运也因此被保留下另一种可能。",
                sources=["最终选择：暗助顾闻护出残页", "关键线索：烧焦残页", "关键线索：半枚红印纸角", "人物命运：顾闻"],
                ai_success=True,
                fallback_used=False,
            )

    monkeypatch.setattr(engine, "history_echo_generator", FakeHistoryEchoGenerator())
    session_id = _seed_ending_state(
        final_choice_id="choice_help_scholar",
        scores=GameScores(truth=5, survival=1),
        flags=["preserved_evidence", "ledger_truth_exposed"],
        discovered_clue_ids=["clue_burned_page", "clue_red_seal", "clue_poem_hidden_copy"],
        completed_combo_ids=["combo_burned_text_is_ledger"],
        npc_trust={"npc_scholar": 2, "npc_worker": 1},
        risk_level=3,
    )

    response = client.post("/api/ending/resolve", json={"session_id": session_id})
    assert response.status_code == 200
    payload = response.json()

    assert payload["ending_id"] == "ending_truth"
    assert payload["history_echo_ai_used"] is True
    assert payload["history_echo_fallback_used"] is False
    assert "烧焦残页" in payload["history_echo"]


def test_resolved_ending_payload_does_not_expose_secret_patterns() -> None:
    session_id = _seed_ending_state(
        final_choice_id="choice_destroy_evidence",
        scores=GameScores(survival=4),
        flags=["burned_remaining_pages"],
        discovered_clue_ids=["clue_owner_moved_box", "clue_missing_manuscript_list"],
    )

    response = client.post("/api/ending/resolve", json={"session_id": session_id})
    assert response.status_code == 200
    serialized = json.dumps(response.json(), ensure_ascii=False)
    assert SECRET_PATTERN.search(serialized) is None
