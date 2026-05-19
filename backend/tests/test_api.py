from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.game_engine import engine

client = TestClient(app)


def setup_function() -> None:
    engine.sessions.clear()


def start_demo_session() -> str:
    response = client.post(
        '/api/session/start',
        json={
            'dynasty_id': 'ming',
            'role_id': 'role_ming_bookshop_apprentice',
            'event_id': 'ming_bookshop_fire',
        },
    )
    assert response.status_code == 200, response.text
    return response.json()['session_id']


def test_catalog_and_health_endpoints() -> None:
    health = client.get('/api/health')
    assert health.status_code == 200
    assert health.json()['display_text'] == '服务运行中'

    dynasties = client.get('/api/dynasties')
    assert dynasties.status_code == 200
    assert dynasties.json()['dynasties'][0]['name'] == '明代'

    roles = client.get('/api/roles', params={'dynasty_id': 'ming'})
    assert roles.status_code == 200
    assert any(role['name'] == '书坊学徒' for role in roles.json()['roles'])


def test_cors_preflight_for_health_endpoint() -> None:
    response = client.options(
        '/api/health',
        headers={
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'content-type',
        },
    )
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'http://localhost:5173'
    assert 'content-type' in response.headers['access-control-allow-headers']





def test_full_demo_flow_to_truth_ending() -> None:
    start = client.post(
        '/api/session/start',
        json={
            'dynasty_id': 'ming',
            'role_id': 'role_ming_bookshop_apprentice',
            'event_id': 'ming_bookshop_fire',
        },
    )
    assert start.status_code == 200
    session = start.json()
    session_id = session['session_id']
    assert session['state']['current_stage'] == 'intro'
    assert session['scene']['name'] == '书坊前厅'

    owner_intro = client.post(
        '/api/dialogue',
        json={
            'session_id': session_id,
            'npc_id': 'npc_owner',
            'message': '昨夜第一眼看见什么？',
            'action_type': 'question',
            'presented_clue_ids': [],
        },
    )
    assert owner_intro.status_code == 200
    assert any(clue['clue_id'] == 'clue_missing_manuscript_list' for clue in owner_intro.json()['new_clues'])

    burned_page = client.post(
        '/api/investigate',
        json={
            'session_id': session_id,
            'scene_id': 'scene_fire_yard',
            'hotspot_id': 'ash_pile',
        },
    )
    assert burned_page.status_code == 200
    assert any(clue['clue_id'] == 'clue_burned_page' for clue in burned_page.json()['new_clues'])

    enter_engraving = client.post(
        '/api/investigate',
        json={'session_id': session_id, 'scene_id': 'scene_engraving_room'},
    )
    assert enter_engraving.status_code == 200

    worker_default = client.post(
        '/api/dialogue',
        json={
            'session_id': session_id,
            'npc_id': 'npc_worker',
            'message': '你昨夜一直在刻坊吗？',
            'action_type': 'question',
            'presented_clue_ids': [],
        },
    )
    assert worker_default.status_code == 200
    worker_clues = {item['clue_id'] for item in worker_default.json()['new_clues']}
    assert {'clue_worker_lie', 'clue_ink_on_sleeve'}.issubset(worker_clues)

    worker_present = client.post(
        '/api/dialogue',
        json={
            'session_id': session_id,
            'npc_id': 'npc_worker',
            'message': '你这话前后对不上。',
            'action_type': 'question',
            'presented_clue_ids': ['clue_worker_lie'],
        },
    )
    assert worker_present.status_code == 200
    assert any(clue['clue_id'] == 'clue_box_before_dawn' for clue in worker_present.json()['new_clues'])

    red_seal = client.post(
        '/api/investigate',
        json={
            'session_id': session_id,
            'scene_id': 'scene_front_hall',
            'hotspot_id': 'old_box',
        },
    )
    assert red_seal.status_code == 200
    assert any(clue['clue_id'] == 'clue_red_seal' for clue in red_seal.json()['new_clues'])

    rain_alley = client.post(
        '/api/investigate',
        json={'session_id': session_id, 'scene_id': 'scene_rain_alley'},
    )
    assert rain_alley.status_code == 200

    scholar_default = client.post(
        '/api/dialogue',
        json={
            'session_id': session_id,
            'npc_id': 'npc_scholar',
            'message': '你回书坊究竟是为了什么？',
            'action_type': 'question',
            'presented_clue_ids': [],
        },
    )
    assert scholar_default.status_code == 200
    assert any(clue['clue_id'] == 'clue_scholar_searches_manuscript' for clue in scholar_default.json()['new_clues'])

    scholar_present = client.post(
        '/api/dialogue',
        json={
            'session_id': session_id,
            'npc_id': 'npc_scholar',
            'message': '这张残页你总该认识。',
            'action_type': 'question',
            'presented_clue_ids': ['clue_burned_page'],
        },
    )
    assert scholar_present.status_code == 200
    assert any(clue['clue_id'] == 'clue_poem_hidden_copy' for clue in scholar_present.json()['new_clues'])

    city_notice_seed = client.post(
        '/api/investigate',
        json={'session_id': session_id, 'scene_id': 'scene_rain_alley', 'hotspot_id': 'search_notice'},
    )
    assert city_notice_seed.status_code == 200

    second_notice = client.post(
        '/api/investigate',
        json={'session_id': session_id, 'scene_id': 'scene_city_gate', 'hotspot_id': 'second_notice'},
    )
    assert second_notice.status_code == 200

    sealed_desk = client.post(
        '/api/investigate',
        json={'session_id': session_id, 'scene_id': 'scene_interrogation_room', 'hotspot_id': 'sealed_desk'},
    )
    assert sealed_desk.status_code == 200

    temp_record = client.post(
        '/api/investigate',
        json={'session_id': session_id, 'scene_id': 'scene_interrogation_room', 'hotspot_id': 'temp_record'},
    )
    assert temp_record.status_code == 200

    session_after_reversal = client.get(f'/api/session/{session_id}')
    assert session_after_reversal.status_code == 200
    assert session_after_reversal.json()['state']['current_stage'] == 'choice'

    interrogation = client.post(
        '/api/investigate',
        json={'session_id': session_id, 'scene_id': 'scene_interrogation_room'},
    )
    assert interrogation.status_code == 200

    lu_default = client.post(
        '/api/dialogue',
        json={
            'session_id': session_id,
            'npc_id': 'npc_jinyiwei',
            'message': '你为何只盯着残页？',
            'action_type': 'question',
            'presented_clue_ids': [],
        },
    )
    assert lu_default.status_code == 200

    choose = client.post(
        '/api/choice',
        json={'session_id': session_id, 'choice_id': 'choice_help_scholar'},
    )
    assert choose.status_code == 200
    assert choose.json()['state']['current_stage'] == 'ending'

    ending = client.post('/api/ending/resolve', json={'session_id': session_id})
    assert ending.status_code == 200
    assert ending.json()['title'] == '暗藏残页'
    assert '历史回声' not in ending.json()['summary']


