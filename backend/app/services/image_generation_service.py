from __future__ import annotations

from datetime import datetime
import base64
import json
import os

from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

from app.services.visual_prompt_agent import VisualAssetPrompt, visual_prompt_agent

CLUE_PROMPT_VERSION = "clue_no_text_v3"
SCENE_PROMPT_VERSION = "scene_integrated_npc_clues_v1"


GAME_VISUAL_ASSET_MAP = {
    "scene_front_hall": "scene_bookshop_front_hall",
    "scene_fire_yard": "scene_bookshop_fire_yard",
    "scene_account_room": "scene_account_room",
    "scene_lamp_shelf": "scene_lamp_shelf",
    "scene_engraving_room": "scene_bookshop_engraving_room",
    "scene_back_gate": "scene_back_gate",
    "scene_rain_alley": "scene_rain_alley",
    "scene_city_gate": "scene_city_gate",
    "scene_interrogation_room": "scene_interrogation_room",
    "npc_owner": "npc_xu_owner_cutout",
    "npc_worker": "npc_ashen_worker_cutout",
    "npc_scholar": "npc_guwen_scholar_cutout",
    "npc_jinyiwei": "npc_luzheng_jinyiwei_cutout",
    "clue_burned_page": "clue_burned_page",
    "clue_red_seal": "clue_red_seal",
    "clue_missing_manuscript_list": "clue_missing_manuscript_list",
    "clue_oil_smell": "clue_oil_smell",
    "clue_jinyiwei_gag_order": "clue_jinyiwei_gag_order",
}

STAGE8_DEMO_ASSET_IDS = [
    "scene_bookshop_front_hall",
    "scene_bookshop_fire_yard",
    "scene_account_room",
    "scene_lamp_shelf",
    "scene_bookshop_engraving_room",
    "scene_back_gate",
    "scene_rain_alley",
    "scene_city_gate",
    "scene_interrogation_room",
    "npc_owner_xu",
    "npc_worker_ashen",
    "npc_jinyiwei_lu",
    "clue_burned_page",
    "clue_red_seal",
    "clue_jinyiwei_gag_order",
]

OPTIONAL_ASSET_IDS = [
    "npc_scholar_guwen",
    "clue_missing_manuscript_list",
    "clue_oil_smell",
]

BOOTSTRAP_MINIMUM_ASSET_IDS = [
    "scene_bookshop_front_hall",
    "npc_worker_ashen",
    "clue_burned_page",
]

ASSET_DESCRIPTIONS = {
    "scene_bookshop_front_hall": "雨夜后的明代书坊前厅，柜台、稿单、旧书箱、烟气和压抑灯火。",
    "scene_bookshop_fire_yard": "雨后后院火场，烧塌的木架、湿灰、纸片与火光残影。",
    "scene_account_room": "狭小账房暗格，账册、暗抽屉、新木屑与墙角纸灰。",
    "scene_lamp_shelf": "灯油架旁的油痕、雨水脚印与被移动过的灯架拖痕。",
    "scene_bookshop_engraving_room": "烧毁的刻版间，残墨、刻刀、焦黑木版与被雨泥蹭过的门槛。",
    "scene_back_gate": "后门雨泥处，门闩磨痕、往返脚印与墙根细纸线。",
    "scene_interrogation_room": "锦衣卫临时问话处，湿封条、木案、薄纸与低压烛影。",
    "scene_rain_alley": "明代雨巷，青石路、湿墙、伞影与远处更鼓灯火。",
    "scene_city_gate": "雨夜城门搜检口，告示、守门火把、纸包书箱与紧张盘查。",
    "npc_owner_xu": "许掌柜，疲惫、谨慎、精明，像是在生计和隐情之间反复权衡。",
    "npc_worker_ashen": "阿沈，年轻刻工，袖口有旧墨，神情胆怯，总避开三更后的问题。",
    "npc_scholar_guwen": "顾闻，落第士子，清瘦焦急，怀里似乎藏着受潮旧稿。",
    "npc_jinyiwei_lu": "陆峥，低阶锦衣卫军官，冷峻克制，奉命封锁却并不掌握完整真相。",
    "npc_xu_owner_cutout": "许掌柜透明抠图立绘，用于主舞台人物背景融合。",
    "npc_ashen_worker_cutout": "阿沈透明抠图立绘，用于主舞台人物背景融合。",
    "npc_guwen_scholar_cutout": "顾闻透明抠图立绘，用于主舞台人物背景融合。",
    "npc_luzheng_jinyiwei_cutout": "陆峥透明抠图立绘，用于主舞台人物背景融合。",
    "clue_burned_page": "灰烬中残留的烧焦纸页，隐约可辨粮册相关字样。",
    "clue_red_seal": "半枚红印纸角，像是从官府文书或封缄处撕下。",
    "clue_missing_manuscript_list": "缺口整齐的稿单，暗示有人提前取走某批文稿。",
    "clue_oil_smell": "异常火油痕，位置与普通灯油走水说法并不相合。",
    "clue_jinyiwei_gag_order": "锦衣卫封口令，纸面潮湿，红印压住了不许外泄的命令。",
}

