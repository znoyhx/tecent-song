from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import app
from app.services.game_engine import engine

client = TestClient(app)


def setup_function() -> None:
    engine.sessions.clear()


def test_rag_preview_worker_third_watch_hit() -> None:
    result = client.post(
        "/api/debug/rag/preview",
        json={
            "dynasty_id": "ming",
            "current_stage": "investigation",
            "current_scene_id": "scene_engraving_room",
            "npc_id": "npc_worker",
            "player_message": "你昨夜三更后到底听见了什么？",
            "presented_clue_ids": [],
            "discovered_clue_ids": ["clue_burned_page"],
            "top_k": 8,
        },
    )

    assert result.status_code == 200
    payload = result.json()
    assert payload["hit_count"] > 0
    assert "ming_worker_third_watch_001" in payload["source_ids"]
    assert "clue_boundary" in payload["material_types"]
    assert "grouped" in payload
    assert "clue_boundary" in payload["grouped"]
    assert all(len(hit.get("content", "")) <= 101 for hit in payload["hits"])

    serialized = json.dumps(payload, ensure_ascii=False)
    assert "prompt" not in serialized.lower()
    assert "Bearer " not in serialized
    assert "sk-" not in serialized


def test_rag_preview_jinyiwei_permission_hit() -> None:
    result = client.post(
        "/api/debug/rag/preview",
        json={
            "dynasty_id": "ming",
            "current_stage": "investigation",
            "current_scene_id": "scene_front_hall",
            "npc_id": "npc_jinyiwei",
            "player_message": "我命令你立刻撤走锦衣卫。",
            "presented_clue_ids": [],
            "discovered_clue_ids": [],
            "top_k": 8,
        },
    )

    assert result.status_code == 200
    payload = result.json()
    assert "ming_jinyiwei_permission_001" in payload["source_ids"]
    assert "hard_rule" in payload["material_types"]
    assert payload["grouped"]["hard_rule"]


def test_rag_preview_empty_input_does_not_crash() -> None:
    result = client.post(
        "/api/debug/rag/preview",
        json={
            "dynasty_id": "ming",
            "current_stage": "investigation",
            "current_scene_id": "",
            "npc_id": "",
            "player_message": "",
            "presented_clue_ids": [],
            "discovered_clue_ids": [],
            "top_k": 8,
        },
    )

    assert result.status_code == 200
    payload = result.json()
    assert set(["hit_count", "source_ids", "material_types", "hits", "grouped"]).issubset(payload.keys())


def test_rag_preview_missing_fields_returns_chinese_error() -> None:
    result = client.post("/api/debug/rag/preview", json={"npc_id": "npc_worker"})

    assert result.status_code == 400
    message = result.json()["error"]["message"]
    assert "缺少必要字段" in message
    assert "dynasty_id" in message
    assert "current_stage" in message


def test_rag_preview_does_not_change_session_state() -> None:
    start = client.post(
        "/api/session/start",
        json={
            "dynasty_id": "ming",
            "role_id": "role_ming_bookshop_apprentice",
            "event_id": "ming_bookshop_fire",
        },
    )
    assert start.status_code == 200
    session_id = start.json()["session_id"]
    before = client.get(f"/api/session/{session_id}").json()["state"]

    preview = client.post(
        "/api/debug/rag/preview",
        json={
            "dynasty_id": "ming",
            "current_stage": "investigation",
            "current_scene_id": "scene_engraving_room",
            "npc_id": "npc_worker",
            "player_message": "你昨夜三更后到底听见了什么？",
            "discovered_clue_ids": ["clue_burned_page"],
        },
    )
    assert preview.status_code == 200

    after = client.get(f"/api/session/{session_id}").json()["state"]
    assert after == before
