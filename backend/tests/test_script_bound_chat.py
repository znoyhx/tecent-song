from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.models.game_models import DialogueRuleResponse
from app.services.ai_client import AIResponse
from app.services.dialogue_orchestrator import DialogueOrchestrator
from app.services.game_engine import engine
from app.services.log_service import LogService
from app.services.supervisor import SupervisorService


client = TestClient(app)


def setup_function() -> None:
    engine.sessions.clear()


def start_session_in_scene(*, stage: str = "investigation", scene_id: str = "scene_engraving_room") -> str:
    response = client.post(
        "/api/session/start",
        json={
            "dynasty_id": "ming",
            "role_id": "role_ming_bookshop_apprentice",
            "event_id": "ming_bookshop_fire",
        },
    )
    assert response.status_code == 200, response.text
    session_id = response.json()["session_id"]
    state = engine.sessions[session_id]["state"]
    state.current_stage = stage
    state.current_scene_id = scene_id
    engine._refresh_state_metadata(state)
    return session_id


def post_dialogue(session_id: str, npc_id: str, message: str, presented: list[str] | None = None):
    return client.post(
        "/api/dialogue",
        json={
            "session_id": session_id,
            "npc_id": npc_id,
            "message": message,
            "action_type": "present_clue" if presented else "question",
            "presented_clue_ids": presented or [],
        },
    )


def make_response(text: str, *, released: list[str] | None = None) -> DialogueRuleResponse:
    return DialogueRuleResponse(
        npc_dialogue=text,
        npc_action="对方低声回应。",
        emotion="fearful",
        released_clue_ids=released or [],
        suggested_questions=["你还知道什么？", "旧书箱是谁动过？", "后门泥痕说明什么？"],
    )


class GreetingAIClient:
    def __init__(self) -> None:
        self.last_prompt = ""

    def generate_json_sync(self, *, module: str, prompt: str, schema_hint: dict) -> AIResponse:
        self.last_prompt = prompt
        payload = {
            "npc_dialogue": "阿沈听见你的招呼，先怔了一下，随即压低声音：别在门口久站，昨夜旧书箱和后门泥痕才是要紧处。",
            "npc_action": "他朝门外飞快看了一眼，又把袖口往身后收。",
            "emotion": "fearful",
            "intent": "off_topic",
            "released_clue_ids": [],
            "highlight_clues": [],
            "red_texts": ["旧书箱", "后门泥痕"],
            "suggested_questions": ["昨夜旧书箱是谁动过？", "后门泥痕能说明什么？", "你袖口为什么有旧墨？"],
            "trust_delta": 0,
            "score_delta": {},
            "risk_delta": 0,
            "add_flags": [],
            "supervisor_notes": ["测试用真实 AI 链路替身。"],
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
            raw_text="{}",
            latency_ms=3,
            fallback_used=False,
            error_message=None,
            model="fake-deepseek",
        )


def test_smalltalk_hooks_back_to_main_case_without_long_chat() -> None:
    session_id = start_session_in_scene()

    response = post_dialogue(session_id, "npc_worker", "你喜欢吃什么？")

    assert response.status_code == 200, response.text
    payload = response.json()
    dialogue = payload["dialogue"]["npc_dialogue"]
    assert payload["dialogue"]["intent"] == "smalltalk"
    assert payload["new_clues"] == []
    assert len(re.findall(r"[。！？]", dialogue)) <= 2
    assert any(term in dialogue for term in ["旧书箱", "后门泥痕", "袖口"])


def test_natural_greeting_uses_ai_agent_when_real_mode_enabled(monkeypatch, tmp_path) -> None:
    fake_ai = GreetingAIClient()
    runtime_settings = Settings(
        app_name="测试",
        version="0.4.0",
        use_mock_ai=False,
        ai_provider="deepseek",
        backend_port=8000,
        frontend_port=5173,
        deepseek_base_url="https://example.invalid",
        deepseek_model="fake-deepseek",
        ai_timeout_seconds=1,
        ai_max_retries=0,
        deepseek_api_key="测试密钥占位",
    )
    monkeypatch.setattr(
        engine,
        "dialogue_orchestrator",
        DialogueOrchestrator(ai_client=fake_ai, runtime_settings=runtime_settings, logs=LogService(tmp_path)),
    )
    session_id = start_session_in_scene()

    response = post_dialogue(session_id, "npc_worker", "你好")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["fallback_used"] is False
    assert payload["dialogue"]["npc_dialogue"].startswith("阿沈听见你的招呼")
    assert "火既然已经扑灭" not in payload["dialogue"]["npc_dialogue"]
    assert "ScriptBoundChat" in fake_ai.last_prompt
    assert "RAG" in fake_ai.last_prompt
    assert engine.sessions[session_id]["logs"][-1].module == "NPCDialogueAgent"


def test_rule_matched_dialogue_still_uses_ai_agent_when_real_mode_enabled(monkeypatch, tmp_path) -> None:
    fake_ai = GreetingAIClient()
    runtime_settings = Settings(
        app_name="测试",
        version="0.4.0",
        use_mock_ai=False,
        ai_provider="deepseek",
        backend_port=8000,
        frontend_port=5173,
        deepseek_base_url="https://example.invalid",
        deepseek_model="fake-deepseek",
        ai_timeout_seconds=1,
        ai_max_retries=0,
        deepseek_api_key="测试密钥占位",
    )
    monkeypatch.setattr(
        engine,
        "dialogue_orchestrator",
        DialogueOrchestrator(ai_client=fake_ai, runtime_settings=runtime_settings, logs=LogService(tmp_path)),
    )
    session_id = start_session_in_scene()

    response = post_dialogue(session_id, "npc_worker", "你袖口的旧墨怎么回事？")

    assert response.status_code == 200, response.text
    assert "ScriptBoundChat" in fake_ai.last_prompt
    assert "RAG" in fake_ai.last_prompt
    assert engine.sessions[session_id]["logs"][-1].module == "NPCDialogueAgent"


