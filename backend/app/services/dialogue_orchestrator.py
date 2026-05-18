from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from app.core.config import Settings, settings
from app.models.game_models import (
    Clue,
    DialogueRequest,
    DialogueRuleResponse,
    DynastyProfile,
    GameState,
    NPCProfile,
    PlayerIdentity,
    PlayerRole,
    Scene,
    SupervisorIssue,
    SupervisorResult,
)
from app.services.ai_client import AIClient, AIResponse
from app.services.log_service import LogService, log_service
from app.services.rag_retriever import RAGRetriever
from app.services.repair_agent import RepairAgent
from app.services.script_bound_chat import ScriptBoundChatContext
from app.services.supervisor import SupervisorService



NPC_DIALOGUE_SCHEMA_HINT: dict[str, Any] = {
    "npc_dialogue": "中文字符串",
    "npc_action": "中文字符串",
    "emotion": "fearful|calm|angry|hesitant|defensive",
    "released_clue_ids": [],
    "highlight_clues": [],
    "suggested_questions": ["中文问题"],
    "state_update_suggestion": {
        "npc_trust_delta": 0,
        "truth_score_delta": 0,
        "order_score_delta": 0,
        "survival_score_delta": 0,
        "risk_level_delta": 0,
        "new_flags": [],
    },
}


@dataclass
class OrchestratedDialogueResult:
    response: DialogueRuleResponse
    supervisor_result: SupervisorResult
    fallback_used: bool
    ai_success: bool
    log_entry: dict[str, Any] | None = None
    rag_hit_count: int = 0
    rag_source_ids: list[str] | None = None
    rag_material_types: list[str] | None = None
    repair_attempted: bool = False
    repair_success: bool = False