ASSET_TYPE_BY_CATEGORY = {
    "scenes": "scene_background",
    "npcs": "npc_portrait",
    "clues": "clue_item",
}


class ImageGenerationService:
    endpoint = "https://api.siliconflow.cn/v1/images/generations"
    model = "Kwai-Kolors/Kolors"

    def __init__(self) -> None:
        self.workspace_dir = Path(__file__).resolve().parents[3]
        self.backend_dir = self.workspace_dir / "backend"
        self.assets_root = self.workspace_dir / "assets" / "generated" / "visuals"
        self.manifest_path = self.assets_root / "asset_manifest.json"
        self.assets_root.mkdir(parents=True, exist_ok=True)
        self._manifest = self._load_manifest()

    def list_status(self) -> dict[str, Any]:
        asset_ids = STAGE8_DEMO_ASSET_IDS + OPTIONAL_ASSET_IDS
        assets = [self._asset_status(asset_id) for asset_id in asset_ids]
        return {
            "provider": self._image_provider(),
            "model": self.model,
            "api_key_available": self._has_api_key(),
            "assets_root": str(self.assets_root.relative_to(self.workspace_dir)).replace("\\", "/"),
            "asset_count": len(assets),
            "generated_count": sum(1 for asset in assets if asset["status"] == "generated"),
            "fallback_count": sum(1 for asset in assets if asset["status"] == "fallback"),
            "blocked_count": sum(1 for asset in assets if asset.get("blocked")),
            "assets": assets,
        }

    def generate_asset(self, asset_id: str, *, force: bool = False, image_size: str | None = None) -> dict[str, Any]:
        prompt = visual_prompt_agent.get_asset(asset_id)
        if prompt is None:
            raise ValueError("未知视觉资产。")

        existing = self._find_existing_file(prompt, asset_id)
        current_existing = self._find_existing_file(prompt, asset_id, require_current_prompt=True)
        if asset_id.endswith("_cutout"):
            if existing:
                self._update_manifest(asset_id, prompt, existing, status="generated", cached=True)
                return self._asset_status(asset_id, cached=True, message="已复用本地透明抠图人物资产。")
            self._update_manifest(asset_id, prompt, None, status="blocked", error="missing_local_cutout")
            return self._asset_status(asset_id, message="透明抠图人物资产缺失，未使用非透明图片冒充。")
        if current_existing and not force:
            self._update_manifest(asset_id, prompt, current_existing, status="generated", cached=True)
            return self._asset_status(asset_id, cached=True, message="已复用本地生成图片。")

        provider = self._image_provider()
        if provider != "siliconflow":
            self._update_manifest(asset_id, prompt, None, status="blocked", error="provider_disabled")
            return self._asset_status(asset_id, message="图片生成服务未启用，已使用本地视觉占位。")

        api_key = self._load_api_key()
        if not api_key:
            self._update_manifest(asset_id, prompt, None, status="blocked", error="missing_api_key")
            return self._asset_status(asset_id, message="未检测到图片生成 Key，已使用本地视觉占位。")

        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt.prompt,
            "negative_prompt": prompt.negative_prompt,
            "image_size": image_size or prompt.image_size,
            "batch_size": 1,
            "num_inference_steps": 20,
            "guidance_scale": 7.5,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        try:
            with httpx.Client(timeout=self._timeout_seconds(), follow_redirects=True) as client:
                response = client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                image_bytes = self._extract_image_bytes(data, client)
                file_path = self._target_file(prompt)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(image_bytes)

        except httpx.HTTPStatusError as exc:
            response = exc.response
            status_code = response.status_code if response is not None else "unknown"
            self._update_manifest(asset_id, prompt, None, status="blocked", error=f"http_{status_code}")
            return self._asset_status(asset_id, message="图片生成接口返回异常，已使用本地视觉占位。")
        except Exception as exc:  # noqa: BLE001 - never leak auth headers or temporary image URLs
            self._update_manifest(asset_id, prompt, None, status="blocked", error=self._safe_error_code(exc))
            return self._asset_status(asset_id, message="图片生成服务暂不可用，已使用本地视觉占位。")

        self._update_manifest(asset_id, prompt, file_path, status="generated", cached=False)

        return self._asset_status(asset_id, cached=False, message="图片已通过后端生成并保存到本地。")

    def bootstrap_demo_assets(self, *, include_clues: bool = False, force: bool = False) -> dict[str, Any]:
        asset_ids = STAGE8_DEMO_ASSET_IDS if include_clues else BOOTSTRAP_MINIMUM_ASSET_IDS
        results = [self.generate_asset(asset_id, force=force) for asset_id in asset_ids]
        return {
            "assets": results,
            "generated_count": sum(1 for asset in results if asset["status"] == "generated"),
            "fallback_count": sum(1 for asset in results if asset["status"] == "fallback"),
            "blocked_count": sum(1 for asset in results if asset.get("blocked")),
        }

    def asset_file_path(self, asset_id: str) -> Path | None:
        prompt = visual_prompt_agent.get_asset(asset_id)
        if prompt is None:
            return None
        return self._find_existing_file(
            prompt,
            asset_id,
            require_current_prompt=prompt.category == "scenes",
        )

    def asset_media_type(self, asset_id: str) -> str:
        file_path = self.asset_file_path(asset_id)
        if file_path and file_path.suffix.lower() == ".svg":
            return "image/svg+xml; charset=utf-8"
        return "image/png"

    def _extract_image_bytes(self, data: dict[str, Any], client: httpx.Client) -> bytes:
        image_item = self._first_image_item(data)
        image_url = image_item.get("url") or image_item.get("image_url")
        if image_url:
            image_response = client.get(str(image_url))
            image_response.raise_for_status()
            content_type = image_response.headers.get("content-type", "")
            if content_type and not content_type.startswith("image/") and not self._looks_like_image_bytes(image_response.content):
                raise RuntimeError("invalid_image_content")
            if not image_response.content:
                raise RuntimeError("empty_image_content")
            return image_response.content

        encoded_image = image_item.get("b64_json") or image_item.get("base64") or image_item.get("image")
        if isinstance(encoded_image, str) and encoded_image.strip():
            raw_value = encoded_image.split(",", 1)[1] if encoded_image.startswith("data:image/") and "," in encoded_image else encoded_image
            try:
                image_bytes = base64.b64decode(raw_value, validate=True)
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError("invalid_base64_image") from exc
            if not image_bytes:
                raise RuntimeError("empty_image_content")
            return image_bytes

        raise RuntimeError("missing_image_url")

    def _looks_like_image_bytes(self, content: bytes) -> bool:
        return (
            content.startswith(b"\x89PNG\r\n\x1a\n")
            or content.startswith(b"\xff\xd8\xff")
            or content.startswith(b"RIFF") and content[8:12] == b"WEBP"
        )

    def _first_image_item(self, data: dict[str, Any]) -> dict[str, Any]:
        for field_name in ("images", "data"):
            value = data.get(field_name)
            if isinstance(value, list) and value:
                first = value[0]
                if isinstance(first, dict):
                    return first
        return {}

    def _safe_error_code(self, exc: Exception) -> str:
        if isinstance(exc, RuntimeError) and str(exc):
            return str(exc)[:80]
        return exc.__class__.__name__

    def fallback_svg(self, asset_id: str) -> str:
        prompt = visual_prompt_agent.get_asset(asset_id)
        if prompt and prompt.category == "clues":
            return self._clue_fallback_svg(prompt.asset_id)
        return f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1024\" height=\"1024\" viewBox=\"0 0 1024 1024\">
  <defs>
    <radialGradient id=\"fire\" cx=\"24%\" cy=\"76%\" r=\"70%\"><stop offset=\"0%\" stop-color=\"#803528\"/><stop offset=\"42%\" stop-color=\"#2b2323\"/><stop offset=\"100%\" stop-color=\"#0d0c10\"/></radialGradient>
    <linearGradient id=\"rain\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\"><stop offset=\"0%\" stop-color=\"#243139\" stop-opacity=\".8\"/><stop offset=\"100%\" stop-color=\"#120d12\" stop-opacity=\".95\"/></linearGradient>
  </defs>
  <rect width=\"1024\" height=\"1024\" fill=\"url(#fire)\"/>
  <rect width=\"1024\" height=\"1024\" fill=\"url(#rain)\" opacity=\".65\"/>
  <path d=\"M70 760 C220 670 318 705 464 632 C612 558 720 590 950 470 L950 1024 L70 1024 Z\" fill=\"#07080b\" opacity=\".58\"/>
  <g opacity=\".22\" stroke=\"#d8b48a\" stroke-width=\"2\">{''.join(f'<line x1=\"{i}\" y1=\"0\" x2=\"{i - 180}\" y2=\"1024\"/>' for i in range(100, 1200, 95))}</g>
  <circle cx=\"764\" cy=\"244\" r=\"96\" fill=\"#b95b4f\" opacity=\".22\"/>
  <path d=\"M318 736 C410 660 515 650 612 706 C678 744 746 738 824 678\" fill=\"none\" stroke=\"#d8b48a\" stroke-width=\"10\" opacity=\".18\"/>