def test_force_truth_does_not_reveal_final_truth_or_superior() -> None:
    session_id = start_session_in_scene()

    response = post_dialogue(session_id, "npc_worker", "真相是不是锦衣卫上级让你们烧的？")

    assert response.status_code == 200, response.text
    payload = response.json()
    dialogue = payload["dialogue"]["npc_dialogue"]
    assert payload["dialogue"]["intent"] == "force_truth"
    assert payload["new_clues"] == []
    assert "完整真相" not in dialogue
    assert "幕后上级" not in dialogue
    assert "锦衣卫上级" not in dialogue
    assert "主谋" not in dialogue


def test_ask_object_can_release_legal_clue_and_highlight_it() -> None:
    session_id = start_session_in_scene()

    response = post_dialogue(session_id, "npc_worker", "你袖口的旧墨怎么回事？")

    assert response.status_code == 200, response.text
    payload = response.json()
    new_clue_ids = {item["clue_id"] for item in payload["new_clues"]}
    assert payload["dialogue"]["intent"] == "ask_object"
    assert "clue_ink_on_sleeve" in new_clue_ids
    assert all(clue_id in engine.npcs["npc_worker"].releasable_clue_ids for clue_id in payload["dialogue"]["released_clue_ids"])
    assert payload["dialogue"]["highlight_clues"]


def test_required_clue_ids_gate_blocks_key_clue_release() -> None:
    session_id = start_session_in_scene(stage="reversal", scene_id="scene_rain_alley")
    session_state = engine.sessions[session_id]["state"]
    session_state.current_stage = "reversal"
    session_state.current_scene_id = "scene_rain_alley"
    session_state.discovered_clue_ids = []
    engine._refresh_state_metadata(session_state)

    context = engine.script_bound_chat.prepare_context(
        state=session_state,
        npc=engine.npcs["npc_scholar"],
        player_message="诗稿里夹带的抄录是什么？",
        clue_map=engine.clues,
        dialogue_turns=[],
    )
    bad_response = make_response("顾闻直接说出诗稿不是诗稿。", released=["clue_poem_hidden_copy"])
    supervisor = engine.supervisor.review_dialogue(
        stage="reversal",
        dynasty=engine.dynasties["ming"],
        npc=engine.npcs["npc_scholar"],
        response=bad_response,
        clue_map=engine.clues,
        player_message="诗稿里夹带的抄录是什么？",
        player_role=engine.roles["role_ming_bookshop_apprentice"],
        allowed_released_clue_ids=context.allowed_released_clue_ids,
        intent=context.intent,
        discovered_clue_ids=session_state.discovered_clue_ids,
    )

    assert "clue_poem_hidden_copy" not in context.allowed_released_clue_ids
    assert supervisor.pass_ is False
    assert any(issue.type == "illegal_clue_release" for issue in supervisor.issues)


def test_npc_cannot_release_clue_outside_own_releasable_ids() -> None:
    result = SupervisorService().review_dialogue(
        stage="investigation",
        dynasty=engine.dynasties["ming"],
        npc=engine.npcs["npc_worker"],
        response=make_response("我交出封口令。", released=["clue_jinyiwei_gag_order"]),
        clue_map=engine.clues,
        player_message="你有封口令吗？",
        player_role=engine.roles["role_ming_bookshop_apprentice"],
    )

    assert result.pass_ is False
    assert any(issue.type == "illegal_clue_release" for issue in result.issues)


@pytest.mark.parametrize(
    ("response", "expected_type"),
    [
        (make_response("我用手机拍下了残页。"), "modern_term"),
        (make_response("八旗兵封住了书坊。"), "wrong_dynasty"),
        (make_response("我交出不该有的线索。", released=["not_exists"]), "illegal_clue_release"),
        (make_response("王千户把铁令牌藏在地下密室。"), "fabricated_fact"),
    ],
)
def test_supervisor_blocks_modern_wrong_dynasty_illegal_clue_and_fabrication(
    response: DialogueRuleResponse,
    expected_type: str,
) -> None:
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


def test_suggested_questions_always_returns_three_chinese_questions() -> None:
    session_id = start_session_in_scene()

    response = post_dialogue(session_id, "npc_worker", "昨夜你为什么不在刻坊？")

    assert response.status_code == 200, response.text
    questions = response.json()["dialogue"]["suggested_questions"]
    assert len(questions) == 3
    assert all(re.search(r"[\u4e00-\u9fff]", item) for item in questions)
    assert all(item.endswith("？") for item in questions)


def test_frontend_types_accept_highlight_clues_and_red_texts() -> None:
    type_file = Path("frontend/src/types/game.ts").read_text(encoding="utf-8")

    assert "highlight_clues?: DialogueHighlight[]" in type_file
    assert "red_texts?: string[]" in type_file
    assert "export type DialogueHighlight" in type_file
