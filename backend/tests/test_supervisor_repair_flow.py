from __future__ import annotations

import json
from typing import Any

import pytest

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
        version="0.5.0",
        use_mock_ai=False,
        ai_provider="deepseek",
        backend_port=8000,
        frontend_port=5173,
        deepseek_base_url="https://example.invalid",
        deepseek_model="fake-flow-model",
        ai_timeout_seconds=1,
        ai_max_retries=0,
        deepseek_api_key="测试密钥占位",
    )


def build_state() -> GameState:
    return GameState(
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


def ai_response(payload: dict[str, Any], *, success: bool = True, raw_text: str | None = None) -> AIResponse:
    return AIResponse(
        success=success,
        parsed_json=payload if success else {},
        raw_text=raw_text if raw_text is not None else json.dumps(payload, ensure_ascii=False),
        latency_ms=7,
        fallback_used=not success,
        error_message=None if success else "AI 返回格式无法解析，已回退到本地回复。",
        model="fake-flow-model",
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


def valid_repair_payload() -> dict[str, Any]:
    return {
        "npc_dialogue": "阿沈把声音压得极低：我只听见后院有人提到旧箱，旁的我不敢乱说。",
        "npc_action": "他躲开门口的影子，把袖口往身后藏。",
        "emotion": "fearful",
        "released_clue_ids": [],
        "highlight_clues": [],
        "suggested_questions": ["你在怕谁？", "旧箱后来去了哪里？"],
        "state_update_suggestion": {
            "npc_trust_delta": 0,
            "truth_score_delta": 0,
            "order_score_delta": 0,
            "survival_score_delta": 0,
            "risk_level_delta": 0,
            "new_flags": [],
        },
    }


def call_orchestrator(ai_client: StaticAIClient, repair_agent: StaticRepairAgent, tmp_path) -> Any:
    orchestrator = DialogueOrchestrator(
        ai_client=ai_client,
        runtime_settings=runtime_settings(),
        logs=LogService(tmp_path),
        repair_agent=repair_agent,
    )
    state = build_state()
    request = DialogueRequest(
        session_id="s_test",
        npc_id="npc_worker",
        message="你昨夜三更后到底听见了什么？",
        action_type="question",
        presented_clue_ids=[],
    )
    return orchestrator.handle_dialogue(
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
    ), state, ai_client


def test_supervisor_failure_repairs_once_and_uses_repaired_response(tmp_path) -> None:
    bad_payload = valid_repair_payload() | {
        "npc_dialogue": "我用手机拍下了完整真相。",
        "released_clue_ids": ["clue_jinyiwei_gag_order"],
    }
    repair_agent = StaticRepairAgent(ai_response(valid_repair_payload()))

    result, state, ai_client = call_orchestrator(StaticAIClient(ai_response(bad_payload)), repair_agent, tmp_path)

    assert result is not None
    assert repair_agent.calls == 1
    assert result.fallback_used is False
    assert result.repair_attempted is True
    assert result.repair_success is True
    assert "手机" not in result.response.npc_dialogue
    assert result.response.released_clue_ids == []
    assert result.log_entry["rag_hit_count"] > 0
    assert "ming_worker_third_watch_001" in result.log_entry["rag_source_ids"]
    assert "clue_boundary" in result.log_entry["rag_material_types"]
    assert result.log_entry["repair_attempted"] is True
    assert "ming_worker_third_watch_001" in ai_client.last_prompt

    assert "clue_jinyiwei_gag_order" not in state.discovered_clue_ids


def test_repair_failure_falls_back_to_chinese_mock(tmp_path) -> None:
    bad_payload = valid_repair_payload() | {
        "npc_dialogue": "我用手机拍下了完整真相。",
        "released_clue_ids": ["clue_jinyiwei_gag_order"],
    }
    repair_agent = StaticRepairAgent(ai_response(bad_payload))

    result, state, _ = call_orchestrator(StaticAIClient(ai_response(bad_payload)), repair_agent, tmp_path)

    assert result is not None
    assert repair_agent.calls == 1
    assert result.fallback_used is True
    assert result.repair_success is False
    assert "手机" not in result.response.npc_dialogue
    assert result.response.released_clue_ids == []
    assert "clue_jinyiwei_gag_order" not in state.discovered_clue_ids


def test_missing_fields_trigger_repair(tmp_path) -> None:
    missing_payload = {
        "npc_dialogue": "阿沈说自己什么都不知道。",
        "emotion": "fearful",
    }
    repair_agent = StaticRepairAgent(ai_response(valid_repair_payload()))

    result, _, _ = call_orchestrator(StaticAIClient(ai_response(missing_payload)), repair_agent, tmp_path)

    assert result is not None
    assert repair_agent.calls == 1
    assert result.fallback_used is False
    assert result.repair_success is True


def make_response(dialogue: str, *, action: str = "对方低声回应。", released: list[str] | None = None) -> DialogueRuleResponse:
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


@pytest.mark.parametrize(
    ("response", "expected_type"),
    [
        (make_response("我昨夜看见有人拿着手机照火场。"), "modern_term"),
        (make_response("八旗兵已经封住书坊。"), "wrong_dynasty"),
        (make_response("完整真相是纵火主谋就是幕后上级。"), "spoiler"),
        (make_response("你已经通关，可以结案了。"), "stage_jump"),
        (make_response("OK，I know this clue。"), "non_chinese_visible_text"),
        (make_response("我给你一条不该有的线索。", released=["not_exists"]), "illegal_clue_release"),
        (make_response("我现在交出封口令。", released=["clue_jinyiwei_gag_order"]), "illegal_clue_release"),
    ],
)
def test_supervisor_blocks_required_rule_categories(response: DialogueRuleResponse, expected_type: str) -> None:
    result = SupervisorService().review_dialogue(
        stage="investigation",
        dynasty=engine.dynasties["ming"],
        npc=engine.npcs["npc_worker"],
        response=response,
        clue_map=engine.clues,
        player_message="继续说。",
        player_role=engine.roles["role_ming_bookshop_apprentice"],
    )

    assert result.pass_ is False
    assert any(issue.type == expected_type for issue in result.issues)


def test_supervisor_blocks_jinyiwei_command_obedience() -> None:
    result = SupervisorService().review_dialogue(
        stage="investigation",
        dynasty=engine.dynasties["ming"],
        npc=engine.npcs["npc_jinyiwei"],
        response=make_response("遵命，我这就撤走锦衣卫。"),
        clue_map=engine.clues,
        player_message="我命令你立刻撤走锦衣卫。",
        player_role=engine.roles["role_ming_bookshop_apprentice"],
    )

    assert result.pass_ is False
    assert any(issue.type == "role_permission" for issue in result.issues)


def test_supervisor_blocks_archive_permission_overreach() -> None:
    result = SupervisorService().review_dialogue(
        stage="investigation",
        dynasty=engine.dynasties["ming"],
        npc=engine.npcs["npc_owner"],
        response=make_response("可以调阅官府密档，我替你取来。"),
        clue_map=engine.clues,
        player_message="我要调阅官府密档。",
        player_role=engine.roles["role_ming_bookshop_apprentice"],
    )

    assert result.pass_ is False
    assert any(issue.type == "role_permission" for issue in result.issues)
