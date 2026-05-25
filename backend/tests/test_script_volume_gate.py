from __future__ import annotations

from copy import deepcopy

from app.models.script_models import ScriptPackage
from app.services.script_volume_gate import script_volume_gate
from script_generation_fixtures import sample_script_payload


def expanded_volume_payload() -> dict:
    payload = deepcopy(sample_script_payload("script_volume_pass"))

    for index in range(5, 8):
        payload["visual_assets"].append(_asset(f"asset_scene_{index}", "scene", f"loc_{index}"))

    payload["locations"] = []
    for index in range(8):
        payload["locations"].append(
            {
                "location_id": f"loc_{index}",
                "name": f"扩展场景{index}",
                "description": "案卷线索分布在这里。",
                "scene_text": "灯影与雨声让痕迹更难辨认。",
                "stage_ids": ["intro", "investigation", "reversal", "choice"],
                "npc_ids": [f"npc_{index % 4}"],
                "hotspots": [],
                "visual_asset_id": f"asset_scene_{index}",
            }
        )

    payload["clues"] = []
    payload["hotspot_positioning"] = []
    for index in range(30):
        location_index = index % 8
        clue_id = f"clue_{index}"
        hotspot_id = f"hotspot_{index}"
        payload["clues"].append(
            {
                "clue_id": clue_id,
                "title": f"扩展线索{index}",
                "type": "物证",
                "is_key": index < 10,
                "source_location_id": f"loc_{location_index}",
                "source_npc_id": None,
                "highlight_text": f"痕迹{index}",
                "display_text": f"第 {index} 条扩展证据。",
                "detail": "证据继续补全军报转移路径。",
                "stage_available": ["intro", "investigation", "reversal", "choice"],
                "unlock_conditions": {},
                "effects": {"flags": [f"flag_{index}"]},
                "related_clue_ids": [],
                "ending_tags": [],
                "forbidden_before_stage": None,
                "visual_asset_id": f"asset_clue_{index % 6}",
            }
        )
        payload["locations"][location_index]["hotspots"].append(
            {
                "hotspot_id": hotspot_id,
                "label": f"查看痕迹{index}",
                "description": "一处可疑痕迹。",
                "clue_ids": [clue_id],
                "required_stage": "intro" if index < 4 else "investigation",
                "required_clue_ids": [],
                "investigation_text": f"你发现了扩展线索 {index}。",
                "repeat_text": "这里已经查过。",
            }
        )
        payload["hotspot_positioning"].append(
            {
                "location_id": f"loc_{location_index}",
                "hotspot_id": hotspot_id,
                "visual_asset_id": f"asset_scene_{location_index}",
                "clue_id": clue_id,
                "anchor_point": {"x": 0.2 + (index % 5) * 0.1, "y": 0.35 + (index % 4) * 0.1},
                "bbox": {"x": 0.12 + (index % 5) * 0.1, "y": 0.28 + (index % 4) * 0.1, "width": 0.08, "height": 0.08},
                "calibration_status": "approved",
                "calibrated_against_path": f"assets/generated/visuals/generated/script_volume_pass/asset_scene_{location_index}.png",
            }
        )

    payload["story"]["truth_chain_clue_ids"] = ["clue_0", "clue_1", "clue_2", "clue_3"]
    payload["clue_graph"] = [
        {
            "rule_id": f"combo_{index}",
            "required_clue_ids": [f"clue_{index}", f"clue_{index + 1}", f"clue_{index + 2}"],
            "result_title": f"组合推理{index}",
            "result_text": "线索可以相互印证。",
            "effects": {"flags": [f"combo_{index}_done"]},
        }
        for index in range(6)
    ]
    payload["deductions"] = [
        {
            "deduction_id": f"deduction_{index}",
            "question": f"第 {index} 个疑团如何成立？",
            "required_clue_ids": [f"clue_{index}"],
            "correct_clue_ids": [f"clue_{index}", f"clue_{index + 1}"],
            "wrong_feedback": "这些证据还不够。",
            "success_text": "这个疑团被证据支持。",
            "effects": {"flags": [f"deduction_{index}_solved"]},
        }
        for index in range(8)
    ]
    payload["chapter_sections"] = [
        {
            "section_id": f"section_{index}",
            "stage": ["intro", "investigation", "reversal", "choice"][index % 4],
            "title": f"章节小节{index}",
            "trigger_conditions": [],
            "scene_id": f"loc_{index % 8}",
            "npc_ids": [f"npc_{index % 4}"],
            "hotspot_ids": [f"hotspot_{index}"],
            "clue_ids": [f"clue_{index}"],
            "next_section_ids": [f"section_{index + 1}"] if index < 11 else [],
            "goal": "推进章节调查。",
            "display_text": "玩家在这一节整理新发现。",
        }
        for index in range(12)
    ]
    payload["choices"] = [
        {"choice_id": f"choice_{index}", "title": f"最终选择{index}", "description": "作出不可逆选择。", "effects": {"flags": [f"choice_{index}"]}}
        for index in range(5)
    ]
    payload["endings"] = [
        {
            "ending_id": f"ending_{index}",
            "title": f"结局{index}",
            "priority": index,
            "conditions": {"final_choice_id": f"choice_{index}"},
            "required_flags": [],
            "blocked_flags": [],
            "result_summary": "案件进入不同收束。",
            "ending_text": "人物各自承担选择后的代价。",
            "history_echo": "驿传文书与地方治理彼此牵连。",
            "related_clue_ids": [f"clue_{index}"],
            "related_choice_ids": [f"choice_{index}"],
            "npc_fates": {},
        }
        for index in range(5)
    ]
    return payload


