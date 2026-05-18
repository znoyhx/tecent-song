from __future__ import annotations

from typing import Any

from app.models.game_models import GameScores, GameState
from app.services.ai_client import AIResponse
from app.services.game_engine import engine
from app.services.history_echo_generator import HistoryEchoGenerator


class StaticHistoryEchoAIClient:
    def __init__(self, response: AIResponse) -> None:
        self.response = response
        self.last_prompt = ""

    def generate_json_sync(self, *, module: str, prompt: str, schema_hint: dict[str, Any]) -> AIResponse:
        self.last_prompt = prompt
        assert module == "HistoryEchoGenerator"
        assert "不得输出、修改或暗示新的 ending_id" in prompt
        return self.response


def build_truth_state() -> GameState:
    return GameState(
        session_id="s_echo",
        event_id="ming_bookshop_fire",
        dynasty_id="ming",
        player_role_id="role_ming_bookshop_apprentice",
        current_stage="ending",
        current_scene_id="scene_interrogation_room",
        discovered_clue_ids=["clue_burned_page", "clue_red_seal", "clue_poem_hidden_copy"],
        completed_combo_ids=["combo_burned_text_is_ledger"],
        npc_trust={"npc_owner": 0, "npc_worker": 1, "npc_scholar": 2, "npc_jinyiwei": 1},
        flags=["preserved_evidence", "ledger_truth_exposed"],
        scores=GameScores(truth=5, survival=1),
        risk_level=3,
        available_scene_ids=["scene_interrogation_room"],
        available_choice_ids=[],
        turn_count=8,
        status="ending_ready",
        final_choice_id="choice_help_scholar",
    )


def test_history_echo_fallback_references_choice_clues_and_fates() -> None:
    ai_client = StaticHistoryEchoAIClient(
        AIResponse(success=False, parsed_json={}, raw_text="", latency_ms=1, fallback_used=True, error_message="测试回退", model="fake")
    )
    generator = HistoryEchoGenerator(ai_client=ai_client)
    ending = engine.endings["ending_truth"]

    result = generator.generate(
        ending=ending,
        state=build_truth_state(),
        choices=engine.choices,
        clues=engine.clues,
        npcs=engine.npcs,
        template_echo="纸页能藏一夜，就有机会再过一城。",
    )

    assert result.ai_success is False
    assert result.fallback_used is True
    assert "暗助顾闻护出残页" in result.text
    assert "烧焦残页" in result.text
    assert "半枚红印纸角" in result.text
    assert "顾闻" in result.text or "阿沈" in result.text
    assert len(result.sources) >= 5


def test_history_echo_ai_result_is_used_without_accepting_ending_id() -> None:
    ai_client = StaticHistoryEchoAIClient(
        AIResponse(
            success=True,
            parsed_json={
                "history_echo": "你选择暗助顾闻护出残页，使烧焦残页与半枚红印纸角不再只是灰烬旁的物证，也让顾闻和阿沈的命运被同一场火照亮。"
                "书坊暂时沉默，封口令背后的时代压力却仍未消散。",
                "ending_id": "ending_hidden",
            },
            raw_text="{}",
            latency_ms=1,
            fallback_used=False,
            error_message=None,
            model="fake",
        )
    )
    generator = HistoryEchoGenerator(ai_client=ai_client)

    result = generator.generate(
        ending=engine.endings["ending_truth"],
        state=build_truth_state(),
        choices=engine.choices,
        clues=engine.clues,
        npcs=engine.npcs,
        template_echo="本地模板。",
    )

    assert result.ai_success is True
    assert result.fallback_used is False
    assert "ending_hidden" not in result.text
    assert "烧焦残页" in result.text


def test_history_echo_ai_result_without_context_references_falls_back() -> None:
    ai_client = StaticHistoryEchoAIClient(
        AIResponse(
            success=True,
            parsed_json={"history_echo": "这是一段很克制的中文收束，但没有引用本局选择、线索或人物去向。"},
            raw_text="{}",
            latency_ms=1,
            fallback_used=False,
            error_message=None,
            model="fake",
        )
    )
    generator = HistoryEchoGenerator(ai_client=ai_client)

    result = generator.generate(
        ending=engine.endings["ending_truth"],
        state=build_truth_state(),
        choices=engine.choices,
        clues=engine.clues,
        npcs=engine.npcs,
        template_echo="纸页能藏一夜，就有机会再过一城。",
    )

    assert result.ai_success is False
    assert result.fallback_used is True
    assert "暗助顾闻护出残页" in result.text
    assert "烧焦残页" in result.text

