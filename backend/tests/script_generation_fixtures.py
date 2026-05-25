from __future__ import annotations

from copy import deepcopy

from app.models.script_models import ImageQualityGateResult, ScriptPackage
from app.services.script_visual_contract import script_visual_contract


def sample_script_payload(script_id: str = "script_test_stage15") -> dict:
    visual_assets = []
    for index in range(5):
        visual_assets.append(_asset(f"asset_scene_{index}", "scene", f"loc_{index}"))
    for index in range(4):
        visual_assets.append(_asset(f"asset_npc_{index}", "npc", f"npc_{index}"))
    for index in range(6):
        visual_assets.append(_asset(f"asset_clue_{index}", "clue", f"clue_{index}"))

    locations = []
    clue_index = 0
    for index in range(5):
        hotspots = []
        for local in range(2 if index == 0 else 1):
            if clue_index >= 6:
                break
            hotspots.append(
                {
                    "hotspot_id": f"hotspot_{clue_index}",
                    "label": f"查看物证{clue_index}",
                    "description": "一处可疑痕迹。",
                    "clue_ids": [f"clue_{clue_index}"],
                    "required_stage": "intro" if clue_index == 0 else "investigation",
                    "required_clue_ids": [],
                    "investigation_text": f"你发现了第 {clue_index} 条线索。",
                    "repeat_text": "这里已经查过。",
                }
            )
            clue_index += 1
        locations.append(
            {
                "location_id": f"loc_{index}",
                "name": f"驿站场景{index}",
                "description": "雨夜驿站中灯影摇动。",
                "scene_text": "驿卒压低声音，案卷仍摊在桌上。",
                "stage_ids": ["intro", "investigation", "reversal", "choice"] if index == 0 else ["investigation", "reversal", "choice"],
                "npc_ids": [f"npc_{index % 4}"],
                "hotspots": hotspots,
                "visual_asset_id": f"asset_scene_{index}",
            }
        )

    return {
        "script_id": script_id,
        "job_id": f"job_{script_id}",
        "dynasty_id": "song",
        "keywords": ["驿站", "军报", "雨夜", "粮草"],
        "script_overview": {
            "title": "雨夜军报案",
            "logline": "一封军报在雨夜驿站失踪。",
            "case_summary": "粮草军报被调包，玩家需查清谁借雨夜转移文书。",
            "opening_location": "城外驿站",
            "public_objective": "查明军报去向。",
            "major_locations": ["城外驿站", "粮仓"],
            "major_npcs": ["驿丞", "押粮吏"],
            "player_briefing": "不要提前泄露最终真相。",
        },
        "playable_identities": [
            {
                "identity_id": "identity_inspector",
                "display_name": "巡检随从",
                "description": "随巡检查验驿站文书的人。",
                "social_rank": "middle",
                "relation_to_case": "有权查验军报交接。",
                "motive": "洗清押运失职嫌疑。",
                "permissions": ["查验驿站", "询问驿卒"],
                "limitations": ["不能调动禁军"],
                "background": "你熟悉路引和驿券格式。",
                "tags": ["文书", "驿站"],
                "is_default": True,
            }
        ],
        "world": {
            "dynasty_id": "song",
            "dynasty_name": "北宋",
            "era_name": "北宋边郡",
            "year_hint": "仁宗年间",
            "location_region": "京西路驿道",
            "rules": ["驿站文书须逐级签押"],
            "forbidden_terms": ["锦衣卫", "电报"],
        },
        "story": {
            "surface_event": "军报失踪。",
            "hidden_truth": "军报被藏入粮袋，借押粮车出驿。",
            "themes": ["文书", "粮草"],
            "culprit_boundary": "驿丞知情但不是唯一主使。",
            "truth_chain_clue_ids": ["clue_0", "clue_1", "clue_2", "clue_3"],
        },
        "stages": [
            {"stage_id": "intro", "name": "入驿", "order": 0, "goal": "先查军报何时失踪。", "entry_location_id": "loc_0", "available_location_ids": ["loc_0"], "key_clue_ids": ["clue_0"]},
            {"stage_id": "investigation", "name": "查验", "order": 1, "goal": "串联驿站证据。", "entry_location_id": "loc_1", "available_location_ids": ["loc_0", "loc_1", "loc_2"], "key_clue_ids": ["clue_1", "clue_2"]},
            {"stage_id": "reversal", "name": "反转", "order": 2, "goal": "确认军报不在文匣。", "entry_location_id": "loc_3", "available_location_ids": ["loc_0", "loc_3", "loc_4"], "key_clue_ids": ["clue_3", "clue_4"]},
            {"stage_id": "choice", "name": "抉择", "order": 3, "goal": "决定如何呈报。", "entry_location_id": "loc_0", "available_location_ids": ["loc_0"], "key_clue_ids": ["clue_5"]},
            {"stage_id": "ending", "name": "结局", "order": 4, "goal": "查看后果。", "entry_location_id": "loc_0", "available_location_ids": ["loc_0"], "key_clue_ids": []},
        ],
        "locations": locations,
        "npcs": [
            {
                "npc_id": f"npc_{index}",
                "name": f"人物{index}",
                "public_identity": "驿站相关人",
                "appearance": "宋式圆领袍，风尘未干。",
                "personality": "谨慎",
                "background_suspicion": "对军报交接含糊其辞。",
                "case_connection": "当夜在驿站。",
                "event_behavior": "声称只听见雨声。",
                "public_goal": "保住差事。",
                "hidden_motive": "隐瞒一段交接疏漏。",
                "known_info": ["知道驿站时辰"],
                "unknown_info": ["不知道完整主使"],
                "forbidden_disclosure": ["不得说出军报被藏入粮袋"],
                "speaking_style": "短句，谨慎。",
                "initial_trust": 0,
                "emotion_state": "guarded",
                "releasable_clue_ids": [f"clue_{index}"],
                "stage_limits": {"intro": "只谈公开事实"},
                "visual_asset_id": f"asset_npc_{index}",
            }
            for index in range(4)
        ],
        "relationships": [],
        "clues": [
            {
                "clue_id": f"clue_{index}",
                "title": f"线索{index}",
                "type": "物证",
                "is_key": True,
                "source_location_id": f"loc_{min(index, 4)}",
                "source_npc_id": None,
                "highlight_text": f"物证{index}",
                "display_text": f"第 {index} 条证据。",
                "detail": "证据指向军报转移路径。",
                "stage_available": ["intro", "investigation", "reversal", "choice"],
                "unlock_conditions": {},
                "effects": {"scores": {"truth": 1}, "flags": [f"flag_{index}"]},
                "related_clue_ids": [],
                "ending_tags": [],
                "forbidden_before_stage": None,
                "visual_asset_id": f"asset_clue_{index}",
            }
            for index in range(6)
        ],
        "clue_graph": [
            {"rule_id": "combo_truth", "required_clue_ids": ["clue_0", "clue_1", "clue_2"], "result_title": "军报路线成立", "result_text": "证据能串成转移路径。", "effects": {"flags": ["chain_confirmed"]}}
        ],
        "deductions": [
            {
                "deduction_id": "deduction_route",
                "question": "军报最可能通过哪条路径离开驿站？",
                "required_clue_ids": ["clue_0"],
                "correct_clue_ids": ["clue_0", "clue_1", "clue_2"],
                "wrong_feedback": "这些线索还不能说明军报的转移路线。",
                "success_text": "残片、账册和脚印能指向押粮车这条暗线。",
                "effects": {"flags": ["deduced_report_route"]},
            }
        ],
        "chapter_sections": [
            {
                "section_id": "section_opening",
                "stage": "intro",
                "title": "雨夜入驿",
                "trigger_conditions": [],
                "scene_id": "loc_0",
                "npc_ids": ["npc_0"],
                "hotspot_ids": ["hotspot_0"],
                "clue_ids": ["clue_0"],
                "next_section_ids": [],
                "goal": "确认军报失踪的第一处痕迹。",
                "display_text": "雨声压住驿门，你先检查前厅遗下的痕迹。",
            }
        ],
        "dialogue_rules": [],
        "choices": [
            {"choice_id": "choice_report", "title": "呈报转运使", "description": "把证据交给上级。", "effects": {"flags": ["reported_truth"], "scores": {"truth": 2}}},
            {"choice_id": "choice_hide", "title": "暂压证据", "description": "先保住驿站人命。", "effects": {"flags": ["withheld_truth"], "scores": {"survival": 2}}},
        ],
        "endings": [
            {"ending_id": "ending_truth", "title": "军报归案", "priority": 0, "conditions": {"final_choice_id": "choice_report"}, "required_flags": [], "blocked_flags": [], "result_summary": "军报被追回。", "ending_text": "粮车被截回，驿站免于冤罪。", "history_echo": "驿传制度靠文书与人心共同维系。", "related_clue_ids": ["clue_0"], "related_choice_ids": ["choice_report"], "npc_fates": {}}
        ],
        "visual_assets": visual_assets,
        "visual_style_guide": {
            "style_keywords": ["宋代", "雨夜", "写实"],
            "forbidden_visuals": ["现代电线", "文字水印"],
            "color_script": "冷雨与暖灯对照。",
            "camera": "平视调查视角。",
            "era_feature_checklist": ["圆领袍", "木构驿站", "纸本文书"],
            "appearance_lock": {"npc_0": "圆领袍"},
        },
        "hotspot_positioning": [
            {
                "location_id": f"loc_{min(index, 4)}",
                "hotspot_id": f"hotspot_{index}",
                "visual_asset_id": f"asset_scene_{min(index, 4)}",
                "clue_id": f"clue_{index}",
                "anchor_point": {"x": 0.2 + index * 0.08, "y": 0.42},
                "bbox": {"x": 0.12 + index * 0.08, "y": 0.34, "width": 0.12, "height": 0.12},
                "calibration_status": "approved",
                "calibrated_against_path": f"assets/generated/visuals/generated/{script_id}/asset_scene_{min(index, 4)}.png",
            }
            for index in range(6)
        ],
        "quality_gate": {"required_scene_count": 5, "required_npc_count": 4, "required_clue_count": 6, "scene_approved": 5, "npc_approved": 4, "clue_approved": 6, "rejected": 0, "regenerated": 0, "blocked": 0},
    }


