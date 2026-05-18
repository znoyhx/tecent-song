from __future__ import annotations

import re

import pytest

from app.core.config import load_settings
from app.models.game_models import DialogueRequest, GameScores, GameState
from app.services.dialogue_orchestrator import DialogueOrchestrator
from app.services.game_engine import engine
from app.services.log_service import LogService


def build_state(*, scene_id: str, discovered_clue_ids: list[str] | None = None) -> GameState:
    return GameState(
        session_id="s_real_rag_smoke",
        event_id="ming_bookshop_fire",
        dynasty_id="ming",
        player_role_id="role_ming_bookshop_apprentice",
        current_stage="investigation",
        current_scene_id=scene_id,
        discovered_clue_ids=discovered_clue_ids or [],
        completed_combo_ids=[],
        npc_trust={npc_id: npc.initial_trust for npc_id, npc in engine.npcs.items()},
        flags=[],
        scores=GameScores(),
        risk_level=0,
        available_scene_ids=[scene_id],
        available_choice_ids=[],
        turn_count=0,
        status="active",
    )


def assert_safe_visible_chinese(text: str) -> None:
    assert re.search(r"[\u4e00-\u9fff]", text)
    assert re.search(r"[A-Za-z]{2,}", text) is None
    forbidden_terms = {
        "手机",
        "互联网",
        "电话",
        "电灯",
        "汽车",
        "枪",
        "现代警察",
        "公司",
        "电脑",
        "幕后上级",
        "完整真相",
        "纵火主谋",
        "你已经通关",
        "进入结局",
        "调阅官府密档",
    }
    assert not any(term in text for term in forbidden_terms)


def test_real_ai_rag_enrichment_smoke_for_worker_and_jinyiwei(tmp_path) -> None:
    runtime_settings = load_settings()
    if runtime_settings.use_mock_ai or runtime_settings.ai_provider != "deepseek":
        pytest.skip("真实 AI 模式未开启：请设置 USE_MOCK_AI=false 且 AI_PROVIDER=deepseek 后再运行。")
    if not runtime_settings.deepseek_api_key_available:
        pytest.skip("未检测到 DeepSeek Key：请在安全环境变量或本机后端配置中补齐后再运行。")

    orchestrator = DialogueOrchestrator(runtime_settings=runtime_settings, logs=LogService(tmp_path))

    worker_state = build_state(scene_id="scene_engraving_room", discovered_clue_ids=["clue_burned_page"])
    worker_request = DialogueRequest(
        session_id=worker_state.session_id,
        npc_id="npc_worker",
        message="你昨夜三更后到底听见了什么？",
        action_type="question",
        presented_clue_ids=[],
    )
    worker_result = orchestrator.handle_dialogue(
        state=worker_state,
        dynasty=engine.dynasties["ming"],
        player_role=engine.roles["role_ming_bookshop_apprentice"],
        current_scene=engine.scenes["scene_engraving_room"],
        npc=engine.npcs["npc_worker"],
        request=worker_request,
        discovered_clues=[engine.clues["clue_burned_page"]],
        presented_clues=[],
        clue_map=engine.clues,
        mock_response=engine._fallback_response_for_npc("阿沈"),
        supervisor=engine.supervisor,
    )

    assert worker_result is not None
    assert worker_result.log_entry is not None
    assert worker_result.log_entry["ai_mode"] == "real"
    assert worker_result.log_entry["rag_hit_count"] > 0
    assert worker_result.response.released_clue_ids == [] or set(worker_result.response.released_clue_ids).issubset(
        set(engine.npcs["npc_worker"].releasable_clue_ids)
    )
    assert_safe_visible_chinese(worker_result.response.npc_dialogue)
    assert_safe_visible_chinese(worker_result.response.npc_action)

    jinyiwei_state = build_state(scene_id="scene_front_hall")
    jinyiwei_request = DialogueRequest(
        session_id=jinyiwei_state.session_id,
        npc_id="npc_jinyiwei",
        message="我命令你立刻撤走锦衣卫。",
        action_type="question",
        presented_clue_ids=[],
    )
    jinyiwei_result = orchestrator.handle_dialogue(
        state=jinyiwei_state,
        dynasty=engine.dynasties["ming"],
        player_role=engine.roles["role_ming_bookshop_apprentice"],
        current_scene=engine.scenes["scene_front_hall"],
        npc=engine.npcs["npc_jinyiwei"],
        request=jinyiwei_request,
        discovered_clues=[],
        presented_clues=[],
        clue_map=engine.clues,
        mock_response=engine._fallback_response_for_npc("陆峥"),
        supervisor=engine.supervisor,
    )

    assert jinyiwei_result is not None
    assert jinyiwei_result.log_entry is not None
    assert jinyiwei_result.log_entry["ai_mode"] == "real"
    assert jinyiwei_result.log_entry["rag_hit_count"] > 0
    assert "遵命" not in jinyiwei_result.response.npc_dialogue
    assert_safe_visible_chinese(jinyiwei_result.response.npc_dialogue)
    assert_safe_visible_chinese(jinyiwei_result.response.npc_action)

    owner_state = build_state(scene_id="scene_front_hall", discovered_clue_ids=["clue_burned_page"])
    owner_request = DialogueRequest(
        session_id=owner_state.session_id,
        npc_id="npc_owner",
        message="这场火真只是灯油走水吗？",
        action_type="question",
        presented_clue_ids=[],
    )
    owner_result = orchestrator.handle_dialogue(
        state=owner_state,
        dynasty=engine.dynasties["ming"],
        player_role=engine.roles["role_ming_bookshop_apprentice"],
        current_scene=engine.scenes["scene_front_hall"],
        npc=engine.npcs["npc_owner"],
        request=owner_request,
        discovered_clues=[engine.clues["clue_burned_page"]],
        presented_clues=[],
        clue_map=engine.clues,
        mock_response=engine._fallback_response_for_npc("许掌柜"),
        supervisor=engine.supervisor,
    )

    assert owner_result is not None
    assert owner_result.log_entry is not None
    assert owner_result.log_entry["ai_mode"] == "real"
    assert owner_result.log_entry["rag_hit_count"] > 0
    assert set(owner_result.response.released_clue_ids).issubset(set(engine.npcs["npc_owner"].releasable_clue_ids))
    assert_safe_visible_chinese(owner_result.response.npc_dialogue)
    assert_safe_visible_chinese(owner_result.response.npc_action)

