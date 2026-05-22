from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import settings
from app.models.game_models import (
    ChoiceRequest,
    DeductionSubmitRequest,
    DialogueRequest,
    EndingResolveRequest,
    InvestigateRequest,
    PlayerIdentityValidationRequest,
    SessionStartRequest,
)
from app.services.ai_client import AIClient
from app.services.game_engine import GameError, engine
from app.services.log_service import log_service


router = APIRouter(prefix="/api")


class AssistantHintRequest(BaseModel):
    session_id: str
    question: str


ASSISTANT_SCHEMA_HINT: dict[str, Any] = {
    "answer": "中文提示，不剧透最终真相",
    "suggested_focus": ["中文调查方向"],
    "safety_note": "中文边界说明",
}


def _error_response(error: GameError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details,
            }
        },
    )


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


@router.get("/health")

def get_health() -> dict:
    return engine.health()


@router.get("/dynasties")
def get_dynasties() -> dict:
    return engine.list_dynasties()


@router.get("/roles")
def get_roles(dynasty_id: str = Query("ming")):
    try:
        return engine.list_roles(dynasty_id)
    except GameError as error:
        return _error_response(error)


@router.get("/player-identities")
def get_player_identities(event_id: str = Query("ming_bookshop_fire"), dynasty_id: str = Query("ming")):
    try:
        return engine.list_player_identities(dynasty_id=dynasty_id, event_id=event_id)
    except GameError as error:
        return _error_response(error)


@router.post("/player-identity/validate")
def post_player_identity_validate(request: PlayerIdentityValidationRequest):
    try:
        return engine.validate_player_identity(request)
    except GameError as error:
        return _error_response(error)


@router.post("/session/start")
def start_session(request: SessionStartRequest):
    try:
        return engine.start_session(request)
    except GameError as error:
        return _error_response(error)


@router.get("/session/{session_id}")
def get_session(session_id: str):
    try:
        return engine.get_session(session_id)
    except GameError as error:
        return _error_response(error)


@router.post("/dialogue")
def post_dialogue(request: DialogueRequest):
    try:
        return engine.dialogue(request)
    except GameError as error:
        return _error_response(error)


@router.post("/debug/rag/preview")
def post_rag_preview(request: dict[str, Any]):
    missing_fields = [field for field in ["dynasty_id", "current_stage"] if not str(request.get(field, "")).strip()]
    if missing_fields:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "BAD_REQUEST",
                    "message": f"缺少必要字段：{', '.join(missing_fields)}。",
                    "details": {"missing_fields": missing_fields},
                }
            },
        )

    try:
        top_k = int(request.get("top_k", 8))
    except (TypeError, ValueError):
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "top_k 必须是数字。",
                    "details": {"field": "top_k"},
                }
            },
        )

    try:
        return engine.dialogue_orchestrator.rag_retriever.preview(
            dynasty_id=str(request.get("dynasty_id", "")).strip(),
            current_stage=str(request.get("current_stage", "")).strip(),
            current_scene_id=str(request.get("current_scene_id", "")).strip(),
            npc_id=str(request.get("npc_id", "")).strip(),
            player_message=str(request.get("player_message", "")),
            presented_clue_ids=_string_list(request.get("presented_clue_ids")),
            discovered_clue_ids=_string_list(request.get("discovered_clue_ids")),
            top_k=top_k,
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "RAG_PREVIEW_FAILED",
                    "message": "RAG 调试预览失败，请检查输入后重试。",
                    "details": {"reason": str(exc)[:80]},
                }
            },
        )


