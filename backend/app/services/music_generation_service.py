from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import io
import json
from pathlib import Path
import time
from typing import Any
from urllib.parse import urlparse
import wave

import httpx

from app.core.config import Settings, settings


MUSIC_PROVIDER = "tianpuyue"
GENERATION_API = "instrumental.generate"
QUERY_API = "instrumental.query"
MODEL_VERSION = "TemPolor i3.5"
DEFAULT_DURATION_SECONDS = 80
FALLBACK_ROUTE = "/api/music/fallback/silence.wav"

MANDATORY_PROMPT_SUFFIX = (
    "Style: Instrumental, loopable visual novel background music, no vocal, no lyrics, no dialogue. "
    "Mood: low-saturation historical suspense, restrained, dark, readable, not pop. "
    "Instruments: guqin, xiao flute, pipa, low strings, very light percussion, subtle low drone. "
    "Avoid: modern pop rhythm, EDM, rock, rap, copyrighted melody imitation, obvious sound effects. "
    "BPM 72, D minor, Dm,Gm,Bb,A, duration 80 seconds, suitable for seamless loop."
)

TRACK_DEFINITIONS: list[dict[str, Any]] = [
    {
        "bgm_id": "pre_game_entry",
        "title": "史隙入口",
        "usage": "进入游戏前",
        "stage": "pre_game",
        "scene_ids": [],
        "npc_ids": [],
        "ending_id": None,
        "priority": "pre_game",
        "music_direction": "历史缝隙、低饱和、神秘、克制",
        "prompt_core": "《史隙》进入游戏前的历史悬疑纯音乐，像隔着雨幕翻开一卷旧案，克制、低饱和、微暗但不惊吓。",
        "volume": 0.32,
        "fade_ms": 1800,
    },
    {
        "bgm_id": "ming_intro_night_fire",
        "title": "夜火初现",
        "usage": "引子 / 夜火",
        "stage": "intro",
        "scene_ids": ["scene_front_hall", "scene_fire_yard"],
        "npc_ids": [],
        "ending_id": None,
        "priority": "stage",
        "music_direction": "雨夜书坊、暗火、异常初现",
        "prompt_core": "明代雨夜书坊后院的历史悬疑纯音乐，旧书箱烧毁、灰烬未冷、锦衣卫封门，情绪克制但有压迫感。",
        "volume": 0.34,
        "fade_ms": 1800,
    },
    {
        "bgm_id": "ming_investigation_threads",
        "title": "线索交织",
        "usage": "调查",
        "stage": "investigation",
        "scene_ids": ["scene_account_room", "scene_lamp_shelf", "scene_engraving_room", "scene_back_gate"],
        "npc_ids": [],
        "ending_id": None,
        "priority": "stage",
        "music_direction": "查证、试探、线索交织",
        "prompt_core": "明代书坊焚稿案调查阶段的纯音乐，账房、灯油架、刻坊与后门线索相互牵扯，像一步步翻查湿纸旧账。",
        "volume": 0.32,
        "fade_ms": 1800,
    },
    {
        "bgm_id": "ming_npc_owner_xu",
        "title": "许掌柜",
        "usage": "许掌柜对话",
        "stage": None,
        "scene_ids": [],
        "npc_ids": ["npc_owner"],
        "ending_id": None,
        "priority": "npc",
        "music_direction": "生计压力、遮掩、算盘般的紧张",
        "prompt_core": "许掌柜对话主题纯音乐，书坊生计与遮掩隐情互相拉扯，算盘珠轻碰般的紧张藏在低弦下。",
        "volume": 0.31,
        "fade_ms": 1600,
    },
    {
        "bgm_id": "ming_npc_worker_ashen",
        "title": "阿沈",
        "usage": "阿沈对话",
        "stage": None,
        "scene_ids": [],
        "npc_ids": ["npc_worker"],
        "ending_id": None,
        "priority": "npc",
        "music_direction": "胆怯、低声、被牵连的恐惧",
        "prompt_core": "刻工阿沈对话主题纯音乐，低声、胆怯、害怕被牵连，像在刻刀和雨声之间吞回真话。",
        "volume": 0.30,
        "fade_ms": 1600,
    },
    {
        "bgm_id": "ming_npc_scholar_guwen",
        "title": "顾闻",
        "usage": "顾闻对话",
        "stage": None,
        "scene_ids": [],
        "npc_ids": ["npc_scholar"],
        "ending_id": None,
        "priority": "npc",
        "music_direction": "士子清寒、执念、悲凉",
        "prompt_core": "落第士子顾闻对话主题纯音乐，清寒、执念、悲凉，像湿透诗稿中夹着不能丢的抄录。",
        "volume": 0.31,
        "fade_ms": 1700,
    },
    {
        "bgm_id": "ming_npc_jinyiwei_luzheng",
        "title": "陆峥",
        "usage": "陆峥对话",
        "stage": None,
        "scene_ids": [],
        "npc_ids": ["npc_jinyiwei"],
        "ending_id": None,
        "priority": "npc",
        "music_direction": "官府压迫、克制、铁律",
        "prompt_core": "锦衣卫陆峥对话主题纯音乐，官府压迫、克制、铁律，低弦像封条压住门缝。",
        "volume": 0.32,
        "fade_ms": 1700,
    },
    {
        "bgm_id": "ming_reversal_grain_record",
        "title": "粮册真相",
        "usage": "反转",
        "stage": "reversal",
        "scene_ids": ["scene_rain_alley", "scene_city_gate", "scene_interrogation_room"],
        "npc_ids": [],
        "ending_id": None,
        "priority": "reversal",
        "music_direction": "烧的不是书、粮册真相浮现",
        "prompt_core": "明代书坊焚稿案中段反转纯音乐，烧的不是普通书稿，粮册抄录与封口命令逐渐浮现。",
        "volume": 0.35,
        "fade_ms": 2000,
    },
    {
        "bgm_id": "ming_choice_evidence",
        "title": "证据与活路",
        "usage": "抉择",
        "stage": "choice",
        "scene_ids": [],
        "npc_ids": [],
        "ending_id": None,
        "priority": "choice",
        "music_direction": "证据与活路、不可两全",
        "prompt_core": "最终抉择阶段纯音乐，证据与活路不可两全，压迫但不喧闹，像一盏灯快要被雨风吹灭。",
        "volume": 0.36,
        "fade_ms": 2200,
    },
    {
        "bgm_id": "ending_truth",
        "title": "残页出城",
        "usage": "真相结局",
        "stage": "ending",
        "scene_ids": [],
        "npc_ids": [],
        "ending_id": "ending_truth",
        "priority": "ending",
        "music_direction": "残页出城、微弱希望",
        "prompt_core": "真相结局纯音乐，残页被护出城，书坊代价沉重但仍有微弱希望，克制而不胜利。",
        "volume": 0.34,
        "fade_ms": 2400,
    },
    {
        "bgm_id": "ending_order",
        "title": "交还官府",
        "usage": "秩序结局",
        "stage": "ending",
        "scene_ids": [],
        "npc_ids": [],
        "ending_id": "ending_order",
        "priority": "ending",
        "music_direction": "官府收束、庄严但寒冷",
        "prompt_core": "秩序结局纯音乐，官府收束一切，庄严但寒冷，真相被封存进更深的柜中。",
        "volume": 0.34,
        "fade_ms": 2400,
    },
    {
        "bgm_id": "ending_survival",
        "title": "灰烬无声",
        "usage": "自保结局",
        "stage": "ending",
        "scene_ids": [],
        "npc_ids": [],
        "ending_id": "ending_survival",
        "priority": "ending",
        "music_direction": "灰烬无声、压抑",
        "prompt_core": "自保结局纯音乐，灰烬无声，书坊暂保但真相断裂，压抑、低回、不煽情。",
        "volume": 0.33,
        "fade_ms": 2400,
    },
    {
        "bgm_id": "ending_tragedy",
        "title": "封口沉坠",
        "usage": "悲剧结局",
        "stage": "ending",
        "scene_ids": [],
        "npc_ids": [],
        "ending_id": "ending_tragedy",
        "priority": "ending",
        "music_direction": "封口、孤立、沉坠",
        "prompt_core": "悲剧结局纯音乐，封口、孤立、沉坠，像潮湿纸页被压入黑箱，情绪低沉但保持克制。",
        "volume": 0.33,
        "fade_ms": 2400,
    },
    {
        "bgm_id": "ending_hidden",
        "title": "借刀留痕",
        "usage": "隐藏结局",
        "stage": "ending",
        "scene_ids": [],
        "npc_ids": [],
        "ending_id": "ending_hidden",
        "priority": "ending",
        "music_direction": "借刀留痕、暗线未断",
        "prompt_core": "隐藏结局纯音乐，借刀留痕，暗线未断，危险中保留一丝清冷的余光。",
        "volume": 0.34,
        "fade_ms": 2500,
    },
]