def _asset(asset_id: str, asset_type: str, owner_id: str) -> dict:
    prompt = "北宋雨夜驿站，核心物件清晰可见。"
    required_subjects = ["军报", "驿站"]
    if asset_type == "scene":
        prompt = "北宋雨夜驿站，人物0、人物1、人物2、人物3与场景一体生成，军报线索物件清晰可见。"
        required_subjects = ["军报", "驿站", "人物0", "人物1", "人物2", "人物3", "人物与场景一体生成", "可点击线索物件"]
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "owner_id": owner_id,
        "title": asset_id,
        "prompt": prompt,
        "negative_prompt": "现代物件，文字水印，占位图",
        "required_subjects": required_subjects,
        "era_feature_checklist": ["宋代服饰", "木构建筑"],
        "prompt_hash": "abc123",
        "generated_path": f"assets/generated/visuals/generated/sample/{asset_id}.png",
        "url": f"/api/scripts/sample/assets/{asset_id}",
        "provider": "test",
        "model": "test",
        "generation_status": "approved",
        "quality_gate": {
            "status": "approved",
            "checked_at": "2026-05-22T00:00:00",
            "attempts": 1,
            "prompt_hash": "abc123",
            "issues": [],
            "approved_path": f"assets/generated/visuals/generated/sample/{asset_id}.png",
            "rejected_paths": [],
            "regenerated_count": 0,
        },
    }


