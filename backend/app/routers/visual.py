from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from app.services.image_generation_service import image_generation_service
from app.services.visual_prompt_agent import visual_prompt_agent

router = APIRouter(prefix="/api/visual")


class VisualGenerateRequest(BaseModel):
    asset_id: str
    force: bool = False
    image_size: str | None = None


@router.get("/status")
def get_visual_status() -> dict:
    status = image_generation_service.list_status()
    known_assets = {
        asset.asset_id: image_generation_service._asset_status(asset.asset_id)
        for asset in visual_prompt_agent.list_assets()
    }
    for item in status.get("assets", []):
        known_assets[item["asset_id"]] = item
    assets = list(known_assets.values())
    return {
        **status,
        "asset_count": len(assets),
        "generated_count": sum(1 for asset in assets if asset["status"] == "generated"),
        "fallback_count": sum(1 for asset in assets if asset["status"] == "fallback"),
        "blocked_count": sum(1 for asset in assets if asset.get("blocked")),
        "assets": assets,
    }


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
    if not include_clues:
        return image_generation_service.bootstrap_demo_assets(include_clues=False, force=force)

    asset_ids = [asset.asset_id for asset in visual_prompt_agent.list_assets()]
    results = [image_generation_service.generate_asset(asset_id, force=force) for asset_id in asset_ids]
    return {
        "assets": results,
        "generated_count": sum(1 for asset in results if asset["status"] == "generated"),
        "fallback_count": sum(1 for asset in results if asset["status"] == "fallback"),
        "blocked_count": sum(1 for asset in results if asset.get("blocked")),
    }


@router.get("/assets/{asset_id}")
def get_visual_asset(asset_id: str):
    file_path = image_generation_service.asset_file_path(asset_id)
    if file_path and file_path.exists():
        return FileResponse(file_path, media_type=image_generation_service.asset_media_type(asset_id))
    svg = image_generation_service.fallback_svg(asset_id)
    return Response(content=svg, media_type="image/svg+xml; charset=utf-8")
