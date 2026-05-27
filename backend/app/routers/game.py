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
    "answer": "中文回答，可以基于完整剧本人物、线索、推理和结局作答",
    "suggested_focus": ["中文后续关注点"],
    "safety_note": "中文上下文范围说明",
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
    catalog = engine._record_catalog(record)
    dynasty = catalog["dynasty"]
    role = catalog["roles"][state.player_role_id]
    event = catalog["event"]
    current_scene = catalog["scenes"][state.current_scene_id]
    discovered_ids = set(state.discovered_clue_ids)
    discovered = [catalog["clues"][clue_id] for clue_id in state.discovered_clue_ids if clue_id in catalog["clues"]]
    available_scenes = [catalog["scenes"][scene_id].name for scene_id in state.available_scene_ids if scene_id in catalog["scenes"]]
    recent_dialogue = [
        {
            "人物": turn.npc_name,
            "玩家": turn.player_message,
            "回应": turn.npc_response,
        }
        for turn in record["dialogue_turns"][-4:]
    ]
    payload = {
        "案件": {
            "标题": event.title,
            "表层事件": event.surface_event,
            "隐藏真相": event.hidden_truth,
            "阶段目标": event.stage_goals,
        },
        "玩家当前状态": {
            "朝代": dynasty.name,
            "当前阶段": state.current_stage,
            "当前地点": current_scene.name,
            "当前地点描述": current_scene.description,
            "玩家身份": state.player_identity.display_name if state.player_identity else role.name,
            "当前目标": engine._current_goal(state.current_stage, catalog),
            "已发现线索ID": state.discovered_clue_ids,
            "可前往地点": available_scenes,
            "信任": state.npc_trust,
            "分数": state.scores.model_dump(),
            "标记": state.flags,
        },
        "人物全档案": [
            {
                "id": npc.npc_id,
                "姓名": npc.name,
                "公开身份": npc.public_identity,
                "案件关系": npc.case_connection,
                "案发行为": npc.event_behavior,
                "公开目标": npc.public_goal,
                "隐藏动机": npc.hidden_motive,
                "已知信息": npc.known_info,
                "未知信息": npc.unknown_info,
                "可释放线索ID": npc.releasable_clue_ids,
            }
            for npc in catalog["npcs"].values()
        ],
        "地点": [
            {
                "id": scene.scene_id,
                "名称": scene.name,
                "描述": scene.description,
                "阶段": scene.available_stage,
                "人物ID": scene.npc_ids,
                "热点": [
                    {
                        "id": hotspot.hotspot_id,
                        "标签": hotspot.label,
                        "线索ID": hotspot.clue_ids,
                        "所需阶段": hotspot.required_stage,
                        "所需线索ID": hotspot.required_clue_ids,
                    }
                    for hotspot in scene.hotspots
                ],
            }
            for scene in catalog["scenes"].values()
        ],
        "全部线索": [
            {
                "id": clue.clue_id,
                "标题": clue.title,
                "类型": clue.type,
                "关键": clue.is_key,
                "已发现": clue.clue_id in discovered_ids,
                "来源地点ID": clue.source_scene_id,
                "来源人物ID": clue.source_npc_id,
                "展示文本": clue.display_text,
                "细节": clue.detail,
                "相关线索ID": clue.related_clue_ids,
                "结局标签": clue.ending_tags,
            }
            for clue in catalog["clues"].values()
        ],
        "线索组合": [
            {
                "id": combo.combo_id,
                "所需线索ID": combo.required_clue_ids,
                "结论": combo.result_title,
                "说明": combo.result_text,
            }
            for combo in catalog["combos"].values()
        ],
        "推理题": [
            {
                "id": deduction.deduction_id,
                "问题": deduction.question,
                "所需线索ID": deduction.required_clue_ids,
                "正确线索ID": deduction.correct_clue_ids,
                "成功文本": deduction.success_text,
                "错误反馈": deduction.wrong_feedback,
            }
            for deduction in catalog["deductions"].values()
        ],
        "选择与结局": {
            "选择": [choice.model_dump() for choice in catalog["choices"].values()],
            "结局": [
                {
                    "id": ending.ending_id,
                    "标题": ending.title,
                    "条件": ending.conditions,
                    "所需标记": ending.required_flags,
                    "阻塞标记": ending.blocked_flags,
                    "摘要": ending.result_summary,
                    "结局文本": ending.ending_text,
                    "人物命运": ending.npc_fates,
                    "相关线索ID": ending.related_clue_ids,
                }
                for ending in catalog["endings"].values()
            ],
        },
        "最近对话": recent_dialogue,
        "玩家问题": request.question,
    }
    prompt = f"""
你是《史隙》游戏内的真实 AI 案件助手，已经接入完整剧本资料。

输出要求：
- 只输出 JSON 对象，字段为 answer、suggested_focus、safety_note。
- 用户可见文本必须全中文。
- 直接依据“完整剧本资料”回答，可以使用人物隐藏动机、未发现线索、推理链、结局和隐藏真相。
- 如果玩家问真相、凶手、下一步、线索价值、人物是否说谎，可以直接回答并给出依据。
- 不要再用“我不能剧透”“目前只能依据已发现线索”这类限制性话术。
- 不要编造剧本资料之外的人物、线索或结局；不确定时说明缺少剧本内依据。
- suggested_focus 给出 1-3 个下一步关注点，必须是剧本内人物、地点、线索或推理方向。
- safety_note 固定说明为“已基于完整剧本上下文回答”。

完整剧本资料：
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""
    input_summary = f"完整剧本助手 阶段={state.current_stage} 地点={current_scene.name} 问题={request.question[:40]}"
    return prompt, input_summary


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
        max_tokens=1800,
        temperature=0.35,
    )

    answer = str(ai_response.parsed_json.get("answer", "")).strip() if ai_response.success else ""
    issues = [] if answer else [{"type": "assistant_empty", "severity": "medium", "detail": "助手未返回有效中文回答。"}]
    log_entry = log_service.record_ai_call(
        module="DeepSeekAssistant",
        model=ai_response.model,
        input_summary=input_summary,
        latency_ms=ai_response.latency_ms,
        success=ai_response.success,
        fallback_used=not ai_response.success,
        supervisor_pass=bool(answer),
        issues=issues,
        prompt=prompt,
        raw_response=ai_response.raw_text,
        extra_fields={"assistant_context_scope": "full_script"},
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

    return {
        "answer": answer,
        "suggested_focus": [str(item).strip() for item in ai_response.parsed_json.get("suggested_focus", []) if str(item).strip()][:3],
        "safety_note": str(ai_response.parsed_json.get("safety_note", "已基于完整剧本上下文回答。")).strip(),
        "ai_mode": "real",
        "context_scope": "full_script",
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
