from __future__ import annotations

import json
import re
from typing import Any

from app.core.config import Settings
from app.models.game_models import DialogueRequest, GameScores, GameState
from app.services.ai_client import AIResponse
from app.services.dialogue_orchestrator import DialogueOrchestrator
from app.services.game_engine import engine
from app.services.log_service import LogService


class FakeAIClient:
    def generate_json_sync(self, *, module: str, prompt: str, schema_hint: dict[str, Any]) -> AIResponse:
        payload = {
            "npc_dialogue": "阿沈攥着袖口，声音低得发颤：我只听见后院有人压着嗓子说，那箱东西不能留到天亮。别再问大声了。",
            "npc_action": "他先看了一眼门口，又把沾着旧墨的袖子往身后藏。",
            "emotion": "fearful",
            "released_clue_ids": [],
            "highlight_clues": [],
            "suggested_questions": ["那箱东西是谁搬的？", "你为何现在才肯说？"],
            "state_update_suggestion": {
                "npc_trust_delta": 0,
                "truth_score_delta": 0,
                "order_score_delta": 0,
                "survival_score_delta": 0,
                "risk_level_delta": 0,
                "new_flags": [],
            },
        }
        return AIResponse(
            success=True,
            parsed_json=payload,
            raw_text=json.dumps(payload, ensure_ascii=False),
            latency_ms=8,
            fallback_used=False,
            error_message=None,
            model="fake-json-model",
        )


def test_ai_dialogue_json_for_worker_is_structured_chinese(tmp_path) -> None:
    runtime_settings = Settings(
        app_name="测试",
        version="0.4.0",
        use_mock_ai=False,
        ai_provider="deepseek",
        backend_port=8000,
        frontend_port=5173,
        deepseek_base_url="https://example.invalid",
        deepseek_model="fake-json-model",
        ai_timeout_seconds=1,
        ai_max_retries=0,
        deepseek_api_key="测试密钥占位",
    )
    orchestrator = DialogueOrchestrator(
        ai_client=FakeAIClient(),
        runtime_settings=runtime_settings,
        logs=LogService(tmp_path),
    )
    state = GameState(
        session_id="s_test",
        event_id="ming_bookshop_fire",
        dynasty_id="ming",
        player_role_id="role_ming_bookshop_apprentice",
        current_stage="investigation",
        current_scene_id="scene_engraving_room",
        discovered_clue_ids=["clue_burned_page"],
        completed_combo_ids=[],
        npc_trust={npc_id: npc.initial_trust for npc_id, npc in engine.npcs.items()},
        flags=[],
        scores=GameScores(),
        risk_level=0,
        available_scene_ids=["scene_engraving_room"],
        available_choice_ids=[],
        turn_count=0,
        status="active",
    )
    request = DialogueRequest(
        session_id="s_test",
        npc_id="npc_worker",
        message="你昨夜三更后到底听见了什么？",
        action_type="question",
        presented_clue_ids=[],
    )

    result = orchestrator.handle_dialogue(
        state=state,
        dynasty=engine.dynasties["ming"],
        player_role=engine.roles["role_ming_bookshop_apprentice"],
        current_scene=engine.scenes["scene_engraving_room"],
        npc=engine.npcs["npc_worker"],
        request=request,
        discovered_clues=[engine.clues["clue_burned_page"]],
        presented_clues=[],
        clue_map=engine.clues,
        mock_response=engine._fallback_response_for_npc("阿沈"),
        supervisor=engine.supervisor,
    )

    assert result is not None
    assert result.fallback_used is False
    assert result.supervisor_result.pass_ is True
    assert result.response.npc_dialogue
    assert result.response.npc_action
    assert result.response.emotion == "fearful"
    assert result.response.suggested_questions
    assert re.search(r"[\u4e00-\u9fff]", result.response.npc_dialogue)
    assert not re.search(r"[A-Za-z]{2,}", result.response.npc_dialogue)
    assert "幕后上级" not in result.response.npc_dialogue
    assert "结局" not in result.response.npc_dialogue
