from __future__ import annotations

import pytest

from app.models.script_models import ScriptPackage
from app.services.script_normalizer import ScriptNormalizationError, script_package_normalizer
from app.services.script_supervisor import script_supervisor
from script_generation_fixtures import sample_script_payload


def test_normalizer_repairs_deepseek_flexible_shape() -> None:
    flexible_payload = {
        "script_id": "rainy_night_station_001",
        "script_overview": {
            "title": "雨夜驿变",
            "description": "雨夜中军报失踪，粮草账目也露出破绽。",
            "pitch": "玩家在驿站内追查军报和粮草之间的隐情。",
        },
        "playable_identities": [{"id": "investigator", "name": "新科进士", "description": "受命查访驿站疑案。"}],
        "world": {"name": "北宋边关驿站", "description": "雨夜中的地方驿站。"},
        "story": {
            "summary": "军报失踪。",
            "hidden_truth": "有人为遮掩粮草亏空调换军报。",
            "truth_chain_clue_ids": ["clue1", "clue2", "clue3", "clue4"],
        },
        "stages": [
            {"id": "stage1", "name": "初抵驿站", "description": "了解表面事件", "clues_unlocked": ["clue1"]},
            {"id": "stage2", "name": "深入调查", "description": "串联证据", "clues_unlocked": ["clue2", "clue3"]},
            {"id": "stage3", "name": "真相浮现", "description": "确认动机", "clues_unlocked": ["clue4", "clue5", "clue6"]},
        ],
        "locations": [
            {"id": "front_hall", "name": "前厅", "description": "接待处有油灯和地图。"},
            {"id": "backyard", "name": "后院", "description": "泥地上有脚印。"},
            {"id": "stable", "name": "马厩", "description": "草料堆旁有马具。"},
            {"id": "granary", "name": "粮仓", "description": "账本与粮袋同在。"},
            {"id": "dispatch_room", "name": "军报房", "description": "书案上有火漆和纸灰。"},
        ],
        "npcs": [
            {"id": "npc1", "name": "驿丞", "role": "关键证人", "secret": "知道军报被换。"},
            {"id": "npc2", "name": "粮草官", "role": "嫌疑人", "secret": "掩盖粮草亏空。", "stage_limits": {"intro": {"disclose_clue_ids": ["clue3"]}}},
            {"id": "npc3", "name": "驿卒", "role": "目击者", "secret": "夜里见人进军报房。"},
            {"id": "npc4", "name": "厨娘", "role": "消息来源", "secret": "知道商人往来。"},
        ],
        "clues": [
            {"id": "clue1", "name": "军报残片", "description": "焦黑纸片。", "location": "dispatch_room", "stage": "stage1"},
            {"id": "clue2", "name": "粮草账本", "description": "账实不符。", "location": "granary", "stage": "stage1"},
            {"id": "clue3", "name": "火漆印", "description": "新火漆。", "location": "dispatch_room", "stage": "stage2"},
            {"id": "clue4", "name": "草鞋印", "description": "大尺码鞋印。", "location": "backyard", "stage": "stage2"},
            {"id": "clue5", "name": "商人信函", "description": "私通信函。", "location": "front_hall", "stage": "stage2"},
            {"id": "clue6", "name": "旧军报副本", "description": "与失踪军报相反。", "location": "backyard", "stage": "stage3"},
        ],
        "visual_assets": {
            "scenes": [{"id": f"scene_{location}", "prompt": f"北宋驿站{location}", "required_subjects": ["驿站"], "era_feature_checklist": ["宋代建筑"]} for location in ["front_hall", "backyard", "stable", "granary", "dispatch_room"]],
            "npcs": [{"id": f"npc{index}_asset", "prompt": "宋代人物", "required_subjects": ["人物"], "era_feature_checklist": ["宋代服饰"]} for index in range(1, 5)],
            "clues": [{"id": f"clue{index}_asset", "prompt": "宋代线索物件", "required_subjects": ["线索"], "era_feature_checklist": ["宋代文书"]} for index in range(1, 7)],
        },
        "hotspot_positioning": [
            {"id": f"hotspot{index}", "location": "dispatch_room", "anchor_point": [0.3, 0.5], "bbox": [0.2, 0.4, 0.4, 0.6]}
            for index in range(1, 7)
        ],
        "choices": [
            {"id": "choice_report", "title": "上报军报", "description": "将证据交给转运司。"},
        ],
        "endings": [
            {
                "id": "ending_truth",
                "name": "军报归案",
                "description": "军报与粮草真相被查明。",
                "conditions": {"final_choice_id": "choice_report"},
                "history_echo": "驿传文书维系着边地军务。",
            }
        ],
    }

    normalized = script_package_normalizer.normalize(
        flexible_payload,
        dynasty_id="song",
        keywords=["驿站", "军报", "雨夜", "粮草"],
        job_id="job_normalizer_test",
    )
    package = ScriptPackage.model_validate(normalized)
    supervisor_result = script_supervisor.review(package)

    assert package.dynasty_id == "song"
    assert package.script_id.endswith("r_test")
    assert len(package.visual_assets) >= 15
    assert isinstance(package.npcs[1].stage_limits["intro"], str)
    assert len([asset for asset in package.visual_assets if asset.asset_type == "scene"]) >= 5
    first_scene = next(asset for asset in package.visual_assets if asset.asset_type == "scene" and asset.owner_id == "front_hall")
    assert "人物与场景一体生成" in first_scene.prompt
    assert "驿丞" in first_scene.prompt
    assert "驿丞" in first_scene.required_subjects
    assert len(package.hotspot_positioning) >= 6
    assert supervisor_result.passed


