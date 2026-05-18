from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.models.game_models import (
    Clue,
    ComboRule,
    DebugLogEntry,
    DeductionRule,
    DeductionSubmitRequest,
    DialogueRequest,
    DialogueRule,
    DialogueRuleResponse,
    DialogueTurn,
    DynastyProfile,
    EndingRule,
    EventTemplate,
    GameScores,
    GameState,
    HistoryEchoRecord,
    InvestigateRequest,
    NPCProfile,
    PlayerIdentityValidationRequest,
    PlayerRole,
    Scene,
    SessionStartRequest,
)
from app.services.dialogue_orchestrator import DialogueOrchestrator
from app.services.history_echo_generator import HistoryEchoGenerator
from app.services.image_generation_service import image_generation_service
from app.services.player_identity_service import IdentityValidationError, PlayerIdentityService
from app.services.script_bound_chat import ScriptBoundChatService
from app.services.supervisor import SupervisorService





class GameError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class GameEngine:
    STAGE_LABELS = {
        "intro": "引子",
        "investigation": "调查",
        "reversal": "异变",
        "choice": "抉择",
        "ending": "结局",
    }

    def __init__(self) -> None:
        self.base_dir = Path(__file__).resolve().parents[2]
        self.data_dir = self.base_dir / "data"
        self.supervisor = SupervisorService()
        self.script_bound_chat = ScriptBoundChatService(self.data_dir)
        self.dialogue_orchestrator = DialogueOrchestrator()
        self.history_echo_generator = HistoryEchoGenerator()
        self.player_identity_service = PlayerIdentityService()
        self.sessions: dict[str, dict] = {}


        self._load_static_data()

    def _load_static_data(self) -> None:
        dynasties_payload = self._read_json("dynasties/dynasties.json")
        self.dynasties = {
            item["dynasty_id"]: DynastyProfile.model_validate(item)
            for item in dynasties_payload["dynasties"]
        }

        roles_payload = self._read_json("roles/roles.json")
        self.roles = {
            item["role_id"]: PlayerRole.model_validate(item)
            for item in roles_payload["roles"]
        }

        event_payload = self._read_json("events/ming_bookshop_fire.json")
        self.event = EventTemplate.model_validate(event_payload)
        self.combos = {combo.combo_id: combo for combo in self.event.combos}
        self.deductions = {deduction.deduction_id: deduction for deduction in self.event.deductions}
        self.choices = {choice.choice_id: choice for choice in self.event.choices}


        scenes_payload = self._read_json("scenes/ming_bookshop_scenes.json")
        self.scenes = {
            item["scene_id"]: Scene.model_validate(item)
            for item in scenes_payload["scenes"]
        }

        npcs_payload = self._read_json("npcs/ming_bookshop_npcs.json")
        self.npcs = {
            item["npc_id"]: NPCProfile.model_validate(item)
            for item in npcs_payload["npcs"]
        }

        clues_payload = self._read_json("clues/ming_bookshop_clues.json")
        self.clues = {
            item["clue_id"]: Clue.model_validate(item)
            for item in clues_payload["clues"]
        }

        endings_payload = self._read_json("endings/ming_bookshop_endings.json")
        self.endings = {
            item["ending_id"]: EndingRule.model_validate(item)
            for item in endings_payload["endings"]
        }

        self.scene_responses = self._read_json("mock/scene_responses.json")["responses"]
        self.history_echoes = {
            item["ending_id"]: HistoryEchoRecord.model_validate(item)
            for item in self._read_json("mock/history_echoes.json")["history_echoes"]
        }
        self.dialogue_rules: dict[str, list[DialogueRule]] = {}
        for path in (self.data_dir / "mock" / "dialogues").glob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.dialogue_rules[payload["npc_id"]] = [
                DialogueRule.model_validate(rule) for rule in payload["rules"]
            ]

    def _read_json(self, relative_path: str) -> dict:
        path = self.data_dir / relative_path
        return json.loads(path.read_text(encoding="utf-8"))

    def health(self) -> dict:
        return {
            "status": "ok",
            "display_text": "服务运行中",
            "version": settings.version,
            "mock_ai": settings.use_mock_ai,
            "ai_provider": settings.ai_provider,
            "deepseek_key_available": settings.deepseek_api_key_available,
            "deepseek_model": settings.deepseek_model,
        }


    def list_dynasties(self) -> dict:
        return {"dynasties": [item.model_dump() for item in self.dynasties.values()]}

    def list_roles(self, dynasty_id: str) -> dict:
        if dynasty_id not in self.dynasties:
            raise GameError(code="BAD_REQUEST", message="未找到对应朝代。", status_code=400)
        roles = [
            role.model_dump()
            for role in self.roles.values()
            if role.dynasty_id == dynasty_id
        ]
        return {"roles": roles}

    def list_player_identities(self, *, dynasty_id: str, event_id: str) -> dict:
        dynasty = self.dynasties.get(dynasty_id)
        if dynasty is None or event_id != self.event.event_id:
            raise GameError(code="BAD_REQUEST", message="未找到对应剧本，无法生成身份推荐。", status_code=400)
        return self.player_identity_service.recommendations_for(dynasty=dynasty, event=self.event).model_dump()

    def validate_player_identity(self, request: PlayerIdentityValidationRequest) -> dict:
        dynasty = self.dynasties.get(request.dynasty_id)
        if dynasty is None or request.event_id != self.event.event_id:
            raise GameError(code="BAD_REQUEST", message="未找到对应剧本，无法校验身份。", status_code=400)
        return self.player_identity_service.validate_custom(
            dynasty=dynasty,
            event=self.event,
            custom_identity_text=request.custom_identity_text,
        ).model_dump()

    def start_session(self, request: SessionStartRequest) -> dict:
        dynasty = self.dynasties.get(request.dynasty_id)
        role = self.roles.get(request.role_id)
        if dynasty is None or role is None or request.event_id != self.event.event_id:
            raise GameError(code="BAD_REQUEST", message="开局参数无效，请重新选择。", status_code=400)
        if role.dynasty_id != dynasty.dynasty_id or not role.enabled:
            raise GameError(code="BAD_REQUEST", message="这个剧本身份暂不可用，请重新选择。", status_code=400)
        try:
            player_identity = self.player_identity_service.resolve_for_session(
                dynasty=dynasty,
                event=self.event,
                identity_id=getattr(request, "identity_id", None),
                custom_identity_text=getattr(request, "custom_identity_text", None),
            )
        except IdentityValidationError as error:
            raise GameError(
                code="INVALID_PLAYER_IDENTITY",
                message=error.message,
                status_code=400,
                details={"suggestions": error.suggestions},
            ) from error

        session_id = f"s_{uuid4().hex[:8]}"
        state = GameState(
            session_id=session_id,
            event_id=request.event_id,
            dynasty_id=request.dynasty_id,
            player_role_id=request.role_id,
            player_identity=player_identity,
            current_stage="intro",
            current_scene_id="scene_front_hall",
            discovered_clue_ids=[],
            completed_combo_ids=[],
            completed_deduction_ids=[],
            npc_trust={npc_id: npc.initial_trust for npc_id, npc in self.npcs.items()},
            flags=[],
            scores=GameScores(),
            risk_level=0,
            available_scene_ids=[],
            available_choice_ids=[],
            turn_count=0,
            status="active",
        )
        record = {
            "state": state,
            "dialogue_turns": [],
            "logs": [],
            "ending": None,
            "last_supervisor": None,
        }
        self._refresh_state_metadata(state)
        self.sessions[session_id] = record
        return self.get_session(session_id)

    def get_session(self, session_id: str) -> dict:
        record = self._require_session(session_id)
        state: GameState = record["state"]
        current_scene = self.scenes[state.current_scene_id]
        scene_npcs = [self._npc_payload(npc_id) for npc_id in current_scene.npc_ids]
        discovered_clues = [self._clue_payload(clue_id) for clue_id in state.discovered_clue_ids]
        combo_summaries = [self._combo_payload(combo_id) for combo_id in state.completed_combo_ids]
        deduction_summaries = [self._deduction_payload(deduction_id) for deduction_id in state.completed_deduction_ids]
        available_deductions = [self._deduction_prompt_payload(deduction_id) for deduction_id in self._available_deductions(state)]
        available_choices = [
            self.choices[choice_id].model_dump()
            for choice_id in state.available_choice_ids
            if choice_id in self.choices
        ]

        ending_catalog = [
            {"ending_id": ending.ending_id, "title": ending.title}
            for ending in sorted(self.endings.values(), key=lambda item: item.priority)
        ]
        return {
            "session_id": session_id,
            "state": state.model_dump(),
            "dynasty": self.dynasties[state.dynasty_id].model_dump(),
            "player_role": self.roles[state.player_role_id].model_dump(),
            "player_identity": state.player_identity.model_dump() if state.player_identity else None,
            "stage_label": self.STAGE_LABELS[state.current_stage],
            "scene": self._scene_payload(state.current_scene_id),
            "scene_npcs": scene_npcs,
            "available_scenes": [self._scene_payload(scene_id) for scene_id in state.available_scene_ids],

            "available_actions": ["调查", "对话", "出示线索"],
            "clues": discovered_clues,
            "combo_summaries": combo_summaries,
            "deduction_summaries": deduction_summaries,
            "available_deductions": available_deductions,
            "dialogue_turns": [turn.model_dump() for turn in record["dialogue_turns"]],
            "current_goal": self._current_goal(state.current_stage),
            "available_choices": available_choices,
            "ending": record["ending"],
            "ending_catalog": ending_catalog,
            "debug_info": {
                "use_mock_ai": settings.use_mock_ai,
                "ai_provider": settings.ai_provider,
                "logs": [log.model_dump() for log in record["logs"][-6:]],
                "last_supervisor": record["last_supervisor"],
            },
        }

    def investigate(self, request: InvestigateRequest) -> dict:
        record = self._require_session(request.session_id)
        state: GameState = record["state"]
        if request.scene_id not in state.available_scene_ids:
            raise GameError(code="INVALID_STAGE_ACTION", message="当前阶段还不能前往这个场景。", status_code=400)

        state.current_scene_id = request.scene_id
        current_scene = self.scenes[request.scene_id]
        text = current_scene.description
        new_clues: list[dict] = []
        new_combos: list[dict] = []
        new_deductions: list[dict] = []

        if request.hotspot_id:
            hotspot = next((item for item in current_scene.hotspots if item.hotspot_id == request.hotspot_id), None)
            if hotspot is None:
                raise GameError(code="BAD_REQUEST", message="未找到对应调查点。", status_code=400)
            stage_order = {"intro": 0, "investigation": 1, "reversal": 2, "choice": 3, "ending": 4}
            if hotspot.required_stage and stage_order.get(state.current_stage, 0) < stage_order.get(hotspot.required_stage, 0):
                raise GameError(code="INVALID_STAGE_ACTION", message="当前阶段还不能调查这个位置。", status_code=400)
            missing_clues = [clue_id for clue_id in hotspot.required_clue_ids if clue_id not in state.discovered_clue_ids]
            if missing_clues:
                raise GameError(code="INVALID_STAGE_ACTION", message="还缺少前置线索，暂时看不出这里的问题。", status_code=400)
            key = f"{request.scene_id}:{request.hotspot_id}"
            hotspot_response = self.scene_responses.get(key)
            if hotspot_response is None:
                raise GameError(code="BAD_REQUEST", message="未找到对应调查点。", status_code=400)
            if all(clue_id in state.discovered_clue_ids for clue_id in hotspot_response.get("clue_ids", [])):
                text = hotspot_response.get("repeat_text") or hotspot.repeat_text or hotspot_response["text"]
            else:
                text = hotspot_response["text"]
            new_clues = self._discover_clues(state, hotspot_response.get("clue_ids", []))
            new_combos = self._evaluate_combos(state)
            new_deductions = []
            self._evaluate_transitions(state)
            state.turn_count += 1
            self._log_call(
                record,
                module="scene_investigate",
                summary=f"调查 {current_scene.name} / {request.hotspot_id}",
                success=True,
                fallback_used=False,
                supervisor_pass=True,
            )

        return {
            "text": text,
            "new_clues": new_clues,
            "new_combos": new_combos,
            "new_deductions": new_deductions,
            "state": state.model_dump(),
            "scene": self._scene_payload(state.current_scene_id),
            "current_goal": self._current_goal(state.current_stage),

        }

    def dialogue(self, request: DialogueRequest) -> dict:
        record = self._require_session(request.session_id)
        state: GameState = record["state"]
        npc = self.npcs.get(request.npc_id)
        if npc is None:
            raise GameError(code="BAD_REQUEST", message="未找到对应人物。", status_code=400)
        if request.npc_id not in self.scenes[state.current_scene_id].npc_ids:
            raise GameError(code="INVALID_STAGE_ACTION", message="当前场景无法与该人物对话。", status_code=400)
        for clue_id in request.presented_clue_ids:
            if clue_id not in state.discovered_clue_ids:
                raise GameError(code="CLUE_NOT_DISCOVERED", message="你还没有发现这条线索，无法出示。", status_code=400)

        script_context = self.script_bound_chat.prepare_context(
            state=state,
            npc=npc,
            player_message=request.message,
            clue_map=self.clues,
            dialogue_turns=record["dialogue_turns"],
            presented_clue_ids=request.presented_clue_ids,
            player_identity=state.player_identity,
        )
        rule = self._pick_dialogue_rule(state=state, request=request)
        base_mock_response = rule.response if rule else self._fallback_response_for_npc(npc.name)
        mock_response = self.script_bound_chat.response_for_context(
            base_response=base_mock_response,
            context=script_context,
            npc=npc,
            clue_map=self.clues,
            rule_matched=rule is not None,
        )
        player_role = self.roles[state.player_role_id]
        current_scene = self.scenes[state.current_scene_id]
        discovered_clues = [self.clues[clue_id] for clue_id in state.discovered_clue_ids if clue_id in self.clues]
        presented_clues = [self.clues[clue_id] for clue_id in request.presented_clue_ids if clue_id in self.clues]
        use_fast_path = self._should_use_local_dialogue_fast_path(rule=rule, context=script_context)
        orchestrated = None
        if not use_fast_path:
            orchestrated = self.dialogue_orchestrator.handle_dialogue(
                state=state,
                dynasty=self.dynasties[state.dynasty_id],
                player_role=player_role,
                player_identity=state.player_identity,
                current_scene=current_scene,
                npc=npc,
                request=request,
                discovered_clues=discovered_clues,
                presented_clues=presented_clues,
                clue_map=self.clues,
                mock_response=mock_response,
                supervisor=self.supervisor,
                script_context=script_context,
            )
        if orchestrated is not None:
            response = self.script_bound_chat.finalize_response(
                response=orchestrated.response,
                context=script_context,
                clue_map=self.clues,
            )
            supervisor_result = orchestrated.supervisor_result
            fallback_used = orchestrated.fallback_used
            ai_success = orchestrated.ai_success
            log_module = "NPCDialogueAgent"
        else:
            response = mock_response
            supervisor_result = self.supervisor.review_dialogue(
                stage=state.current_stage,
                dynasty=self.dynasties[state.dynasty_id],
                npc=npc,
                response=response,
                clue_map=self.clues,
                player_message=request.message,
                player_role=player_role,
                player_identity=state.player_identity,
                allowed_released_clue_ids=script_context.allowed_released_clue_ids,
                intent=script_context.intent,
                discovered_clue_ids=state.discovered_clue_ids,
            )
            fallback_used = False
            ai_success = True
            log_module = "script_bound_fast_dialogue" if use_fast_path else "mock_dialogue"
            if not supervisor_result.pass_:
                response = self.script_bound_chat.response_for_context(
                    base_response=self._fallback_response_for_npc(npc.name),
                    context=script_context,
                    npc=npc,
                    clue_map=self.clues,
                    rule_matched=False,
                )
                fallback_used = True

        response = self.script_bound_chat.finalize_response(
            response=response,
            context=script_context,
            clue_map=self.clues,
        )
        self._apply_dialogue_effects(state, npc.npc_id, response)

        new_clues = self._discover_clues(state, response.released_clue_ids)
        new_combos = self._evaluate_combos(state)
        new_deductions = []
        self._evaluate_transitions(state)
        state.turn_count += 1

        turn = DialogueTurn(
            turn_id=f"t_{uuid4().hex[:8]}",
            session_id=state.session_id,
            npc_id=npc.npc_id,
            npc_name=npc.name,
            player_message=request.message,
            action_type=request.action_type,
            presented_clue_ids=request.presented_clue_ids,
            npc_response=response.npc_dialogue,
            npc_action=response.npc_action,
            emotion=response.emotion,
            intent=response.intent,
            released_clue_ids=response.released_clue_ids,
            highlight_clues=response.highlight_clues,
            red_texts=response.red_texts,

            suggested_questions=response.suggested_questions,
            supervisor_notes=response.supervisor_notes,
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
        record["dialogue_turns"].append(turn)
        record["last_supervisor"] = supervisor_result.model_dump(by_alias=True)
        self._log_call(
            record,
            module=log_module,
            summary=f"与 {npc.name} 对话",
            success=ai_success,
            fallback_used=fallback_used,
            supervisor_pass=supervisor_result.pass_,
        )


        return {
            "dialogue": {
                "npc_id": npc.npc_id,
                "npc_name": npc.name,
                "npc_dialogue": response.npc_dialogue,
                "npc_action": response.npc_action,
                "emotion": response.emotion,
                "intent": response.intent,
                "released_clue_ids": response.released_clue_ids,
                "highlight_clues": [item.model_dump() for item in response.highlight_clues],
                "red_texts": response.red_texts,
                "suggested_questions": response.suggested_questions,
                "trust_delta": response.trust_delta,
                "score_delta": response.score_delta,
                "risk_delta": response.risk_delta,
                "add_flags": response.add_flags,
                "supervisor_notes": response.supervisor_notes,
            },
            "new_clues": new_clues,
            "new_combos": new_combos,
            "new_deductions": new_deductions,
            "state": state.model_dump(),
            "supervisor": supervisor_result.model_dump(by_alias=True),
            "fallback_used": fallback_used,
            "current_goal": self._current_goal(state.current_stage),
        }

    def _should_use_local_dialogue_fast_path(self, *, rule: DialogueRule | None, context) -> bool:
        runtime_settings = self.dialogue_orchestrator.settings
        if runtime_settings.use_mock_ai:
            return False
        if runtime_settings.ai_provider != "deepseek" or not runtime_settings.deepseek_api_key_available:
            return False
        if context.intent in {"smalltalk", "force_truth"}:
            return True
        if context.intent == "off_topic":
            return False
        return rule is not None or bool(context.preferred_clue_ids)

    def submit_deduction(self, request: DeductionSubmitRequest) -> dict:
        record = self._require_session(request.session_id)
        state: GameState = record["state"]
        if state.current_stage == "ending" or state.status not in {"active", "ending_ready"}:
            raise GameError(code="INVALID_STAGE_ACTION", message="结局已定，不能再提交推理。", status_code=400)

        deduction = self.deductions.get(request.deduction_id)
        if deduction is None:
            raise GameError(code="BAD_REQUEST", message="未找到对应思维疑团。", status_code=400)

        selected = {clue_id for clue_id in request.selected_clue_ids if clue_id.strip()}
        undiscovered = sorted(selected.difference(set(state.discovered_clue_ids)))
        if undiscovered:
            raise GameError(code="CLUE_NOT_DISCOVERED", message="你还没有发现这些线索，无法用于推理。", status_code=400)

        required = set(deduction.required_clue_ids or deduction.correct_clue_ids)
        missing_required = sorted(required.difference(set(state.discovered_clue_ids)))
        if missing_required:
            raise GameError(code="INVALID_STAGE_ACTION", message="证据还不足，暂时不能解开这个疑团。", status_code=400)

        if deduction.deduction_id in state.completed_deduction_ids:
            return {
                "correct": True,
                "feedback": "这个疑团已经完成。",
                "deduction": self._deduction_payload(deduction.deduction_id),
                "state": state.model_dump(),
                "available_deductions": [self._deduction_prompt_payload(item) for item in self._available_deductions(state)],
                "current_goal": self._current_goal(state.current_stage),
            }

        correct = set(deduction.correct_clue_ids).issubset(selected)
        if not correct:
            state.turn_count += 1
            self._log_call(
                record,
                module="deduction_submit",
                summary=f"推理未成立 {deduction.question}",
                success=True,
                fallback_used=False,
                supervisor_pass=True,
            )
            return {
                "correct": False,
                "feedback": deduction.wrong_feedback,
                "deduction": self._deduction_prompt_payload(deduction.deduction_id),
                "state": state.model_dump(),
                "available_deductions": [self._deduction_prompt_payload(item) for item in self._available_deductions(state)],
                "current_goal": self._current_goal(state.current_stage),
            }

        state.completed_deduction_ids.append(deduction.deduction_id)
        self._apply_effect_bundle(state, deduction.effects)
        self._evaluate_transitions(state)
        state.turn_count += 1
        self._log_call(
            record,
            module="deduction_submit",
            summary=f"推理成立 {deduction.question}",
            success=True,
            fallback_used=False,
            supervisor_pass=True,
        )
        return {
            "correct": True,
            "feedback": deduction.success_text,
            "deduction": self._deduction_payload(deduction.deduction_id),
            "state": state.model_dump(),
            "available_deductions": [self._deduction_prompt_payload(item) for item in self._available_deductions(state)],
            "current_goal": self._current_goal(state.current_stage),
        }

    def submit_choice(self, session_id: str, choice_id: str) -> dict:
        record = self._require_session(session_id)
        state: GameState = record["state"]
        if state.current_stage != "choice":
            raise GameError(code="INVALID_STAGE_ACTION", message="当前还不能做最终抉择。", status_code=400)
        choice = self.choices.get(choice_id)
        if choice is None:
            raise GameError(code="BAD_REQUEST", message="未找到对应选择。", status_code=400)

        state.final_choice_id = choice.choice_id
        self._apply_choice_effects(state, choice.effects)
        state.current_stage = "ending"
        state.status = "ending_ready"
        self._refresh_state_metadata(state)
        self._log_call(
            record,
            module="choice",
            summary=f"提交抉择 {choice.title}",
            success=True,
            fallback_used=False,
            supervisor_pass=True,
        )
        return {
            "state": state.model_dump(),
            "next": "resolve_ending",
        }

    def resolve_ending(self, session_id: str) -> dict:
        record = self._require_session(session_id)
        state: GameState = record["state"]
        if state.current_stage != "ending":
            raise GameError(code="INVALID_STAGE_ACTION", message="尚未进入结局判定阶段。", status_code=400)
        if record["ending"] is None:
            ending = self._pick_ending(state)
            history_echo = self.history_echoes.get(ending.ending_id)
            echo_result = self.history_echo_generator.generate(
                ending=ending,
                state=state,
                choices=self.choices,
                clues=self.clues,
                npcs=self.npcs,
                template_echo=history_echo.text if history_echo else ending.history_echo,
            )
            ending_payload = {
                "ending_id": ending.ending_id,
                "title": ending.title,
                "summary": ending.result_summary,
                "ending_text": ending.ending_text,
                "history_echo": echo_result.text,
                "history_echo_sources": echo_result.sources,
                "history_echo_ai_used": echo_result.ai_success,
                "history_echo_fallback_used": echo_result.fallback_used,
                "npc_fates": ending.npc_fates,
                "related_clue_ids": ending.related_clue_ids,
                "related_choice_ids": ending.related_choice_ids,
            }
            record["ending"] = image_generation_service.attach_visual(ending_payload, "scene_interrogation_room")

            state.status = "finished"
            self._log_call(
                record,
                module="history_echo",
                summary=f"历史回声 {ending.title}",
                success=echo_result.ai_success,
                fallback_used=echo_result.fallback_used,
                supervisor_pass=True,
            )
            self._log_call(
                record,
                module="ending_resolve",
                summary=f"结局判定 {ending.title}",
                success=True,
                fallback_used=False,
                supervisor_pass=True,
            )

        return record["ending"]

    def _require_session(self, session_id: str) -> dict:
        record = self.sessions.get(session_id)
        if record is None:
            raise GameError(code="SESSION_NOT_FOUND", message="未找到这局演示，请重新开始。", status_code=404)
        return record

    def _refresh_state_metadata(self, state: GameState) -> None:
        stage_to_scenes = {
            "intro": ["scene_front_hall", "scene_fire_yard"],
            "investigation": [
                "scene_front_hall",
                "scene_account_room",
                "scene_fire_yard",
                "scene_lamp_shelf",
                "scene_engraving_room",
                "scene_back_gate",
            ],
            "reversal": [
                "scene_front_hall",
                "scene_account_room",
                "scene_fire_yard",
                "scene_lamp_shelf",
                "scene_engraving_room",
                "scene_back_gate",
                "scene_rain_alley",
                "scene_city_gate",
                "scene_interrogation_room",
            ],
            "choice": [
                "scene_front_hall",
                "scene_account_room",
                "scene_fire_yard",
                "scene_lamp_shelf",
                "scene_engraving_room",
                "scene_back_gate",
                "scene_rain_alley",
                "scene_city_gate",
                "scene_interrogation_room",
            ],
            "ending": [state.current_scene_id],
        }
        state.available_scene_ids = stage_to_scenes[state.current_stage]
        state.available_choice_ids = [choice.choice_id for choice in self.event.choices] if state.current_stage == "choice" else []

    def _current_goal(self, stage: str) -> str:
        goals = {
            "intro": "先稳住火后的局面，找出最先不对劲的痕迹。",
            "investigation": "在矛盾证词与物证之间建立第一层证据链。",
            "reversal": "确认焚毁的并非普通诗稿，而是牵动封口命令的抄录。",
            "choice": "决定你要保全书坊、自救，还是把真相往前推一步。",
            "ending": "结局已定，查看众人命运与这场焚稿案留下的回声。",
        }
        return goals[stage]

    def _scene_payload(self, scene_id: str) -> dict:
        payload = self.scenes[scene_id].model_dump()
        return image_generation_service.attach_visual(payload, scene_id)

    def _npc_payload(self, npc_id: str) -> dict:
        payload = self.npcs[npc_id].model_dump()
        return image_generation_service.attach_visual(payload, npc_id)

    def _clue_payload(self, clue_id: str) -> dict:
        payload = self.clues[clue_id].model_dump()
        payload["discovered"] = True
        return image_generation_service.attach_visual(payload, clue_id)

    def _combo_payload(self, combo_id: str) -> dict:

        combo: ComboRule = self.combos[combo_id]
        return combo.model_dump()

    def _deduction_payload(self, deduction_id: str) -> dict:
        deduction: DeductionRule = self.deductions[deduction_id]
        return deduction.model_dump()

    def _deduction_prompt_payload(self, deduction_id: str) -> dict:
        deduction: DeductionRule = self.deductions[deduction_id]
        return {
            "deduction_id": deduction.deduction_id,
            "question": deduction.question,
        }

    def _available_deductions(self, state: GameState) -> list[str]:
        if state.current_stage == "ending":
            return []
        discovered = set(state.discovered_clue_ids)
        available: list[str] = []
        for deduction in self.deductions.values():
            if deduction.deduction_id in state.completed_deduction_ids:
                continue
            required = set(deduction.required_clue_ids or deduction.correct_clue_ids)
            if required.issubset(discovered):
                available.append(deduction.deduction_id)
        return available

    def _discover_clues(self, state: GameState, clue_ids: list[str]) -> list[dict]:
        discovered: list[dict] = []
        for clue_id in clue_ids:
            clue = self.clues.get(clue_id)
            if clue is None:
                continue
            if clue_id in state.discovered_clue_ids:
                continue
            if not self._can_release_clue(state, clue):
                continue
            state.discovered_clue_ids.append(clue_id)
            self._apply_effect_bundle(state, clue.effects)
            if clue.after_unlock_flags:
                self._apply_effect_bundle(state, {"flags": clue.after_unlock_flags})
            discovered.append(self._clue_payload(clue_id))
        return discovered

    def _can_release_clue(self, state: GameState, clue: Clue) -> bool:
        if state.current_stage not in clue.stage_available:
            return False
        conditions = clue.unlock_conditions or {}
        discovered = set(state.discovered_clue_ids)
        flags = set(state.flags)

        required_clue_ids = set(conditions.get("required_clue_ids", []))
        if not required_clue_ids.issubset(discovered):
            return False

        required_flags = set(conditions.get("required_flags", []))
        if not required_flags.issubset(flags):
            return False

        min_risk = conditions.get("min_risk")
        if min_risk is not None and state.risk_level < int(min_risk):
            return False

        max_risk = conditions.get("max_risk")
        if max_risk is not None and state.risk_level > int(max_risk):
            return False

        min_trust = conditions.get("min_trust")
        if isinstance(min_trust, dict):
            for npc_id, required_value in min_trust.items():
                if state.npc_trust.get(npc_id, 0) < int(required_value):
                    return False
        elif min_trust is not None and clue.source_npc_id:
            if state.npc_trust.get(clue.source_npc_id, 0) < int(min_trust):
                return False

        return True

    def _evaluate_combos(self, state: GameState) -> list[dict]:
        new_combos: list[dict] = []
        discovered = set(state.discovered_clue_ids)
        for combo in self.combos.values():
            if combo.combo_id in state.completed_combo_ids:
                continue
            if set(combo.required_clue_ids).issubset(discovered):
                state.completed_combo_ids.append(combo.combo_id)
                self._apply_effect_bundle(state, combo.effects)
                new_combos.append(combo.model_dump())
        return new_combos

    def _evaluate_deductions(self, state: GameState) -> list[dict]:
        return []

    def _evaluate_transitions(self, state: GameState) -> None:
        discovered = set(state.discovered_clue_ids)
        flags = set(state.flags)
        key_count = sum(1 for clue_id in state.discovered_clue_ids if self.clues[clue_id].is_key)

        if state.current_stage == "intro":
            intro_anomalies = {
                "clue_missing_manuscript_list",
                "clue_fire_origin_wrong",
                "clue_burned_page",
                "clue_red_seal",
            }
            if discovered.intersection(intro_anomalies):
                state.current_stage = "investigation"
                self._refresh_state_metadata(state)

        if state.current_stage == "investigation":
            if (
                key_count >= 3
                or "combo_fire_is_arson" in state.completed_combo_ids
                or "worker_contradiction_confirmed" in flags
            ):
                state.current_stage = "reversal"
                self._refresh_state_metadata(state)

        if state.current_stage == "reversal":
            if self._choice_requirements_met(state):
                state.current_stage = "choice"
                self._refresh_state_metadata(state)

    def _choice_requirements_met(self, state: GameState) -> bool:
        flags = set(state.flags)
        completed = set(state.completed_combo_ids)
        burned_target_confirmed = (
            "combo_burned_text_is_ledger" in completed
            or "deduced_burned_not_poem" in flags
        )
        hidden_chain_confirmed = (
            "combo_hidden_chain" in completed
            or "deduced_hidden_chain" in flags
        )
        return burned_target_confirmed and hidden_chain_confirmed

    def _apply_effect_bundle(self, state: GameState, effects: dict) -> None:
        for score_name in ("truth", "order", "survival", "sacrifice"):
            if score_name in effects:
                current_value = getattr(state.scores, score_name)
                setattr(state.scores, score_name, current_value + int(effects[score_name]))
        if "scores" in effects:
            for score_name, delta in effects["scores"].items():
                current_value = getattr(state.scores, score_name)
                setattr(state.scores, score_name, current_value + int(delta))
        if "score_delta" in effects:
            for score_name, delta in effects["score_delta"].items():
                current_value = getattr(state.scores, score_name)
                setattr(state.scores, score_name, current_value + int(delta))
        if "risk" in effects:
            state.risk_level = max(0, state.risk_level + int(effects["risk"]))
        if "risk_delta" in effects:
            state.risk_level = max(0, state.risk_level + int(effects["risk_delta"]))
        if "flags" in effects:
            for flag in effects["flags"]:
                if flag not in state.flags:
                    state.flags.append(flag)
        if "add_flags" in effects:
            for flag in effects["add_flags"]:
                if flag not in state.flags:
                    state.flags.append(flag)
        if "trust" in effects:
            for npc_id, delta in effects["trust"].items():
                self._change_trust(state, npc_id, int(delta))

    def _apply_dialogue_effects(self, state: GameState, npc_id: str, response: DialogueRuleResponse) -> None:
        if response.trust_delta:
            self._change_trust(state, npc_id, response.trust_delta)
        if response.score_delta:
            self._apply_effect_bundle(state, {"scores": response.score_delta})
        if response.risk_delta:
            self._apply_effect_bundle(state, {"risk": response.risk_delta})
        if response.add_flags:
            self._apply_effect_bundle(state, {"flags": response.add_flags})

    def _apply_choice_effects(self, state: GameState, effects: dict) -> None:
        self._apply_effect_bundle(state, effects)

    def _change_trust(self, state: GameState, npc_id: str, delta: int) -> None:
        current = state.npc_trust.get(npc_id, 0)
        state.npc_trust[npc_id] = max(-2, min(3, current + delta))

    def _pick_dialogue_rule(self, *, state: GameState, request: DialogueRequest) -> DialogueRule | None:
        candidate_rules = self.dialogue_rules.get(request.npc_id, [])
        message = request.message.strip()
        presented = set(request.presented_clue_ids)
        matched: list[DialogueRule] = []
        for rule in candidate_rules:
            if rule.stage != state.current_stage:
                continue
            trigger = rule.trigger
            if trigger.presented_clue_ids and not set(trigger.presented_clue_ids).issubset(presented):
                continue
            if trigger.keywords and not any(keyword in message for keyword in trigger.keywords):
                continue
            if trigger.min_trust is not None and state.npc_trust.get(request.npc_id, 0) < trigger.min_trust:
                continue
            if trigger.required_flags and not set(trigger.required_flags).issubset(set(state.flags)):
                continue
            matched.append(rule)
        matched.sort(key=lambda item: item.priority, reverse=True)
        return matched[0] if matched else None

    def _fallback_response_for_npc(self, npc_name: str) -> DialogueRuleResponse:
        return DialogueRuleResponse(
            npc_dialogue=f"{npc_name}沉默了片刻，只说现在还不能把话说得太满。",
            npc_action="对方压低声音，明显在权衡是否继续开口。",
            emotion="guarded",
            released_clue_ids=[],
            suggested_questions=["你在怕谁？", "昨夜到底是谁先到火场？"],
            trust_delta=0,
            score_delta={},
            risk_delta=0,
            add_flags=[],
        )

    def _pick_ending(self, state: GameState) -> EndingRule:
        flags = set(state.flags)
        discovered = set(state.discovered_clue_ids)
        trust = state.npc_trust
        if (
            "found_hidden_chain" in flags
            and "preserved_evidence" in flags
            and ("ledger_truth_exposed" in flags or "deduced_burned_not_poem" in flags)
            and "deduced_scholar_motive" in flags
            and "clue_poem_hidden_copy" in discovered
            and trust.get("npc_jinyiwei", 0) >= 2
            and trust.get("npc_scholar", 0) >= 2
            and state.risk_level <= 6
            and state.final_choice_id == "choice_reverse_trace"
        ):
            return self.endings["ending_hidden"]
        if state.final_choice_id == "choice_force_worker":
            return self.endings["ending_tragedy"]
        if (
            state.scores.truth >= 5
            and "preserved_evidence" in flags
            and state.final_choice_id in {"choice_help_scholar", "choice_reverse_trace"}
        ):
            return self.endings["ending_truth"]
        if state.scores.order >= 4 or state.final_choice_id == "choice_give_to_lu":
            return self.endings["ending_order"]
        if state.scores.survival >= 4 or state.final_choice_id == "choice_destroy_evidence":
            return self.endings["ending_survival"]
        if state.risk_level >= 6 and (
            trust.get("npc_jinyiwei", 0) < 1 or trust.get("npc_scholar", 0) < 1
        ):
            return self.endings["ending_tragedy"]
        return self.endings["ending_truth"]

    def _log_call(
        self,
        record: dict,
        *,
        module: str,
        summary: str,
        success: bool,
        fallback_used: bool,
        supervisor_pass: bool,
    ) -> None:
        entry = DebugLogEntry(
            call_id=f"log_{uuid4().hex[:8]}",
            module=module,
            summary=summary,
            success=success,
            fallback_used=fallback_used,
            supervisor_pass=supervisor_pass,
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
        record["logs"].append(entry)


engine = GameEngine()
