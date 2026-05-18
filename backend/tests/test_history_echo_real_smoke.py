from __future__ import annotations

import pytest

from app.core.config import load_settings
from app.models.game_models import GameScores, GameState
from app.services.history_echo_generator import HistoryEchoGenerator
from app.services.game_engine import engine


def test_real_history_echo_smoke_or_explicit_fallback() -> None:
    runtime_settings = load_settings()
    if runtime_settings.use_mock_ai or runtime_settings.ai_provider != "deepseek":
        pytest.skip("真实 AI 模式未开启：请设置 USE_MOCK_AI=false 且 AI_PROVIDER=deepseek 后再运行。")
    if not runtime_settings.deepseek_api_key_available:
        pytest.skip("未检测到 DeepSeek Key：请在安全环境变量或本机后端配置中补齐后再运行。")

    state = GameState(
        session_id="s_real_echo",
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
    result = HistoryEchoGenerator(runtime_settings=runtime_settings).generate(
        ending=engine.endings["ending_truth"],
        state=state,
        choices=engine.choices,
        clues=engine.clues,
        npcs=engine.npcs,
        template_echo="纸页能藏一夜，就有机会再过一城。",
    )

    assert result.text
    assert any("\u4e00" <= char <= "\u9fff" for char in result.text)
    if result.ai_success:
        assert result.fallback_used is False
    else:
        assert result.fallback_used is True
