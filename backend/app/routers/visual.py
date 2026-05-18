from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from app.services.image_generation_service import image_generation_service

router = APIRouter(prefix="/api/visual")


class VisualGenerateRequest(BaseModel):
    asset_id: str
    force: bool = False
    image_size: str | None = None


@router.get("/status")
def get_visual_status() -> dict:
    return image_generation_service.list_status()


@router.post("/generate")
def generate_visual_asset(request: VisualGenerateRequest) -> dict:
    try:
        return image_generation_service.generate_asset(
            request.asset_id,
            force=request.force,
            image_size=request.image_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/bootstrap-demo-assets")
def bootstrap_demo_assets(
    include_clues: bool = Query(False),
    force: bool = Query(False),
) -> dict:
    return image_generation_service.bootstrap_demo_assets(include_clues=include_clues, force=force)


@router.get("/assets/{asset_id}")
def get_visual_asset(asset_id: str):
    file_path = image_generation_service.asset_file_path(asset_id)
    if file_path and file_path.exists():
        return FileResponse(file_path, media_type=image_generation_service.asset_media_type(asset_id))
    svg = image_generation_service.fallback_svg(asset_id)
    return Response(content=svg, media_type="image/svg+xml; charset=utf-8")