def test_visual_status_and_fallback_asset_endpoints() -> None:
    status = client.get('/api/visual/status')
    assert status.status_code == 200
    payload = status.json()
    assert payload['provider'] == 'siliconflow'
    assert any(asset['asset_id'] == 'scene_bookshop_front_hall' for asset in payload['assets'])

    fallback = client.get('/api/visual/assets/scene_bookshop_front_hall')
    assert fallback.status_code == 200
    assert 'image/svg+xml' in fallback.headers['content-type'] or fallback.headers['content-type'] == 'image/png'

    generate_unknown = client.post('/api/visual/generate', json={'asset_id': 'not_exists'})
    assert generate_unknown.status_code == 404


def test_npc_identity_profile_fields_are_player_facing() -> None:
    for npc in engine.npcs.values():
        assert npc.public_identity
        assert npc.appearance
        assert npc.personality
        assert npc.background_suspicion
        assert npc.case_connection
        assert npc.event_behavior
        assert npc.profile_progression


def test_initial_owner_profile_does_not_spoil_undiscovered_clues() -> None:
    start = client.post(
        "/api/session/start",
        json={
            "dynasty_id": "ming",
            "role_id": "role_ming_bookshop_apprentice",
            "event_id": "ming_bookshop_fire",
        },
    )
    assert start.status_code == 200
    owner = next(item for item in start.json()["scene_npcs"] if item["npc_id"] == "npc_owner")
    visible_text = "".join([
        owner["background_suspicion"],
        owner["event_behavior"],
        owner["case_connection"],
    ])
    assert "提前挪动旧书箱" not in visible_text
    assert "被刮去的账目" not in visible_text
    assert "不能留到天亮" not in visible_text
    assert "红印纸角" not in visible_text
    assert owner["profile_progression"]["background_suspicion"]


def test_cannot_present_undiscovered_clue() -> None:

    start = client.post(
        '/api/session/start',
        json={
            'dynasty_id': 'ming',
            'role_id': 'role_ming_bookshop_apprentice',
            'event_id': 'ming_bookshop_fire',
        },
    )
    session_id = start.json()['session_id']

    result = client.post(
        '/api/dialogue',
        json={
            'session_id': session_id,
            'npc_id': 'npc_owner',
            'message': '我有证据。',
            'action_type': 'question',
            'presented_clue_ids': ['clue_burned_page'],
        },
    )
    assert result.status_code == 400
    assert result.json()['error']['code'] == 'CLUE_NOT_DISCOVERED'