class DialogueOrchestrator:
    def __init__(
        self,
        *,
        ai_client: AIClient | None = None,
        runtime_settings: Settings | None = None,
        logs: LogService | None = None,
        rag_retriever: RAGRetriever | None = None,
        repair_agent: RepairAgent | None = None,
    ) -> None:
        self.settings = runtime_settings or settings
        self.ai_client = ai_client or AIClient(self.settings)
        self.log_service = logs or log_service
        self.rag_retriever = rag_retriever or RAGRetriever()
        self.repair_agent = repair_agent or RepairAgent(ai_client=self.ai_client, runtime_settings=self.settings)
        backend_root = Path(__file__).resolve().parents[2]
        self.prompt_path = backend_root / "data" / "prompts" / "npc_dialogue.md"


    def handle_dialogue(
        self,
        *,
        state: GameState,
        dynasty: DynastyProfile,
        player_role: PlayerRole,
        current_scene: Scene,
        npc: NPCProfile,
        request: DialogueRequest,
        discovered_clues: list[Clue],
        presented_clues: list[Clue],
        clue_map: dict[str, Clue],
        mock_response: DialogueRuleResponse,
        supervisor: SupervisorService,
        script_context: ScriptBoundChatContext | None = None,
        player_identity: PlayerIdentity | None = None,
    ) -> OrchestratedDialogueResult | None:
        if self.settings.use_mock_ai:
            return None

        input_summary = self._input_summary(state=state, npc=npc, request=request)
        if self.settings.ai_provider != "deepseek" or not self.settings.deepseek_api_key_available:
            issue = SupervisorIssue(
                type="ai_config_missing",
                severity="medium",
                detail="真实 AI 配置不可用，已使用本地中文回复。",
            )
            supervisor_result = SupervisorResult(
                pass_=False,
                issues=[issue],
                repair_instruction="继续使用本地 Mock 对话，保持游戏可用。",
            )
            log_entry = self._record_call(
                input_summary=input_summary,
                ai_response=AIResponse(
                    success=False,
                    parsed_json={},
                    raw_text="",
                    latency_ms=0,
                    fallback_used=True,
                    error_message="未检测到 DeepSeek Key 或提供方配置不正确，已回退到本地回复。",
                    model=self.settings.deepseek_model,
                ),
                supervisor_result=supervisor_result,
                prompt=None,
                fallback_used=True,
                rag_hit_count=0,
                repair_attempted=False,
                repair_success=False,
            )
            return OrchestratedDialogueResult(
                response=mock_response,
                supervisor_result=supervisor_result,
                fallback_used=True,
                ai_success=False,
                log_entry=log_entry,
            )

        rag_hits = self.rag_retriever.retrieve(
            dynasty_id=state.dynasty_id,
            current_stage=state.current_stage,
            current_scene_id=state.current_scene_id,
            npc_id=npc.npc_id,
            player_message=request.message,
            presented_clue_ids=request.presented_clue_ids,
            discovered_clue_ids=state.discovered_clue_ids,
            top_k=8,
        )
        rag_source_ids = self._rag_source_ids(rag_hits)
        rag_material_types = self._rag_material_types(rag_hits)
        prompt = self._build_prompt(

            state=state,
            dynasty=dynasty,
            player_role=player_role,
            player_identity=player_identity,
            current_scene=current_scene,
            npc=npc,
            request=request,
            discovered_clues=discovered_clues,
            presented_clues=presented_clues,
            clue_map=clue_map,
            rag_hits=rag_hits,
            script_context=script_context,
        )
        ai_response = self.ai_client.generate_json_sync(
            module="NPCDialogueAgent",
            prompt=prompt,
            schema_hint=NPC_DIALOGUE_SCHEMA_HINT,
        )

        repair_attempted = False
        repair_success = False
        repair_log_entry: dict[str, Any] | None = None

        if not ai_response.success:
            supervisor_result = SupervisorResult(
                pass_=False,
                issues=[
                    SupervisorIssue(
                        type="invalid_json" if ai_response.raw_text else "ai_call_failed",
                        severity="high" if ai_response.raw_text else "medium",
                        detail=ai_response.error_message or "AI 调用失败，已使用本地中文回复。",
                    )
                ],
                repair_instruction="如果原始输出包含可修复内容，只输出符合 Schema 的中文 JSON；否则使用本地 Mock 对话。",
            )
            repaired = None
            if ai_response.raw_text:
                repair_attempted = True
                repaired, supervisor_result, repair_ai_response = self._attempt_repair(
                    original_response={"raw_text": ai_response.raw_text},
                    initial_supervisor_result=supervisor_result,
                    state=state,
                    dynasty=dynasty,
                    player_role=player_role,
                    player_identity=player_identity,
                    current_scene=current_scene,
                    npc=npc,
                    request=request,
                    clue_map=clue_map,
                    supervisor=supervisor,
                    script_context=script_context,
                )
                repair_success = repaired is not None and supervisor_result.pass_
                repair_log_entry = self._record_repair_call(
                    input_summary=input_summary,
                    repair_ai_response=repair_ai_response,
                    supervisor_result=supervisor_result,
                )
            if repaired is not None:
                log_entry = self._record_call(
                    input_summary=input_summary,
                    ai_response=ai_response,
                    supervisor_result=supervisor_result,
                    prompt=prompt,
                    fallback_used=False,
                    rag_hit_count=len(rag_hits),
                    repair_attempted=repair_attempted,
                    repair_success=repair_success,
                    repair_call_id=repair_log_entry.get("call_id") if repair_log_entry else None,
                    rag_source_ids=rag_source_ids,
                    rag_material_types=rag_material_types,
                )
                return OrchestratedDialogueResult(
                    response=repaired,
                    supervisor_result=supervisor_result,
                    fallback_used=False,
                    ai_success=True,
                    log_entry=log_entry,
                    rag_hit_count=len(rag_hits),
                    rag_source_ids=rag_source_ids,
                    rag_material_types=rag_material_types,
                    repair_attempted=repair_attempted,
                    repair_success=repair_success,
                )

            log_entry = self._record_call(
                input_summary=input_summary,
                ai_response=ai_response,
                supervisor_result=supervisor_result,
                prompt=prompt,
                fallback_used=True,
                rag_hit_count=len(rag_hits),
                repair_attempted=repair_attempted,
                repair_success=repair_success,
                repair_call_id=repair_log_entry.get("call_id") if repair_log_entry else None,
                rag_source_ids=rag_source_ids,
                rag_material_types=rag_material_types,
            )
            return OrchestratedDialogueResult(
                response=mock_response,
                supervisor_result=supervisor_result,
                fallback_used=True,
                ai_success=False,
                log_entry=log_entry,
                rag_hit_count=len(rag_hits),
                rag_source_ids=rag_source_ids,
                rag_material_types=rag_material_types,
                repair_attempted=repair_attempted,
                repair_success=repair_success,
            )


        try:
            response = self._dialogue_response_from_ai(ai_response.parsed_json)
        except ValueError as exc:
            supervisor_result = SupervisorResult(
                pass_=False,
                issues=[SupervisorIssue(type="invalid_json", severity="high", detail=str(exc))],
                repair_instruction="补齐缺失字段，只输出符合 Schema 的中文 JSON。",
            )
            repair_attempted = True
            repaired, supervisor_result, repair_ai_response = self._attempt_repair(
                original_response=ai_response.parsed_json or {"raw_text": ai_response.raw_text},
                initial_supervisor_result=supervisor_result,
                state=state,
                dynasty=dynasty,
                player_role=player_role,
                player_identity=player_identity,
                current_scene=current_scene,
                npc=npc,
                request=request,
                clue_map=clue_map,
                supervisor=supervisor,
                script_context=script_context,
            )
            repair_success = repaired is not None and supervisor_result.pass_
            repair_log_entry = self._record_repair_call(
                input_summary=input_summary,
                repair_ai_response=repair_ai_response,
                supervisor_result=supervisor_result,
            )
            log_entry = self._record_call(
                input_summary=input_summary,
                ai_response=ai_response,
                supervisor_result=supervisor_result,
                prompt=prompt,
                fallback_used=repaired is None,
                rag_hit_count=len(rag_hits),
                repair_attempted=repair_attempted,
                repair_success=repair_success,
                repair_call_id=repair_log_entry.get("call_id") if repair_log_entry else None,
                rag_source_ids=rag_source_ids,
                rag_material_types=rag_material_types,
            )
            return OrchestratedDialogueResult(
                response=repaired or mock_response,
                supervisor_result=supervisor_result,
                fallback_used=repaired is None,
                ai_success=True,
                log_entry=log_entry,
                rag_hit_count=len(rag_hits),
                rag_source_ids=rag_source_ids,
                rag_material_types=rag_material_types,
                repair_attempted=repair_attempted,
                repair_success=repair_success,
            )


        supervisor_result = supervisor.review_dialogue(
            stage=state.current_stage,
            dynasty=dynasty,
            npc=npc,
            response=response,
            clue_map=clue_map,
            player_message=request.message,
            player_role=player_role,
            player_identity=player_identity,
            allowed_released_clue_ids=script_context.allowed_released_clue_ids if script_context else None,
            intent=script_context.intent if script_context else response.intent,
            discovered_clue_ids=state.discovered_clue_ids,
        )
        final_response = response
        fallback_used = False
        if not supervisor_result.pass_:
            repair_attempted = True
            repaired, supervisor_result, repair_ai_response = self._attempt_repair(
                original_response=ai_response.parsed_json,
                initial_supervisor_result=supervisor_result,
                state=state,
                dynasty=dynasty,
                player_role=player_role,
                player_identity=player_identity,
                current_scene=current_scene,
                npc=npc,
                request=request,
                clue_map=clue_map,
                supervisor=supervisor,
                script_context=script_context,
            )
            repair_success = repaired is not None and supervisor_result.pass_
            repair_log_entry = self._record_repair_call(
                input_summary=input_summary,
                repair_ai_response=repair_ai_response,
                supervisor_result=supervisor_result,
            )
            if repaired is not None:
                final_response = repaired
            else:
                final_response = mock_response
                fallback_used = True

        log_entry = self._record_call(
            input_summary=input_summary,
            ai_response=ai_response,
            supervisor_result=supervisor_result,
            prompt=prompt,
            fallback_used=fallback_used,
            rag_hit_count=len(rag_hits),
            repair_attempted=repair_attempted,
            repair_success=repair_success,
            repair_call_id=repair_log_entry.get("call_id") if repair_log_entry else None,
            rag_source_ids=rag_source_ids,
            rag_material_types=rag_material_types,
        )
        return OrchestratedDialogueResult(
            response=final_response,
            supervisor_result=supervisor_result,
            fallback_used=fallback_used,
            ai_success=True,
            log_entry=log_entry,
            rag_hit_count=len(rag_hits),
            rag_source_ids=rag_source_ids,
            rag_material_types=rag_material_types,
            repair_attempted=repair_attempted,
            repair_success=repair_success,
        )




    def _build_prompt(
        self,
        *,
        state: GameState,
        dynasty: DynastyProfile,
        player_role: PlayerRole,
        player_identity: PlayerIdentity | None = None,
        current_scene: Scene,
        npc: NPCProfile,
        request: DialogueRequest,
        discovered_clues: list[Clue],
        presented_clues: list[Clue],
        clue_map: dict[str, Clue],
        rag_hits: list[dict[str, Any]],
        script_context: ScriptBoundChatContext | None = None,
    ) -> str:

        template = self.prompt_path.read_text(encoding="utf-8")
        allowed_current_stage_clues = [
            clue_id
            for clue_id in npc.releasable_clue_ids
            if clue_id in clue_map and state.current_stage in clue_map[clue_id].stage_available
        ]
        allowed_script_clues = script_context.allowed_released_clue_ids if script_context else allowed_current_stage_clues
        npc_permission = {
            "known_info": npc.known_info,
            "unknown_info": npc.unknown_info,
            "forbidden_disclosure": npc.forbidden_disclosure,
            "releasable_clue_ids": npc.releasable_clue_ids,
            "allowed_current_stage_clue_ids": allowed_current_stage_clues,
            "allowed_script_bound_clue_ids": allowed_script_clues,
            "stage_limits": npc.stage_limits,
        }
        script_payload = self._script_context_payload(script_context)
        replacements = {
            "{dynasty_name}": dynasty.name,
            "{current_stage}": state.current_stage,
            "{current_scene}": json.dumps(current_scene.model_dump(), ensure_ascii=False),
            "{player_role}": json.dumps(player_role.model_dump(), ensure_ascii=False),
            "{player_identity_context}": self._player_identity_context(player_role=player_role, player_identity=player_identity),
            "{npc_profile_json}": json.dumps(npc.model_dump(), ensure_ascii=False),
            "{npc_permission_json}": json.dumps(npc_permission, ensure_ascii=False),
            "{discovered_clues_json}": json.dumps([clue.model_dump() for clue in discovered_clues], ensure_ascii=False),
            "{presented_clues_json}": json.dumps([clue.model_dump() for clue in presented_clues], ensure_ascii=False),
            "{npc_trust}": str(state.npc_trust.get(npc.npc_id, npc.initial_trust)),
            "{rag_context}": self._format_rag_context(rag_hits),
            "{player_message}": request.message,
            "{script_bound_context_json}": json.dumps(script_payload, ensure_ascii=False),

        }
        prompt = template
        for placeholder, value in replacements.items():
            prompt = prompt.replace(placeholder, value)
        return prompt

    def _player_identity_context(self, *, player_role: PlayerRole, player_identity: PlayerIdentity | None) -> str:
        if player_identity is None:
            return (
                f"身份名称：{player_role.name}\n"
                f"归一身份：{player_role.name}\n"
                "社会地位：low\n"
                f"个人背景：{player_role.social_position}\n"
                f"身份标签：{json.dumps(player_role.permissions, ensure_ascii=False)}"
            )
        return (
            f"身份名称：{player_identity.display_name}\n"
            f"归一身份：{player_identity.normalized_name}\n"
            f"社会地位：{player_identity.social_rank}\n"
            f"个人背景：{player_identity.background}\n"
            f"身份标签：{json.dumps(player_identity.tags, ensure_ascii=False)}"
        )

    def _format_rag_context(self, rag_hits: list[dict[str, Any]]) -> str:
        grouped = self._group_rag_hits(rag_hits)
        if not rag_hits:
            return "【RAG 硬约束】\n- 未检索到额外硬约束；仍必须遵守角色卡、线索白名单、当前阶段和后端结局规则。\n\n【RAG 历史制度参考】\n- 无额外制度参考。\n\n【RAG 场景与器物细节】\n- 无额外细节；不要自行编造可用线索。\n\n【RAG NPC 口吻参考】\n- 仍以 NPC 角色卡 speaking_style 为准。\n\n【RAG 禁止使用内容】\n- 不得释放非法线索、不得跳阶段、不得决定结局、不得剧透幕后真相。"

        sections = [
            ("【RAG 硬约束】", ["hard_rule", "clue_boundary"]),
            ("【RAG 历史制度参考】", ["institution"]),
            ("【RAG 场景与器物细节】", ["space_detail", "object_detail", "daily_life", "occupation", "scene_atmosphere"]),
            ("【RAG NPC 口吻参考】", ["dialogue_lexicon"]),
            ("【RAG 禁止使用内容】", ["forbidden_content"]),
        ]
        lines: list[str] = []
        for title, material_types in sections:
            lines.append(title)
            section_hits = [hit for material_type in material_types for hit in grouped.get(material_type, [])]
            if not section_hits:
                lines.append("- 无。")
            for hit in section_hits[:4]:
                lines.append(
                    "- "
                    f"source_id={hit.get('source_id')}；"
                    f"topic={hit.get('topic')}；"
                    f"level={hit.get('source_level')}；"
                    f"severity={hit.get('severity')}；"
                    f"content={hit.get('content')}；"
                    f"usage_rule={hit.get('usage_rule')}"
                )
            lines.append("")
        return "\n".join(lines).strip()

    def _group_rag_hits(self, rag_hits: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for hit in rag_hits:
            grouped.setdefault(str(hit.get("material_type") or "unknown"), []).append(hit)
        return grouped

    def _rag_source_ids(self, rag_hits: list[dict[str, Any]]) -> list[str]:
        return [str(hit.get("source_id")) for hit in rag_hits if hit.get("source_id")]

    def _rag_material_types(self, rag_hits: list[dict[str, Any]]) -> list[str]:
        return sorted({str(hit.get("material_type")) for hit in rag_hits if hit.get("material_type")})


    def _attempt_repair(
        self,
        *,
        original_response: dict[str, Any],
        initial_supervisor_result: SupervisorResult,
        state: GameState,
        dynasty: DynastyProfile,
        player_role: PlayerRole,
        player_identity: PlayerIdentity | None,
        current_scene: Scene,
        npc: NPCProfile,
        request: DialogueRequest,
        clue_map: dict[str, Clue],
        supervisor: SupervisorService,
        script_context: ScriptBoundChatContext | None = None,
    ) -> tuple[DialogueRuleResponse | None, SupervisorResult, AIResponse]:
        repair_ai_response = self.repair_agent.repair_dialogue_json(
            original_response=original_response,
            supervisor_issues=initial_supervisor_result.issues,
            repair_instruction=initial_supervisor_result.repair_instruction or "输出合规中文 JSON。",
            context_summary=self._repair_context_summary(
                state=state,
                dynasty=dynasty,
                player_role=player_role,
                player_identity=player_identity,
                current_scene=current_scene,
                npc=npc,
                request=request,
                clue_map=clue_map,
                script_context=script_context,
            ),
            schema_hint=NPC_DIALOGUE_SCHEMA_HINT,
        )
        if not repair_ai_response.success:
            return (
                None,
                SupervisorResult(
                    pass_=False,
                    issues=[
                        *initial_supervisor_result.issues,
                        SupervisorIssue(
                            type="repair_failed",
                            severity="high",
                            detail=repair_ai_response.error_message or "修复模型未返回合规 JSON，已使用本地中文回复。",
                        ),
                    ],
                    repair_instruction="修复失败，使用本地 Mock 对话。",
                ),
                repair_ai_response,
            )
        try:
            repaired_response = self._dialogue_response_from_ai(repair_ai_response.parsed_json)
        except ValueError as exc:
            return (
                None,
                SupervisorResult(
                    pass_=False,
                    issues=[
                        *initial_supervisor_result.issues,
                        SupervisorIssue(type="repair_invalid_json", severity="high", detail=str(exc)),
                    ],
                    repair_instruction="修复 JSON 仍不合规，使用本地 Mock 对话。",
                ),
                repair_ai_response,
            )
        repaired_supervisor = supervisor.review_dialogue(
            stage=state.current_stage,
            dynasty=dynasty,
            npc=npc,
            response=repaired_response,
            clue_map=clue_map,
            player_message=request.message,
            player_role=player_role,
            player_identity=player_identity,
            allowed_released_clue_ids=script_context.allowed_released_clue_ids if script_context else None,
            intent=script_context.intent if script_context else repaired_response.intent,
            discovered_clue_ids=state.discovered_clue_ids,
        )
        if not repaired_supervisor.pass_:
            return None, repaired_supervisor, repair_ai_response
        return repaired_response, repaired_supervisor, repair_ai_response

    def _repair_context_summary(
        self,
        *,
        state: GameState,
        dynasty: DynastyProfile,
        player_role: PlayerRole,
        player_identity: PlayerIdentity | None,
        current_scene: Scene,
        npc: NPCProfile,
        request: DialogueRequest,
        clue_map: dict[str, Clue],
        script_context: ScriptBoundChatContext | None = None,
    ) -> dict[str, Any]:
        allowed_current_stage_clues = [
            clue_id
            for clue_id in npc.releasable_clue_ids
            if clue_id in clue_map and state.current_stage in clue_map[clue_id].stage_available
        ]
        return {
            "dynasty_id": dynasty.dynasty_id,
            "dynasty_name": dynasty.name,
            "current_stage": state.current_stage,
            "current_scene_id": current_scene.scene_id,
            "player_role": player_role.name,
            "player_identity": player_identity.model_dump() if player_identity else None,
            "npc_id": npc.npc_id,
            "npc_name": npc.name,
            "player_message": request.message,
            "presented_clue_ids": request.presented_clue_ids,
            "discovered_clue_ids": state.discovered_clue_ids,
            "allowed_released_clue_ids": allowed_current_stage_clues,
            "script_bound_allowed_clue_ids": script_context.allowed_released_clue_ids if script_context else allowed_current_stage_clues,
            "script_bound_intent": script_context.intent if script_context else "",
            "script_bound_blocked_clues": script_context.blocked_clues if script_context else [],
            "script_bound_suggested_questions": script_context.suggested_questions if script_context else [],
            "forbidden_disclosure": npc.forbidden_disclosure,
            "stage_limit": npc.stage_limits.get(state.current_stage, ""),
        }

    def _dialogue_response_from_ai(self, payload: dict[str, Any]) -> DialogueRuleResponse:

        missing = [key for key in NPC_DIALOGUE_SCHEMA_HINT.keys() if key not in payload]
        if missing:
            raise ValueError(f"AI JSON 缺少字段：{', '.join(missing)}")

        emotion = payload.get("emotion")
        if emotion not in {"fearful", "calm", "angry", "hesitant", "defensive"}:
            raise ValueError("AI JSON 的 emotion 字段不在允许范围内。")

        dialogue = payload.get("npc_dialogue")
        action = payload.get("npc_action")
        released = payload.get("released_clue_ids")
        suggested = payload.get("suggested_questions")
        if not isinstance(dialogue, str) or not dialogue.strip():
            raise ValueError("AI JSON 的 npc_dialogue 字段无效。")
        if not isinstance(action, str) or not action.strip():
            raise ValueError("AI JSON 的 npc_action 字段无效。")
        if not isinstance(released, list) or not all(isinstance(item, str) for item in released):
            raise ValueError("AI JSON 的 released_clue_ids 字段无效。")
        if not isinstance(suggested, list) or not all(isinstance(item, str) for item in suggested):
            raise ValueError("AI JSON 的 suggested_questions 字段无效。")
        if not isinstance(payload.get("state_update_suggestion"), dict):
            raise ValueError("AI JSON 的 state_update_suggestion 字段无效。")

        state_update = payload.get("state_update_suggestion") or {}
        score_delta = payload.get("score_delta")
        if not isinstance(score_delta, dict):
            score_delta = {
                "truth": state_update.get("truth_score_delta", 0),
                "order": state_update.get("order_score_delta", 0),
                "survival": state_update.get("survival_score_delta", 0),
            }
        clean_score_delta = {
            str(key): self._clamp_int(value, -1, 1)
            for key, value in score_delta.items()
            if str(key) in {"truth", "order", "survival", "sacrifice"} and self._is_int_like(value)
        }
        highlight_clues = self._parse_highlight_clues(payload.get("highlight_clues"))
        red_texts = [str(item).strip() for item in payload.get("red_texts", []) if str(item).strip()] if isinstance(payload.get("red_texts", []), list) else []
        supervisor_notes = (
            [str(item).strip() for item in payload.get("supervisor_notes", []) if str(item).strip()]
            if isinstance(payload.get("supervisor_notes", []), list)
            else []
        )

        return DialogueRuleResponse(
            npc_dialogue=dialogue.strip(),
            npc_action=action.strip(),
            emotion=emotion,
            intent=str(payload.get("intent") or "ask_object"),
            released_clue_ids=released,
            highlight_clues=highlight_clues,
            red_texts=red_texts,
            suggested_questions=[item.strip() for item in suggested[:3] if item.strip()],
            trust_delta=self._clamp_int(payload.get("trust_delta", state_update.get("npc_trust_delta", 0)), -1, 1),
            score_delta=clean_score_delta,
            risk_delta=self._clamp_int(payload.get("risk_delta", state_update.get("risk_level_delta", 0)), -1, 1),
            add_flags=self._string_list(payload.get("add_flags", state_update.get("new_flags", []))),
            supervisor_notes=supervisor_notes,
        )

    def _parse_highlight_clues(self, value: Any) -> list[dict[str, str]]:
        if not isinstance(value, list):
            return []
        highlights: list[dict[str, str]] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            clue_id = str(item.get("clue_id", "")).strip()
            highlight_text = str(item.get("highlight_text", "")).strip()
            display_text = str(item.get("display_text", "")).strip()
            if clue_id and highlight_text and display_text:
                highlights.append(
                    {
                        "clue_id": clue_id,
                        "highlight_text": highlight_text,
                        "display_text": display_text,
                    }
                )
        return highlights

    def _string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    def _is_int_like(self, value: Any) -> bool:
        try:
            int(value)
        except (TypeError, ValueError):
            return False
        return True

    def _clamp_int(self, value: Any, minimum: int, maximum: int) -> int:
        if not self._is_int_like(value):
            return 0
        return max(minimum, min(maximum, int(value)))

    def _script_context_payload(self, script_context: ScriptBoundChatContext | None) -> dict[str, Any]:
        if script_context is None:
            return {
                "intent": "",
                "allowed_released_clue_ids": [],
                "candidate_clue_ids": [],
                "blocked_clues": [],
                "recent_turns": [],
                "suggested_questions": [],
                "supervisor_notes": [],
            }
        return {
            "intent": script_context.intent,
            "npc_trust": script_context.npc_trust,
            "discovered_clue_ids": script_context.discovered_clue_ids,
            "candidate_clue_ids": script_context.candidate_clue_ids,
            "preferred_clue_ids": script_context.preferred_clue_ids,
            "allowed_released_clue_ids": script_context.allowed_released_clue_ids,
            "blocked_clues": script_context.blocked_clues,
            "recent_turns": script_context.recent_turns,
            "suggested_questions": script_context.suggested_questions,
            "supervisor_notes": script_context.supervisor_notes,
        }

    def _record_call(
        self,
        *,
        input_summary: str,
        ai_response: AIResponse,
        supervisor_result: SupervisorResult,
        prompt: str | None,
        fallback_used: bool,
        rag_hit_count: int,
        repair_attempted: bool,
        repair_success: bool,
        repair_call_id: str | None = None,
        rag_source_ids: list[str] | None = None,
        rag_material_types: list[str] | None = None,
    ) -> dict[str, Any]:
        return self.log_service.record_ai_call(
            module="NPCDialogueAgent",
            model=ai_response.model,
            input_summary=input_summary,
            latency_ms=ai_response.latency_ms,
            success=ai_response.success,
            fallback_used=fallback_used,
            supervisor_pass=supervisor_result.pass_,
            issues=supervisor_result.issues,
            prompt=prompt,
            raw_response=ai_response.raw_text,
            extra_fields={
                "ai_mode": self._ai_mode(),
                "rag_hit_count": rag_hit_count,
                "rag_source_ids": rag_source_ids or [],
                "rag_material_types": rag_material_types or [],
                "repair_attempted": repair_attempted,
                "repair_success": repair_success,
                "repair_call_id": repair_call_id,
            },

        )


    def _record_repair_call(
        self,
        *,
        input_summary: str,
        repair_ai_response: AIResponse,
        supervisor_result: SupervisorResult,
    ) -> dict[str, Any]:
        return self.log_service.record_ai_call(
            module="RepairAgent",
            model=repair_ai_response.model,
            input_summary=f"修复 {input_summary}",
            latency_ms=repair_ai_response.latency_ms,
            success=repair_ai_response.success,
            fallback_used=not supervisor_result.pass_,
            supervisor_pass=supervisor_result.pass_,
            issues=supervisor_result.issues,
            prompt=getattr(self.repair_agent, "last_prompt", None),
            raw_response=repair_ai_response.raw_text,
            extra_fields={
                "ai_mode": self._ai_mode(),
                "repair_attempted": True,
                "repair_success": supervisor_result.pass_,
            },
        )

    def _ai_mode(self) -> str:
        if self.settings.use_mock_ai or self.settings.ai_provider == "mock":
            return "mock"
        if self.settings.ai_provider == "deepseek" and self.settings.deepseek_api_key_available:
            return "real"
        return "unavailable"


    def _input_summary(self, *, state: GameState, npc: NPCProfile, request: DialogueRequest) -> str:

        message = request.message.strip().replace("\n", " ")[:60]
        return f"NPC={npc.name}，阶段={state.current_stage}，玩家问题={message}"