def _assistant_prompt(request: AssistantHintRequest) -> tuple[str, str]:
    record = engine._require_session(request.session_id)
    state = record["state"]
    dynasty = engine.dynasties[state.dynasty_id]
    role = engine.roles[state.player_role_id]
    current_scene = engine.scenes[state.current_scene_id]
    discovered = [engine.clues[clue_id] for clue_id in state.discovered_clue_ids if clue_id in engine.clues]
    available_scenes = [engine.scenes[scene_id].name for scene_id in state.available_scene_ids if scene_id in engine.scenes]
    recent_dialogue = [
        {
            "人物": turn.npc_name,
            "玩家": turn.player_message,
            "回应": turn.npc_response,
        }
        for turn in record["dialogue_turns"][-4:]
    ]
    payload = {
        "朝代": dynasty.name,
        "当前阶段": state.current_stage,
        "当前地点": current_scene.name,
        "玩家身份": state.player_identity.display_name if state.player_identity else role.name,
        "当前目标": engine._current_goal(state.current_stage),
        "已发现线索": [
            {
                "线索名": clue.title,
                "描述": clue.display_text,
                "细节": clue.detail,
            }
            for clue in discovered
        ],
        "可前往地点": available_scenes,
        "最近对话": recent_dialogue,
        "玩家问题": request.question,
    }
    prompt = f"""
你是《史隙》游戏内智能助手，只能根据后端提供的当前案卷上下文给玩家提示。

硬性规则：
- 只输出 JSON 对象，字段为 answer、suggested_focus、safety_note。
- 用户可见文本必须全中文。
- 只能引用“已发现线索”“当前地点”“当前阶段”“可前往地点”“最近对话”。
- 不得释放未发现线索，不得说出最终真相，不得替玩家决定结局或关键选择。
- 如果证据不足，必须明确说“目前证据不足”，并建议下一步调查方向。
- 不要提及 API、模型、系统提示或密钥。

当前案卷上下文：
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""
    input_summary = f"助手提示 阶段={state.current_stage} 地点={current_scene.name} 问题={request.question[:40]}"
    return prompt, input_summary


def _assistant_answer_is_safe(answer: str, request: AssistantHintRequest) -> tuple[bool, list[dict[str, str]]]:
    record = engine._require_session(request.session_id)
    state = record["state"]
    discovered = set(state.discovered_clue_ids)
    issues: list[dict[str, str]] = []
    for clue in engine.clues.values():
        if clue.clue_id in discovered:
            continue
        forbidden_terms = [clue.title, clue.highlight_text]
        if any(term and term in answer for term in forbidden_terms):
            issues.append({"type": "assistant_hidden_clue", "severity": "high", "detail": f"回答提及未发现线索：{clue.title}"})
    if "幕后上级" in answer or "最终真相是" in answer:
        issues.append({"type": "assistant_spoiler_risk", "severity": "high", "detail": "回答有直接剧透风险。"})
    return len(issues) == 0, issues


@router.post("/assistant/hint")
def post_assistant_hint(request: AssistantHintRequest):
    if settings.use_mock_ai or settings.ai_provider != "deepseek" or not settings.deepseek_api_key_available:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "AI_UNAVAILABLE",
                    "message": "智能助手需要后端真实 DeepSeek 配置；当前未启用真实助手，未使用模拟回答。",
                    "details": {"ai_provider": settings.ai_provider, "mock_ai": settings.use_mock_ai},
                }
            },
        )

    try:
        prompt, input_summary = _assistant_prompt(request)
    except GameError as error:
        return _error_response(error)

    ai_response = AIClient(settings).generate_json_sync(
        module="DeepSeekAssistant",
        prompt=prompt,
        schema_hint=ASSISTANT_SCHEMA_HINT,
    )

    answer = str(ai_response.parsed_json.get("answer", "")).strip() if ai_response.success else ""
    safe, issues = _assistant_answer_is_safe(answer, request) if answer else (False, [{"type": "assistant_empty", "severity": "medium", "detail": "助手未返回有效中文提示。"}])
    log_entry = log_service.record_ai_call(
        module="DeepSeekAssistant",
        model=ai_response.model,
        input_summary=input_summary,
        latency_ms=ai_response.latency_ms,
        success=ai_response.success,
        fallback_used=not ai_response.success,
        supervisor_pass=safe,
        issues=issues,
        prompt=prompt,
        raw_response=ai_response.raw_text,
        extra_fields={"assistant_guard_pass": safe},
    )

    if not ai_response.success:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "AI_UNAVAILABLE",
                    "message": "智能助手真实调用失败，未使用模拟回答。",
                    "details": {"call_id": log_entry.get("call_id")},
                }
            },
        )
    if not safe:
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "AI_RESPONSE_BLOCKED",
                    "message": "助手回答触及未公开案卷，已被后端拦截。",
                    "details": {"call_id": log_entry.get("call_id")},
                }
            },
        )

    return {
        "answer": answer,
        "suggested_focus": [str(item).strip() for item in ai_response.parsed_json.get("suggested_focus", []) if str(item).strip()][:3],
        "safety_note": str(ai_response.parsed_json.get("safety_note", "仅基于当前已发现线索。")).strip(),
        "ai_mode": "real",
        "log": {
            "call_id": log_entry.get("call_id"),
            "latency_ms": log_entry.get("latency_ms"),
            "supervisor_pass": log_entry.get("supervisor_pass"),
        },
    }


@router.post("/investigate")
def post_investigate(request: InvestigateRequest):

    try:
        return engine.investigate(request)
    except GameError as error:
        return _error_response(error)


@router.post("/choice")
def post_choice(request: ChoiceRequest):
    try:
        return engine.submit_choice(request.session_id, request.choice_id)
    except GameError as error:
        return _error_response(error)


@router.post("/deduction/submit")
def post_deduction_submit(request: DeductionSubmitRequest):
    try:
        return engine.submit_deduction(request)
    except GameError as error:
        return _error_response(error)


@router.post("/ending/resolve")
def post_ending_resolve(request: EndingResolveRequest):
    try:
        return engine.resolve_ending(request.session_id)
    except GameError as error:
        return _error_response(error)