def test_normalizer_rejects_missing_world_instead_of_fabricating_default() -> None:
    payload = sample_script_payload()
    payload.pop("world")

    with pytest.raises(ScriptNormalizationError, match="SCRIPT_WORLD_MISSING"):
        script_package_normalizer.normalize(
            payload,
            dynasty_id="song",
            keywords=["驿站", "军报"],
            job_id="job_missing_world",
        )


def test_normalizer_rejects_missing_story_core_fields() -> None:
    payload = sample_script_payload()
    payload["story"] = {"summary": "军报失踪。"}

    with pytest.raises(ScriptNormalizationError, match="SCRIPT_STORY_INCOMPLETE"):
        script_package_normalizer.normalize(
            payload,
            dynasty_id="song",
            keywords=["驿站", "军报"],
            job_id="job_missing_story",
        )


def test_normalizer_rejects_underfilled_core_content() -> None:
    payload = sample_script_payload()
    payload["locations"] = payload["locations"][:4]

    with pytest.raises(ScriptNormalizationError, match="locations 至少需要 5 项"):
        script_package_normalizer.normalize(
            payload,
            dynasty_id="song",
            keywords=["驿站", "军报"],
            job_id="job_underfilled_locations",
        )


def test_normalizer_rejects_missing_choices_or_endings() -> None:
    no_choices = sample_script_payload()
    no_choices["choices"] = []

    with pytest.raises(ScriptNormalizationError, match="choices 至少需要 1 项"):
        script_package_normalizer.normalize(
            no_choices,
            dynasty_id="song",
            keywords=["驿站", "军报"],
            job_id="job_missing_choices",
        )

    no_endings = sample_script_payload()
    no_endings["endings"] = []

    with pytest.raises(ScriptNormalizationError, match="endings 至少需要 1 项"):
        script_package_normalizer.normalize(
            no_endings,
            dynasty_id="song",
            keywords=["驿站", "军报"],
            job_id="job_missing_endings",
        )


def test_normalizer_rejects_missing_visual_asset_mapping() -> None:
    payload = sample_script_payload()
    payload["visual_assets"] = [asset for asset in payload["visual_assets"] if asset["asset_type"] != "scene"]

    with pytest.raises(ScriptNormalizationError, match="visual_assets 缺少 scene 资产映射"):
        script_package_normalizer.normalize(
            payload,
            dynasty_id="song",
            keywords=["驿站", "军报"],
            job_id="job_missing_scene_assets",
        )


def test_normalizer_rejects_ending_without_generated_text() -> None:
    payload = sample_script_payload()
    payload["endings"][0].pop("history_echo")

    with pytest.raises(ScriptNormalizationError, match="SCRIPT_ENDING_INCOMPLETE"):
        script_package_normalizer.normalize(
            payload,
            dynasty_id="song",
            keywords=["驿站", "军报"],
            job_id="job_incomplete_ending",
        )
