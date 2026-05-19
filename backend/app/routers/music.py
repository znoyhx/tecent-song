from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from app.services.music_generation_service import music_generation_service


router = APIRouter(prefix="/api/music")


class MusicGenerateRequest(BaseModel):
    bgm_id: str
    force: bool = False
    wait_for_audio: bool = False
    poll_seconds: int = Field(default=0, ge=0, le=180)


@router.get("/manifest")
def get_music_manifest() -> dict:
    return music_generation_service.public_manifest()


@router.get("/status")
def get_music_status() -> dict:
    return music_generation_service.list_status()


@router.post("/generate")
def generate_music_track(request: MusicGenerateRequest) -> dict:
    try:
        return music_generation_service.generate_track(
            request.bgm_id,
            force=request.force,
            wait_for_audio=request.wait_for_audio,
            poll_seconds=request.poll_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tasks/{task_id}")
def get_music_task(task_id: str, bgm_id: str | None = None) -> dict:
    return music_generation_service.query_task(task_id, bgm_id=bgm_id, download_on_success=True)


@router.post("/callback")
def post_music_callback(payload: dict) -> Response:
    music_generation_service.handle_callback(payload)
    return Response(content="success", media_type="text/plain; charset=utf-8")


@router.get("/assets/{bgm_id}")
def get_music_asset(bgm_id: str):
    file_path = music_generation_service.asset_file_path(bgm_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="这首 BGM 暂未生成，前端会使用静音兜底。")
    return FileResponse(file_path, media_type=music_generation_service.asset_media_type(bgm_id))


@router.get("/fallback/silence.wav")
def get_music_fallback() -> Response:
    return Response(content=music_generation_service.silence_wav_bytes(), media_type="audio/wav")
