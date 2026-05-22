from __future__ import annotations

from copy import deepcopy


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
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "owner_id": owner_id,
        "title": asset_id,
        "prompt": "北宋雨夜驿站，核心物件清晰可见。",
        "negative_prompt": "现代物件，文字水印，占位图",
        "required_subjects": ["军报", "驿站"],
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
