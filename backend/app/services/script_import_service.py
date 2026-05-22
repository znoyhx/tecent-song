from __future__ import annotations

from app.models.game_models import (
    ChoiceCard,
    Clue,
    ComboRule,
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


class ScriptImportService:
    def validate_ready_for_session(self, *, script_id: str, identity_id: str) -> tuple[ScriptPackage, PlayableIdentity]:
        package = script_job_store.get_script(script_id)
        if package is None:
            raise GameError(code="SCRIPT_NOT_FOUND", message="未找到生成剧本。", status_code=404)

        job = script_job_store.find_job_by_script_id(script_id)
        if job is None or job.status != "completed" or not job.ready_for_overview:
            raise GameError(code="SCRIPT_JOB_NOT_COMPLETED", message="剧本生成尚未完成，不能进入概览或正式游玩。", status_code=409)

        identity = next((item for item in package.playable_identities if item.identity_id == identity_id), None)
        if identity is None:
            raise GameError(code="IDENTITY_NOT_IN_SCRIPT", message="所选身份不属于该生成剧本。", status_code=400)

        if not self.required_images_approved(package):
            raise GameError(code="VISUALS_NOT_APPROVED", message="必需图片尚未全部通过质量门禁，不能进入正式游玩。", status_code=409)

        return package, identity

    def start_generated_session(self, *, script_id: str, identity_id: str) -> dict:
        package, identity = self.validate_ready_for_session(script_id=script_id, identity_id=identity_id)
        catalog = self.build_catalog(package=package, identity=identity)
        return engine.start_generated_session(catalog=catalog, package=package, identity=identity)

    def required_images_approved(self, package: ScriptPackage) -> bool:
        required = [asset for asset in package.visual_assets if asset.asset_type in {"scene", "npc", "clue"}]
        scene_count = sum(1 for asset in required if asset.asset_type == "scene" and asset.quality_gate.status == "approved")
        npc_count = sum(1 for asset in required if asset.asset_type == "npc" and asset.quality_gate.status == "approved")
        clue_count = sum(1 for asset in required if asset.asset_type == "clue" and asset.quality_gate.status == "approved")
        return scene_count >= 5 and npc_count >= 4 and clue_count >= 6 and all(asset.quality_gate.status == "approved" for asset in required)

    def build_catalog(self, *, package: ScriptPackage, identity: PlayableIdentity) -> dict:
        dynasty = DynastyProfile(
            dynasty_id=package.dynasty_id,
            name=package.world.dynasty_name,
            enabled=True,
            period_label=package.world.era_name,
            core_mood=package.script_overview.logline,
            allowed_roles=[item.display_name for item in package.playable_identities],
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
            source="recommended",
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
            for hotspot in location.hotspots:
                positioning = hotspot_map.get((location.location_id, hotspot.hotspot_id))
                first_clue_id = hotspot.clue_ids[0] if hotspot.clue_ids else None
                scene_hotspots.append(
                    SceneHotspot(
                        hotspot_id=hotspot.hotspot_id,
                        label=hotspot.label,
                        clue_ids=hotspot.clue_ids,
                        description=hotspot.description,
                        required_stage=hotspot.required_stage,
                        required_clue_ids=hotspot.required_clue_ids,
                        repeat_text=hotspot.repeat_text,
                        anchor_point=positioning.anchor_point.model_dump() if positioning else None,
                        bbox=positioning.bbox.model_dump() if positioning else None,
                        calibration_status=positioning.calibration_status if positioning else None,
                    )
                )
                if first_clue_id:
                    highlights.append(SceneHighlight(text=hotspot.label, hotspot_id=hotspot.hotspot_id, clue_id=first_clue_id))
                scene_responses[f"{location.location_id}:{hotspot.hotspot_id}"] = {
                    "text": hotspot.investigation_text,
                    "repeat_text": hotspot.repeat_text or hotspot.investigation_text,
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
                title=clue.title,
                type=clue.type,
                is_key=clue.is_key,
                source_scene_id=clue.source_location_id,
                source_npc_id=clue.source_npc_id,
                highlight_text=clue.highlight_text,
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
            for clue in package.clues
        }

        choices = {choice.choice_id: ChoiceCard(choice_id=choice.choice_id, title=choice.title, description=choice.description, effects=choice.effects) for choice in package.choices}
        combos = {rule.rule_id: ComboRule(combo_id=rule.rule_id, required_clue_ids=rule.required_clue_ids, result_title=rule.result_title, result_text=rule.result_text, effects=rule.effects) for rule in package.clue_graph}
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
            deductions=[],
            chapter_sections=[],
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
            "deductions": {},
            "choices": choices,
            "endings": endings,
            "dialogue_rules": dialogue_rules,
            "scene_responses": scene_responses,
            "script_id": package.script_id,
        }


script_import_service = ScriptImportService()
