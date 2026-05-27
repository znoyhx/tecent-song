from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path
from typing import Any

import httpx


class VisualLocatorService:
    """Optional VLM adapter for locating generated clue objects in scene images.

    Configure HISTORYGAME_VISION_LOCATOR_ENDPOINT to enable it. The endpoint is
    expected to accept an image plus target labels and return normalized boxes.
    Without that API we keep the existing deterministic fallback coordinates.
    """

    def __init__(self) -> None:
        self.endpoint = os.environ.get("HISTORYGAME_VISION_LOCATOR_ENDPOINT", "").strip()
        self.api_key = os.environ.get("HISTORYGAME_VISION_LOCATOR_API_KEY", "").strip()
        self.model = os.environ.get("HISTORYGAME_VISION_LOCATOR_MODEL", "").strip()

    @property
    def configured(self) -> bool:
        return bool(self.endpoint)

    def locate_hotspots(self, *, image_path: Path | None, targets: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
        if not self.configured or image_path is None or not image_path.exists() or not targets:
            return {}

        payload: dict[str, Any] = {
            "model": self.model or None,
            "image": {
                "mime_type": mimetypes.guess_type(str(image_path))[0] or "image/png",
                "base64": base64.b64encode(image_path.read_bytes()).decode("ascii"),
            },
            "targets": targets,
            "instructions": (
                "For each target, locate the visible concrete evidence object in the scene image. "
                "Return normalized bbox and anchor_point in 0..1 image coordinates. "
                "Ignore labels, captions, UI, abstract concepts, and people unless the target itself is testimony material."
            ),
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            with httpx.Client(timeout=float(os.environ.get("HISTORYGAME_VISION_LOCATOR_TIMEOUT", "45"))) as client:
                response = client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception:
            return {}

        return self._parse_results(data)

    def _parse_results(self, data: Any) -> dict[str, dict[str, Any]]:
        items = []
        if isinstance(data, dict):
            for key in ("targets", "results", "detections", "items"):
                value = data.get(key)
                if isinstance(value, list):
                    items = value
                    break
        elif isinstance(data, list):
            items = data

        parsed: dict[str, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            hotspot_id = str(item.get("id") or item.get("target_id") or item.get("hotspot_id") or "").strip()
            if not hotspot_id:
                continue
            bbox = self._normalize_bbox(item.get("bbox") or item.get("box") or item.get("box_2d"))
            anchor = self._normalize_point(item.get("anchor_point") or item.get("point") or item.get("center"))
            if bbox is None and anchor is None:
                continue
            if bbox is None and anchor is not None:
                bbox = self._bbox_from_anchor(anchor)
            if anchor is None and bbox is not None:
                anchor = {
                    "x": round(bbox["x"] + bbox["width"] / 2, 4),
                    "y": round(bbox["y"] + bbox["height"] / 2, 4),
                }
            parsed[hotspot_id] = {"bbox": bbox, "anchor_point": anchor, "confidence": item.get("confidence")}
        return parsed

    def _normalize_bbox(self, raw: Any) -> dict[str, float] | None:
        if isinstance(raw, dict):
            x = self._number(raw.get("x"))
            y = self._number(raw.get("y"))
            width = self._number(raw.get("width") or raw.get("w"))
            height = self._number(raw.get("height") or raw.get("h"))
            if None not in (x, y, width, height):
                return {
                    "x": self._clamp(x),
                    "y": self._clamp(y),
                    "width": self._clamp_size(width),
                    "height": self._clamp_size(height),
                }
            x1 = self._number(raw.get("x1"))
            y1 = self._number(raw.get("y1"))
            x2 = self._number(raw.get("x2"))
            y2 = self._number(raw.get("y2"))
            if None not in (x1, y1, x2, y2):
                return self._bbox_from_corners(x1, y1, x2, y2)
        if isinstance(raw, list) and len(raw) >= 4:
            values = [self._number(value) for value in raw[:4]]
            if all(value is not None for value in values):
                return self._bbox_from_corners(values[0], values[1], values[2], values[3])
        return None

    def _normalize_point(self, raw: Any) -> dict[str, float] | None:
        if isinstance(raw, dict):
            x = self._number(raw.get("x"))
            y = self._number(raw.get("y"))
            if x is not None and y is not None:
                return {"x": self._clamp(x), "y": self._clamp(y)}
        if isinstance(raw, list) and len(raw) >= 2:
            x = self._number(raw[0])
            y = self._number(raw[1])
            if x is not None and y is not None:
                return {"x": self._clamp(x), "y": self._clamp(y)}
        return None

    def _bbox_from_corners(self, x1: float, y1: float, x2: float, y2: float) -> dict[str, float]:
        x1 = self._clamp(x1)
        y1 = self._clamp(y1)
        x2 = self._clamp(x2)
        y2 = self._clamp(y2)
        left = min(x1, x2)
        top = min(y1, y2)
        return {
            "x": left,
            "y": top,
            "width": self._clamp_size(abs(x2 - x1)),
            "height": self._clamp_size(abs(y2 - y1)),
        }

    def _bbox_from_anchor(self, anchor: dict[str, float]) -> dict[str, float]:
        size = 0.1
        return {
            "x": self._clamp(anchor["x"] - size / 2),
            "y": self._clamp(anchor["y"] - size / 2),
            "width": size,
            "height": size,
        }

    def _number(self, value: Any) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if number > 1:
            number = number / 1000 if number <= 1000 else number / 10000
        return number

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, round(value, 4)))

    def _clamp_size(self, value: float) -> float:
        return max(0.02, min(0.5, round(value, 4)))


visual_locator_service = VisualLocatorService()
