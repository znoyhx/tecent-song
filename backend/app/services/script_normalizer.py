from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import re
from typing import Any


STAGE_SEQUENCE = ["intro", "investigation", "reversal", "choice", "ending"]
STAGE_NAMES = {
    "intro": "入局",
    "investigation": "查证",
    "reversal": "转折",
    "choice": "抉择",
    "ending": "收束",
}
DYNASTY_NAMES = {"song": "北宋", "late_tang": "晚唐"}


class ScriptNormalizationError(ValueError):
    """Raised when model output is too incomplete to normalize safely."""


class ScriptPackageNormalizer:
    """Convert model-shaped JSON into the strict ScriptPackage contract.

    DeepSeek sometimes follows the story intent but uses natural field names such
    as id/name/description or grouped visual_assets. This normalizer repairs that
    shape before Pydantic validation. It does not mark a job successful by itself:
    the strict schema, ScriptSupervisor, image gate, hotspot calibration, and
    import checks still run afterwards.
    """

    def normalize(
        self,
        payload: dict[str, Any],
        *,
        dynasty_id: str,
        keywords: list[str],
        job_id: str | None = None,
        base_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        source = self._unwrap(payload)
        base = self._unwrap(base_payload or {})
        if base:
            source = self._deep_fill_missing(source, base)

        raw_locations = self._require_minimum_items(source.get("locations"), min_count=5, field_name="locations")
        raw_npcs = self._require_minimum_items(source.get("npcs"), min_count=4, field_name="npcs")
        raw_clues = self._require_minimum_items(source.get("clues"), min_count=6, field_name="clues")
        raw_stages = self._list_of_dicts(source.get("stages"))

        location_ids = [self._slug(self._field(item, "location_id", "id", "location"), f"loc_{index}") for index, item in enumerate(raw_locations)]
        npc_ids = [self._slug(self._field(item, "npc_id", "id"), f"npc_{index}") for index, item in enumerate(raw_npcs)]
        clue_ids = [self._slug(self._field(item, "clue_id", "id"), f"clue_{index}") for index, item in enumerate(raw_clues)]

        stage_map = self._stage_map(raw_stages)
        visual_assets = self._normalize_visual_assets(
            source.get("visual_assets"),
            location_ids=location_ids,
            npc_ids=npc_ids,
            clue_ids=clue_ids,
            dynasty_id=dynasty_id,
        )
        asset_by_owner_type = {(asset["asset_type"], asset["owner_id"]): asset["asset_id"] for asset in visual_assets}

        clues = self._normalize_clues(
            raw_clues,
            clue_ids=clue_ids,
            location_ids=location_ids,
            npc_ids=npc_ids,
            stage_map=stage_map,
            asset_by_owner_type=asset_by_owner_type,
        )
        locations, generated_hotspots = self._normalize_locations(
            raw_locations,
            location_ids=location_ids,
            npc_ids=npc_ids,
            clues=clues,
            stage_map=stage_map,
            asset_by_owner_type=asset_by_owner_type,
        )
        npcs = self._normalize_npcs(raw_npcs, npc_ids=npc_ids, clue_ids=clue_ids, asset_by_owner_type=asset_by_owner_type)
        stages = self._normalize_stages(raw_stages, stage_map=stage_map, locations=locations, clues=clues)
        story = self._normalize_story(source.get("story"), clues)
        overview = self._normalize_overview(source.get("script_overview"), source, locations, npcs, story)
        style_guide = self._normalize_style_guide(source.get("visual_style_guide"), dynasty_id, npcs)
        visual_assets = self._enrich_scene_visual_assets(
            visual_assets,
            locations=locations,
            npcs=npcs,
            clues=clues,
            visual_style_guide=style_guide,
            dynasty_id=dynasty_id,
        )

        return {
            "script_id": self._script_id(source.get("script_id") or source.get("id"), dynasty_id=dynasty_id, job_id=job_id),
            "job_id": job_id,
            "dynasty_id": dynasty_id,
            "keywords": [str(item).strip() for item in keywords if str(item).strip()][:8],
            "generation_source": "deepseek",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "script_overview": overview,
            "playable_identities": self._normalize_identities(source.get("playable_identities")),
            "world": self._normalize_world(source.get("world"), dynasty_id),
            "story": story,
            "stages": stages,
            "locations": locations,
            "npcs": npcs,
            "relationships": self._normalize_relationships(source.get("relationships")),
            "clues": clues,
            "clue_graph": self._normalize_clue_graph(source.get("clue_graph"), story["truth_chain_clue_ids"]),
            "deductions": self._normalize_deductions(source.get("deductions")),
            "chapter_sections": self._normalize_chapter_sections(
                source.get("chapter_sections"),
                stage_map=stage_map,
            ),
            "dialogue_rules": self._normalize_dialogue_rules(source.get("dialogue_rules"), stage_map),
            "choices": self._normalize_choices(source.get("choices")),
            "endings": self._normalize_endings(source.get("endings"), clue_ids),
            "visual_assets": visual_assets,
            "visual_style_guide": style_guide,
            "hotspot_positioning": self._normalize_hotspots(
                source.get("hotspot_positioning"),
                generated_hotspots=generated_hotspots,
                locations=locations,
                asset_by_owner_type=asset_by_owner_type,
            ),
            "quality_gate": {
                "required_scene_count": 8,
                "required_npc_count": 4,
                "required_clue_count": 6,
                "scene_approved": 0,
                "npc_approved": 0,
                "clue_approved": 0,
                "rejected": 0,
                "regenerated": 0,
                "blocked": 0,
            },
        }

    def _unwrap(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        current = deepcopy(payload)
        while isinstance(current.get("script_package"), dict):
            current = deepcopy(current["script_package"])
        return current

    def _deep_fill_missing(self, source: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
        result = deepcopy(source)
        for key, base_value in base.items():
            if key not in result or result[key] in (None, "", [], {}):
                result[key] = deepcopy(base_value)
            elif isinstance(result[key], dict) and isinstance(base_value, dict):
                result[key] = self._deep_fill_missing(result[key], base_value)
        return result

    def _normalize_overview(self, raw: Any, source: dict[str, Any], locations: list[dict[str, Any]], npcs: list[dict[str, Any]], story: dict[str, Any]) -> dict[str, Any]:
        item = raw if isinstance(raw, dict) else {}
        title = self._text(item.get("title"), source.get("title"), story.get("surface_event"), default="生成剧本")
        case_summary = self._text(item.get("case_summary"), item.get("description"), item.get("pitch"), story.get("surface_event"), default="一桩牵涉文书、人物证言与现场物证的疑案正在展开。")
        return {
            "title": title,
            "logline": self._text(item.get("logline"), item.get("description"), item.get("pitch"), default=case_summary),
            "case_summary": case_summary,
            "opening_location": self._text(item.get("opening_location"), locations[0]["name"] if locations else None, default="案发现场"),
            "public_objective": self._text(item.get("public_objective"), default="查明事件经过，找出关键证据。"),
            "major_locations": self._string_list(item.get("major_locations")) or [location["name"] for location in locations[:5]],
            "major_npcs": self._string_list(item.get("major_npcs")) or [npc["name"] for npc in npcs[:4]],
            "player_briefing": self._text(item.get("player_briefing"), default="你需要循证调查，避免在早期逼问最终真相。"),
        }

    def _normalize_identities(self, raw: Any) -> list[dict[str, Any]]:
        identities = self._require_minimum_items(raw, min_count=1, field_name="playable_identities")
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(identities):
            identity_id = self._slug(self._field(item, "identity_id", "id"), f"identity_{index}")
            description = self._text(item.get("description"), item.get("background"), default="受命查明案情的人。")
            normalized.append(
                {
                    "identity_id": identity_id,
                    "display_name": self._text(item.get("display_name"), item.get("name"), default=f"可选身份{index + 1}"),
                    "description": description,
                    "social_rank": item.get("social_rank") if item.get("social_rank") in {"low", "middle", "high"} else "middle",
                    "relation_to_case": self._text(item.get("relation_to_case"), default="有正当理由接触案发现场。"),
                    "motive": self._text(item.get("motive"), default="查清疑案，洗清无辜者嫌疑。"),
                    "permissions": self._string_list(item.get("permissions")) or ["查验现场", "询问相关人物", "整理线索"],
                    "limitations": self._string_list(item.get("limitations")) or ["不能越权定罪", "不能提前公开最终判断"],
                    "background": self._text(item.get("background"), description, default=description),
                    "tags": self._string_list(item.get("tags")) or ["调查", "文书"],
                    "is_default": bool(item.get("is_default", index == 0)),
                }
            )
        return normalized

    def _normalize_world(self, raw: Any, dynasty_id: str) -> dict[str, Any]:
        if not isinstance(raw, dict) or not raw:
            raise ScriptNormalizationError("SCRIPT_WORLD_MISSING: DeepSeek 未输出 world，拒绝用本地默认世界观补齐。")
        item = raw
        dynasty_name = DYNASTY_NAMES.get(dynasty_id, dynasty_id)
        era_name = self._text(item.get("era_name"), item.get("name"), default="")
        location_region = self._text(item.get("location_region"), item.get("description"), item.get("name"), default="")
        missing = []
        if not era_name:
            missing.append("era_name/name")
        if not location_region:
            missing.append("location_region/description")
        if missing:
            raise ScriptNormalizationError(f"SCRIPT_WORLD_INCOMPLETE: world 缺少 {', '.join(missing)}。")
        return {
            "dynasty_id": dynasty_id,
            "dynasty_name": self._text(item.get("dynasty_name"), item.get("dynasty"), default=dynasty_name),
            "era_name": era_name,
            "year_hint": self._text(item.get("year_hint"), default=f"{dynasty_name}年间"),
            "location_region": location_region,
            "rules": self._string_list(item.get("rules")) or ["证据需由现场、口供和文书共同支撑。"],
            "forbidden_terms": self._string_list(item.get("forbidden_terms")) or ["手机", "电话", "电报", "火车", "报纸", "公司"],
        }

    def _normalize_story(self, raw: Any, clues: list[dict[str, Any]]) -> dict[str, Any]:
        if not isinstance(raw, dict) or not raw:
            raise ScriptNormalizationError("SCRIPT_STORY_MISSING: DeepSeek 未输出 story，拒绝用本地默认案情补齐。")
        item = raw
        surface_event = self._text(item.get("surface_event"), item.get("summary"), default="")
        hidden_truth = self._text(item.get("hidden_truth"), default="")
        truth_chain = self._string_list(item.get("truth_chain_clue_ids"))
        missing = []
        if not surface_event:
            missing.append("surface_event/summary")
        if not hidden_truth:
            missing.append("hidden_truth")
        if len(truth_chain) < 3:
            missing.append("truth_chain_clue_ids")
        if missing:
            raise ScriptNormalizationError(f"SCRIPT_STORY_INCOMPLETE: story 缺少 {', '.join(missing)}。")
        return {
            "surface_event": surface_event,
            "hidden_truth": hidden_truth,
            "themes": self._string_list(item.get("themes")) or ["文书", "证据", "人心"],
            "culprit_boundary": self._text(item.get("culprit_boundary"), default="真凶必须通过完整线索链才能确认，早期证言只能提供侧面信息。"),
            "truth_chain_clue_ids": truth_chain[: max(3, min(len(truth_chain), 6))],
        }

    def _normalize_stages(self, raw_stages: list[dict[str, Any]], *, stage_map: dict[str, str], locations: list[dict[str, Any]], clues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        location_ids = [location["location_id"] for location in locations]
        first_location = location_ids[0]
        stages: list[dict[str, Any]] = []
        for order, stage_id in enumerate(STAGE_SEQUENCE):
            raw = raw_stages[order] if order < len(raw_stages) else {}
            stage_clues = self._string_list(raw.get("key_clue_ids")) or self._string_list(raw.get("clues_unlocked"))
            stage_clues = [clue_id for clue_id in stage_clues if clue_id in {clue["clue_id"] for clue in clues}]
            available = self._string_list(raw.get("available_location_ids")) or location_ids
            available = [location_id for location_id in available if location_id in location_ids] or location_ids
            entry = self._slug(raw.get("entry_location_id"), first_location)
            if entry not in location_ids:
                entry = available[0]
            stages.append(
                {
                    "stage_id": stage_id,
                    "name": self._text(raw.get("name"), default=STAGE_NAMES[stage_id]),
                    "order": order,
                    "goal": self._text(raw.get("goal"), raw.get("description"), default=f"推进{STAGE_NAMES[stage_id]}阶段。"),
                    "entry_location_id": entry,
                    "unlock_conditions": self._string_list(raw.get("unlock_conditions")),
                    "available_location_ids": available,
                    "key_clue_ids": stage_clues,
                }
            )
        return stages

    def _normalize_locations(
        self,
        raw_locations: list[dict[str, Any]],
        *,
        location_ids: list[str],
        npc_ids: list[str],
        clues: list[dict[str, Any]],
        stage_map: dict[str, str],
        asset_by_owner_type: dict[tuple[str, str], str],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        clues_by_location: dict[str, list[dict[str, Any]]] = {}
        for clue in clues:
            location_id = clue.get("source_location_id") or location_ids[0]
            clues_by_location.setdefault(location_id, []).append(clue)

        generated_hotspots: list[dict[str, Any]] = []
        normalized: list[dict[str, Any]] = []
        hotspot_index = 0
        for index, item in enumerate(raw_locations):
            location_id = location_ids[index]
            stage_ids = [self._stage_mapped(value, stage_map) for value in self._string_list(item.get("stage_ids"))]
            stage_ids = [value for value in stage_ids if value in STAGE_SEQUENCE] or STAGE_SEQUENCE[:4]
            location_npcs = [self._slug(value, "") for value in self._string_list(item.get("npc_ids"))]
            if not location_npcs and npc_ids:
                location_npcs = [npc_ids[index % len(npc_ids)]]
            location_npcs = [value for value in location_npcs if value in npc_ids]
            hotspots: list[dict[str, Any]] = []
            for clue in clues_by_location.get(location_id, []):
                hotspot_id = f"hotspot_{hotspot_index}"
                hotspot_index += 1
                required_stage = clue["stage_available"][0] if clue.get("stage_available") else "investigation"
                hotspots.append(
                    {
                        "hotspot_id": hotspot_id,
                        "label": clue["highlight_text"],
                        "description": f"与“{clue['title']}”有关的可疑痕迹。",
                        "clue_ids": [clue["clue_id"]],
                        "required_stage": required_stage,
                        "required_clue_ids": [],
                        "investigation_text": f"你仔细查验后，发现了“{clue['title']}”。",
                        "repeat_text": "这里已经查验过，痕迹仍与先前判断一致。",
                    }
                )
                generated_hotspots.append({"location_id": location_id, "hotspot_id": hotspot_id, "clue_id": clue["clue_id"]})
            normalized.append(
                {
                    "location_id": location_id,
                    "name": self._text(item.get("name"), default=f"场景{index + 1}"),
                    "description": self._text(item.get("description"), default="这里留有与案件有关的痕迹。"),
                    "scene_text": self._text(item.get("scene_text"), item.get("description"), default="四周的细节等待进一步查验。"),
                    "stage_ids": stage_ids,
                    "npc_ids": location_npcs,
                    "hotspots": hotspots,
                    "visual_asset_id": asset_by_owner_type.get(("scene", location_id), f"asset_scene_{index}"),
                }
            )
        return normalized, generated_hotspots

    def _normalize_npcs(self, raw_npcs: list[dict[str, Any]], *, npc_ids: list[str], clue_ids: list[str], asset_by_owner_type: dict[tuple[str, str], str]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(raw_npcs):
            npc_id = npc_ids[index]
            secret = self._text(item.get("hidden_motive"), item.get("secret"), default="隐瞒了一段与案情相关的旧事。")
            normalized.append(
                {
                    "npc_id": npc_id,
                    "name": self._text(item.get("name"), default=f"人物{index + 1}"),
                    "public_identity": self._text(item.get("public_identity"), item.get("role"), item.get("description"), default="案发相关人物"),
                    "appearance": self._text(item.get("appearance"), item.get("description"), default="衣着符合时代身份，神情谨慎。"),
                    "personality": self._text(item.get("personality"), default="谨慎"),
                    "background_suspicion": self._text(item.get("background_suspicion"), item.get("secret"), default="对部分事实含糊其辞。"),
                    "case_connection": self._text(item.get("case_connection"), item.get("role"), default="案发前后曾出现在关键地点。"),
                    "event_behavior": self._text(item.get("event_behavior"), default="声称只知道公开经过。"),
                    "public_goal": self._text(item.get("public_goal"), default="保住自身名声与差事。"),
                    "hidden_motive": secret,
                    "known_info": self._string_list(item.get("known_info")) or ["知道案发当夜的公开经过。"],
                    "unknown_info": self._string_list(item.get("unknown_info")) or ["不了解完整真相链。"],
                    "forbidden_disclosure": self._string_list(item.get("forbidden_disclosure")) or ["不得在早期直接说出最终真相、真凶身份或结局条件。"],
                    "speaking_style": self._text(item.get("speaking_style"), default="短句、谨慎、避重就轻。"),
                    "initial_trust": int(item.get("initial_trust", 0) or 0),
                    "emotion_state": self._text(item.get("emotion_state"), default="guarded"),
                    "releasable_clue_ids": [clue_id for clue_id in self._string_list(item.get("releasable_clue_ids")) if clue_id in clue_ids],
                    "stage_limits": self._stage_limits(item.get("stage_limits")),
                    "visual_asset_id": asset_by_owner_type.get(("npc", npc_id), f"asset_npc_{index}"),
                }
            )
        return normalized

    def _normalize_clues(
        self,
        raw_clues: list[dict[str, Any]],
        *,
        clue_ids: list[str],
        location_ids: list[str],
        npc_ids: list[str],
        stage_map: dict[str, str],
        asset_by_owner_type: dict[tuple[str, str], str],
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(raw_clues):
            clue_id = clue_ids[index]
            source_location = self._slug(self._field(item, "source_location_id", "location"), location_ids[min(index, len(location_ids) - 1)])
            if source_location not in location_ids:
                source_location = location_ids[min(index, len(location_ids) - 1)]
            raw_stage_values = self._string_list(item.get("stage_available")) or self._string_list(item.get("stages")) or [item.get("stage")]
            stages = [self._stage_mapped(value, stage_map) for value in raw_stage_values if value]
            stages = [stage for stage in stages if stage in STAGE_SEQUENCE] or ["intro", "investigation", "reversal", "choice"]
            source_npc = self._slug(item.get("source_npc_id"), "")
            normalized.append(
                {
                    "clue_id": clue_id,
                    "title": self._text(item.get("title"), item.get("name"), default=f"线索{index + 1}"),
                    "type": self._text(item.get("type"), default="物证"),
                    "is_key": bool(item.get("is_key", index < 6)),
                    "source_location_id": source_location,
                    "source_npc_id": source_npc if source_npc in npc_ids else None,
                    "highlight_text": self._text(item.get("highlight_text"), item.get("name"), default=f"线索{index + 1}"),
                    "display_text": self._text(item.get("display_text"), item.get("description"), default="一条可用于推理的证据。"),
                    "detail": self._text(item.get("detail"), item.get("description"), default="这条线索能帮助还原案发过程。"),
                    "stage_available": stages,
                    "unlock_conditions": item.get("unlock_conditions") if isinstance(item.get("unlock_conditions"), dict) else {},
                    "effects": item.get("effects") if isinstance(item.get("effects"), dict) else {"scores": {"truth": 1}},
                    "related_clue_ids": [value for value in self._string_list(item.get("related_clue_ids")) if value in clue_ids],
                    "ending_tags": self._string_list(item.get("ending_tags")),
                    "forbidden_before_stage": item.get("forbidden_before_stage"),
                    "visual_asset_id": asset_by_owner_type.get(("clue", clue_id), f"asset_clue_{index}"),
                }
            )
        return normalized

    def _normalize_relationships(self, raw: Any) -> list[dict[str, Any]]:
        items = self._list_of_dicts(raw)
        return [
            {
                "source_id": self._slug(self._field(item, "source_id", "from"), "npc_0"),
                "target_id": self._slug(self._field(item, "target_id", "to"), "npc_1"),
                "relation": self._text(item.get("relation"), item.get("type"), default="相关"),
                "public_state": self._text(item.get("public_state"), item.get("description"), default="表面关系尚可。"),
                "hidden_state": self._text(item.get("hidden_state"), default=""),
            }
            for item in items
        ]

    def _normalize_clue_graph(self, raw: Any, truth_chain: list[str]) -> list[dict[str, Any]]:
        items = self._list_of_dicts(raw)
        rules: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            required = self._string_list(item.get("required_clue_ids"))
            if not required and "nodes" in item:
                required = self._string_list(item.get("nodes"))
            if required:
                rules.append(
                    {
                        "rule_id": self._slug(self._field(item, "rule_id", "id"), f"combo_{index}"),
                        "required_clue_ids": required,
                        "result_title": self._text(item.get("result_title"), default="线索链成立"),
                        "result_text": self._text(item.get("result_text"), item.get("relation"), default="这些线索可以互相印证。"),
                        "effects": item.get("effects") if isinstance(item.get("effects"), dict) else {"flags": ["truth_chain_confirmed"]},
                    }
                )
        if not rules and truth_chain:
            rules.append(
                {
                    "rule_id": "combo_truth_chain",
                    "required_clue_ids": truth_chain[: max(3, min(len(truth_chain), 6))],
                    "result_title": "真相链成立",
                    "result_text": "关键线索能够串联出案发经过。",
                    "effects": {"flags": ["truth_chain_confirmed"]},
                }
            )
        return rules

    def _normalize_dialogue_rules(self, raw: Any, stage_map: dict[str, str]) -> list[dict[str, Any]]:
        items = self._list_of_dicts(raw)
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            normalized.append(
                {
                    "dialogue_id": self._slug(self._field(item, "dialogue_id", "id"), f"dialogue_{index}"),
                    "npc_id": self._slug(item.get("npc_id"), f"npc_{index % 4}"),
                    "stage": self._stage_mapped(item.get("stage"), stage_map),
                    "priority": int(item.get("priority", 0) or 0),
                    "trigger_keywords": self._string_list(item.get("trigger_keywords")) or self._string_list(item.get("condition")),
                    "presented_clue_ids": self._string_list(item.get("presented_clue_ids")),
                    "response": self._text(item.get("response"), item.get("dialogue"), default="此人谨慎回应，没有直接说出最终真相。"),
                    "released_clue_ids": self._string_list(item.get("released_clue_ids")),
                    "suggested_questions": self._string_list(item.get("suggested_questions")) or ["继续追问时间", "询问可疑物件"],
                }
            )
        return normalized

    def _normalize_deductions(self, raw: Any) -> list[dict[str, Any]]:
        items = self._list_of_dicts(raw)
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            question = self._text(item.get("question"), item.get("title"), item.get("description"), default="")
            required = self._string_list(item.get("required_clue_ids"))
            correct = self._string_list(item.get("correct_clue_ids")) or required
            if not question or not correct:
                continue
            deduction_id = self._slug(self._field(item, "deduction_id", "id"), f"deduction_{index}")
            normalized.append(
                {
                    "deduction_id": deduction_id,
                    "question": question,
                    "required_clue_ids": required,
                    "correct_clue_ids": correct,
                    "wrong_feedback": self._text(item.get("wrong_feedback"), default="这些线索还不能支持这个判断。"),
                    "success_text": self._text(item.get("success_text"), item.get("result_text"), default="这组证据能够支撑该推理。"),
                    "effects": item.get("effects") if isinstance(item.get("effects"), dict) else {"flags": [f"{deduction_id}_solved"]},
                }
            )
        return normalized

    def _normalize_chapter_sections(self, raw: Any, *, stage_map: dict[str, str]) -> list[dict[str, Any]]:
        items = self._list_of_dicts(raw)
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            title = self._text(item.get("title"), item.get("name"), default="")
            scene_id = self._slug(self._field(item, "scene_id", "location_id", "location"), "")
            if not title or not scene_id:
                continue
            section_id = self._slug(self._field(item, "section_id", "id"), f"section_{index}")
            normalized.append(
                {
                    "section_id": section_id,
                    "stage": self._stage_mapped(item.get("stage"), stage_map),
                    "title": title,
                    "trigger_conditions": self._string_list(item.get("trigger_conditions")),
                    "scene_id": scene_id,
                    "npc_ids": self._string_list(item.get("npc_ids")),
                    "hotspot_ids": self._string_list(item.get("hotspot_ids")),
                    "clue_ids": self._string_list(item.get("clue_ids")),
                    "next_section_ids": self._string_list(item.get("next_section_ids")),
                    "goal": self._text(item.get("goal"), item.get("objective"), default=title),
                    "display_text": self._text(item.get("display_text"), item.get("description"), default=title),
                }
            )
        return normalized

    def _normalize_choices(self, raw: Any) -> list[dict[str, Any]]:
        items = self._require_minimum_items(raw, min_count=1, field_name="choices")
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            choice_id = self._slug(self._field(item, "choice_id", "id"), f"choice_{index}")
            normalized.append(
                {
                    "choice_id": choice_id,
                    "title": self._text(item.get("title"), item.get("description"), default=f"抉择{index + 1}"),
                    "description": self._text(item.get("description"), item.get("outcome"), default="根据证据作出选择。"),
                    "effects": item.get("effects") if isinstance(item.get("effects"), dict) else {"flags": [choice_id]},
                }
            )
        return normalized

    def _normalize_endings(self, raw: Any, clue_ids: list[str]) -> list[dict[str, Any]]:
        items = self._require_minimum_items(raw, min_count=1, field_name="endings")
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            ending_id = self._slug(self._field(item, "ending_id", "id"), f"ending_{index}")
            result_summary = self._text(item.get("result_summary"), item.get("description"), item.get("ending_text"), default="")
            ending_text = self._text(item.get("ending_text"), item.get("description"), item.get("result_summary"), default="")
            history_echo = self._text(item.get("history_echo"), default="")
            missing = []
            if not result_summary:
                missing.append("result_summary/description")
            if not ending_text:
                missing.append("ending_text/description")
            if not history_echo:
                missing.append("history_echo")
            if missing:
                raise ScriptNormalizationError(f"SCRIPT_ENDING_INCOMPLETE: ending {ending_id} 缺少 {', '.join(missing)}。")
            condition = (
                item.get("conditions")
                if isinstance(item.get("conditions"), dict) and item.get("conditions")
                else {"condition_text": self._text(item.get("condition"), default="收集关键线索后可达。")}
            )
            normalized.append(
                {
                    "ending_id": ending_id,
                    "title": self._text(item.get("title"), item.get("name"), default=f"结局{index + 1}"),
                    "priority": int(item.get("priority", index) or 0),
                    "conditions": condition,
                    "required_flags": self._string_list(item.get("required_flags")),
                    "blocked_flags": self._string_list(item.get("blocked_flags")),
                    "result_summary": result_summary,
                    "ending_text": ending_text,
                    "history_echo": history_echo,
                    "related_clue_ids": [clue_id for clue_id in self._string_list(item.get("related_clue_ids")) if clue_id in clue_ids] or clue_ids[:1],
                    "related_choice_ids": self._string_list(item.get("related_choice_ids")),
                    "npc_fates": item.get("npc_fates") if isinstance(item.get("npc_fates"), dict) else {},
                    "visual_asset_id": item.get("visual_asset_id"),
                }
            )
        return normalized

    def _normalize_visual_assets(
        self,
        raw: Any,
        *,
        location_ids: list[str],
        npc_ids: list[str],
        clue_ids: list[str],
        dynasty_id: str,
    ) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        if isinstance(raw, dict):
            grouped = [("scene", raw.get("scenes")), ("npc", raw.get("npcs")), ("clue", raw.get("clues")), ("ending", raw.get("endings"))]
            for asset_type, group in grouped:
                for item in self._list_of_dicts(group):
                    assets.append(self._asset_from_raw(item, asset_type, location_ids, npc_ids, clue_ids, dynasty_id))
        else:
            for item in self._list_of_dicts(raw):
                asset_type = item.get("asset_type") if item.get("asset_type") in {"scene", "npc", "clue", "ending"} else "clue"
                assets.append(self._asset_from_raw(item, asset_type, location_ids, npc_ids, clue_ids, dynasty_id))

        assets = self._dedupe_assets(assets)
        self._require_assets_for("scene", location_ids[:5], assets)
        self._require_assets_for("npc", npc_ids[:4], assets)
        self._require_assets_for("clue", clue_ids[:6], assets)
        return assets

    def _enrich_scene_visual_assets(
        self,
        assets: list[dict[str, Any]],
        *,
        locations: list[dict[str, Any]],
        npcs: list[dict[str, Any]],
        clues: list[dict[str, Any]],
        visual_style_guide: dict[str, Any],
        dynasty_id: str,
    ) -> list[dict[str, Any]]:
        dynasty_name = DYNASTY_NAMES.get(dynasty_id, dynasty_id)
        npc_by_id = {npc["npc_id"]: npc for npc in npcs}
        clue_by_id = {clue["clue_id"]: clue for clue in clues}
        location_by_id = {location["location_id"]: location for location in locations}
        location_by_scene_asset = {location["visual_asset_id"]: location for location in locations}
        appearance_lock = visual_style_guide.get("appearance_lock") if isinstance(visual_style_guide.get("appearance_lock"), dict) else {}
        style_keywords = self._string_list(visual_style_guide.get("style_keywords")) or [dynasty_name, "写实", "悬疑"]
        color_script = self._text(visual_style_guide.get("color_script"), default="低饱和雨夜与暖灯对照。")
        camera = self._text(visual_style_guide.get("camera"), default="平视调查视角。")
        enriched: list[dict[str, Any]] = []

        for asset in assets:
            if asset.get("asset_type") != "scene":
                enriched.append(asset)
                continue

            location = location_by_id.get(asset.get("owner_id", "")) or location_by_scene_asset.get(asset.get("asset_id", ""))
            if not location:
                enriched.append(asset)
                continue

            scene_npcs = [npc_by_id[npc_id] for npc_id in location.get("npc_ids", []) if npc_id in npc_by_id]
            clue_ids: list[str] = []
            for hotspot in location.get("hotspots", []):
                clue_ids.extend(self._string_list(hotspot.get("clue_ids")))
            scene_clues = [clue_by_id[clue_id] for clue_id in clue_ids if clue_id in clue_by_id][:4]

            npc_phrase = "、".join(
                f"{npc['name']}（{npc['public_identity']}，{appearance_lock.get(npc['npc_id']) or npc['appearance']}）"
                for npc in scene_npcs
            )
            clue_phrase = "、".join(clue["title"] for clue in scene_clues)
            prompt_parts = [
                "这是一张人物与场景一体生成的完整主舞台图，不是空场景，也不是背景图加后期立绘。",
                f"地点：{location['name']}；{location['description']}",
                f"统一风格：{'、'.join(style_keywords)}；{color_script}；{camera}",
            ]
            if npc_phrase:
                prompt_parts.append(f"画面中必须自然出现可交互人物：{npc_phrase}。人物要融入同一透视、同一光源和同一时代服饰。")
            if clue_phrase:
                prompt_parts.append(f"画面中必须清楚出现可点击线索物件：{clue_phrase}。线索物件要可定位、无遮挡、不能只是装饰。")
            prompt_parts.append("保留低饱和中国历史悬疑气质，主体清晰，符合时代建筑、服饰、器物，不含现代物件、文字水印、空白背景。")

            current_prompt = self._text(asset.get("prompt"), default=f"{dynasty_name}历史悬疑调查场景")
            if "人物与场景一体生成" not in current_prompt:
                asset["prompt"] = f"{current_prompt}\n" + "\n".join(prompt_parts)

            required_subjects = self._string_list(asset.get("required_subjects"))
            required_subjects.extend([npc["name"] for npc in scene_npcs])
            required_subjects.extend([clue["title"] for clue in scene_clues])
            if scene_npcs:
                required_subjects.append("人物与场景一体生成")
            if scene_clues:
                required_subjects.append("可点击线索物件")
            asset["required_subjects"] = self._dedupe_strings(required_subjects)
            enriched.append(asset)

        return enriched

    def _asset_from_raw(self, item: dict[str, Any], asset_type: str, location_ids: list[str], npc_ids: list[str], clue_ids: list[str], dynasty_id: str) -> dict[str, Any]:
        raw_id = self._field(item, "asset_id", "id")
        owner_id = self._slug(item.get("owner_id"), "")
        if not owner_id:
            owner_id = self._infer_owner_id(raw_id, asset_type, location_ids, npc_ids, clue_ids)
        if not owner_id:
            pools = {"scene": location_ids, "npc": npc_ids, "clue": clue_ids}
            pool = pools.get(asset_type, clue_ids)
            owner_id = pool[0] if pool else "owner_0"
        asset_id = self._slug(raw_id, f"asset_{asset_type}_{owner_id}")
        return {
            "asset_id": asset_id,
            "asset_type": asset_type,
            "owner_id": owner_id,
            "title": self._text(item.get("title"), item.get("name"), default=asset_id),
            "prompt": self._visual_prompt(item.get("prompt"), asset_type, dynasty_id),
            "negative_prompt": self._text(item.get("negative_prompt"), default="现代物件、文字水印、空白图、错朝代服饰、低清晰度"),
            "required_subjects": self._string_list(item.get("required_subjects")) or self._default_subjects(asset_type),
            "era_feature_checklist": self._string_list(item.get("era_feature_checklist")) or self._era_features(dynasty_id),
            "prompt_hash": item.get("prompt_hash"),
            "generated_path": item.get("generated_path"),
            "url": item.get("url"),
            "provider": item.get("provider"),
            "model": item.get("model"),
            "generation_status": item.get("generation_status") if item.get("generation_status") in {"pending", "generated", "approved", "rejected", "blocked"} else "pending",
            "quality_gate": item.get("quality_gate") if isinstance(item.get("quality_gate"), dict) else {"status": "pending", "attempts": 0, "issues": []},
        }

    def _normalize_style_guide(self, raw: Any, dynasty_id: str, npcs: list[dict[str, Any]]) -> dict[str, Any]:
        item = raw if isinstance(raw, dict) else {}
        dynasty_name = DYNASTY_NAMES.get(dynasty_id, dynasty_id)
        appearance_lock = item.get("appearance_lock") if isinstance(item.get("appearance_lock"), dict) else {npc["npc_id"]: npc["appearance"] for npc in npcs[:4]}
        return {
            "style_keywords": self._string_list(item.get("style_keywords")) or [dynasty_name, "写实", "悬疑", "可调查场景"],
            "forbidden_visuals": self._string_list(item.get("forbidden_visuals")) or ["现代电线", "塑料", "水印", "空白背景", "错朝代服饰"],
            "color_script": self._text(item.get("color_script"), item.get("lighting"), default="冷色雨夜与暖色灯火对照。"),
            "camera": self._text(item.get("camera"), default="平视调查视角，核心物件清楚可辨。"),
            "era_feature_checklist": self._string_list(item.get("era_feature_checklist")) or self._era_features(dynasty_id),
            "appearance_lock": appearance_lock,
        }

    def _normalize_hotspots(
        self,
        raw: Any,
        *,
        generated_hotspots: list[dict[str, Any]],
        locations: list[dict[str, Any]],
        asset_by_owner_type: dict[tuple[str, str], str],
    ) -> list[dict[str, Any]]:
        raw_items = self._list_of_dicts(raw)
        location_ids = [location["location_id"] for location in locations]
        result: list[dict[str, Any]] = []
        for index, generated in enumerate(generated_hotspots[: max(6, len(generated_hotspots))]):
            raw_item = raw_items[index] if index < len(raw_items) else {}
            location_id = self._slug(self._field(raw_item, "location_id", "location"), generated["location_id"])
            if location_id not in location_ids:
                location_id = generated["location_id"]
            result.append(
                {
                    "location_id": location_id,
                    "hotspot_id": generated["hotspot_id"],
                    "visual_asset_id": asset_by_owner_type.get(("scene", location_id), locations[0]["visual_asset_id"]),
                    "clue_id": generated.get("clue_id"),
                    "anchor_point": self._point(raw_item.get("anchor_point"), index),
                    "bbox": self._bbox(raw_item.get("bbox"), index),
                    "calibration_status": "pending",
                    "calibrated_against_path": None,
                }
            )
        return result[: max(6, len(result))]

    def _stage_map(self, raw_stages: list[dict[str, Any]]) -> dict[str, str]:
        mapping = {stage: stage for stage in STAGE_SEQUENCE}
        for index, item in enumerate(raw_stages):
            raw_id = self._field(item, "stage_id", "id")
            if raw_id:
                mapping[str(raw_id)] = STAGE_SEQUENCE[min(index, len(STAGE_SEQUENCE) - 1)]
        mapping.update({"stage1": "intro", "stage2": "investigation", "stage3": "reversal", "stage4": "choice", "stage5": "ending"})
        return mapping

    def _stage_mapped(self, value: Any, stage_map: dict[str, str]) -> str:
        if value is None:
            return "investigation"
        return stage_map.get(str(value), str(value) if str(value) in STAGE_SEQUENCE else "investigation")

    def _stage_limits(self, raw: Any) -> dict[str, str]:
        if not isinstance(raw, dict) or not raw:
            return {"intro": "只谈公开事实。"}
        normalized: dict[str, str] = {}
        for key, value in raw.items():
            stage_key = str(key)
            if isinstance(value, str):
                normalized[stage_key] = value
            elif isinstance(value, list):
                normalized[stage_key] = "、".join(str(item) for item in value)
            elif isinstance(value, dict):
                parts = []
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, list):
                        nested_text = "、".join(str(item) for item in nested_value)
                    else:
                        nested_text = str(nested_value)
                    parts.append(f"{nested_key}: {nested_text}")
                normalized[stage_key] = "；".join(parts) or "只谈公开事实。"
            else:
                normalized[stage_key] = str(value)
        return normalized or {"intro": "只谈公开事实。"}

    def _require_minimum_items(self, raw: Any, *, min_count: int, field_name: str) -> list[dict[str, Any]]:
        items = self._list_of_dicts(raw)
        if len(items) < min_count:
            raise ScriptNormalizationError(
                f"SCRIPT_CONTENT_INCOMPLETE: {field_name} 至少需要 {min_count} 项，DeepSeek 只返回 {len(items)} 项。"
            )
        return items

    def _require_assets_for(self, asset_type: str, owners: list[str], assets: list[dict[str, Any]]) -> None:
        existing = {(asset["asset_type"], asset["owner_id"]) for asset in assets}
        missing = [owner_id for owner_id in owners if (asset_type, owner_id) not in existing]
        if missing:
            raise ScriptNormalizationError(
                f"SCRIPT_VISUAL_ASSETS_INCOMPLETE: visual_assets 缺少 {asset_type} 资产映射：{', '.join(missing)}。"
            )

    def _dedupe_assets(self, assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for asset in assets:
            asset_id = asset["asset_id"]
            if asset_id in seen:
                suffix = 2
                while f"{asset_id}_{suffix}" in seen:
                    suffix += 1
                asset["asset_id"] = f"{asset_id}_{suffix}"
            seen.add(asset["asset_id"])
            result.append(asset)
        return result

    def _infer_owner_id(self, raw_id: Any, asset_type: str, location_ids: list[str], npc_ids: list[str], clue_ids: list[str]) -> str:
        value = self._slug(raw_id, "")
        pools = {"scene": location_ids, "npc": npc_ids, "clue": clue_ids}
        for candidate in pools.get(asset_type, []):
            if value == candidate or value.endswith(candidate) or candidate in value:
                return candidate
        if value.endswith("_asset"):
            stripped = value.removesuffix("_asset")
            if stripped in pools.get(asset_type, []):
                return stripped
        return ""

    def _script_id(self, raw: Any, *, dynasty_id: str, job_id: str | None) -> str:
        base = self._slug(raw, f"generated_{dynasty_id}")
        if job_id and not base.endswith(job_id[-6:]):
            base = f"{base}_{job_id[-6:]}"
        return base[:80]

    def _point(self, raw: Any, index: int) -> dict[str, float]:
        if isinstance(raw, dict):
            return {"x": self._clamp(raw.get("x"), 0.25 + (index % 4) * 0.15), "y": self._clamp(raw.get("y"), 0.38 + (index % 3) * 0.12)}
        if isinstance(raw, list) and len(raw) >= 2:
            return {"x": self._clamp(raw[0], 0.5), "y": self._clamp(raw[1], 0.5)}
        return {"x": self._clamp(0.25 + (index % 4) * 0.15, 0.5), "y": self._clamp(0.38 + (index % 3) * 0.12, 0.5)}

    def _bbox(self, raw: Any, index: int) -> dict[str, float]:
        if isinstance(raw, dict):
            x = self._clamp(raw.get("x"), 0.2)
            y = self._clamp(raw.get("y"), 0.3)
            width = self._size(raw.get("width"), 0.16)
            height = self._size(raw.get("height"), 0.16)
        elif isinstance(raw, list) and len(raw) >= 4:
            x = self._clamp(raw[0], 0.2)
            y = self._clamp(raw[1], 0.3)
            third = self._clamp(raw[2], x + 0.16)
            fourth = self._clamp(raw[3], y + 0.16)
            if third > x and fourth > y:
                width = self._size(third - x, 0.16)
                height = self._size(fourth - y, 0.16)
            else:
                width = self._size(raw[2], 0.16)
                height = self._size(raw[3], 0.16)
        else:
            x = self._clamp(0.17 + (index % 4) * 0.15, 0.2)
            y = self._clamp(0.3 + (index % 3) * 0.12, 0.3)
            width = 0.16
            height = 0.16
        width = min(width, max(0.02, 0.98 - x))
        height = min(height, max(0.02, 0.98 - y))
        return {"x": x, "y": y, "width": width, "height": height}

    def _field(self, item: dict[str, Any], *names: str) -> Any:
        for name in names:
            value = item.get(name)
            if value not in (None, "", [], {}):
                return value
        return None

    def _text(self, *values: Any, default: str) -> str:
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, list) and value:
                return "、".join(str(item).strip() for item in value if str(item).strip())
        return default

    def _string_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            parts = re.split(r"[，,、;\n]+", value)
            return [part.strip() for part in parts if part.strip()]
        return [str(value).strip()] if str(value).strip() else []

    def _dedupe_strings(self, values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            text = str(value).strip()
            if text and text not in seen:
                seen.add(text)
                result.append(text)
        return result

    def _list_of_dicts(self, value: Any) -> list[dict[str, Any]]:
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            if "edges" in value and isinstance(value.get("edges"), list):
                return [value]
            return [value]
        return []

    def _slug(self, value: Any, fallback: str) -> str:
        if value is None:
            return fallback
        text = str(value).strip().lower()
        text = re.sub(r"[^a-z0-9_\-]+", "_", text)
        text = re.sub(r"_+", "_", text).strip("_")
        return text or fallback

    def _clamp(self, value: Any, default: float) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = float(default)
        return max(0.0, min(1.0, round(number, 4)))

    def _size(self, value: Any, default: float) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = float(default)
        return max(0.02, min(1.0, round(number, 4)))

    def _visual_prompt(self, raw: Any, asset_type: str, dynasty_id: str) -> str:
        dynasty_name = DYNASTY_NAMES.get(dynasty_id, dynasty_id)
        subject = self._text(raw, default="核心物件清楚可见")
        return f"{dynasty_name}历史悬疑调查场景，写实风格，{subject}，主体清晰，符合时代建筑、服饰、器物，不含现代物件。"

    def _default_subjects(self, asset_type: str) -> list[str]:
        if asset_type == "scene":
            return ["场景空间", "时代器物", "可调查痕迹"]
        if asset_type == "npc":
            return ["人物面貌", "时代服饰", "身份特征"]
        if asset_type == "clue":
            return ["核心线索物件", "材质细节", "使用痕迹"]
        return ["结局氛围"]

    def _era_features(self, dynasty_id: str) -> list[str]:
        if dynasty_id == "late_tang":
            return ["唐后期服饰", "木构建筑", "纸本文书", "油灯烛火"]
        return ["宋代服饰", "木构建筑", "纸本文书", "油灯烛火"]


script_package_normalizer = ScriptPackageNormalizer()