</svg>"""

    def _clue_fallback_svg(self, source_asset_id: str) -> str:
        object_markup = {
            "clue_burned_page": """
  <ellipse cx=\"512\" cy=\"730\" rx=\"330\" ry=\"92\" fill=\"#080608\" opacity=\".7\"/>
  <path d=\"M318 260 L706 300 L762 626 L594 806 L350 716 L288 530 L332 442 Z\" fill=\"#b98550\" stroke=\"#20100d\" stroke-width=\"18\"/>
  <path d=\"M492 304 L716 310 L744 468 L560 438 Z\" fill=\"#1a0705\" opacity=\".92\"/>
  <path d=\"M364 536 C454 494 554 492 650 530\" fill=\"none\" stroke=\"#3a211a\" stroke-width=\"9\" opacity=\".55\"/>
  <path d=\"M360 618 C474 570 602 586 678 640\" fill=\"none\" stroke=\"#3a211a\" stroke-width=\"8\" opacity=\".42\"/>
  <circle cx=\"262\" cy=\"784\" r=\"10\" fill=\"#d36840\" opacity=\".9\"/>
  <circle cx=\"708\" cy=\"724\" r=\"9\" fill=\"#d36840\" opacity=\".72\"/>
""",
            "clue_red_seal_fragment": """
  <rect x=\"262\" y=\"318\" width=\"496\" height=\"390\" rx=\"26\" fill=\"#2b180f\" opacity=\".75\"/>
  <path d=\"M372 274 L692 360 L612 740 L300 632 Z\" fill=\"#c99b68\" stroke=\"#1b0d09\" stroke-width=\"14\"/>
  <path d=\"M548 382 L704 424 L650 642 L504 592 Z\" fill=\"#8f2d2d\" opacity=\".88\"/>
  <path d=\"M580 414 L658 436 L626 568 L548 546 Z\" fill=\"#c8574a\" opacity=\".55\"/>
  <path d=\"M324 600 L450 634 L432 704 L300 662 Z\" fill=\"#e6c18a\" opacity=\".5\"/>
