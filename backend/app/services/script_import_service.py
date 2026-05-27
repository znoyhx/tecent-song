from __future__ import annotations

import hashlib

from app.models.game_models import (
    ChoiceCard,
    ChapterSection,
    Clue,
    ComboRule,
    DeductionRule,
    DialogueRule,
    DialogueRuleResponse,
    DialogueRuleTrigger,
    DynastyProfile,
    EndingRule,
    EventTemplate,
    NPCProfile,
    PlayerIdentity,
    PlayerRole,
    Scene,
    SceneHighlight,
    SceneHotspot,
)
from app.models.script_models import PlayableIdentity, ScriptPackage
from app.services.game_engine import GameError, engine
from app.services.script_job_store import script_job_store
from app.services.visual_clue_sanitizer import concrete_clue_title


class ScriptImportService:
    def validate_ready_for_session(
        self,
        *,
        script_id: str,
        identity_id: str | None,
        custom_identity_text: str | None = None,
    ) -> tuple[ScriptPackage, PlayableIdentity]:
        package = script_job_store.get_script(script_id)
        if package is None:
            raise GameError(code="SCRIPT_NOT_FOUND", message="未找到生成剧本。", status_code=404)

        job = script_job_store.find_job_by_script_id(script_id)
        if job is None or job.status != "completed" or not job.ready_for_overview:
            raise GameError(code="SCRIPT_JOB_NOT_COMPLETED", message="剧本生成尚未完成，不能进入概览或正式游玩。", status_code=409)

        identity = self._resolve_playable_identity(
            package=package,
            identity_id=identity_id,
            custom_identity_text=custom_identity_text,
            require_valid=True,
        )

        if not script_job_store.package_passes_demo_gates(package):
            gate_status = script_job_store.script_package_gate_status(package)
            raise GameError(
                code="SCRIPT_DEMO_GATE_BLOCKED",
                message="生成剧本尚未通过体量、剧本监督或严格视觉门禁，不能进入正式游玩。",
                status_code=409,
                details={"gate_status": gate_status},
            )

        return package, identity

    def start_generated_session(self, *, script_id: str, identity_id: str | None, custom_identity_text: str | None = None) -> dict:
        package, identity = self.validate_ready_for_session(
            script_id=script_id,
            identity_id=identity_id,
            custom_identity_text=custom_identity_text,
        )
        catalog = self.build_catalog(package=package, identity=identity)
        return engine.start_generated_session(catalog=catalog, package=package, identity=identity)

    def validate_custom_identity(self, *, script_id: str, identity_id: str | None, custom_identity_text: str) -> dict:
        package = script_job_store.get_script(script_id)
        if package is None:
            raise GameError(code="SCRIPT_NOT_FOUND", message="未找到生成剧本。", status_code=404)
        try:
            identity = self._resolve_playable_identity(
                package=package,
                identity_id=identity_id,
                custom_identity_text=custom_identity_text,
                require_valid=True,
            )
        except GameError as error:
            if error.code != "INVALID_CUSTOM_IDENTITY":
                raise
            return {
                "is_valid": False,
                "identity": None,
                "rejection_reason": error.message,
                "suggestions": ["可填写书生、医者、行商、胥吏、匠人、旅人等符合时代的身份。"],
                "warnings": [],
            }
        return {
            "is_valid": True,
            "identity": PlayerIdentity(
                identity_id=identity.identity_id,
                source="custom",
                display_name=identity.display_name,
                normalized_name=identity.display_name,
                description=identity.description,
                background=identity.background,
                social_rank=identity.social_rank,
                era_fit_score=0.9,
                story_fit_score=0.82,
                tags=identity.tags,
                is_valid=True,
                rejection_reason="",
            ).model_dump(),
            "rejection_reason": "",
            "suggestions": [],
            "warnings": ["自定义身份将沿用所选身份卡的调查权限与限制。"],
        }

    def _resolve_playable_identity(
        self,
        *,
        package: ScriptPackage,
        identity_id: str | None,
        custom_identity_text: str | None,
        require_valid: bool,
    ) -> PlayableIdentity:
        base_identity = next((item for item in package.playable_identities if item.identity_id == identity_id), None)
        if base_identity is None:
            base_identity = next((item for item in package.playable_identities if item.is_default), package.playable_identities[0])
        custom_text = (custom_identity_text or "").strip()
        if custom_text:
            return self._build_custom_identity(package=package, base_identity=base_identity, custom_identity_text=custom_text, require_valid=require_valid)
        if identity_id and base_identity.identity_id == identity_id:
            return base_identity
        raise GameError(code="IDENTITY_NOT_IN_SCRIPT", message="所选身份不属于该生成剧本。", status_code=400)

    def _build_custom_identity(
        self,
        *,
        package: ScriptPackage,
        base_identity: PlayableIdentity,
        custom_identity_text: str,
        require_valid: bool,
    ) -> PlayableIdentity:
        cleaned = custom_identity_text.strip()
        issues = self._custom_identity_issues(package=package, custom_identity_text=cleaned)
        if issues and require_valid:
            raise GameError(code="INVALID_CUSTOM_IDENTITY", message=issues[0], status_code=400, details={"issues": issues})
        digest = hashlib.sha1(cleaned.encode("utf-8")).hexdigest()[:10]
        return PlayableIdentity(
            identity_id=f"custom_{digest}",
            display_name=cleaned,
            description=f"玩家自选身份：{cleaned}",
            social_rank=base_identity.social_rank,
            relation_to_case=base_identity.relation_to_case,
            motive=f"以“{cleaned}”的身份介入此案，寻找能自保也能接近真相的位置。",
            permissions=base_identity.permissions,
            limitations=[*base_identity.limitations, "自定义身份沿用所选身份卡的调查边界。"],
            background=f"你自称“{cleaned}”，借由与案件相关的人情、差事或旅途停留进入现场。你的具体过往由玩家扮演，但行动权限仍受当前剧本规则约束。",
            tags=[*base_identity.tags, "自定义身份"],
            is_default=False,
        )

    def _custom_identity_issues(self, *, package: ScriptPackage, custom_identity_text: str) -> list[str]:
        if len(custom_identity_text) < 2:
            return ["自定义身份至少需要 2 个字。"]
        if len(custom_identity_text) > 16:
            return ["自定义身份请控制在 16 个字以内。"]
        forbidden_terms = set(package.world.forbidden_terms) | {"手机", "电报", "火车", "记者", "警察", "现代", "穿越者"}
        conflict = next((term for term in forbidden_terms if term and term in custom_identity_text), None)
        if conflict:
            return [f"身份包含不符合时代或剧本边界的词：{conflict}。"]
        return []

    def required_images_approved(self, package: ScriptPackage) -> bool:
        required = [asset for asset in package.visual_assets if asset.asset_type in {"scene", "npc", "clue"}]
        approved = [asset for asset in required if asset.quality_gate.status == "approved" and asset.url]
        scene_count = sum(1 for asset in approved if asset.asset_type == "scene")
        npc_count = sum(1 for asset in approved if asset.asset_type == "npc")
        clue_count = sum(1 for asset in approved if asset.asset_type == "clue")
        return (
            scene_count >= max(8, package.quality_gate.required_scene_count)
            and npc_count >= max(4, package.quality_gate.required_npc_count)
            and clue_count >= max(6, package.quality_gate.required_clue_count)
            and len(approved) == len(required)
        )

    def _normalize_hotspot_label(self, value: str) -> str:
        return "".join(str(value or "").split()).strip("「」《》[]【】")

    def _dedupe_location_hotspots(self, hotspots: list) -> list:
        seen_labels: set[str] = set()
        seen_clue_sets: set[tuple[str, ...]] = set()
        result: list = []
        for hotspot in hotspots:
            label_key = self._normalize_hotspot_label(getattr(hotspot, "label", ""))
            clue_key = tuple(getattr(hotspot, "clue_ids", []) or [])
            if label_key and label_key in seen_labels:
                continue
            if clue_key and clue_key in seen_clue_sets:
                continue
            if label_key:
                seen_labels.add(label_key)
            if clue_key:
                seen_clue_sets.add(clue_key)
            result.append(hotspot)
        return result

    def _replace_label(self, text: str, raw_label: str, display_label: str) -> str:
        if not text:
            return text
        if raw_label and raw_label != display_label:
            return text.replace(raw_label, display_label)
        return text

    def _clamp_unit(self, value: float, low: float = 0.12, high: float = 0.88) -> float:
        return max(low, min(high, value))

    def _semantic_hotspot_base(self, text: str) -> tuple[float, float]:
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

    def _runtime_hotspot_anchor(
        self,
        *,
        location_id: str,
        hotspot_id: str,
        label: str,
        description: str,
        clue_id: str | None,
        local_index: int,
        used_points: list[tuple[float, float]],
    ) -> dict[str, float]:
        text = f"{label}{description}{clue_id or ''}"
        base_x, base_y = self._semantic_hotspot_base(text)
        digest = hashlib.sha1(f"{location_id}:{hotspot_id}:{text}".encode("utf-8")).hexdigest()
        seed = int(digest[:8], 16)
        ring = local_index % 7
        jitter_x = (((seed % 1000) / 999) - 0.5) * 0.24
        jitter_y = ((((seed // 1000) % 1000) / 999) - 0.5) * 0.18
        x = self._clamp_unit(base_x + jitter_x + ((ring % 3) - 1) * 0.055)
        y = self._clamp_unit(base_y + jitter_y + ((ring // 3) - 1) * 0.055, 0.22, 0.8)

        for attempt in range(8):
            if all((x - prev_x) ** 2 + (y - prev_y) ** 2 >= 0.012 for prev_x, prev_y in used_points):
                break
            x = self._clamp_unit(x + (0.07 if attempt % 2 == 0 else -0.05))
            y = self._clamp_unit(y + (0.055 if attempt % 3 == 0 else -0.045), 0.22, 0.8)
        used_points.append((x, y))
        return {"x": round(x, 4), "y": round(y, 4)}

    def _runtime_hotspot_bbox(self, anchor: dict[str, float]) -> dict[str, float]:
        size = 0.11
        x = self._clamp_unit(anchor["x"] - size / 2, 0.04, 0.94)
        y = self._clamp_unit(anchor["y"] - size / 2, 0.08, 0.88)
        return {"x": round(x, 4), "y": round(y, 4), "width": size, "height": size}

    def build_catalog(self, *, package: ScriptPackage, identity: PlayableIdentity) -> dict:
        dynasty = DynastyProfile(
            dynasty_id=package.dynasty_id,
            name=package.world.dynasty_name,
            enabled=True,
            period_label=package.world.era_name,
            core_mood=package.script_overview.logline,
            allowed_roles=[item.display_name for item in package.playable_identities] + ([identity.display_name] if identity.identity_id.startswith("custom_") else []),
            forbidden_terms=package.world.forbidden_terms,
            visual_keywords=package.visual_style_guide.style_keywords,
        )
        role = PlayerRole(
            role_id=identity.identity_id,
            dynasty_id=package.dynasty_id,
            name=identity.display_name,
            enabled=True,
            social_position=identity.relation_to_case,
            permissions=identity.permissions,
            limitations=identity.limitations,
        )
        player_identity = PlayerIdentity(
            identity_id=identity.identity_id,
            source="custom" if identity.identity_id.startswith("custom_") else "recommended",
            display_name=identity.display_name,
            normalized_name=identity.display_name,
            description=identity.description,
            background=identity.background,
            social_rank=identity.social_rank,
            era_fit_score=0.95,
            story_fit_score=0.95,
            tags=identity.tags,
            is_valid=True,
            rejection_reason="",
        )
        assets = {asset.asset_id: asset for asset in package.visual_assets}
        hotspot_map = {(item.location_id, item.hotspot_id): item for item in package.hotspot_positioning}

        scenes: dict[str, Scene] = {}
        scene_responses: dict[str, dict] = {}
        for location in package.locations:
            scene_hotspots: list[SceneHotspot] = []
            highlights: list[SceneHighlight] = []
            asset = assets.get(location.visual_asset_id)
            used_points: list[tuple[float, float]] = []
            for hotspot in self._dedupe_location_hotspots(location.hotspots):
                positioning = hotspot_map.get((location.location_id, hotspot.hotspot_id))
                first_clue_id = hotspot.clue_ids[0] if hotspot.clue_ids else None
                display_label = concrete_clue_title(hotspot.label, index=len(scene_hotspots), location_name=location.name)
                display_description = self._replace_label(hotspot.description, hotspot.label, display_label)
                display_investigation_text = self._replace_label(hotspot.investigation_text, hotspot.label, display_label)
                display_repeat_text = self._replace_label(hotspot.repeat_text or hotspot.investigation_text, hotspot.label, display_label)
                if positioning is not None and positioning.anchor_point:
                    anchor_point = dict(positioning.anchor_point)
                    used_points.append((float(anchor_point.get("x", 0.5)), float(anchor_point.get("y", 0.5))))
                    bbox = dict(positioning.bbox) if positioning.bbox else self._runtime_hotspot_bbox(anchor_point)
                    calibration_status = positioning.calibration_status or "approved"
                else:
                    anchor_point = self._runtime_hotspot_anchor(
                        location_id=location.location_id,
                        hotspot_id=hotspot.hotspot_id,
                        label=display_label,
                        description=display_description,
                        clue_id=first_clue_id,
                        local_index=len(scene_hotspots),
                        used_points=used_points,
                    )
                    bbox = self._runtime_hotspot_bbox(anchor_point)
                    calibration_status = "approved"
                scene_hotspots.append(
                    SceneHotspot(
                        hotspot_id=hotspot.hotspot_id,
                        label=display_label,
                        clue_ids=hotspot.clue_ids,
                        description=display_description,
                        required_stage=None,
                        required_clue_ids=[],
                        repeat_text=display_repeat_text,
                        anchor_point=anchor_point,
                        bbox=bbox,
                        calibration_status=calibration_status,
                    )
                )
                if first_clue_id:
                    highlights.append(SceneHighlight(text=display_label, hotspot_id=hotspot.hotspot_id, clue_id=first_clue_id))
                scene_responses[f"{location.location_id}:{hotspot.hotspot_id}"] = {
                    "text": display_investigation_text,
                    "repeat_text": display_repeat_text,
                    "clue_ids": hotspot.clue_ids,
                }

            scenes[location.location_id] = Scene(
                scene_id=location.location_id,
                name=location.name,
                description=location.description,
                background_asset=asset.generated_path if asset else "",
                available_stage=location.stage_ids,
                npc_ids=location.npc_ids,
                scene_text=location.scene_text,
                highlights=highlights,
                hotspots=scene_hotspots,
                visual_asset_id=asset.asset_id if asset else None,
                visual_asset_url=asset.url if asset else None,
                visual_status=asset.quality_gate.status if asset else "fallback",
            )

        npcs = {
            npc.npc_id: NPCProfile(
                npc_id=npc.npc_id,
                name=npc.name,
                public_identity=npc.public_identity,
                appearance=npc.appearance,
                personality=npc.personality,
                background_suspicion=npc.background_suspicion,
                case_connection=npc.case_connection,
                event_behavior=npc.event_behavior,
                public_goal=npc.public_goal,
                hidden_motive=npc.hidden_motive,
                known_info=npc.known_info,
                unknown_info=npc.unknown_info,
                forbidden_disclosure=npc.forbidden_disclosure,
                speaking_style=npc.speaking_style,
                initial_trust=npc.initial_trust,
                emotion_state=npc.emotion_state,
                releasable_clue_ids=npc.releasable_clue_ids,
                stage_limits=npc.stage_limits,
                visual_asset_id=npc.visual_asset_id,
                visual_asset_url=assets.get(npc.visual_asset_id).url if assets.get(npc.visual_asset_id) else None,
                visual_status=assets.get(npc.visual_asset_id).quality_gate.status if assets.get(npc.visual_asset_id) else "fallback",
            )
            for npc in package.npcs
        }
        clues = {
            clue.clue_id: Clue(
                clue_id=clue.clue_id,
                title=concrete_clue_title(clue.title, index=index, location_name=clue.source_location_id),
                type=clue.type,
                is_key=clue.is_key,
                source_scene_id=clue.source_location_id,
                source_npc_id=clue.source_npc_id,
                highlight_text=concrete_clue_title(clue.highlight_text or clue.title, index=index, location_name=clue.source_location_id)[:18],
                display_text=clue.display_text,
                detail=clue.detail,
                stage_available=clue.stage_available,
                unlock_conditions=clue.unlock_conditions,
                effects=clue.effects,
                related_clue_ids=clue.related_clue_ids,
                ending_tags=clue.ending_tags,
                forbidden_before_stage=clue.forbidden_before_stage,
                visual_asset_id=clue.visual_asset_id,
                visual_asset_url=assets.get(clue.visual_asset_id).url if assets.get(clue.visual_asset_id) else None,
                visual_status=assets.get(clue.visual_asset_id).quality_gate.status if assets.get(clue.visual_asset_id) else "fallback",
            )
            for index, clue in enumerate(package.clues)
        }

        choices = {choice.choice_id: ChoiceCard(choice_id=choice.choice_id, title=choice.title, description=choice.description, effects=choice.effects) for choice in package.choices}
        combos = {rule.rule_id: ComboRule(combo_id=rule.rule_id, required_clue_ids=rule.required_clue_ids, result_title=rule.result_title, result_text=rule.result_text, effects=rule.effects) for rule in package.clue_graph}
        deductions = {
            deduction.deduction_id: DeductionRule(
                deduction_id=deduction.deduction_id,
                question=deduction.question,
                required_clue_ids=deduction.required_clue_ids,
                correct_clue_ids=deduction.correct_clue_ids,
                wrong_feedback=deduction.wrong_feedback,
                success_text=deduction.success_text,
                effects=deduction.effects,
            )
            for deduction in package.deductions
        }
        chapter_sections = {
            section.section_id: ChapterSection(
                section_id=section.section_id,
                stage=section.stage,
                title=section.title,
                trigger_conditions=section.trigger_conditions,
                scene_id=section.scene_id,
                npc_ids=section.npc_ids,
                hotspot_ids=section.hotspot_ids,
                clue_ids=section.clue_ids,
                next_section_ids=section.next_section_ids,
                goal=section.goal,
                display_text=section.display_text,
            )
            for section in package.chapter_sections
        }
        endings = {
            ending.ending_id: EndingRule(
                ending_id=ending.ending_id,
                title=ending.title,
                priority=ending.priority,
                conditions=ending.conditions,
                required_flags=ending.required_flags,
                blocked_flags=ending.blocked_flags,
                result_summary=ending.result_summary,
                ending_text=ending.ending_text,
                history_echo=ending.history_echo,
                related_clue_ids=ending.related_clue_ids,
                related_choice_ids=ending.related_choice_ids,
                npc_fates=ending.npc_fates,
                visual_asset_id=ending.visual_asset_id,
            )
            for ending in package.endings
        }
        dialogue_rules: dict[str, list[DialogueRule]] = {}
        for rule in package.dialogue_rules:
            dialogue_rules.setdefault(rule.npc_id, []).append(
                DialogueRule(
                    dialogue_id=rule.dialogue_id,
                    stage=rule.stage,
                    priority=rule.priority,
                    trigger=DialogueRuleTrigger(
                        presented_clue_ids=rule.presented_clue_ids,
                        keywords=rule.trigger_keywords,
                    ),
                    response=DialogueRuleResponse(
                        npc_dialogue=rule.response,
                        npc_action="对方谨慎回应，仍然守住不该提前说出的部分。",
                        emotion="guarded",
                        released_clue_ids=rule.released_clue_ids,
                        suggested_questions=rule.suggested_questions,
                    ),
                )
            )

        event = EventTemplate(
            event_id=package.script_id,
            dynasty_id=package.dynasty_id,
            title=package.script_overview.title,
            surface_event=package.story.surface_event,
            hidden_truth=package.story.hidden_truth,
            stages=[stage.stage_id for stage in sorted(package.stages, key=lambda item: item.order)],
            stage_goals={stage.stage_id: stage.goal for stage in package.stages},
            scene_ids=[location.location_id for location in package.locations],
            npc_ids=[npc.npc_id for npc in package.npcs],
            required_clue_ids=package.story.truth_chain_clue_ids,
            ending_rule_ids=[ending.ending_id for ending in package.endings],
            choices=list(choices.values()),
            combos=list(combos.values()),
            deductions=list(deductions.values()),
            chapter_sections=list(chapter_sections.values()),
        )

        return {
            "dynasty": dynasty,
            "roles": {role.role_id: role},
            "player_identity": player_identity,
            "event": event,
            "scenes": scenes,
            "npcs": npcs,
            "clues": clues,
            "combos": combos,
            "deductions": deductions,
            "chapter_sections": chapter_sections,
            "choices": choices,
            "endings": endings,
            "dialogue_rules": dialogue_rules,
            "scene_responses": scene_responses,
            "script_id": package.script_id,
        }


script_import_service = ScriptImportService()
