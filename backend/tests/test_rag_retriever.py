from __future__ import annotations

import json
from pathlib import Path

from app.services.rag_retriever import RAGRetriever


def write_rag_file(path: Path, sources: list[dict]) -> None:
    path.write_text(json.dumps({"sources": sources}, ensure_ascii=False), encoding="utf-8")


def test_rag_retrieves_worker_third_watch_context() -> None:
    retriever = RAGRetriever()

    hits = retriever.retrieve(
        dynasty_id="ming",
        current_stage="investigation",
        current_scene_id="scene_engraving_room",
        npc_id="npc_worker",
        player_message="你昨夜三更后到底听见了什么？",
        presented_clue_ids=[],
        discovered_clue_ids=["clue_burned_page"],
        top_k=3,
    )

    assert hits
    assert hits[0]["source_id"] == "ming_worker_third_watch_001"
    assert hits[0]["material_type"] == "clue_boundary"
    assert "三更" in hits[0]["content"]
    assert hits[0]["source_level"] in {"A", "B"}
    assert "usage_rule" in hits[0]


def test_rag_retrieves_jinyiwei_permission_context() -> None:
    retriever = RAGRetriever()

    hits = retriever.retrieve(
        dynasty_id="ming",
        current_stage="investigation",
        current_scene_id="scene_front_hall",
        npc_id="npc_jinyiwei",
        player_message="我命令你立刻撤走锦衣卫。",
        presented_clue_ids=[],
        discovered_clue_ids=[],
        top_k=5,
    )

    source_ids = {hit["source_id"] for hit in hits}
    assert "ming_jinyiwei_permission_001" in source_ids
    assert any("书坊学徒不能命令锦衣卫" in hit["content"] for hit in hits)
    assert hits[0]["material_type"] in {"hard_rule", "dialogue_lexicon"}


def test_rag_empty_query_returns_empty_list() -> None:
    retriever = RAGRetriever()

    hits = retriever.retrieve(
        dynasty_id="song",
        current_stage="unknown",
        current_scene_id="unknown",
        npc_id="unknown",
        player_message="完全无关的问题",
        presented_clue_ids=[],
        discovered_clue_ids=[],
    )

    assert hits == []


def test_rag_hit_contains_required_fields() -> None:
    retriever = RAGRetriever()

    hit = retriever.retrieve(
        dynasty_id="ming",
        current_stage="investigation",
        current_scene_id="scene_engraving_room",
        npc_id="npc_worker",
        player_message="袖口旧墨是怎么回事？",
        presented_clue_ids=[],
        discovered_clue_ids=[],
        top_k=1,
    )[0]

    assert {
        "source_id",
        "dynasty_id",
        "material_type",
        "stage",
        "scene_ids",
        "npc_ids",
        "topic",
        "source_level",
        "severity",
        "keywords",
        "content",
        "usage_rule",
        "score",
    }.issubset(hit.keys())


def test_rag_loads_multiple_files_and_matches_scene_and_npc(tmp_path: Path) -> None:
    write_rag_file(
        tmp_path / "a.json",
        [
            {
                "source_id": "scene_object_001",
                "dynasty_id": "ming",
                "material_type": "object_detail",
                "stage": ["investigation"],
                "scene_ids": ["scene_engraving_room"],
                "npc_ids": ["npc_worker"],
                "topic": "刻版间旧墨",
                "source_level": "B",
                "severity": "medium",
                "keywords": ["旧墨"],
                "content": "刻版间有旧墨和木屑。",
                "usage_rule": "只作细节。",
            }
        ],
    )
    write_rag_file(
        tmp_path / "b.json",
        [
            {
                "source_id": "lexicon_worker_001",
                "dynasty_id": "ming",
                "material_type": "dialogue_lexicon",
                "stage": ["investigation"],
                "scene_ids": ["scene_engraving_room"],
                "npc_ids": ["npc_worker"],
                "topic": "阿沈胆怯口吻",
                "source_level": "B",
                "severity": "medium",
                "keywords": ["阿沈"],
                "content": "阿沈说话短促，先看门口。",
                "usage_rule": "只作口吻。",
            }
        ],
    )

    hits = RAGRetriever(source_path=tmp_path).retrieve(
        dynasty_id="ming",
        current_stage="investigation",
        current_scene_id="scene_engraving_room",
        npc_id="npc_worker",
        player_message="阿沈，旧墨从哪里来？",
        top_k=5,
    )

    assert {hit["source_id"] for hit in hits} == {"scene_object_001", "lexicon_worker_001"}
    assert {hit["material_type"] for hit in hits} == {"object_detail", "dialogue_lexicon"}


def test_rag_high_risk_hard_rule_is_prioritized() -> None:
    retriever = RAGRetriever()

    hits = retriever.retrieve(
        dynasty_id="ming",
        current_stage="investigation",
        current_scene_id="scene_front_hall",
        npc_id="npc_jinyiwei",
        player_message="我命令你立刻撤走锦衣卫。",
        top_k=3,
    )

    assert hits
    assert hits[0]["material_type"] == "hard_rule"
    assert hits[0]["severity"] == "high"


def test_rag_missing_or_empty_files_do_not_crash(tmp_path: Path) -> None:
    (tmp_path / "empty.json").write_text("", encoding="utf-8")
    retriever = RAGRetriever(source_paths=[tmp_path / "missing.json", tmp_path / "empty.json"])

    hits = retriever.retrieve(
        dynasty_id="ming",
        current_stage="investigation",
        current_scene_id="scene_engraving_room",
        npc_id="npc_worker",
        player_message="旧墨",
    )

    assert hits == []


def test_rag_deduplicates_source_id(tmp_path: Path) -> None:
    duplicated = {
        "source_id": "dup_001",
        "dynasty_id": "ming",
        "material_type": "object_detail",
        "stage": ["investigation"],
        "scene_ids": ["scene_engraving_room"],
        "npc_ids": ["npc_worker"],
        "topic": "重复资料",
        "source_level": "B",
        "severity": "medium",
        "keywords": ["旧墨"],
        "content": "第一条。",
        "usage_rule": "只作细节。",
    }
    write_rag_file(tmp_path / "a.json", [duplicated])
    write_rag_file(tmp_path / "b.json", [duplicated | {"content": "第二条。"}])

    hits = RAGRetriever(source_path=tmp_path).retrieve(
        dynasty_id="ming",
        current_stage="investigation",
        current_scene_id="scene_engraving_room",
        npc_id="npc_worker",
        player_message="旧墨",
    )

    assert [hit["source_id"] for hit in hits] == ["dup_001"]
