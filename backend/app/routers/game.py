from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.models.game_models import (
    ChoiceRequest,
    DeductionSubmitRequest,
    DialogueRequest,
    EndingResolveRequest,
    InvestigateRequest,
    PlayerIdentityValidationRequest,
    SessionStartRequest,
)
from app.services.game_engine import GameError, engine


router = APIRouter(prefix="/api")


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