def test_presenting_key_clues_has_visible_dialogue_and_state_effects() -> None:
    session_id = start_demo_session()
    state = engine.sessions[session_id]["state"]

    state.current_stage = "investigation"
    state.current_scene_id = "scene_front_hall"
    state.discovered_clue_ids = ["clue_fire_origin_wrong"]
    engine._refresh_state_metadata(state)
    before_truth = state.scores.truth
    owner = client.post(
        "/api/dialogue",
        json={
            "session_id": session_id,
            "npc_id": "npc_owner",
            "message": "焦痕不在灯油架旁。",
            "action_type": "present_clue",
            "presented_clue_ids": ["clue_fire_origin_wrong"],
        },
    )
    assert owner.status_code == 200, owner.text
    owner_payload = owner.json()
    assert "焦痕" in owner_payload["dialogue"]["npc_dialogue"]
    assert owner_payload["state"]["scores"]["truth"] > before_truth
    assert "owner_fire_claim_cracked" in owner_payload["state"]["flags"]

    state.current_stage = "investigation"
    state.current_scene_id = "scene_engraving_room"
    state.discovered_clue_ids = ["clue_backdoor_latch"]
    state.npc_trust["npc_worker"] = 0
    state.flags = []
    state.scores.truth = 0
    engine._refresh_state_metadata(state)
    worker = client.post(
        "/api/dialogue",
        json={
            "session_id": session_id,
            "npc_id": "npc_worker",
            "message": "后门门闩昨夜松过。",
            "action_type": "present_clue",
            "presented_clue_ids": ["clue_backdoor_latch"],
        },
    )
    assert worker.status_code == 200, worker.text
    worker_payload = worker.json()
    assert "门闩" in worker_payload["dialogue"]["npc_dialogue"]
    assert worker_payload["state"]["npc_trust"]["npc_worker"] == 1
    assert any(clue["clue_id"] == "clue_box_before_dawn" for clue in worker_payload["new_clues"])

    state.current_stage = "reversal"
    state.current_scene_id = "scene_rain_alley"
    state.discovered_clue_ids = ["clue_burned_page", "clue_hidden_page_thread", "clue_scholar_outer_wrapper"]
    state.npc_trust["npc_scholar"] = 0
    state.flags = []
    state.scores.truth = 0
    engine._refresh_state_metadata(state)
    scholar = client.post(
        "/api/dialogue",
        json={
            "session_id": session_id,
            "npc_id": "npc_scholar",
            "message": "诗稿外皮能证明你不是为纵火回来。",
            "action_type": "present_clue",
            "presented_clue_ids": ["clue_scholar_outer_wrapper"],
        },
    )
    assert scholar.status_code == 200, scholar.text
    scholar_payload = scholar.json()
    assert "外皮" in scholar_payload["dialogue"]["npc_dialogue"]
    assert scholar_payload["state"]["npc_trust"]["npc_scholar"] == 1
    assert "scholar_motive_visible" in scholar_payload["state"]["flags"]
    assert "deduced_scholar_motive" not in scholar_payload["state"]["flags"]
    assert any(clue["clue_id"] == "clue_poem_hidden_copy" for clue in scholar_payload["new_clues"])


def test_presenting_lu_seal_chain_clues_pushes_order_investigation() -> None:
    cases = [
        ("clue_jinyiwei_gag_order", ["clue_red_seal", "clue_jinyiwei_gag_order"], "clue_lu_order_conflict"),
        ("clue_lu_order_conflict", ["clue_jinyiwei_gag_order", "clue_lu_order_conflict"], "clue_lu_search_list"),
        ("clue_temp_interrogation_record", ["clue_jinyiwei_gag_order", "clue_temp_interrogation_record"], "clue_gag_order_wording"),
    ]

    for presented_clue_id, discovered_clue_ids, expected_release in cases:
        session_id = start_demo_session()
        state = engine.sessions[session_id]["state"]
        state.current_stage = "reversal"
        state.current_scene_id = "scene_interrogation_room"
        state.discovered_clue_ids = discovered_clue_ids
        state.npc_trust["npc_jinyiwei"] = 0
        state.flags = []
        state.scores.truth = 0
        state.scores.order = 0
        state.risk_level = 0
        engine._refresh_state_metadata(state)

        result = client.post(
            "/api/dialogue",
            json={
                "session_id": session_id,
                "npc_id": "npc_jinyiwei",
                "message": "这条封口链路对不上。",
                "action_type": "present_clue",
                "presented_clue_ids": [presented_clue_id],
            },
        )
        assert result.status_code == 200, result.text
        payload = result.json()
        assert payload["state"]["npc_trust"]["npc_jinyiwei"] >= 1
        assert any(clue["clue_id"] == expected_release for clue in payload["new_clues"])
        assert payload["dialogue"]["npc_dialogue"] != "陆峥沉默了片刻，只说现在还不能把话说得太满。"
