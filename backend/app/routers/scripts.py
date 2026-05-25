from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import ValidationError

from app.models.script_models import ScriptGenerateRequest, StartGeneratedRequest, keyword_encoding_issue
from app.services.game_engine import GameError
from app.services.image_generation_service import image_generation_service
from app.services.script_generation_service import script_generation_service
from app.services.script_import_service import script_import_service
from app.services.script_job_store import script_job_store
from app.services.script_supervisor import script_supervisor
from app.services.script_volume_gate import script_volume_gate

router = APIRouter(prefix="/api")


def _error_response(*, code: str, message: str, status_code: int = 400, details: dict[str, Any] | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or {}}},
    )


def _game_error_response(error: GameError) -> JSONResponse:
    return _error_response(code=error.code, message=error.message, status_code=error.status_code, details=error.details)


def _keywords_from_payload(payload: dict[str, Any]) -> list[str]:
    raw = payload.get("keywords")
    if isinstance(raw, str):
        pieces = raw.replace("，", ",").replace("、", ",").replace("；", ",").split(",")
    elif isinstance(raw, list):
        pieces = [str(item) for item in raw]
    else:
        pieces = []
    return [item.strip() for item in pieces if item.strip()]


def _keyword_encoding_issues(keywords: list[str]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for keyword in keywords:
        issue = keyword_encoding_issue(keyword)
        if issue:
            issues.append({"keyword": keyword, "reason": issue})
    return issues


@router.post("/scripts/generate")
def post_generate_script(payload: dict[str, Any], background_tasks: BackgroundTasks):
    dynasty_id = str(payload.get("dynasty_id", "")).strip()
    if dynasty_id == "ming":
        return _error_response(
            code="AI_GENERATION_DISABLED_FOR_STABLE_DEMO",
            message="明代仍为固定 Demo，不进入 AI 剧本生成。",
            status_code=409,
        )
    if dynasty_id == "tang":
        dynasty_id = "late_tang"
    if dynasty_id not in {"song", "late_tang"}:
        return _error_response(code="DYNASTY_NOT_SUPPORTED", message="P0 只支持北宋和晚唐生成。")

    keywords = _keywords_from_payload(payload)
    if not keywords:
        return _error_response(code="KEYWORDS_REQUIRED", message="请填写 1-8 个关键词后再开始生成。")
    if len(keywords) > 8:
        return _error_response(code="KEYWORDS_TOO_MANY", message="关键词最多 8 个，请删减后重试。")
    encoding_issues = _keyword_encoding_issues(keywords)
    if encoding_issues:
        return _error_response(
            code="KEYWORDS_ENCODING_INVALID",
            message="关键词疑似编码损坏，请重新输入中文关键词后再生成。",
            details={"issues": encoding_issues},
        )
    if _keywords_conflict(dynasty_id, keywords):
        return _error_response(code="KEYWORDS_CONFLICT_WITH_DYNASTY", message="关键词与所选朝代明显冲突，请改写后重试。")

    try:
        request = ScriptGenerateRequest(dynasty_id=dynasty_id, keywords=keywords)
    except ValidationError as exc:
        return _error_response(code="BAD_REQUEST", message="生成请求字段不完整或不合法。", details={"reason": str(exc)[:160]})
    job = script_job_store.create_job(request)
    background_tasks.add_task(script_generation_service.run_job, job.job_id)
    return job.model_dump(mode="json")


@router.get("/scripts/jobs/{job_id}")
def get_script_job(job_id: str):
    job = script_job_store.get_job(job_id)
    if job is None:
        return _error_response(code="JOB_NOT_FOUND", message="未找到生成任务。", status_code=404)
    return job.model_dump(mode="json")


@router.get("/scripts/demos")
def list_generated_demos():
    return {"demos": script_job_store.list_demo_scripts(playable_only=True)}


@router.get("/scripts/{script_id}")
def get_script(script_id: str):
    package = script_job_store.get_script(script_id)
    if package is None:
        return _error_response(code="SCRIPT_NOT_FOUND", message="未找到生成剧本。", status_code=404)
    return package.model_dump(mode="json")


@router.post("/scripts/{script_id}/validate")
def validate_script(script_id: str):
    package = script_job_store.get_script(script_id)
    if package is None:
        return _error_response(code="SCRIPT_NOT_FOUND", message="未找到生成剧本。", status_code=404)
    supervisor_result = script_supervisor.review(package)
    volume_result = script_volume_gate.review(package)
    supervisor_payload = supervisor_result.model_dump()
    volume_payload = volume_result.model_dump()
    return {
        "passed": supervisor_result.passed and volume_result.passed,
        "issues": [*supervisor_payload["issues"], *volume_payload["issues"]],
        "blocking_issues": [*supervisor_payload["blocking_issues"], *volume_payload["blocking_issues"]],
        "supervisor": supervisor_payload,
        "volume_gate": volume_payload,
    }


@router.post("/scripts/{script_id}/identity/validate")
def validate_generated_identity(script_id: str, payload: dict[str, Any]):
    try:
        return script_import_service.validate_custom_identity(
            script_id=script_id,
            identity_id=str(payload.get("identity_id") or "").strip() or None,
            custom_identity_text=str(payload.get("custom_identity_text") or ""),
        )
    except GameError as error:
        return _game_error_response(error)


@router.post("/scripts/{script_id}/visuals/generate")
def generate_script_visuals(script_id: str, background_tasks: BackgroundTasks, force: bool = Query(default=False)):
    package = script_job_store.get_script(script_id)
    if package is None:
        return _error_response(code="SCRIPT_NOT_FOUND", message="未找到生成剧本。", status_code=404)
    job = script_job_store.find_job_by_script_id(script_id)
    if job is None:
        return _error_response(code="JOB_NOT_FOUND", message="未找到该剧本对应的生成任务。", status_code=404)
    if job.status not in {"visual_blocked", "failed", "running"} and not (force and job.status == "completed"):
        return _error_response(code="VISUAL_REGENERATION_NOT_ALLOWED", message="当前剧本不需要重新生成图片。", status_code=409)
    background_tasks.add_task(script_generation_service.continue_visuals_for_script, script_id, force=force)
    return job.model_dump(mode="json")


@router.get("/scripts/{script_id}/assets/{asset_id}")
def get_generated_script_asset(script_id: str, asset_id: str):
    path = image_generation_service.generated_script_asset_path(script_id=script_id, asset_id=asset_id)
    if not path.exists() or not _is_safe_generated_asset_path(path, script_id):
        return _error_response(code="ASSET_NOT_FOUND", message="未找到该生成图片资产。", status_code=404)
    return FileResponse(path, media_type="image/png")


@router.post("/session/start-generated")
def start_generated_session(request: StartGeneratedRequest):
    try:
        return script_import_service.start_generated_session(
            script_id=request.script_id,
            identity_id=request.identity_id,
            custom_identity_text=request.custom_identity_text,
        )
    except GameError as error:
        return _game_error_response(error)


def _keywords_conflict(dynasty_id: str, keywords: list[str]) -> bool:
    joined = "".join(keywords)
    common_conflicts = ("锦衣卫", "东厂", "西厂", "军机处", "火车", "电报", "手机", "报纸")
    if dynasty_id == "song":
        return any(term in joined for term in common_conflicts)
    return any(term in joined for term in common_conflicts + ("殿试",))


def _is_safe_generated_asset_path(path: Path, script_id: str) -> bool:
    normalized = path.resolve().as_posix()
    return f"/generated/{script_id}/" in normalized
