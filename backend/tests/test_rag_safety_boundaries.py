from __future__ import annotations

import json
from typing import Any

from app.core.config import Settings
from app.models.game_models import DialogueRequest, DialogueRuleResponse, GameScores, GameState
from app.services.ai_client import AIResponse
from app.services.dialogue_orchestrator import DialogueOrchestrator
from app.services.game_engine import engine
from app.services.log_service import LogService
from app.services.supervisor import SupervisorService


def runtime_settings() -> Settings:
    return Settings(
        app_name="测试",
        version="0.6.0",
        use_mock_ai=False,
        ai_provider="deepseek",
        backend_port=8000,
        frontend_port=5173,
        deepseek_base_url="https://example.invalid",
        deepseek_model="fake-rag-model",
        ai_timeout_seconds=1,
        ai_max_retries=0,
        deepseek_api_key="测试密钥占位",
    )


def build_state() -> GameState:
    return GameState(
        session_id="s_safety",
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


def ai_response(payload: dict[str, Any], *, success: bool = True) -> AIResponse:
    return AIResponse(
        success=success,
        parsed_json=payload if success else {},
        raw_text=json.dumps(payload, ensure_ascii=False),
        latency_ms=5,
        fallback_used=not success,
        error_message=None if success else "AI 返回格式无法解析，已回退到本地回复。",
        model="fake-rag-model",
    )


class StaticAIClient:
    def __init__(self, response: AIResponse) -> None:
        self.response = response
        self.last_prompt = ""

    def generate_json_sync(self, *, module: str, prompt: str, schema_hint: dict[str, Any]) -> AIResponse:
        self.last_prompt = prompt
        return self.response


class StaticRepairAgent:
    def __init__(self, response: AIResponse) -> None:
        self.response = response
        self.calls = 0
        self.last_prompt = "修复调用摘要"

    def repair_dialogue_json(self, **kwargs: Any) -> AIResponse:
        self.calls += 1
        return self.response


def valid_payload() -> dict[str, Any]:
    return {
        "npc_dialogue": "阿沈先看了一眼门口，低声说：刻版间旧墨味还没散，我只听见些脚步，不敢说死。",
        "npc_action": "他把沾着墨灰的袖口往身后收了收。",
        "emotion": "fearful",
        "released_clue_ids": [],
        "highlight_clues": [],
        "suggested_questions": ["你听见脚步从哪里来？", "你为何不敢说死？"],
        "state_update_suggestion": {
            "npc_trust_delta": 3,
            "truth_score_delta": 9,
            "order_score_delta": 9,
            "survival_score_delta": 9,
            "risk_level_delta": 9,
            "new_flags": ["rag_should_not_mutate_state"],
            "current_stage": "ending",
            "final_choice_id": "choice_reverse_trace",
        },
    }


def make_response(dialogue: str, *, action: str = "对方压低声音回应。", released: list[str] | None = None) -> DialogueRuleResponse:
    return DialogueRuleResponse(
        npc_dialogue=dialogue,
        npc_action=action,
        emotion="fearful",
        released_clue_ids=released or [],
        suggested_questions=["你还知道什么？"],
        trust_delta=0,
        score_delta={},
        risk_delta=0,
        add_flags=[],
    )


def call_orchestrator(payload: dict[str, Any], repair_payload: dict[str, Any], tmp_path):
    orchestrator = DialogueOrchestrator(
        ai_client=StaticAIClient(ai_response(payload)),
        runtime_settings=runtime_settings(),
        logs=LogService(tmp_path),
        repair_agent=StaticRepairAgent(ai_response(repair_payload)),
    )
    state = build_state()
    request = DialogueRequest(
        session_id="s_safety",
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
    return result, state


def test_rag_enriched_ai_response_does_not_mutate_game_state(tmp_path) -> None:
    state_before = build_state().model_dump()

    result, state_after = call_orchestrator(valid_payload(), valid_payload(), tmp_path)

    assert result is not None
    assert result.log_entry["rag_hit_count"] > 0
    assert result.log_entry["rag_source_ids"]
    assert result.log_entry["rag_material_types"]
    assert state_after.model_dump() == state_before


def test_supervisor_blocks_nonexistent_clue_id_from_rag_like_output() -> None:
    result = SupervisorService().review_dialogue(
        stage="investigation",
        dynasty=engine.dynasties["ming"],
        npc=engine.npcs["npc_worker"],
        response=make_response("阿沈说出了一条不该入库的资料。", released=["ming_space_engraving_room_001"]),
        clue_map=engine.clues,
        player_message="继续说。",
        player_role=engine.roles["role_ming_bookshop_apprentice"],
    )

    assert result.pass_ is False
    assert any(issue.type == "illegal_clue_release" for issue in result.issues)


def test_supervisor_blocks_clue_not_authorized_for_current_npc() -> None:
    result = SupervisorService().review_dialogue(
        stage="investigation",
        dynasty=engine.dynasties["ming"],
        npc=engine.npcs["npc_worker"],
        response=make_response("阿沈交出了封口令。", released=["clue_jinyiwei_gag_order"]),
        clue_map=engine.clues,
        player_message="继续说。",
        player_role=engine.roles["role_ming_bookshop_apprentice"],
    )

    assert result.pass_ is False
    assert any(issue.type == "illegal_clue_release" for issue in result.issues)


def test_supervisor_blocks_ai_attempt_to_enter_ending() -> None:
    result = SupervisorService().review_dialogue(
        stage="investigation",
        dynasty=engine.dynasties["ming"],
        npc=engine.npcs["npc_worker"],
        response=make_response("结局就是你已经查清一切，此案就此定局。"),
        clue_map=engine.clues,
        player_message="继续说。",
        player_role=engine.roles["role_ming_bookshop_apprentice"],
    )

    assert result.pass_ is False
    assert any(issue.type == "stage_jump" for issue in result.issues)


def test_supervisor_blocks_english_visible_text() -> None:
    result = SupervisorService().review_dialogue(
        stage="investigation",
        dynasty=engine.dynasties["ming"],
        npc=engine.npcs["npc_worker"],
        response=make_response("OK，我知道这个 clue。"),
        clue_map=engine.clues,
        player_message="继续说。",
        player_role=engine.roles["role_ming_bookshop_apprentice"],
    )

    assert result.pass_ is False
    assert any(issue.type == "non_chinese_visible_text" for issue in result.issues)


def test_failed_repair_uses_chinese_fallback(tmp_path) -> None:
    bad_payload = valid_payload() | {
        "npc_dialogue": "我用手机拍下完整真相，结局就是你已经通关。",
        "released_clue_ids": ["clue_jinyiwei_gag_order"],
    }

    result, state = call_orchestrator(bad_payload, bad_payload, tmp_path)

    assert result is not None
    assert result.fallback_used is True
    assert "手机" not in result.response.npc_dialogue
    assert result.response.released_clue_ids == []
    assert "clue_jinyiwei_gag_order" not in state.discovered_clue_ids
