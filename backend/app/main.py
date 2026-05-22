from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers.game import router as game_router
from app.routers.music import router as music_router
from app.routers.scripts import router as scripts_router
from app.routers.visual import router as visual_router

app = FastAPI(title=settings.app_name, version=settings.version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(game_router)
app.include_router(scripts_router)
app.include_router(visual_router)
app.include_router(music_router)



@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": "史隙阶段二视觉演示后端已启动",
        "mode": "mock_with_visual_generation",
    }

