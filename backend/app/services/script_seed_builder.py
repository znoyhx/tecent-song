from __future__ import annotations

from datetime import datetime
import hashlib
from typing import Any

from app.services.hotspot_layout_contract import (
    HOTSPOT_LAYOUT_VERSION,
    anchor_for_index,
    bbox_from_anchor,
    prompt_line,
)
from app.services.visual_clue_sanitizer import (
    concrete_clue_title,
    concrete_clue_visual_subject,
    scene_clue_visual_requirement,
)


STAGES = ["intro", "investigation", "reversal", "choice", "ending"]
DYNASTY_NAMES = {"song": "北宋", "late_tang": "晚唐"}


class CompactScriptSeedBuilder:
    """Build a full ScriptPackage payload from a compact AI-authored story seed.

    The model is best at creating the historical mystery premise, people, and
    texture. The backend is better at guaranteeing IDs, reference integrity, and
    Stage 15 minimum volume. This keeps the AI response small enough to avoid
    truncation while preserving a generated story core.
    """

    def build(
        self,
        seed_payload: dict[str, Any],
        *,
        dynasty_id: str,
        keywords: list[str],
        job_id: str,
    ) -> dict[str, Any]:
        seed = self._unwrap(seed_payload)
        dynasty_name = DYNASTY_NAMES.get(dynasty_id, dynasty_id)
        script_id = f"p0_{dynasty_id}_{job_id[-6:]}"
        title = self._text(seed.get("title"), seed.get("case_title"), default=f"{dynasty_name}疑案")
        logline = self._text(seed.get("logline"), seed.get("summary"), default=f"{'、'.join(keywords)}牵出一桩隐秘旧案。")
        surface_event = self._text(seed.get("surface_event"), seed.get("case_summary"), seed.get("summary"), default=logline)
        hidden_truth = self._text(seed.get("hidden_truth"), default=f"{keywords[0]}背后另有调包与灭口安排，真相被分散在现场线索与证言中。")

        locations = self._build_locations(seed, dynasty_name)
        npcs = self._build_npcs(seed)
        clues = self._build_clues(seed, keywords, locations)
        locations = self._attach_hotspots(locations, clues)
        choices = self._build_choices(seed)
        endings = self._build_endings(seed, choices, clues)
        style_guide = self._build_style_guide(seed, dynasty_name, npcs)
        visual_assets = self._build_visual_assets(dynasty_name, locations, npcs, clues, endings, style_guide)
        hotspot_positioning = self._build_hotspot_positioning(locations)

        return {
            "script_id": script_id,
            "job_id": job_id,
            "dynasty_id": dynasty_id,
            "keywords": keywords[:8],
            "generation_source": "deepseek",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "script_overview": {
                "title": title,
                "logline": logline,
                "case_summary": self._text(seed.get("case_summary"), surface_event, default=surface_event),
                "opening_location": locations[0]["name"],
                "public_objective": self._text(seed.get("public_objective"), default="查明表面事件背后的真相，确认关键证据链。"),
                "major_locations": [location["name"] for location in locations[:8]],
                "major_npcs": [npc["name"] for npc in npcs[:4]],
                "player_briefing": self._text(seed.get("player_briefing"), default="你可以查验现场、询问相关人物、整理线索并在最后作出取舍。"),
            },
            "playable_identities": self._build_identities(dynasty_name),
            "world": {
                "dynasty_id": dynasty_id,
                "dynasty_name": dynasty_name,
                "era_name": self._text(seed.get("era_name"), default=f"{dynasty_name}年间"),
                "year_hint": self._text(seed.get("year_hint"), default=f"{dynasty_name}地方治所"),
                "location_region": self._text(seed.get("location_region"), seed.get("region"), default=f"{dynasty_name}州县"),
                "rules": [
                    "文书、印记、口供与现场物证需要相互印证。",
                    "人物只会透露自己在当前阶段能够合理知道的内容。",
                ],
                "forbidden_terms": ["手机", "电话", "电报", "火车", "报纸", "公司", "警察", "现代"],
            },
            "story": {
                "surface_event": surface_event,
                "hidden_truth": hidden_truth,
                "themes": self._string_list(seed.get("themes")) or ["文书", "证言", "权责", "自保"],
                "culprit_boundary": self._text(seed.get("culprit_boundary"), default="真凶和包庇者必须通过完整证据链确认，任何单一口供都不足以下结论。"),
                "truth_chain_clue_ids": [f"clue_{index:02d}" for index in range(6)],
            },
            "stages": self._build_stages(locations, clues),
            "locations": locations,
            "npcs": npcs,
            "relationships": self._build_relationships(npcs),
            "clues": clues,
            "clue_graph": self._build_clue_graph(),
            "deductions": self._build_deductions(clues, seed),
            "chapter_sections": self._build_chapter_sections(locations),
            "dialogue_rules": self._build_dialogue_rules(npcs),
            "choices": choices,
            "endings": endings,
            "visual_assets": visual_assets,
            "visual_style_guide": style_guide,
            "hotspot_positioning": hotspot_positioning,
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
        if isinstance(payload.get("script_seed"), dict):
            return payload["script_seed"]
        return payload

    def _build_locations(self, seed: dict[str, Any], dynasty_name: str) -> list[dict[str, Any]]:
        raw_locations = self._list_of_dicts(seed.get("locations"))
        defaults = [
            "前厅", "文书房", "后院", "仓房", "客舍", "门廊", "井边", "小祠",
        ]
        locations: list[dict[str, Any]] = []
        for index in range(8):
            raw = raw_locations[index] if index < len(raw_locations) else {}
            location_id = f"loc_{index:02d}"
            name = self._text(raw.get("name"), default=f"{dynasty_name}{defaults[index]}")
            description = self._text(raw.get("description"), default=f"{name}留有与案件相关的痕迹，灯影、泥痕和旧物彼此呼应。")
            locations.append(
                {
                    "location_id": location_id,
                    "name": name,
                    "description": description,
                    "scene_text": self._text(raw.get("scene_text"), default=f"{name}里空气压低，几处细节等待查验。"),
                    "stage_ids": STAGES[:4] if index == 0 else ["investigation", "reversal", "choice"],
                    "npc_ids": [f"npc_{index % 4:02d}"],
                    "hotspots": [],
                    "visual_asset_id": f"asset_scene_{index:02d}",
                }
            )
        locations[0]["npc_ids"] = ["npc_00", "npc_01"]
        return locations

    def _build_npcs(self, seed: dict[str, Any]) -> list[dict[str, Any]]:
        raw_npcs = self._list_of_dicts(seed.get("npcs"))
        fallback_names = ["主事", "见证人", "经手人", "外来客"]
        npcs: list[dict[str, Any]] = []
        for index in range(4):
            raw = raw_npcs[index] if index < len(raw_npcs) else {}
            npc_id = f"npc_{index:02d}"
            name = self._text(raw.get("name"), default=fallback_names[index])
            public_identity = self._text(raw.get("public_identity"), raw.get("role"), default="案件相关人物")
            appearance = self._text(raw.get("appearance"), default="衣着符合时代身份，神情谨慎，身上带有风尘与疲惫。")
            npcs.append(
                {
                    "npc_id": npc_id,
                    "name": name,
                    "public_identity": public_identity,
                    "appearance": appearance,
                    "personality": self._text(raw.get("personality"), default="谨慎，话语留有余地"),
                    "background_suspicion": self._text(raw.get("background_suspicion"), raw.get("suspicion"), default="对关键时间和物件说法含糊。"),
                    "case_connection": self._text(raw.get("case_connection"), default="案发前后曾接触现场或涉案文书。"),
                    "event_behavior": self._text(raw.get("event_behavior"), default="声称自己只看见表面经过。"),
                    "public_goal": self._text(raw.get("public_goal"), default="保全自身名声和差事。"),
                    "hidden_motive": self._text(raw.get("hidden_motive"), raw.get("secret"), default="隐瞒了一段会让自己被牵连的旧事。"),
                    "known_info": self._string_list(raw.get("known_info")) or ["知道案发时序的一部分"],
                    "unknown_info": self._string_list(raw.get("unknown_info")) or ["不知道完整幕后安排"],
                    "forbidden_disclosure": self._string_list(raw.get("forbidden_disclosure")) or ["不得提前说出最终真相", "不得替玩家完成核心推理"],
                    "speaking_style": self._text(raw.get("speaking_style"), default="短句，克制，避重就轻"),
                    "initial_trust": int(raw.get("initial_trust", 0) or 0),
                    "emotion_state": self._text(raw.get("emotion_state"), default="guarded"),
                    "releasable_clue_ids": [f"clue_{clue_index:02d}" for clue_index in range(index, 30, 4)][:6],
                    "stage_limits": {
                        "intro": "只谈公开事实，不说幕后安排。",
                        "investigation": "可在证据提示下补充见闻。",
                        "reversal": "可以承认先前说法中的漏洞。",
                    },
                    "visual_asset_id": f"asset_npc_{index:02d}",
                }
            )
        return npcs

    def _build_clues(self, seed: dict[str, Any], keywords: list[str], locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        raw_clues = self._list_of_dicts(seed.get("clue_themes")) or self._list_of_dicts(seed.get("clues"))
        clues: list[dict[str, Any]] = []
        for index in range(30):
            raw = raw_clues[index % len(raw_clues)] if raw_clues else {}
            location = locations[index % len(locations)]
            raw_title = self._text(raw.get("title"), raw.get("name"), default=f"{keywords[index % len(keywords)]}痕迹{index + 1}")
            title = concrete_clue_title(raw_title, index=index, keyword=keywords[index % len(keywords)], location_name=location["name"])
            stage = self._stage_for_clue(index)
            clues.append(
                {
                    "clue_id": f"clue_{index:02d}",
                    "title": title,
                    "type": self._text(raw.get("type"), default="物证"),
                    "is_key": index < 10,
                    "source_location_id": location["location_id"],
                    "source_npc_id": None,
                    "highlight_text": concrete_clue_title(self._text(raw.get("highlight_text"), default=title[:18]), index=index, keyword=keywords[index % len(keywords)], location_name=location["name"])[:18],
                    "display_text": self._text(raw.get("display_text"), raw.get("description"), default=f"你记录下“{title}”，它能补足案发时序。"),
                    "detail": self._text(raw.get("detail"), raw.get("description"), default=f"{title}与{location['name']}的细节相互印证，指向隐藏的转移路线。"),
                    "stage_available": [stage],
                    "unlock_conditions": {},
                    "effects": {"flags": [f"found_clue_{index:02d}"], "scores": {"truth": 1}},
                    "related_clue_ids": [f"clue_{max(0, index - 1):02d}"] if index > 0 else [],
                    "ending_tags": [f"tag_{index % 5}"],
                    "forbidden_before_stage": None,
                    "visual_asset_id": f"asset_clue_{index % 6:02d}",
                }
            )
        return clues

    def _attach_hotspots(self, locations: list[dict[str, Any]], clues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for index, clue in enumerate(clues):
            location = locations[index % len(locations)]
            hotspot_id = f"hotspot_{index:02d}"
            location["hotspots"].append(
                {
                    "hotspot_id": hotspot_id,
                    "label": clue["highlight_text"],
                    "description": f"一处与“{clue['title']}”相关的可疑痕迹。",
                    "clue_ids": [clue["clue_id"]],
                    "required_stage": None,
                    "required_clue_ids": [],
                    "investigation_text": f"你细查此处，发现了“{clue['title']}”。",
                    "repeat_text": "这里已经查验过，痕迹仍与先前记录一致。",
                }
            )
        return locations

    def _build_identities(self, dynasty_name: str) -> list[dict[str, Any]]:
        return [
            {
                "identity_id": "identity_clerk",
                "display_name": "随行文吏",
                "description": f"{dynasty_name}地方文吏，熟悉文书、印记和交接规程。",
                "social_rank": "middle",
                "relation_to_case": "有权查验案发现场与相关簿册。",
                "motive": "厘清文书失误背后的责任，避免无辜者被牵连。",
                "permissions": ["查验现场", "询问相关人物", "整理线索", "提交推理"],
                "limitations": ["不能越权定罪", "不能提前公开未证实的真相"],
                "background": "你随官署入场，既要顾及规程，也要找出真正能站住脚的证据。",
                "tags": ["文书", "调查", "谨慎"],
                "is_default": True,
            },
            {
                "identity_id": "identity_runner",
                "display_name": "驿路差人",
                "description": f"{dynasty_name}驿路差人，熟悉行旅、马匹与夜间出入痕迹。",
                "social_rank": "low",
                "relation_to_case": "能接触驿路、仓房、后门与差役口供。",
                "motive": "证明自己没有卷入案中，同时找出真正破坏规程的人。",
                "permissions": ["查验驿路痕迹", "询问差役", "辨认行旅物件"],
                "limitations": ["身份低微，不能强逼高阶人物认罪"],
                "background": "你在驿路上见过太多仓促交接，知道细节比响亮口供更可靠。",
                "tags": ["驿路", "现场", "民间"],
                "is_default": False,
            },
        ]

    def _build_stages(self, locations: list[dict[str, Any]], clues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        goals = {
            "intro": "确认表面事件与第一批可见证据。",
            "investigation": "扩大现场范围，串联文书、物件与口供。",
            "reversal": "识破早期说法中的漏洞，逼近隐藏动机。",
            "choice": "根据证据决定如何呈报或处理真相。",
            "ending": "查看选择造成的历史余波。",
        }
        return [
            {
                "stage_id": stage,
                "name": {"intro": "入局", "investigation": "查证", "reversal": "转折", "choice": "抉择", "ending": "收束"}[stage],
                "order": order,
                "goal": goals[stage],
                "entry_location_id": locations[0 if order == 0 else min(order, len(locations) - 1)]["location_id"],
                "unlock_conditions": [] if order == 0 else [f"完成上一阶段核心线索"],
                "available_location_ids": [location["location_id"] for location in locations],
                "key_clue_ids": [clue["clue_id"] for clue in clues if stage in clue["stage_available"]][:6],
            }
            for order, stage in enumerate(STAGES)
        ]

    def _build_relationships(self, npcs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "source_id": npcs[index]["npc_id"],
                "target_id": npcs[(index + 1) % len(npcs)]["npc_id"],
                "relation": "互相认识",
                "public_state": "表面上只是案发前后的普通往来。",
                "hidden_state": "彼此对关键时间的说法并不完全一致。",
            }
            for index in range(len(npcs))
        ]

    def _build_clue_graph(self) -> list[dict[str, Any]]:
        return [
            {
                "rule_id": f"combo_{index:02d}",
                "required_clue_ids": [f"clue_{index:02d}", f"clue_{index + 1:02d}", f"clue_{index + 2:02d}"],
                "result_title": f"证据组合{index + 1}",
                "result_text": "这些线索可以相互印证，排除一个表面说法。",
                "effects": {"flags": [f"combo_{index:02d}_confirmed"], "scores": {"truth": 1}},
            }
            for index in range(6)
        ]

    def _normalize_key(self, value: Any) -> str:
        return str(value or "").strip().replace(" ", "").replace("「", "").replace("」", "").replace("《", "").replace("》", "")

    def _clue_ids_for_blueprint(self, blueprint: dict[str, Any], clues: list[dict[str, Any]]) -> list[str]:
        title_to_ids: dict[str, list[str]] = {}
        id_to_title: dict[str, str] = {}
        for clue in clues:
            clue_id = str(clue.get("clue_id", "")).strip()
            title = self._normalize_key(clue.get("title"))
            if not clue_id:
                continue
            id_to_title[clue_id] = title
            if title:
                title_to_ids.setdefault(title, []).append(clue_id)

        references = (
            self._string_list(blueprint.get("correct_clue_titles"))
            or self._string_list(blueprint.get("clue_titles"))
            or self._string_list(blueprint.get("evidence_titles"))
            or self._string_list(blueprint.get("correct_clue_ids"))
        )
        matched: list[str] = []
        for reference in references:
            normalized = self._normalize_key(reference)
            clue_id = ""
            if reference in id_to_title:
                clue_id = reference
            elif normalized in title_to_ids:
                clue_id = title_to_ids[normalized][0]
            else:
                for title, ids in title_to_ids.items():
                    if normalized and (normalized in title or title in normalized):
                        clue_id = ids[0]
                        break
            if clue_id and clue_id not in matched:
                matched.append(clue_id)
        return matched[:4]

    def _deduction_from_blueprint(
        self,
        blueprint: dict[str, Any],
        *,
        index: int,
        clue_ids: list[str],
        clue_by_id: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        titles = [self._text(clue_by_id[clue_id].get("title"), default=f"线索{index + 1}") for clue_id in clue_ids]
        evidence = "」「".join(titles[:3])
        default_question = f"「{evidence}」共同锁定了哪条案内行动链？"
        return {
            "deduction_id": f"deduction_{index:02d}",
            "question": self._text(blueprint.get("question"), default=default_question),
            "required_clue_ids": clue_ids[:1],
            "correct_clue_ids": clue_ids,
            "wrong_feedback": self._text(
                blueprint.get("wrong_feedback"),
                default=f"这几条证据还没有完整回答「{titles[0]}」牵出的案件问题。",
            ),
            "success_text": self._text(
                blueprint.get("answer_summary"),
                blueprint.get("success_text"),
                blueprint.get("result_text"),
                default=f"「{evidence}」已经互相印证，可以作为这一问题的完整证据链。",
            ),
            "effects": {"flags": [f"deduction_{index:02d}_solved"], "scores": {"truth": 1}},
        }

    def _build_deductions(self, clues: list[dict[str, Any]], seed: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        deductions: list[dict[str, Any]] = []
        clue_by_id = {str(clue.get("clue_id")): clue for clue in clues if clue.get("clue_id")}
        used_groups: set[tuple[str, ...]] = set()

        for blueprint in self._list_of_dicts((seed or {}).get("deduction_blueprints")):
            clue_ids = self._clue_ids_for_blueprint(blueprint, clues)
            if len(clue_ids) < 2:
                continue
            group_key = tuple(clue_ids)
            if group_key in used_groups:
                continue
            deductions.append(
                self._deduction_from_blueprint(
                    blueprint,
                    index=len(deductions),
                    clue_ids=clue_ids,
                    clue_by_id=clue_by_id,
                )
            )
            used_groups.add(group_key)
            if len(deductions) >= 8:
                return deductions

        max_index = min(len(clues) - 2, 16)
        for index in range(max_index):
            if len(deductions) >= 8:
                break
            clue_group = clues[index:index + 3]
            clue_ids = [clue["clue_id"] for clue in clue_group]
            group_key = tuple(clue_ids)
            if group_key in used_groups:
                continue
            titles = [self._text(clue.get("title"), default=f"线索{index + 1}") for clue in clue_group]
            evidence = "」「".join(titles)
            deductions.append(
                {
                    "deduction_id": f"deduction_{len(deductions):02d}",
                    "question": f"「{evidence}」共同指向案发前后的哪条关键事实？",
                    "required_clue_ids": clue_ids[:1],
                    "correct_clue_ids": clue_ids,
                    "wrong_feedback": f"还缺能把「{titles[0]}」与另外两条线索连起来的证据。",
                    "success_text": f"「{evidence}」已经互相印证，可以作为这一问题的完整证据链。",
                    "effects": {"flags": [f"deduction_{len(deductions):02d}_solved"], "scores": {"truth": 1}},
                }
            )
            used_groups.add(group_key)
        return deductions

    def _build_chapter_sections(self, locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        sections: list[dict[str, Any]] = []
        for index in range(12):
            stage = STAGES[min(index // 3, 3)]
            location = locations[index % len(locations)]
            sections.append(
                {
                    "section_id": f"section_{index:02d}",
                    "stage": stage,
                    "title": f"章节{index + 1}",
                    "trigger_conditions": [] if index == 0 else [f"section_{index - 1:02d} completed"],
                    "scene_id": location["location_id"],
                    "npc_ids": location["npc_ids"][:1],
                    "hotspot_ids": [f"hotspot_{index:02d}"],
                    "clue_ids": [f"clue_{index:02d}"],
                    "next_section_ids": [f"section_{index + 1:02d}"] if index < 11 else [],
                    "goal": "推进本节调查并确认新的证据关系。",
                    "display_text": "你把现场细节和人物说法并列记录，新的矛盾开始浮现。",
                }
            )
        return sections

    def _build_dialogue_rules(self, npcs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rules: list[dict[str, Any]] = []
        for npc_index, npc in enumerate(npcs):
            for stage_index, stage in enumerate(STAGES[:3]):
                rules.append(
                    {
                        "dialogue_id": f"dialogue_{npc_index:02d}_{stage}",
                        "npc_id": npc["npc_id"],
                        "stage": stage,
                        "priority": stage_index,
                        "trigger_keywords": ["时辰", "物证", "去向"],
                        "presented_clue_ids": [f"clue_{npc_index + stage_index:02d}"] if stage != "intro" else [],
                        "response": f"{npc['name']}避开最尖锐的问题，只承认自己知道其中一段经过。",
                        "released_clue_ids": [f"clue_{npc_index + stage_index + 4:02d}"] if stage != "intro" else [],
                        "suggested_questions": ["案发时你在哪里？", "这件物证为何会在现场？", "还有谁接触过这里？"],
                    }
                )
        return rules

    def _build_choices(self, seed: dict[str, Any]) -> list[dict[str, Any]]:
        raw_choices = self._list_of_dicts(seed.get("choices"))
        defaults = ["如实呈报", "暂缓公开", "保护证人", "追查上级", "保全自身"]
        choices: list[dict[str, Any]] = []
        for index in range(5):
            raw = raw_choices[index] if index < len(raw_choices) else {}
            choice_id = f"choice_{index:02d}"
            choices.append(
                {
                    "choice_id": choice_id,
                    "title": self._text(raw.get("title"), default=defaults[index]),
                    "description": self._text(raw.get("description"), default="根据现有证据作出不可逆选择。"),
                    "effects": {"flags": [choice_id], "scores": {"truth": 1 if index == 0 else 0, "survival": 1 if index == 4 else 0}},
                }
            )
        return choices

    def _build_endings(self, seed: dict[str, Any], choices: list[dict[str, Any]], clues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        raw_endings = self._list_of_dicts(seed.get("endings"))
        endings: list[dict[str, Any]] = []
        for index in range(5):
            raw = raw_endings[index] if index < len(raw_endings) else {}
            choice_id = choices[index]["choice_id"]
            endings.append(
                {
                    "ending_id": f"ending_{index:02d}",
                    "title": self._text(raw.get("title"), raw.get("name"), default=f"结局{index + 1}"),
                    "priority": index,
                    "conditions": {"final_choice_id": choice_id},
                    "required_flags": [],
                    "blocked_flags": [],
                    "result_summary": self._text(raw.get("result_summary"), raw.get("description"), default="案件走向一个明确但代价不同的收束。"),
                    "ending_text": self._text(raw.get("ending_text"), raw.get("description"), default="你的选择改变了相关人物的命运，也决定了真相被如何记录。"),
                    "history_echo": self._text(raw.get("history_echo"), default="地方文书、口供和人情共同塑造了这段悬案的余波。"),
                    "related_clue_ids": [clues[index]["clue_id"], clues[index + 1]["clue_id"]],
                    "related_choice_ids": [choice_id],
                    "npc_fates": {},
                    "visual_asset_id": f"asset_ending_{index:02d}",
                }
            )
        return endings

    def _build_style_guide(self, seed: dict[str, Any], dynasty_name: str, npcs: list[dict[str, Any]]) -> dict[str, Any]:
        raw = seed.get("visual_style_guide") if isinstance(seed.get("visual_style_guide"), dict) else {}
        appearance_lock = raw.get("appearance_lock") if isinstance(raw.get("appearance_lock"), dict) else {}
        for npc in npcs:
            appearance_lock.setdefault(npc["npc_id"], f"{npc['name']}：{npc['appearance']}")
        return {
            "style_keywords": self._string_list(raw.get("style_keywords")) or [dynasty_name, "低饱和", "写实工笔", "历史悬疑", "可调查场景", "统一角色风格"],
            "forbidden_visuals": self._string_list(raw.get("forbidden_visuals")) or ["现代电线", "塑料", "水印", "空白背景", "错误朝代服饰", "动漫脸", "夸张卡通", "抽象时间线", "关系图", "实验室玻璃器皿", "锥形瓶", "烧杯", "试管", "现代玻璃瓶"],
            "color_script": self._text(raw.get("color_script"), default="冷雨、暗木、油灯暖色形成低饱和对比。"),
            "camera": self._text(raw.get("camera"), default="平视调查视角，人物居中完整露出脸和上半身，核心线索物件靠近画面中部且清晰可辨。"),
            "era_feature_checklist": self._string_list(raw.get("era_feature_checklist")) or [f"{dynasty_name}服饰", "木构建筑", "纸本文书", "油灯烛火"],
            "appearance_lock": appearance_lock,
        }

    def _build_visual_assets(
        self,
        dynasty_name: str,
        locations: list[dict[str, Any]],
        npcs: list[dict[str, Any]],
        clues: list[dict[str, Any]],
        endings: list[dict[str, Any]],
        style_guide: dict[str, Any],
    ) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        npc_by_id = {npc["npc_id"]: npc for npc in npcs}
        clues_by_location: dict[str, list[dict[str, Any]]] = {}
        for clue in clues:
            clues_by_location.setdefault(clue["source_location_id"], []).append(clue)

        for index, location in enumerate(locations):
            scene_npcs = [npc_by_id[npc_id] for npc_id in location["npc_ids"] if npc_id in npc_by_id]
            scene_clues = clues_by_location.get(location["location_id"], [])[:4]
            npc_names = "、".join(npc["name"] for npc in scene_npcs) or "相关人物"
            clue_titles = "、".join(
                concrete_clue_visual_subject(clue["title"], index=clue_index, location_name=location["name"])
                for clue_index, clue in enumerate(scene_clues)
            ) or "关键线索物件"
            clue_requirements = "；".join(
                scene_clue_visual_requirement(clue, index=clue_index, location_name=location["name"])
                for clue_index, clue in enumerate(scene_clues)
            ) or "关键线索必须作为具体可见物件或痕迹出现在场景中"
            clue_slot_lines = "; ".join(
                prompt_line(
                    clue_index,
                    concrete_clue_visual_subject(clue["title"], index=clue_index, location_name=location["name"]),
                    location["location_id"],
                )
                for clue_index, clue in enumerate(scene_clues)
            ) or "use the declared safe hotspot slots"
            assets.append(
                {
                    "asset_id": f"asset_scene_{index:02d}",
                    "asset_type": "scene",
                    "owner_id": location["location_id"],
                    "title": f"{location['name']}主舞台图",
                    "prompt": (
                        f"{dynasty_name}历史悬疑调查主舞台图，遵循本剧本 visual_style_guide 的统一历史悬疑插画风格。"
                        "人物、地点和线索必须一体生成，NPC自然处在同一透视和同一光源中。"
                        "画面必须完整展现场景，不要裁掉人物头部或脸；主人物靠近画面中部，完整露出整脸和上半身，不要巨大胸像裁切。"
                        f"地点：{location['name']}。地点描述：{location['description']}。场景文字：{location['scene_text']}。场景内必须出现人物：{npc_names}。"
                        f"可点击线索物件必须真实出现在场景里并靠近画面中部，清晰可定位、无遮挡、留出热点标注空间：{clue_titles}。"
                        f"线索画面硬要求：{clue_requirements}。有尸体就画尸体或覆布尸身；有空盒就画打开的空木盒；有暗格就画打开暗格；有刀伤就画在尸身衣物和验尸痕迹上，不能只画一把刀。"
                        f"Wide 16:9 private investigation tableau based on the actual named location, not the same generic courtyard each time; one primary living NPC is preferred, but a corpse required by clues must appear as evidence; never side profile, never back-facing; top-priority evidence slot contract {HOTSPOT_LAYOUT_VERSION}: {clue_slot_lines}. "
                        "Do not draw background people, second person, rows of soldiers, guard corridors, horse teams, flags, banners, weapons, military staging, parade, or distant exterior establishing shot. "
                        "Place evidence as physical props on natural scene surfaces such as a desk, counter, hidden compartment, floor, stone step, dock ground, body area, shelf, tray, or wall niche; never on sky, roof, high wall, plaque, banner, signboard, or text area. "
                        "Dynasty prop audit: no mountains, no lakes, no cabins, no deer, no western scenery, no lab glassware, no conical flask, no beaker, no test tube, no modern glass bottle; use ceramic, lacquered wood, bamboo, cloth, bronze, iron, sealed paper, and oil lamps only. "
                        "在人物附近的中景设置多个自然证物区，例如小桌、托盘、台阶、地面痕迹区、暗格、柜台或尸身旁，把这些线索作为分开的具体物件放进去。"
                        "线索必须是具体物件或痕迹，不要抽象时间线、关系图、流程图或漂浮文字。"
                        "统一遵循本剧本的历史悬疑插画/工笔混合风格，不要丑陋塑料感、廉价写实渲染、动漫脸、Q版、现代概念图或风格跳变。"
                        "不要牌匾、横幅、竖幅、书法、可读文字、乱码或任何像文字的装饰。"
                        "生成后自查：地点是否像该地点；人物是否整脸上半身完整可见；每个线索要素是否按标题和细节出现且靠近中部；风格是否遵循本剧本 visual_style_guide；图片是否成功。"
                        f"风格：{', '.join(style_guide['style_keywords'])}。"
                    ),
                    "negative_prompt": "现代物件，文字水印，空白背景，错误朝代服饰，低清晰度，裁头，裁脸，背身主角，背影，从背后看，遮脸，看向远方，侧脸，只有侧脸，第二个人，背景人物，远处人物，大军阵，士兵队列，大量人群，人群远景，马队，战场，旗帜，兵器，巨大胸像，方图构图，竖幅人像，黑边，抽象时间线，关系图，流程图，动漫脸，Q版，牌匾，门匾，横幅，书法，文字，乱码，山景，湖泊，木屋，鹿，西式风景，实验室玻璃器皿，锥形瓶，烧杯，试管，现代玻璃瓶",
                    "required_subjects": [*([npc["name"] for npc in scene_npcs]), *([clue["title"] for clue in scene_clues]), *([scene_clue_visual_requirement(clue, index=clue_index, location_name=location["name"]) for clue_index, clue in enumerate(scene_clues)]), "NPC", "人物与场景一体生成", "线索", "可点击线索物件", "遵循本剧本visual_style_guide"],
                    "era_feature_checklist": style_guide["era_feature_checklist"],
                }
            )

        for index, npc in enumerate(npcs):
            assets.append(
                {
                    "asset_id": f"asset_npc_{index:02d}",
                    "asset_type": "npc",
                    "owner_id": npc["npc_id"],
                    "title": f"{npc['name']}人物图",
                    "prompt": f"{dynasty_name}历史悬疑人物图，{npc['name']}，{npc['public_identity']}，{npc['appearance']}，整脸居中完整，上半身完整可见，统一写实工笔低饱和风格，不要动漫脸。",
                    "negative_prompt": "现代服饰，水印，空白背景，错误朝代，裁头，裁脸，动漫脸，Q版，夸张卡通",
                    "required_subjects": [npc["name"], npc["public_identity"], "时代服饰"],
                    "era_feature_checklist": style_guide["era_feature_checklist"],
                }
            )

        for index in range(6):
            clue = clues[index]
            clue_subject = concrete_clue_visual_subject(clue["title"], index=index)
            assets.append(
                {
                    "asset_id": f"asset_clue_{index:02d}",
                    "asset_type": "clue",
                    "owner_id": clue["clue_id"],
                    "title": f"{clue['title']}线索图",
                    "prompt": (
                        f"{dynasty_name}历史悬疑线索物件特写，画面只表现一个具体可见物证：{clue_subject}。"
                        "材质细节清晰，可作为线索卡缩略图；禁止把抽象线索画成时间线、时间轴、动机图、关系图、流程图或概念图；"
                        "没有文字水印，没有可读正文，没有乱码。"
                    ),
                    "negative_prompt": "现代物件，水印，空白图，错朝代，时间线，时间轴，关系图，流程图，抽象图表，可读文字，乱码",
                    "required_subjects": [clue_subject, "线索物件", "材质细节"],
                    "era_feature_checklist": style_guide["era_feature_checklist"],
                }
            )

        for index, ending in enumerate(endings):
            assets.append(
                {
                    "asset_id": f"asset_ending_{index:02d}",
                    "asset_type": "ending",
                    "owner_id": ending["ending_id"],
                    "title": f"{ending['title']}结局图",
                    "prompt": f"{dynasty_name}历史悬疑结局氛围图，表现选择后的余波，不含现代物件。",
                    "negative_prompt": "现代物件，水印，空白图",
                    "required_subjects": ["结局氛围", "历史场景"],
                    "era_feature_checklist": style_guide["era_feature_checklist"],
                }
            )
        return assets

    def _build_hotspot_positioning(self, locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        positioning: list[dict[str, Any]] = []
        for location in locations:
            for local_index, hotspot in enumerate(location["hotspots"]):
                anchor = anchor_for_index(local_index, location["location_id"])
                positioning.append(
                    {
                        "location_id": location["location_id"],
                        "hotspot_id": hotspot["hotspot_id"],
                        "visual_asset_id": location["visual_asset_id"],
                        "clue_id": hotspot["clue_ids"][0] if hotspot["clue_ids"] else None,
                        "anchor_point": anchor,
                        "bbox": bbox_from_anchor(anchor),
                        "calibration_status": "pending",
                        "calibrated_against_path": None,
                    }
                )
        return sorted(positioning, key=lambda item: int(item["hotspot_id"].rsplit("_", 1)[1]))

    def _clamp_unit(self, value: float, low: float = 0.12, high: float = 0.88) -> float:
        return max(low, min(high, value))

    def _hotspot_base(self, text: str) -> tuple[float, float]:
        if any(term in text for term in ("脚", "印", "辙", "泥", "灰", "血", "拖", "地", "痕")):
            return 0.48, 0.7
        if any(term in text for term in ("门", "窗", "墙", "匾", "帘", "栏", "井")):
            return 0.74, 0.46
        if any(term in text for term in ("书", "信", "册", "账", "令", "文", "图", "纸", "符", "印")):
            return 0.42, 0.54
        if any(term in text for term in ("杯", "盏", "药", "茶", "碗", "瓶", "袋", "箱", "柜")):
            return 0.58, 0.58
        if any(term in text for term in ("尸", "衣", "手", "人", "证言", "口供")):
            return 0.34, 0.52
        return 0.5, 0.56

    def _hotspot_anchor(
        self,
        location_id: str,
        hotspot: dict[str, Any],
        local_index: int,
        used_points: list[tuple[float, float]],
    ) -> dict[str, float]:
        text = f"{hotspot.get('label', '')}{hotspot.get('description', '')}{','.join(hotspot.get('clue_ids', []))}"
        base_x, base_y = self._hotspot_base(text)
        digest = hashlib.sha1(f"{location_id}:{hotspot.get('hotspot_id')}:{text}".encode("utf-8")).hexdigest()
        seed = int(digest[:8], 16)
        jitter_x = (((seed % 1000) / 999) - 0.5) * 0.24
        jitter_y = ((((seed // 1000) % 1000) / 999) - 0.5) * 0.18
        x = self._clamp_unit(base_x + jitter_x + ((local_index % 3) - 1) * 0.055)
        y = self._clamp_unit(base_y + jitter_y + ((local_index // 3) - 1) * 0.05, 0.22, 0.8)
        for attempt in range(8):
            if all((x - prev_x) ** 2 + (y - prev_y) ** 2 >= 0.012 for prev_x, prev_y in used_points):
                break
            x = self._clamp_unit(x + (0.07 if attempt % 2 == 0 else -0.05))
            y = self._clamp_unit(y + (0.055 if attempt % 3 == 0 else -0.045), 0.22, 0.8)
        used_points.append((x, y))
        return {"x": round(x, 4), "y": round(y, 4)}

    def _stage_for_clue(self, index: int) -> str:
        if index < 5:
            return "intro"
        if index < 18:
            return "investigation"
        if index < 26:
            return "reversal"
        return "choice"

    def _text(self, *values: Any, default: str) -> str:
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
        return default

    def _string_list(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [part.strip() for part in value.replace("，", ",").replace("、", ",").split(",") if part.strip()]
        return []

    def _list_of_dicts(self, value: Any) -> list[dict[str, Any]]:
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        return []


compact_script_seed_builder = CompactScriptSeedBuilder()