def test_volume_gate_accepts_expanded_script() -> None:
    package = ScriptPackage.model_validate(expanded_volume_payload())

    result = script_volume_gate.review(package)

    assert result.passed is True
    assert result.missing["locations"] == 0
    assert result.missing["hotspots"] == 0
    assert result.missing["clues"] == 0


def test_volume_gate_blocks_stage15_minimum_sample() -> None:
    package = ScriptPackage.model_validate(sample_script_payload("script_volume_small"))

    result = script_volume_gate.review(package)

    assert result.passed is False
    assert any(issue.code == "SCRIPT_VOLUME_TOO_SMALL" for issue in result.blocking_issues)
    assert any(issue.code == "HOTSPOT_VOLUME_TOO_SMALL" for issue in result.blocking_issues)
    assert any(issue.code == "CLUE_VOLUME_TOO_SMALL" for issue in result.blocking_issues)
    assert any(issue.code == "DEDUCTION_MISSING" for issue in result.blocking_issues)
    assert any(issue.code == "CHAPTER_SECTION_MISSING" for issue in result.blocking_issues)


def test_volume_gate_blocks_broken_deduction_reference() -> None:
    payload = expanded_volume_payload()
    payload["deductions"][0]["correct_clue_ids"] = ["missing_clue"]
    package = ScriptPackage.model_validate(payload)

    result = script_volume_gate.review(package)

    assert result.passed is False
    assert any(
        issue.code == "VOLUME_REFERENCE_BROKEN" and issue.details.get("deduction_id") == "deduction_0"
        for issue in result.blocking_issues
    )


def _asset(asset_id: str, asset_type: str, owner_id: str) -> dict:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "owner_id": owner_id,
        "title": asset_id,
        "prompt": "北宋雨夜驿站，人物与场景一体生成，线索物件清晰可见。",
        "negative_prompt": "现代物件，文字水印，占位图",
        "required_subjects": ["军报", "人物与场景一体生成", "可点击线索物件"],
        "era_feature_checklist": ["宋代服饰", "木构建筑"],
        "generation_status": "approved",
        "quality_gate": {
            "status": "approved",
            "attempts": 1,
            "issues": [],
            "approved_path": f"assets/generated/visuals/generated/sample/{asset_id}.png",
            "rejected_paths": [],
            "regenerated_count": 0,
        },
    }
