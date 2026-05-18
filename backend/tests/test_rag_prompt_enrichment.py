from __future__ import annotations

from app.models.game_models import DialogueRequest, GameScores, GameState
from app.services.dialogue_orchestrator import DialogueOrchestrator
from app.services.game_engine import engine


def build_state() -> GameState:
    return GameState(
        session_id="s_prompt",
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


def build_prompt() -> str:
    orchestrator = DialogueOrchestrator()
    state = build_state()
    request = DialogueRequest(
        session_id="s_prompt",
        npc_id="npc_worker",
        message="你昨夜三更后到底听见了什么？",
        action_type="question",
        presented_clue_ids=[],
    )
    rag_hits = orchestrator.rag_retriever.retrieve(
        dynasty_id="ming",
        current_stage=state.current_stage,
        current_scene_id=state.current_scene_id,
        npc_id="npc_worker",
        player_message=request.message,
        discovered_clue_ids=state.discovered_clue_ids,
        top_k=8,
    )
    return orchestrator._build_prompt(
        state=state,
        dynasty=engine.dynasties["ming"],
        player_role=engine.roles["role_ming_bookshop_apprentice"],
        current_scene=engine.scenes["scene_engraving_room"],
        npc=engine.npcs["npc_worker"],
        request=request,
        discovered_clues=[engine.clues["clue_burned_page"]],
        presented_clues=[],
        clue_map=engine.clues,
        rag_hits=rag_hits,
    )


def test_prompt_contains_structured_rag_blocks() -> None:
    prompt = build_prompt()

    assert "【RAG 硬约束】" in prompt
    assert "【RAG 历史制度参考】" in prompt
    assert "【RAG 场景与器物细节】" in prompt
    assert "【RAG NPC 口吻参考】" in prompt
    assert "【RAG 禁止使用内容】" in prompt


def test_prompt_contains_hit_source_id_or_topic() -> None:
    prompt = build_prompt()

    assert "ming_worker_third_watch_001" in prompt
    assert "阿沈三更后证词边界" in prompt


def test_prompt_limits_rag_detail_absorption() -> None:
    prompt = build_prompt()

    assert "每次回复最多自然吸收 1～2 个 RAG 细节" in prompt
    assert "不要像百科一样讲制度或史料" in prompt


def test_prompt_declares_rag_does_not_control_game_state() -> None:
    prompt = build_prompt()

    assert "不要因为 RAG 自行释放线索" in prompt
    assert "不要因为 RAG 推进阶段" in prompt
    assert "决定 final_choice_id 或决定结局" in prompt
    assert "以后端规则为准" in prompt
