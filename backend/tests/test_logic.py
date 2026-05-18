from __future__ import annotations

from app.models.game_models import DialogueRuleResponse, GameScores, GameState
from app.services.game_engine import engine
from app.services.supervisor import SupervisorService


def build_state() -> GameState:
    return GameState(
        session_id='s_test',
        event_id='ming_bookshop_fire',
        dynasty_id='ming',
        player_role_id='role_ming_bookshop_apprentice',
        current_stage='ending',
        current_scene_id='scene_front_hall',
        discovered_clue_ids=[],
        completed_combo_ids=[],
        npc_trust={
            'npc_owner': 0,
            'npc_worker': 0,
            'npc_scholar': 0,
            'npc_jinyiwei': 0,
        },
        flags=[],
        scores=GameScores(),
        risk_level=0,
        available_scene_ids=['scene_front_hall'],
        available_choice_ids=[],
        turn_count=0,
        status='ending_ready',
        final_choice_id=None,
    )


def test_all_five_endings_are_deterministic() -> None:
    survival = build_state()
    survival.scores.survival = 4
    survival.final_choice_id = 'choice_destroy_evidence'
    assert engine._pick_ending(survival).ending_id == 'ending_survival'

    order = build_state()
    order.scores.order = 4
    order.final_choice_id = 'choice_give_to_lu'
    assert engine._pick_ending(order).ending_id == 'ending_order'

    truth = build_state()
    truth.scores.truth = 5
    truth.flags = ['preserved_evidence']
    truth.final_choice_id = 'choice_help_scholar'
    assert engine._pick_ending(truth).ending_id == 'ending_truth'

    tragedy = build_state()
    tragedy.risk_level = 6
    tragedy.final_choice_id = 'choice_force_worker'
    assert engine._pick_ending(tragedy).ending_id == 'ending_tragedy'

    hidden = build_state()
    hidden.discovered_clue_ids = ['clue_poem_hidden_copy']
    hidden.flags = ['found_hidden_chain', 'preserved_evidence', 'ledger_truth_exposed', 'deduced_scholar_motive']
    hidden.npc_trust['npc_scholar'] = 2
    hidden.npc_trust['npc_jinyiwei'] = 2
    hidden.risk_level = 1
    hidden.final_choice_id = 'choice_reverse_trace'
    assert engine._pick_ending(hidden).ending_id == 'ending_hidden'


def test_supervisor_blocks_modern_term() -> None:
    supervisor = SupervisorService()
    dynasty = engine.dynasties['ming']
    npc = engine.npcs['npc_worker']
    response = DialogueRuleResponse(
        npc_dialogue='我昨夜还看见有人拿着手机照火场。',
        npc_action='阿沈说完便低下头。',
        emotion='fearful',
        released_clue_ids=['clue_worker_lie'],
        suggested_questions=[],
        trust_delta=0,
        score_delta={},
        risk_delta=0,
        add_flags=[],
    )

    result = supervisor.review_dialogue(
        stage='investigation',
        dynasty=dynasty,
        npc=npc,
        response=response,
        clue_map=engine.clues,
    )
    assert result.pass_ is False
    assert any(issue.type == 'modern_term' for issue in result.issues)