""",
            "clue_missing_manuscript_list": """
  <ellipse cx=\"512\" cy=\"736\" rx=\"310\" ry=\"84\" fill=\"#070608\" opacity=\".62\"/>
  <path d=\"M300 248 L708 218 L740 702 L350 762 L278 626 L334 560 Z\" fill=\"#d6b982\" stroke=\"#352119\" stroke-width=\"12\"/>
  <path d=\"M300 248 L430 258 L342 548 L278 626 Z\" fill=\"#0f0908\" opacity=\".38\"/>
  <path d=\"M410 342 L646 324\" stroke=\"#8a684a\" stroke-width=\"8\" opacity=\".22\"/>
  <path d=\"M398 430 L664 404\" stroke=\"#8a684a\" stroke-width=\"8\" opacity=\".2\"/>
  <path d=\"M390 520 L636 502\" stroke=\"#8a684a\" stroke-width=\"8\" opacity=\".18\"/>
""",
            "clue_oil_smell": """
  <rect x=\"186\" y=\"250\" width=\"652\" height=\"548\" rx=\"36\" fill=\"#1c1715\" opacity=\".86\"/>
  <path d=\"M274 652 C376 584 442 644 530 590 C640 522 704 586 774 522 L774 748 L274 748 Z\" fill=\"#5e3a1f\" opacity=\".54\"/>
  <path d=\"M332 566 C408 492 524 502 596 560 C654 606 704 600 752 560\" fill=\"none\" stroke=\"#d28645\" stroke-width=\"32\" opacity=\".38\"/>
  <path d=\"M358 592 C454 546 562 574 646 616\" fill=\"none\" stroke=\"#e4b36a\" stroke-width=\"18\" opacity=\".22\"/>
  <circle cx=\"702\" cy=\"468\" r=\"42\" fill=\"#6e3a20\" opacity=\".48\"/>