@dataclass(frozen=True)
class MusicSelectionContext:
    current_stage: str | None = None
    current_scene_id: str | None = None
    current_npc_id: str | None = None
    risk_level: int = 0
    ending_id: str | None = None


class MusicGenerationService:
    def __init__(self, runtime_settings: Settings = settings) -> None:
        self.settings = runtime_settings
        self.workspace_dir = Path(__file__).resolve().parents[3]
        self.backend_dir = self.workspace_dir / "backend"
        self.data_dir = self.backend_dir / "data" / "music"
        self.generated_root = self.workspace_dir / "assets" / "generated" / "music"
        self.manifest_path = self.data_dir / "music_manifest.json"
        self.tasks_path = self.data_dir / "music_tasks.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.generated_root.mkdir(parents=True, exist_ok=True)

    def public_manifest(self) -> dict[str, Any]:
        return self.ensure_manifest()

    def list_status(self) -> dict[str, Any]:
        manifest = self.ensure_manifest()
        tasks = self._load_tasks()
        return {
            "provider": self.settings.music_provider,
            "endpoint": "天谱乐纯音乐接口",
            "generate_api": GENERATION_API,
            "query_api": QUERY_API,
            "completion_strategy": "query_polling",
            "model": self.settings.music_model,
            "api_key_available": self.settings.music_api_key_available,
            "callback_url_available": bool(self.settings.music_callback_url),
            "callback_required_for_completion": False,
            "track_count": len(manifest["tracks"]),
            "generated_count": sum(1 for track in manifest["tracks"] if track.get("asset_available")),
            "task_count": len(tasks.get("tasks", [])),
            "fallback_url": FALLBACK_ROUTE,
        }

    def ensure_manifest(self) -> dict[str, Any]:
        existing = self._load_manifest()
        existing_tracks = (
            {track.get("bgm_id"): track for track in existing.get("tracks", []) if track.get("bgm_id")}
            if existing.get("provider") == MUSIC_PROVIDER
            else {}
        )
        tracks = [self._manifest_track(definition, existing_tracks.get(definition["bgm_id"], {})) for definition in TRACK_DEFINITIONS]
        manifest = {
            "version": 1,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "provider": MUSIC_PROVIDER,
            "generation_api": GENERATION_API,
            "query_api": QUERY_API,
            "model": self.settings.music_model,
            "tracks": tracks,
        }
        self._save_json(self.manifest_path, manifest)
        return manifest

    def generate_track(
        self,
        bgm_id: str,
        *,
        force: bool = False,
        wait_for_audio: bool = False,
        poll_seconds: int = 0,
    ) -> dict[str, Any]:
        definition = self._definition_for(bgm_id)
        existing_file = self._find_existing_file(bgm_id)
        if existing_file and not force:
            self._update_manifest_item(bgm_id, status="generated", generated_path=existing_file)
            return {
                "bgm_id": bgm_id,
                "status": "generated",
                "task_id": None,
                "item_id": None,
                "asset_available": True,
                "generated_path": self._relative_path(existing_file),
                "message": "已复用本地生成音乐。",
            }

        if self.settings.music_provider != MUSIC_PROVIDER:
            return self._blocked_result(bgm_id, "provider_disabled", "音乐生成服务未启用，已使用静音兜底。")

        if not self.settings.music_api_key_available:
            return self._blocked_result(bgm_id, "missing_credentials", "未检测到音乐生成 Key，已使用静音兜底。")

        payload = self._generation_payload(definition)
        try:
            data = self._api_post(self.settings.music_generate_endpoint, payload)
        except Exception as exc:  # noqa: BLE001 - do not leak signed headers or credentials
            return self._blocked_result(bgm_id, self._safe_error_code(exc), "音乐生成接口暂不可用，已使用静音兜底。")

        if not self._is_success_response(data):
            error_code = self._response_error_code(data)
            return self._blocked_result(bgm_id, error_code, "音乐生成接口返回异常，已使用静音兜底。")

        item_ids = self._extract_item_ids(data)
        if not item_ids:
            return self._blocked_result(bgm_id, "missing_item_id", "音乐生成接口未返回作品编号，已使用静音兜底。")
        item_id = item_ids[0]

        self._record_task(
            {
                "task_id": item_id,
                "item_id": item_id,
                "bgm_id": bgm_id,
                "status": "Submitted",
                "api": GENERATION_API,
                "request_id": data.get("request_id"),
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        self._update_manifest_item(bgm_id, status="submitted", task_id=item_id, generated_path=None)

        task_result = {
            "bgm_id": bgm_id,
            "status": "submitted",
            "task_id": item_id,
            "item_id": item_id,
            "asset_available": False,
            "message": "音乐生成任务已提交，等待异步结果。",
        }
        if wait_for_audio:
            task_result = self.poll_task(item_id, bgm_id=bgm_id, max_wait_seconds=max(0, poll_seconds))
        return task_result

    def poll_task(self, task_id: str, *, bgm_id: str | None = None, max_wait_seconds: int = 0) -> dict[str, Any]:
        # The current smoke path queries once by default; callers can pass a
        # short wait budget, but no user flow depends on blocking for music.
        result = self.query_task(task_id, bgm_id=bgm_id, download_on_success=True)
        if max_wait_seconds <= 0 or result.get("status") in {"succeeded", "failed", "part_failed"}:
            return result

        deadline = time.time() + max_wait_seconds
        while time.time() < deadline and result.get("status") in {"running", "submitted", "unknown", "main_succeeded"}:
            time.sleep(3)
            result = self.query_task(task_id, bgm_id=bgm_id, download_on_success=True)
            if result.get("status") in {"succeeded", "failed", "part_failed"}:
                break
        return result

    def query_task(self, task_id: str, *, bgm_id: str | None = None, download_on_success: bool = False) -> dict[str, Any]:
        if not self.settings.music_api_key_available:
            return {
                "task_id": task_id,
                "item_id": task_id,
                "bgm_id": bgm_id,
                "status": "blocked",
                "asset_available": False,
                "message": "未检测到音乐生成 Key，无法查询任务。",
            }
        try:
            data = self._api_post(self.settings.music_query_endpoint, {"item_ids": [task_id]})
        except Exception as exc:  # noqa: BLE001
            return {
                "task_id": task_id,
                "item_id": task_id,
                "bgm_id": bgm_id,
                "status": "failed",
                "asset_available": False,
                "error_code": self._safe_error_code(exc),
                "message": "音乐任务查询失败，已保留静音兜底。",
            }

        job = self._normalize_job_payload(data)
        status = job["status"]
        audio_url = job.get("audio_url")
        generated_path: Path | None = None
        if status in {"succeeded", "main_succeeded"} and audio_url and download_on_success and bgm_id:
            generated_path = self._download_audio(bgm_id, audio_url)

        self._record_task(
            {
                "task_id": task_id,
                "item_id": task_id,
                "bgm_id": bgm_id,
                "status": status,
                "audio_url_present": bool(audio_url),
                "event": job.get("event"),
                "audio_hi_status": job.get("audio_hi_status"),
                "generated_path": self._relative_path(generated_path) if generated_path else None,
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        if bgm_id:
            self._update_manifest_item(
                bgm_id,
                status="generated" if generated_path else status.lower(),
                task_id=task_id,
                generated_path=generated_path,
            )

        return {
            "task_id": task_id,
            "item_id": task_id,
            "bgm_id": bgm_id,
            "status": status,
            "audio_url_present": bool(audio_url),
            "asset_available": bool(generated_path),
            "generated_path": self._relative_path(generated_path) if generated_path else None,
            "message": "音乐任务查询完成。" if status in {"succeeded", "main_succeeded"} else "音乐仍在生成或已失败，游戏继续使用兜底音频。",
        }

    def handle_callback(self, payload: dict[str, Any]) -> dict[str, Any]:
        instrumentals = payload.get("instrumentals") if isinstance(payload.get("instrumentals"), list) else []
        instrumental = instrumentals[0] if instrumentals and isinstance(instrumentals[0], dict) else payload
        task_id = str(instrumental.get("item_id") or payload.get("item_id") or "").strip()
        if not task_id:
            return {"accepted": False, "message": "回调缺少任务编号。"}
        task = self._task_by_id(task_id)
        bgm_id = str(task.get("bgm_id") or instrumental.get("bgm_id") or payload.get("bgm_id") or "").strip() or None
        job = self._normalize_job_payload({"data": {"instrumentals": [instrumental]}})
        generated_path = None
        if job["status"] in {"succeeded", "main_succeeded"} and job.get("audio_url") and bgm_id:
            generated_path = self._download_audio(bgm_id, job["audio_url"])
        self._record_task(
            {
                "task_id": task_id,
                "item_id": task_id,
                "bgm_id": bgm_id,
                "status": job["status"],
                "audio_url_present": bool(job.get("audio_url")),
                "event": job.get("event"),
                "audio_hi_status": job.get("audio_hi_status"),
                "generated_path": self._relative_path(generated_path) if generated_path else None,
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        if bgm_id:
            self._update_manifest_item(
                bgm_id,
                status="generated" if generated_path else job["status"].lower(),
                task_id=task_id,
                generated_path=generated_path,
            )
        return {"accepted": True, "task_id": task_id, "status": job["status"], "asset_available": bool(generated_path)}

    def select_bgm_id(self, context: MusicSelectionContext) -> str:
        return select_bgm_id(context)

    def asset_file_path(self, bgm_id: str) -> Path | None:
        if self._definition_for(bgm_id, required=False) is None:
            return None
        file_path = self._find_existing_file(bgm_id)
        return file_path if file_path and file_path.exists() else None

    def asset_media_type(self, bgm_id: str) -> str:
        file_path = self.asset_file_path(bgm_id)
        suffix = file_path.suffix.lower() if file_path else ".mp3"
        return {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
        }.get(suffix, "application/octet-stream")

    def silence_wav_bytes(self, *, seconds: int = 1, sample_rate: int = 16000) -> bytes:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b"\x00\x00" * sample_rate * max(1, seconds))
        return buffer.getvalue()

    def _generation_payload(self, definition: dict[str, Any]) -> dict[str, Any]:
        return {
            "prompt": self._full_prompt(definition),
            "model": self.settings.music_model,
            "callback_url": self.settings.music_callback_url,
        }

    def _full_prompt(self, definition: dict[str, Any]) -> str:
        return f"{definition['prompt_core']} {MANDATORY_PROMPT_SUFFIX}"

    def _manifest_track(self, definition: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
        bgm_id = definition["bgm_id"]
        file_path = self._find_existing_file(bgm_id)
        generated_path = self._relative_path(file_path) if file_path else None
        status = "generated" if file_path else existing.get("status", "configured")
        return {
            "bgm_id": bgm_id,
            "title": definition["title"],
            "usage": definition["usage"],
            "stage": definition["stage"],
            "scene_ids": definition["scene_ids"],
            "npc_ids": definition["npc_ids"],
            "ending_id": definition["ending_id"],
            "priority": definition["priority"],
            "asset_url": f"/api/music/assets/{bgm_id}",
            "fallback_url": FALLBACK_ROUTE,
            "asset_available": bool(file_path),
            "generated_path": generated_path,
            "status": status,
            "task_id": existing.get("task_id"),
            "item_id": existing.get("item_id") or existing.get("task_id"),
            "volume": definition["volume"],
            "fade_ms": definition["fade_ms"],
            "duration_seconds": DEFAULT_DURATION_SECONDS,
            "prompt_summary": definition["music_direction"],
        }

    def _blocked_result(self, bgm_id: str, error_code: str, message: str) -> dict[str, Any]:
        self._update_manifest_item(bgm_id, status="blocked", error_code=error_code, generated_path=None)
        return {
            "bgm_id": bgm_id,
            "status": "blocked",
            "asset_available": False,
            "error_code": error_code,
            "message": message,
        }

    def _api_post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": self.settings.music_api_key or "",
            "Content-Type": "application/json; charset=utf-8",
        }
        with httpx.Client(timeout=self.settings.music_timeout_seconds, follow_redirects=True) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data if isinstance(data, dict) else {}

    def _download_audio(self, bgm_id: str, audio_url: str) -> Path:
        with httpx.Client(timeout=max(30, self.settings.music_timeout_seconds), follow_redirects=True) as client:
            response = client.get(audio_url)
            response.raise_for_status()
            content = response.content
            content_type = response.headers.get("content-type", "")
        if not content:
            raise RuntimeError("empty_audio_content")
        if content_type and not (content_type.startswith("audio/") or content_type.startswith("application/octet-stream")):
            raise RuntimeError("invalid_audio_content")
        suffix = self._audio_suffix(audio_url, content_type)
        target = self.generated_root / f"{bgm_id}{suffix}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return target

    def _audio_suffix(self, audio_url: str, content_type: str) -> str:
        suffix = Path(urlparse(audio_url).path).suffix.lower()
        if suffix in {".mp3", ".wav", ".ogg", ".m4a"}:
            return suffix
        if "wav" in content_type:
            return ".wav"
        if "ogg" in content_type:
            return ".ogg"
        if "mp4" in content_type or "m4a" in content_type:
            return ".m4a"
        return ".mp3"

    def _normalize_job_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        data_block = data.get("data") if isinstance(data.get("data"), dict) else data
        instrumentals = data_block.get("instrumentals") if isinstance(data_block.get("instrumentals"), list) else []
        item = instrumentals[0] if instrumentals and isinstance(instrumentals[0], dict) else data_block
        status = str(item.get("status") or "unknown").strip().lower()
        audio_url = item.get("audio_hi_url") or item.get("audio_url") or ""
        return {
            "status": status,
            "audio_url": str(audio_url).strip() if audio_url else "",
            "event": item.get("event"),
            "audio_hi_status": item.get("audio_hi_status"),
        }

    def _record_task(self, task_update: dict[str, Any]) -> None:
        tasks = self._load_tasks()
        task_id = task_update.get("task_id")
        items = tasks.setdefault("tasks", [])
        existing = next((item for item in items if item.get("task_id") == task_id), None)
        safe_update = {key: value for key, value in task_update.items() if key != "audio_url"}
        if existing:
            existing.update({key: value for key, value in safe_update.items() if value is not None})
        else:
            items.append(safe_update)
        self._save_json(self.tasks_path, tasks)

    def _task_by_id(self, task_id: str) -> dict[str, Any]:
        return next((task for task in self._load_tasks().get("tasks", []) if task.get("task_id") == task_id), {})

    def _update_manifest_item(
        self,
        bgm_id: str,
        *,
        status: str,
        task_id: str | None = None,
        generated_path: Path | None = None,
        error_code: str | None = None,
    ) -> None:
        manifest = self.ensure_manifest()
        for track in manifest["tracks"]:
            if track["bgm_id"] != bgm_id:
                continue
            track["status"] = status
            track["asset_available"] = bool(generated_path or self._find_existing_file(bgm_id))
            fallback_file = self._find_existing_file(bgm_id)
            track["generated_path"] = self._relative_path(generated_path or fallback_file)
            if task_id:
                track["task_id"] = task_id
                track["item_id"] = task_id
            if error_code:
                track["error_code"] = error_code
            track["updated_at"] = datetime.now().isoformat(timespec="seconds")
            break
        self._save_json(self.manifest_path, manifest)

    def _find_existing_file(self, bgm_id: str) -> Path | None:
        for suffix in (".mp3", ".wav", ".ogg", ".m4a"):
            candidate = self.generated_root / f"{bgm_id}{suffix}"
            if candidate.exists():
                return candidate
        return None

    def _definition_for(self, bgm_id: str, *, required: bool = True) -> dict[str, Any] | None:
        definition = next((item for item in TRACK_DEFINITIONS if item["bgm_id"] == bgm_id), None)
        if definition is None and required:
            raise ValueError("未知 BGM 曲目。")
        return definition

    def _load_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {}
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _load_tasks(self) -> dict[str, Any]:
        if not self.tasks_path.exists():
            return {"tasks": []}
        try:
            return json.loads(self.tasks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"tasks": []}

    def _save_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _relative_path(self, path: Path | None) -> str | None:
        if path is None:
            return None
        return str(path.relative_to(self.workspace_dir)).replace("\\", "/")

    def _extract_item_ids(self, data: dict[str, Any]) -> list[str]:
        data_block = data.get("data") if isinstance(data.get("data"), dict) else {}
        item_ids = data_block.get("item_ids")
        if not isinstance(item_ids, list):
            return []
        return [str(item_id).strip() for item_id in item_ids if str(item_id).strip()]

    def _is_success_response(self, data: dict[str, Any]) -> bool:
        return data.get("status") in {200000, "200000"}

    def _response_error_code(self, data: dict[str, Any]) -> str:
        code = data.get("status") or data.get("message") or "api_error"
        return str(code)[:80]

    def _safe_error_code(self, exc: Exception) -> str:
        if isinstance(exc, RuntimeError) and str(exc):
            return str(exc)[:80]
        return exc.__class__.__name__


def select_bgm_id(context: MusicSelectionContext) -> str:
    ending_map = {item["ending_id"]: item["bgm_id"] for item in TRACK_DEFINITIONS if item.get("ending_id")}
    npc_map = {npc_id: item["bgm_id"] for item in TRACK_DEFINITIONS for npc_id in item.get("npc_ids", [])}
    scene_map = {scene_id: item["bgm_id"] for item in TRACK_DEFINITIONS for scene_id in item.get("scene_ids", [])}
    stage_map = {item["stage"]: item["bgm_id"] for item in TRACK_DEFINITIONS if item.get("stage")}

    if context.ending_id and context.ending_id in ending_map:
        return ending_map[context.ending_id]
    if context.current_stage == "choice":
        return "ming_choice_evidence"
    if context.current_stage == "reversal":
        return "ming_reversal_grain_record"
    if context.current_npc_id and context.current_stage not in {"choice", "reversal", "ending"}:
        npc_track = npc_map.get(context.current_npc_id)
        if npc_track:
            return npc_track
    if context.risk_level >= 6 and context.current_stage in {"intro", "investigation"}:
        return "ming_reversal_grain_record"
    if context.current_scene_id and context.current_scene_id in scene_map:
        return scene_map[context.current_scene_id]
    if context.current_stage and context.current_stage in stage_map:
        return stage_map[context.current_stage]
    return "pre_game_entry"


music_generation_service = MusicGenerationService()
