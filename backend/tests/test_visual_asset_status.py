from __future__ import annotations

import json
import re

from fastapi.testclient import TestClient

from app.main import app
from app.services.game_engine import engine

client = TestClient(app)

REQUIRED_ASSET_IDS = {
    "scene_bookshop_front_hall",
    "scene_bookshop_fire_yard",
    "scene_account_room",
    "scene_lamp_shelf",
    "scene_bookshop_engraving_room",
    "scene_back_gate",
    "scene_rain_alley",
    "scene_city_gate",
    "scene_interrogation_room",
    "npc_owner_xu",
    "npc_worker_ashen",
    "npc_jinyiwei_lu",
    "clue_burned_page",
    "clue_red_seal",
    "clue_jinyiwei_gag_order",
}

REQUIRED_SCENE_IDS = {
    "scene_front_hall": "scene_bookshop_front_hall",
    "scene_fire_yard": "scene_bookshop_fire_yard",
    "scene_account_room": "scene_account_room",
    "scene_lamp_shelf": "scene_lamp_shelf",
    "scene_engraving_room": "scene_bookshop_engraving_room",
    "scene_back_gate": "scene_back_gate",
    "scene_rain_alley": "scene_rain_alley",
    "scene_city_gate": "scene_city_gate",
    "scene_interrogation_room": "scene_interrogation_room",
}


def setup_function() -> None:
    engine.sessions.clear()


def test_visual_status_returns_stage8_asset_manifest_without_secrets() -> None:
    response = client.get("/api/visual/status")
    assert response.status_code == 200
    payload = response.json()
    assets = {asset["asset_id"]: asset for asset in payload["assets"]}

    assert payload["provider"] == "siliconflow"
    assert REQUIRED_ASSET_IDS.issubset(assets.keys())
    assert payload["asset_count"] >= len(REQUIRED_ASSET_IDS)

    for asset_id in REQUIRED_ASSET_IDS:
        asset = assets[asset_id]
        assert asset["asset_type"] in {"scene_background", "npc_portrait", "clue_item"}
        assert re.search(r"[\u4e00-\u9fff]", asset["display_name"])
        assert re.search(r"[\u4e00-\u9fff]", asset["description"])
        assert asset["fallback_path"].startswith("/api/visual/assets/")
        assert asset["status"] in {"generated", "fallback"}

    serialized = json.dumps(payload, ensure_ascii=False)
    assert "Authorization" not in serialized
    assert "Bearer " not in serialized
    assert not re.search(r"sk-[A-Za-z0-9_\-]{8,}", serialized)


def test_session_snapshot_contains_visual_asset_urls() -> None:
    response = client.post(
        "/api/session/start",
        json={
            "dynasty_id": "ming",
            "role_id": "role_ming_bookshop_apprentice",
            "event_id": "ming_bookshop_fire",
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["scene"]["visual_asset_id"] == "scene_bookshop_front_hall"
    assert payload["scene"]["visual_asset_url"].startswith("/api/visual/assets/")
    assert payload["scene"]["visual_status"] in {"generated", "fallback"}
    assert payload["available_scenes"][0]["visual_asset_url"].startswith("/api/visual/assets/")
    assert payload["scene_npcs"][0]["visual_asset_url"].startswith("/api/visual/assets/")


def test_all_ming_bookshop_scenes_have_visual_asset_routes() -> None:
    response = client.post(
        "/api/session/start",
        json={
            "dynasty_id": "ming",
            "role_id": "role_ming_bookshop_apprentice",
            "event_id": "ming_bookshop_fire",
        },
    )
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    state = engine.sessions[session_id]["state"]
    state.current_stage = "reversal"
    engine._refresh_state_metadata(state)

    snapshot = client.get(f"/api/session/{session_id}")
    assert snapshot.status_code == 200
    scenes = {scene["scene_id"]: scene for scene in snapshot.json()["available_scenes"]}

    assert set(REQUIRED_SCENE_IDS).issubset(scenes.keys())
    for scene_id, asset_id in REQUIRED_SCENE_IDS.items():
        scene = scenes[scene_id]
        assert scene["visual_asset_id"] == asset_id
        assert scene["visual_asset_url"] == f"/api/visual/assets/{asset_id}"
        assert scene["visual_status"] in {"generated", "fallback"}
        asset_response = client.get(scene["visual_asset_url"])
        assert asset_response.status_code == 200
        assert "image/png" in asset_response.headers["content-type"] or "image/svg+xml" in asset_response.headers["content-type"]


def test_key_clue_assets_use_specific_local_art() -> None:
    for asset_id in {"clue_burned_page", "clue_red_seal", "clue_jinyiwei_gag_order"}:
        status_response = client.get("/api/visual/status")
        asset = next(item for item in status_response.json()["assets"] if item["asset_id"] == asset_id)
        assert asset["status"] == "generated"
        assert asset["generated_path"]

        response = client.get(f"/api/visual/assets/{asset_id}")
        assert response.status_code == 200
        assert "image/svg+xml" in response.headers["content-type"] or "image/png" in response.headers["content-type"]
        if "image/svg+xml" in response.headers["content-type"]:
            assert "史隙视觉占位" not in response.text
            assert "占位图" not in response.text