""",
            "clue_jinyiwei_gag_order": """
  <ellipse cx=\"512\" cy=\"742\" rx=\"330\" ry=\"88\" fill=\"#070608\" opacity=\".65\"/>
  <path d=\"M314 236 L690 290 L744 698 L376 762 Z\" fill=\"#c8a96f\" stroke=\"#2c1711\" stroke-width=\"14\"/>
  <path d=\"M354 286 L666 332 L706 662 L400 716 Z\" fill=\"#e0c891\" opacity=\".42\"/>
  <circle cx=\"560\" cy=\"500\" r=\"86\" fill=\"#7f2426\" opacity=\".9\"/>
  <circle cx=\"560\" cy=\"500\" r=\"48\" fill=\"#c44d43\" opacity=\".46\"/>
  <path d=\"M418 342 L652 376\" stroke=\"#8a684a\" stroke-width=\"10\" opacity=\".16\"/>
  <path d=\"M392 654 L642 610\" stroke=\"#8a684a\" stroke-width=\"9\" opacity=\".14\"/>
""",
        }.get(source_asset_id)
        if object_markup is None:
            object_markup = """
  <ellipse cx=\"512\" cy=\"730\" rx=\"320\" ry=\"86\" fill=\"#070608\" opacity=\".65\"/>
  <path d=\"M330 300 L704 276 L748 674 L392 760 L292 578 Z\" fill=\"#c6a06b\" stroke=\"#25140f\" stroke-width=\"14\"/>
  <circle cx=\"622\" cy=\"520\" r=\"78\" fill=\"#8f2d2d\" opacity=\".72\"/>
