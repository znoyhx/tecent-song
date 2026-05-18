from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from app.services.game_engine import engine

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "backend" / "data"
SECRET_PATTERN = re.compile(r"Bearer\s+|Authorization|sk-[A-Za-z0-9_\-]{8,}")
ENGLISH_UI_PATTERN = re.compile(r"\b(Start|Loading|Error|Submit|Continue|Inventory|Clue|Session|Choice|Ending|Back|Next)\b")
client = TestClient(app)


def setup_function() -> None:
    engine.sessions.clear()


def load_json(relative_path: str) -> dict[str, Any]:
    return json.loads((DATA / relative_path).read_text(encoding="utf-8"))


def has_chinese(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def test_stage_11_volume_targets_are_met() -> None:
    event = load_json("events/ming_bookshop_fire.json")
    scenes = load_json("scenes/ming_bookshop_scenes.json")["scenes"]
    clues = load_json("clues/ming_bookshop_clues.json")["clues"]
    dialogues = [json.loads(path.read_text(encoding="utf-8")) for path in (DATA / "mock" / "dialogues").glob("*.json")]
    endings = load_json("endings/ming_bookshop_endings.json")["endings"]

    hotspot_count = sum(len(scene.get("hotspots", [])) for scene in scenes)
    highlight_count = sum(len(scene.get("highlights", [])) for scene in scenes)
    evidence_reactions = sum(
        1
        for payload in dialogues
        for rule in payload["rules"]
        if rule.get("trigger", {}).get("presented_clue_ids")
    )

    assert 8 <= len(scenes) <= 10
    assert 24 <= hotspot_count <= 36
    assert 30 <= len(clues) <= 45
    assert sum(1 for clue in clues if clue.get("red_highlight")) >= 18
    assert highlight_count >= 18
    assert all(6 <= len(payload["rules"]) <= 10 for payload in dialogues)
    assert 12 <= evidence_reactions <= 18
    assert 6 <= len(event.get("combos", [])) <= 10
    assert 8 <= len(event.get("deductions", [])) <= 12
    assert 12 <= len(event.get("chapter_sections", [])) <= 18
    assert len(endings) == 5


def test_stage_11_references_and_hotspot_responses_are_valid() -> None:
    event = load_json("events/ming_bookshop_fire.json")
    scenes = load_json("scenes/ming_bookshop_scenes.json")["scenes"]
    clues = load_json("clues/ming_bookshop_clues.json")["clues"]
    npcs = load_json("npcs/ming_bookshop_npcs.json")["npcs"]
    responses = load_json("mock/scene_responses.json")["responses"]
    endings = load_json("endings/ming_bookshop_endings.json")["endings"]

    scene_ids = {scene["scene_id"] for scene in scenes}
    clue_ids = {clue["clue_id"] for clue in clues}
    npc_ids = {npc["npc_id"] for npc in npcs}
    choice_ids = {choice["choice_id"] for choice in event["choices"]}
    ending_ids = {ending["ending_id"] for ending in endings}

    assert set(event["scene_ids"]).issubset(scene_ids)
    assert set(event["npc_ids"]).issubset(npc_ids)
    assert set(event["required_clue_ids"]).issubset(clue_ids)
    assert set(event["ending_rule_ids"]).issubset(ending_ids)

    scene_hotspot_keys: set[str] = set()
    for scene in scenes:
        assert set(scene.get("npc_ids", [])).issubset(npc_ids)
        for hotspot in scene.get("hotspots", []):
            key = f"{scene['scene_id']}:{hotspot['hotspot_id']}"
            scene_hotspot_keys.add(key)
            assert key in responses
            assert set(hotspot.get("clue_ids", [])).issubset(clue_ids)
            assert set(hotspot.get("required_clue_ids", [])).issubset(clue_ids)
        for highlight in scene.get("highlights", []):
            if highlight.get("clue_id"):
                assert highlight["clue_id"] in clue_ids

    assert set(responses).issubset(scene_hotspot_keys)
    for response in responses.values():
        assert set(response.get("clue_ids", [])).issubset(clue_ids)

    for clue in clues:
        if clue.get("source_scene_id"):
            assert clue["source_scene_id"] in scene_ids
        if clue.get("source_npc_id"):
            assert clue["source_npc_id"] in npc_ids
        assert set(clue.get("related_clue_ids", [])).issubset(clue_ids)

    for combo in event["combos"]:
        assert set(combo["required_clue_ids"]).issubset(clue_ids)
    for deduction in event["deductions"]:
        assert set(deduction["required_clue_ids"]).issubset(clue_ids)
        assert set(deduction["correct_clue_ids"]).issubset(clue_ids)
    for section in event["chapter_sections"]:
        assert section["scene_id"] in scene_ids
        assert set(section.get("npc_ids", [])).issubset(npc_ids)
        assert set(section.get("clue_ids", [])).issubset(clue_ids)
    for ending in endings:
        assert set(ending.get("related_clue_ids", [])).issubset(clue_ids)
        assert set(ending.get("related_choice_ids", [])).issubset(choice_ids)


def test_stage_11_user_visible_text_is_chinese_and_has_no_secret() -> None:
    checked_files = [
        DATA / "events" / "ming_bookshop_fire.json",
        DATA / "scenes" / "ming_bookshop_scenes.json",
        DATA / "clues" / "ming_bookshop_clues.json",
        DATA / "npcs" / "ming_bookshop_npcs.json",
        DATA / "mock" / "scene_responses.json",
        DATA / "mock" / "history_echoes.json",
        DATA / "endings" / "ming_bookshop_endings.json",
        *list((DATA / "mock" / "dialogues").glob("*.json")),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in checked_files)
    assert SECRET_PATTERN.search(combined) is None
    assert ENGLISH_UI_PATTERN.search(combined) is None

    for path in checked_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        serialized = json.dumps(payload, ensure_ascii=False)
        assert has_chinese(serialized), path


def post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post(path, json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def start_session() -> str:
    payload = post_json(
        "/api/session/start",
        {"dynasty_id": "ming", "role_id": "role_ming_bookshop_apprentice", "event_id": "ming_bookshop_fire"},
    )
    assert payload["state"]["current_stage"] == "intro"
    return payload["session_id"]


def investigate(session_id: str, scene_id: str, hotspot_id: str) -> dict[str, Any]:
    return post_json("/api/investigate", {"session_id": session_id, "scene_id": scene_id, "hotspot_id": hotspot_id})


def dialogue(session_id: str, npc_id: str, message: str, clues: list[str] | None = None) -> dict[str, Any]:
    return post_json(
        "/api/dialogue",
        {"session_id": session_id, "npc_id": npc_id, "message": message, "action_type": "question", "presented_clue_ids": clues or []},
    )


def test_stage_11_api_route_covers_investigation_dialogue_deduction_and_hidden_ending() -> None:
    session_id = start_session()

    investigation_steps = [
        ("scene_front_hall", "ledger_desk"),
        ("scene_front_hall", "old_box"),
        ("scene_front_hall", "apprentice_watch"),
        ("scene_fire_yard", "ash_pile"),
        ("scene_fire_yard", "char_mark"),
        ("scene_fire_yard", "fire_bucket"),
        ("scene_lamp_shelf", "oil_jar"),
        ("scene_lamp_shelf", "rain_tracks"),
        ("scene_account_room", "torn_ledger_line"),
        ("scene_account_room", "deposit_receipt"),
        ("scene_back_gate", "hidden_thread"),
        ("scene_rain_alley", "search_notice"),
        ("scene_city_gate", "second_notice"),
        ("scene_city_gate", "outer_wrapper"),
        ("scene_interrogation_room", "sealed_desk"),
        ("scene_interrogation_room", "order_conflict_note"),
        ("scene_interrogation_room", "temp_record"),
        ("scene_interrogation_room", "search_list"),
    ]
    successful_investigations = []
    for scene_id, hotspot_id in investigation_steps:
        result = investigate(session_id, scene_id, hotspot_id)
        successful_investigations.append((scene_id, hotspot_id, result))
    assert len(successful_investigations) >= 10

    lu_boundary = dialogue(session_id, "npc_jinyiwei", "你的命令为何不问火因？", ["clue_lu_order_conflict"])
    assert lu_boundary["dialogue"]["npc_name"] == "陆峥"
    lu_record = dialogue(session_id, "npc_jinyiwei", "问话记录的顺序不对。", ["clue_temp_interrogation_record"])
    assert lu_record["dialogue"]["npc_name"] == "陆峥"

    investigate(session_id, "scene_front_hall", "old_box")
    repeated = investigate(session_id, "scene_front_hall", "old_box")
    assert repeated["new_clues"] == []

    owner = dialogue(session_id, "npc_owner", "这半枚红印纸角怎么解释？", ["clue_red_seal"])
    assert owner["dialogue"]["npc_name"] == "许掌柜"

    post_json("/api/investigate", {"session_id": session_id, "scene_id": "scene_engraving_room"})
    worker = dialogue(session_id, "npc_worker", "你昨夜一直在刻坊吗？")
    assert worker["dialogue"]["npc_name"] == "阿沈"

    post_json("/api/investigate", {"session_id": session_id, "scene_id": "scene_rain_alley"})
    scholar_default = dialogue(session_id, "npc_scholar", "你冒雨回来究竟找什么？")
    assert scholar_default["dialogue"]["npc_name"] == "顾闻"
    scholar_evidence = dialogue(session_id, "npc_scholar", "残页和诗稿外皮已经对上了。", ["clue_scholar_outer_wrapper"])
    assert scholar_evidence["dialogue"]["npc_name"] == "顾闻"

    post_json("/api/investigate", {"session_id": session_id, "scene_id": "scene_interrogation_room"})

    scholar_deduction = post_json(
        "/api/deduction/submit",
        {
            "session_id": session_id,
            "deduction_id": "deduce_scholar_motive",
            "selected_clue_ids": ["clue_scholar_searches_manuscript", "clue_scholar_outer_wrapper", "clue_poem_hidden_copy"],
        },
    )
    assert scholar_deduction["correct"] is True
    hidden_chain_deduction = post_json(
        "/api/deduction/submit",
        {
            "session_id": session_id,
            "deduction_id": "deduce_hidden_chain",
            "selected_clue_ids": ["clue_gag_order_wording", "clue_temp_interrogation_record", "clue_city_gate_second_notice"],
        },
    )
    assert hidden_chain_deduction["correct"] is True

    snapshot = client.get(f"/api/session/{session_id}").json()
    assert snapshot["state"]["current_stage"] == "choice"
    completed_combo_count = len(snapshot["state"]["completed_combo_ids"])
    completed_deduction_count = len(snapshot["state"].get("completed_deduction_ids", []))
    assert completed_combo_count >= 2
    assert completed_deduction_count >= 2
    assert any(choice["choice_id"] == "choice_reverse_trace" for choice in snapshot["available_choices"])

    hidden_support = dialogue(session_id, "npc_jinyiwei", "书坊、城门和问话处已经连成一条线。")
    assert hidden_support["dialogue"]["npc_name"] == "陆峥"

    choose = post_json("/api/choice", {"session_id": session_id, "choice_id": "choice_reverse_trace"})
    assert choose["state"]["current_stage"] == "ending"
    ending = post_json("/api/ending/resolve", {"session_id": session_id})
    assert ending["ending_id"] == "ending_hidden"
    assert has_chinese(ending["history_echo"])
    assert len(ending["npc_fates"]) >= 3

