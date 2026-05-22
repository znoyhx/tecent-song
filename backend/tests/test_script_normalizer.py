from __future__ import annotations

from app.models.script_models import ScriptPackage
from app.services.script_normalizer import script_package_normalizer
from app.services.script_supervisor import script_supervisor


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
        "story": {"summary": "军报失踪。", "hidden_truth": "有人为遮掩粮草亏空调换军报。"},
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
    assert len(package.hotspot_positioning) >= 6
    assert supervisor_result.passed