"""
        return f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1024\" height=\"1024\" viewBox=\"0 0 1024 1024\">
  <defs>
    <radialGradient id=\"glow\" cx=\"30%\" cy=\"74%\" r=\"72%\"><stop offset=\"0%\" stop-color=\"#7b3526\"/><stop offset=\"45%\" stop-color=\"#292121\"/><stop offset=\"100%\" stop-color=\"#0a090d\"/></radialGradient>
    <linearGradient id=\"shade\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\"><stop offset=\"0%\" stop-color=\"#26323a\" stop-opacity=\".75\"/><stop offset=\"100%\" stop-color=\"#100c11\" stop-opacity=\".96\"/></linearGradient>
  </defs>
  <rect width=\"1024\" height=\"1024\" fill=\"url(#glow)\"/>
  <rect width=\"1024\" height=\"1024\" fill=\"url(#shade)\" opacity=\".66\"/>
  <g opacity=\".2\" stroke=\"#d8b48a\" stroke-width=\"2\">{''.join(f'<line x1=\"{i}\" y1=\"0\" x2=\"{i - 180}\" y2=\"1024\"/>' for i in range(100, 1200, 95))}</g>
{object_markup}
</svg>"""

    def attach_visual(self, payload: dict[str, Any], game_object_id: str) -> dict[str, Any]:
        asset_id = GAME_VISUAL_ASSET_MAP.get(game_object_id)
        if not asset_id:
            return payload
        status = self._asset_status(asset_id)
        payload["visual_asset_id"] = asset_id
        payload["visual_asset_url"] = status["url"]
        payload["visual_status"] = status["status"]
        return payload

    def _asset_status(self, asset_id: str, *, cached: bool | None = None, message: str | None = None) -> dict[str, Any]:
        prompt = visual_prompt_agent.get_asset(asset_id)
        if prompt is None:
            return {
                "asset_id": asset_id,
                "asset_type": "unknown",
                "display_name": asset_id,
                "description": "未登记的视觉资产。",
                "status": "missing",
                "url": None,
                "fallback_path": None,
                "generated_path": None,
                "blocked": True,
                "message": "未找到对应视觉资产。",
            }

        file_path = self._find_existing_file(
            prompt,
            asset_id,
            require_current_prompt=prompt.category == "scenes",
        )
        manifest_item = self._manifest.get("assets", {}).get(asset_id, {})
        file_is_generated_png = file_path is not None and file_path.suffix.lower() == ".png"
        generation_status = "generated" if file_is_generated_png else manifest_item.get("status", "fallback")
        status = "generated" if file_is_generated_png else "fallback"
        route_path = f"/api/visual/assets/{asset_id}"
        description = ASSET_DESCRIPTIONS.get(asset_id) or ASSET_DESCRIPTIONS.get(visual_prompt_agent.normalize_asset_id(asset_id), prompt.title)
        generated_path = str(file_path.relative_to(self.workspace_dir)).replace("\\", "/") if file_is_generated_png and file_path else None
        result: dict[str, Any] = {
            "asset_id": asset_id,
            "source_asset_id": prompt.asset_id,
            "asset_type": ASSET_TYPE_BY_CATEGORY.get(prompt.category, prompt.category),
            "display_name": prompt.title,
            "title": prompt.title,
            "description": description,
            "category": prompt.category,
            "status": status,
            "generation_status": generation_status,
            "blocked": generation_status == "blocked" and not file_is_generated_png,
            "url": route_path,
            "fallback_path": route_path,
            "generated_path": generated_path,
            "path": generated_path,
            "updated_at": manifest_item.get("updated_at"),
            "message": message or self._status_message(status, generation_status),
        }
        if cached is not None:
            result["cached"] = cached
        if manifest_item.get("error"):
            result["error_code"] = manifest_item["error"]
        return result

    def _status_message(self, status: str, generation_status: str) -> str:
        if status == "generated":
            return "已使用本地生成图片。"
        if generation_status == "blocked":
            return "图片生成受阻，已使用本地视觉占位。"
        return "当前使用本地视觉占位。"

    def _load_api_key(self) -> str | None:
        env_key = os.getenv("SILICONFLOW_API_KEY") or os.getenv("IMAGE_GENERATION_API_KEY")
        if env_key:
            return env_key.strip()

        env_file_key = self._backend_env_value("SILICONFLOW_API_KEY") or self._backend_env_value("IMAGE_GENERATION_API_KEY")
        if env_file_key:
            return env_file_key.strip()

        return None

    def _has_api_key(self) -> bool:
        return bool(self._load_api_key())

    def _image_provider(self) -> str:
        return (os.getenv("IMAGE_PROVIDER") or self._backend_env_value("IMAGE_PROVIDER") or "siliconflow").strip().lower()

    def _timeout_seconds(self) -> float:
        value = os.getenv("IMAGE_GENERATION_TIMEOUT_SECONDS") or self._backend_env_value("IMAGE_GENERATION_TIMEOUT_SECONDS")
        try:
            return float(value) if value else 90.0
        except ValueError:
            return 90.0

    def _backend_env_value(self, name: str) -> str | None:
        for env_path in (self.backend_dir / ".env", self.workspace_dir / ".env"):
            value = self._env_file_value(env_path, name)
            if value:
                return value
        return None

    def _env_file_value(self, env_path: Path, name: str) -> str | None:
        if not env_path.exists():
            return None
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export ") :].strip()
            key, value = line.split("=", 1)
            if key.strip() == name:
                return value.strip().strip('"').strip("'")
        return None

    def _target_file(self, prompt: VisualAssetPrompt) -> Path:
        return self.assets_root / prompt.category / f"{prompt.asset_id}.png"

    def _find_existing_file(
        self,
        prompt: VisualAssetPrompt,
        requested_asset_id: str | None = None,
        *,
        require_current_prompt: bool = False,
    ) -> Path | None:
        requested_id = requested_asset_id or prompt.asset_id
        if prompt.category == "clues":
            manifest_item = self._manifest.get("assets", {}).get(requested_id, {})
            png_path = self._target_file(prompt)
            if manifest_item.get("prompt_version") == CLUE_PROMPT_VERSION and png_path.exists():
                return png_path
            return None
        if prompt.category == "scenes" and require_current_prompt:
            manifest_item = self._manifest.get("assets", {}).get(requested_id, {})
            png_path = self._target_file(prompt)
            if (
                manifest_item.get("status") == "generated"
                and manifest_item.get("prompt_version") == SCENE_PROMPT_VERSION
                and png_path.exists()
            ):
                return png_path
            return None
        for file_path in (self._target_file(prompt), self.assets_root / prompt.category / f"{prompt.asset_id}.svg"):
            if file_path.exists():
                return file_path
        return None

    def _load_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {"version": 1, "assets": {}}
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"version": 1, "assets": {}}

    def _save_manifest(self) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(self._manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def _update_manifest(
        self,
        requested_asset_id: str,
        prompt: VisualAssetPrompt,
        file_path: Path | None,
        *,
        status: str,
        cached: bool = False,
        error: str | None = None,
    ) -> None:
        item = {
            "asset_id": requested_asset_id,
            "source_asset_id": prompt.asset_id,
            "display_name": prompt.title,
            "category": prompt.category,
            "status": status,
            "path": str(file_path.relative_to(self.workspace_dir)).replace("\\", "/") if file_path else None,
            "model": self.model,
            "cached": cached,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "call_id": f"img_{uuid4().hex[:8]}",
            "input_summary": f"{prompt.title} / {ASSET_TYPE_BY_CATEGORY.get(prompt.category, prompt.category)}",
        }
        if prompt.category == "clues":
            item["prompt_version"] = CLUE_PROMPT_VERSION
        if prompt.category == "scenes":
            item["prompt_version"] = SCENE_PROMPT_VERSION
        if error:
            item["error"] = error
        self._manifest.setdefault("assets", {})[requested_asset_id] = item
        self._save_manifest()


image_generation_service = ImageGenerationService()