def sample_script_payload_with_broken_chain() -> dict:
    payload = deepcopy(sample_script_payload("script_broken_chain"))
    payload["story"]["truth_chain_clue_ids"] = ["clue_0", "missing_clue"]
    return payload


def stage15_script_payload(script_id: str = "script_stage15_pass") -> dict:
    visual_assets = [
        *_stage15_assets("scene", 8, "loc"),
        *_stage15_assets("npc", 4, "npc"),
        *_stage15_assets("clue", 6, "clue"),
    ]
    locations = []
    hotspot_positioning = []
    clues = []
    for index in range(30):
        location_index = index % 8
        clue_id = f"clue_{index}"
        clues.append(
            {
                "clue_id": clue_id,
                "title": f"Evidence token {index}",
                "type": "evidence",
                "is_key": index < 10,
                "source_location_id": f"loc_{location_index}",
                "source_npc_id": None,
                "highlight_text": f"trace {index}",
                "display_text": f"Evidence detail {index} points to the hidden dispatch route.",
                "detail": f"Material trace {index} supports the route and motive.",
                "stage_available": ["intro", "investigation", "reversal", "choice"],
                "unlock_conditions": {},
                "effects": {"flags": [f"flag_{index}"]},
                "related_clue_ids": [f"clue_{(index + 1) % 30}"],
                "ending_tags": [],
                "forbidden_before_stage": None,
                "visual_asset_id": f"asset_clue_{index % 6}",
            }
        )
        hotspot_positioning.append(
            {
                "location_id": f"loc_{location_index}",
                "hotspot_id": f"hotspot_{index}",
                "visual_asset_id": f"asset_scene_{location_index}",
                "clue_id": clue_id,
                "anchor_point": {"x": 0.18 + (index % 5) * 0.12, "y": 0.28 + (index % 4) * 0.12},
                "bbox": {"x": 0.12 + (index % 5) * 0.12, "y": 0.22 + (index % 4) * 0.12, "width": 0.08, "height": 0.08},
                "calibration_status": "approved",
                "calibrated_against_path": f"assets/generated/visuals/generated/{script_id}/asset_scene_{location_index}.png",
            }
        )

    for location_index in range(8):
        location_hotspots = []
        for clue_index in range(location_index, 30, 8):
            location_hotspots.append(
                {
                    "hotspot_id": f"hotspot_{clue_index}",
                    "label": f"Inspect trace {clue_index}",
                    "description": "A suspicious object is reachable in this scene.",
                    "clue_ids": [f"clue_{clue_index}"],
                    "required_stage": "intro" if clue_index < 4 else "investigation",
                    "required_clue_ids": [],
                    "investigation_text": f"You discover evidence token {clue_index}.",
                    "repeat_text": "This trace has already been checked.",
                }
            )
        locations.append(
            {
                "location_id": f"loc_{location_index}",
                "name": f"Station scene {location_index}",
                "description": "A Northern Song courier station with rain, lamps, records, and visible suspects.",
                "scene_text": "Lantern light catches damp wood and scattered evidence.",
                "stage_ids": ["intro", "investigation", "reversal", "choice"],
                "npc_ids": [f"npc_{location_index % 4}"],
                "hotspots": location_hotspots,
                "visual_asset_id": f"asset_scene_{location_index}",
            }
        )

    payload = {
        "script_id": script_id,
        "job_id": f"job_{script_id}",
        "dynasty_id": "song",
        "keywords": ["station", "dispatch", "rain", "grain"],
        "script_overview": {
            "title": "Rain Dispatch Case",
            "logline": "A courier dispatch vanishes during a storm.",
            "case_summary": "The player traces a missing dispatch across a courier station, grain yard, and ledger chain.",
            "opening_location": "Courier station hall",
            "public_objective": "Find where the dispatch went.",
            "major_locations": [f"Station scene {index}" for index in range(8)],
            "major_npcs": [f"Witness {index}" for index in range(4)],
            "player_briefing": "Investigate without forcing the final truth too early.",
        },
        "playable_identities": [
            {
                "identity_id": "identity_inspector",
                "display_name": "Circuit aide",
                "description": "An aide allowed to inspect station records and cargo.",
                "social_rank": "middle",
                "relation_to_case": "Authorized to inspect courier transfer records.",
                "motive": "Clear the broken dispatch chain.",
                "permissions": ["inspect station", "question witnesses"],
                "limitations": ["cannot command soldiers"],
                "background": "You know road permits and courier seals.",
                "tags": ["records", "station"],
                "is_default": True,
            }
        ],
        "world": {
            "dynasty_id": "song",
            "dynasty_name": "Northern Song",
            "era_name": "border courier route",
            "year_hint": "Renzong era atmosphere",
            "location_region": "western capital road",
            "rules": ["Courier documents require layered seals."],
            "forbidden_terms": ["phone", "telegraph"],
        },
        "story": {
            "surface_event": "The dispatch is missing.",
            "hidden_truth": "The dispatch was hidden inside grain cargo and moved out through a side gate.",
            "themes": ["records", "grain", "power"],
            "culprit_boundary": "The station keeper knows part of it but is not the only mover.",
            "truth_chain_clue_ids": ["clue_0", "clue_1", "clue_2", "clue_3"],
        },
        "stages": [
            {"stage_id": "intro", "name": "Arrival", "order": 0, "goal": "Confirm the dispatch vanished.", "entry_location_id": "loc_0", "available_location_ids": ["loc_0", "loc_1"], "key_clue_ids": ["clue_0"]},
            {"stage_id": "investigation", "name": "Search", "order": 1, "goal": "Connect station traces.", "entry_location_id": "loc_1", "available_location_ids": [f"loc_{index}" for index in range(8)], "key_clue_ids": ["clue_1", "clue_2"]},
            {"stage_id": "reversal", "name": "Reversal", "order": 2, "goal": "Prove the dispatch left with cargo.", "entry_location_id": "loc_3", "available_location_ids": [f"loc_{index}" for index in range(8)], "key_clue_ids": ["clue_3", "clue_4"]},
            {"stage_id": "choice", "name": "Choice", "order": 3, "goal": "Choose how to report the truth.", "entry_location_id": "loc_0", "available_location_ids": [f"loc_{index}" for index in range(8)], "key_clue_ids": ["clue_5"]},
            {"stage_id": "ending", "name": "Ending", "order": 4, "goal": "See the result.", "entry_location_id": "loc_0", "available_location_ids": ["loc_0"], "key_clue_ids": []},
        ],
        "locations": locations,
        "npcs": [
            {
                "npc_id": f"npc_{index}",
                "name": f"Witness {index}",
                "public_identity": "courier station witness",
                "appearance": "Song robe, damp sleeves, tired face, no modern items.",
                "personality": "guarded",
                "background_suspicion": "Their account of the rain hour is incomplete.",
                "case_connection": "Present at the courier station that night.",
                "event_behavior": "Claims to have heard only rain and cart wheels.",
                "public_goal": "Keep their post safe.",
                "hidden_motive": "Hide a smaller procedural failure.",
                "known_info": ["Knows the station schedule."],
                "unknown_info": ["Does not know the whole mastermind."],
                "forbidden_disclosure": ["Must not reveal the grain cargo route before evidence is found."],
                "speaking_style": "short cautious phrases",
                "initial_trust": 0,
                "emotion_state": "guarded",
                "releasable_clue_ids": [f"clue_{index}", f"clue_{index + 4}"],
                "stage_limits": {"intro": "public facts only"},
                "visual_asset_id": f"asset_npc_{index}",
            }
            for index in range(4)
        ],
        "relationships": [],
        "clues": clues,
        "clue_graph": [
            {
                "rule_id": f"combo_{index}",
                "required_clue_ids": [f"clue_{index}", f"clue_{index + 1}", f"clue_{index + 2}", f"clue_{index + 3}"],
                "result_title": f"Link result {index}",
                "result_text": "These clues reinforce the cargo route.",
                "effects": {"flags": [f"combo_{index}_done"]},
            }
            for index in range(6)
        ],
        "deductions": [
            {
                "deduction_id": f"deduction_{index}",
                "question": f"Why does suspicion {index} hold?",
                "required_clue_ids": [f"clue_{index}"],
                "correct_clue_ids": [f"clue_{index}", f"clue_{index + 1}"],
                "wrong_feedback": "The evidence chain is still thin.",
                "success_text": "The selected clues support this suspicion.",
                "effects": {"flags": [f"deduction_{index}_solved"]},
            }
            for index in range(8)
        ],
        "chapter_sections": [
            {
                "section_id": f"section_{index}",
                "stage": ["intro", "investigation", "reversal", "choice"][index % 4],
                "title": f"Chapter beat {index}",
                "trigger_conditions": [],
                "scene_id": f"loc_{index % 8}",
                "npc_ids": [f"npc_{index % 4}"],
                "hotspot_ids": [f"hotspot_{index}"],
                "clue_ids": [f"clue_{index}"],
                "next_section_ids": [f"section_{index + 1}"] if index < 11 else [],
                "goal": "Advance the investigation.",
                "display_text": "The player organizes the newest discovery.",
            }
            for index in range(12)
        ],
        "dialogue_rules": [],
        "choices": [
            {"choice_id": f"choice_{index}", "title": f"Final choice {index}", "description": "Choose an irreversible report path.", "effects": {"flags": [f"choice_{index}"]}}
            for index in range(5)
        ],
        "endings": [
            {
                "ending_id": f"ending_{index}",
                "title": f"Ending {index}",
                "priority": index,
                "conditions": {"final_choice_id": f"choice_{index}"},
                "required_flags": [],
                "blocked_flags": [],
                "result_summary": "The case closes in a different way.",
                "ending_text": "The witnesses bear the cost of the chosen truth.",
                "history_echo": "Courier systems depend on records and human fear alike.",
                "related_clue_ids": [f"clue_{index}"],
                "related_choice_ids": [f"choice_{index}"],
                "npc_fates": {},
            }
            for index in range(5)
        ],
        "visual_assets": visual_assets,
        "visual_style_guide": {
            "style_keywords": ["Northern Song", "rain night", "historical mystery", "grounded realism"],
            "forbidden_visuals": ["modern wires", "watermark"],
            "color_script": "cold rain against warm lamps",
            "camera": "investigation eye level",
            "era_feature_checklist": ["Song clothing", "wooden station", "paper records"],
            "appearance_lock": {f"npc_{index}": "Song robe, damp sleeves, tired face" for index in range(4)},
        },
        "hotspot_positioning": hotspot_positioning,
        "quality_gate": {
            "required_scene_count": 8,
            "required_npc_count": 4,
            "required_clue_count": 6,
            "scene_approved": 8,
            "npc_approved": 4,
            "clue_approved": 6,
            "rejected": 0,
            "regenerated": 0,
            "blocked": 0,
        },
    }
    package = script_visual_contract.apply(ScriptPackage.model_validate(payload))
    for asset in package.visual_assets:
        if asset.asset_type not in {"scene", "npc", "clue"}:
            continue
        asset.generated_path = f"assets/generated/visuals/generated/{script_id}/{asset.asset_id}.png"
        asset.url = f"/api/scripts/{script_id}/assets/{asset.asset_id}"
        asset.provider = "test"
        asset.model = "test"
        asset.generation_status = "approved"
        asset.quality_gate = ImageQualityGateResult(
            status="approved",
            attempts=1,
            prompt_hash=asset.prompt_hash,
            approved_path=asset.generated_path,
            issues=[],
            rejected_paths=[],
            regenerated_count=0,
        )
    return package.model_dump(mode="json")


def _stage15_assets(asset_type: str, count: int, owner_prefix: str) -> list[dict]:
    return [
        {
            "asset_id": f"asset_{asset_type}_{index}",
            "asset_type": asset_type,
            "owner_id": f"{owner_prefix}_{index}",
            "title": f"{asset_type} asset {index}",
            "prompt": f"Initial {asset_type} prompt {index}",
            "negative_prompt": "modern object, watermark",
            "required_subjects": [f"{asset_type} subject {index}"],
            "era_feature_checklist": ["Song clothing", "wooden station"],
        }
        for index in range(count)
    ]
