from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


WORKSPACE = Path(__file__).resolve().parents[4]
NPC_DIR = WORKSPACE / "assets" / "generated" / "visuals" / "npcs"
MANIFEST_PATH = WORKSPACE / "assets" / "generated" / "visuals" / "asset_manifest.json"


PROFILES = {
    "npc_xu_owner": {
        "clip": [
            (0.13, 1), (0.13, 0.72), (0.18, 0.62), (0.29, 0.56),
            (0.36, 0.44), (0.36, 0.28), (0.43, 0.17), (0.56, 0.17),
            (0.64, 0.27), (0.66, 0.43), (0.73, 0.55), (0.85, 0.64),
            (0.88, 1),
        ],
        "fg": [
            ("ellipse", 0.52, 0.18, 0.17, 0.09),
            ("ellipse", 0.52, 0.34, 0.19, 0.2),
            ("ellipse", 0.53, 0.61, 0.43, 0.45),
            ("rect", 0.1, 0.55, 0.82, 0.44),
        ],
        "bg": [("rect", 0, 0, 1, 0.1), ("rect", 0, 0, 0.05, 1), ("rect", 0.95, 0, 0.05, 1)],
        "rect": (0.08, 0.11, 0.84, 0.88),
    },
    "npc_ashen_worker": {
        "clip": [
            (0.27, 0.23), (0.35, 0.15), (0.47, 0.15), (0.59, 0.22),
            (0.63, 0.33), (0.59, 0.41), (0.66, 0.54), (0.68, 1),
            (0.27, 1), (0.22, 0.82), (0.27, 0.64), (0.32, 0.49),
            (0.29, 0.34),
        ],
        "fg": [
            ("ellipse", 0.42, 0.19, 0.18, 0.09),
            ("ellipse", 0.49, 0.29, 0.17, 0.18),
            ("ellipse", 0.5, 0.66, 0.33, 0.46),
            ("rect", 0.25, 0.36, 0.5, 0.62),
        ],
        "bg": [("rect", 0, 0, 1, 0.08), ("rect", 0, 0, 0.08, 1), ("rect", 0.84, 0, 0.16, 1)],
        "rect": (0.12, 0.08, 0.72, 0.91),
    },
    "npc_guwen_scholar": {
        "clip": [
            (0.25, 0.12), (0.39, 0.04), (0.55, 0.06), (0.67, 0.19),
            (0.79, 0.34), (0.9, 0.52), (0.92, 1), (0.24, 1),
            (0.02, 0.9), (0.17, 0.78), (0.32, 0.61), (0.26, 0.43),
            (0.2, 0.26),
        ],
        "fg": [
            ("ellipse", 0.48, 0.25, 0.22, 0.22),
            ("ellipse", 0.65, 0.67, 0.38, 0.46),
            ("ellipse", 0.23, 0.86, 0.26, 0.16),
            ("rect", 0.38, 0.38, 0.54, 0.6),
        ],
        "bg": [("rect", 0, 0, 0.05, 0.65), ("rect", 0, 0, 1, 0.04), ("rect", 0.95, 0, 0.05, 1)],
        "rect": (0.1, 0.04, 0.86, 0.95),
    },
    "npc_luzheng_jinyiwei": {
        "clip": [
            (0.18, 0.13), (0.35, 0.06), (0.5, 0.17), (0.63, 0.31),
            (0.84, 0.39), (0.98, 1), (0.25, 1), (0.17, 0.68),
            (0.1, 0.5), (0.15, 0.3),
        ],
        "fg": [
            ("ellipse", 0.35, 0.13, 0.16, 0.08),
            ("ellipse", 0.38, 0.3, 0.22, 0.2),
            ("ellipse", 0.58, 0.68, 0.42, 0.45),
            ("rect", 0.22, 0.35, 0.68, 0.64),
        ],
        "bg": [("rect", 0, 0, 1, 0.05), ("rect", 0, 0, 0.06, 0.7), ("rect", 0.95, 0, 0.05, 1)],
        "rect": (0.07, 0.04, 0.9, 0.95),
    },
}


def rel_path(path: Path) -> str:
    return str(path.relative_to(WORKSPACE)).replace("\\", "/")


def draw_shape(mask: np.ndarray, shape: tuple, value: int) -> None:
    kind = shape[0]
    height, width = mask.shape
    if kind == "ellipse":
        _, cx, cy, rx, ry = shape
        cv2.ellipse(
            mask,
            (int(cx * width), int(cy * height)),
            (int(rx * width), int(ry * height)),
            0,
            0,
            360,
            value,
            -1,
        )
        return
    if kind == "rect":
        _, x, y, w, h = shape
        cv2.rectangle(
            mask,
            (int(x * width), int(y * height)),
            (int((x + w) * width), int((y + h) * height)),
            value,
            -1,
        )


def keep_seed_components(alpha: np.ndarray, seed_mask: np.ndarray) -> np.ndarray:
    component_count, labels, stats, _ = cv2.connectedComponentsWithStats((alpha > 0).astype(np.uint8), 8)
    kept = np.zeros_like(alpha)
    image_area = alpha.shape[0] * alpha.shape[1]
    for component in range(1, component_count):
        area = stats[component, cv2.CC_STAT_AREA]
        component_mask = labels == component
        seed_overlap = np.count_nonzero(component_mask & (seed_mask > 0))
        if seed_overlap > 0 or area > image_area * 0.08:
            kept[component_mask] = 255
    return kept


def clip_mask_for_profile(width: int, height: int, profile: dict) -> np.ndarray:
    points = np.array(
        [[int(x * width), int(y * height)] for x, y in profile["clip"]],
        dtype=np.int32,
    )
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillPoly(mask, [points], 255)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    return cv2.GaussianBlur(mask, (0, 0), 1.8)


def make_cutout(asset_id: str, profile: dict) -> Path:
    source_path = NPC_DIR / f"{asset_id}.png"
    output_path = NPC_DIR / f"{asset_id}_cutout.png"
    image = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(source_path)

    height, width = image.shape[:2]
    mask = np.full((height, width), cv2.GC_BGD, dtype=np.uint8)
    rx, ry, rw, rh = profile["rect"]
    rect = (int(rx * width), int(ry * height), int(rw * width), int(rh * height))
    mask[rect[1] : rect[1] + rect[3], rect[0] : rect[0] + rect[2]] = cv2.GC_PR_FGD

    seed_mask = np.zeros((height, width), dtype=np.uint8)
    for shape in profile["bg"]:
        draw_shape(mask, shape, cv2.GC_BGD)
    for shape in profile["fg"]:
        draw_shape(mask, shape, cv2.GC_FGD)
        draw_shape(seed_mask, shape, 255)

    bg_model = np.zeros((1, 65), np.float64)
    fg_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(image, mask, None, bg_model, fg_model, 8, cv2.GC_INIT_WITH_MASK)

    alpha = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    alpha = keep_seed_components(alpha, seed_mask)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel, iterations=2)
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, kernel, iterations=1)
    alpha = np.minimum(alpha, clip_mask_for_profile(width, height, profile))
    inner = cv2.erode(alpha, kernel, iterations=1)
    soft = cv2.GaussianBlur(alpha, (0, 0), 1.15)
    alpha = np.where(inner > 0, 255, soft).astype(np.uint8)
    alpha[alpha < 10] = 0

    rgba = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
    rgba[:, :, 3] = alpha
    Image.fromarray(rgba).save(output_path)
    return output_path


def write_preview(outputs: list[Path]) -> Path:
    tile_w, tile_h = 240, 320
    preview = Image.new("RGBA", (tile_w * len(outputs), tile_h), (18, 15, 13, 255))
    draw = ImageDraw.Draw(preview)
    for index, output in enumerate(outputs):
        tile = Image.new("RGBA", (tile_w, tile_h), (18, 15, 13, 255))
        d = ImageDraw.Draw(tile)
        cell = 24
        for y in range(0, tile_h, cell):
            for x in range(0, tile_w, cell):
                if (x // cell + y // cell) % 2 == 0:
                    d.rectangle([x, y, x + cell, y + cell], fill=(44, 38, 32, 255))
        cutout = Image.open(output).convert("RGBA")
        cutout.thumbnail((tile_w - 18, tile_h - 28), Image.Resampling.LANCZOS)
        tile.alpha_composite(cutout, ((tile_w - cutout.width) // 2, tile_h - cutout.height - 8))
        preview.alpha_composite(tile, (index * tile_w, 0))
        draw.text((index * tile_w + 8, 8), output.stem, fill=(232, 210, 174, 255))
    preview_path = NPC_DIR / "npc_cutout_preview.png"
    preview.convert("RGB").save(preview_path)
    return preview_path


def update_manifest(outputs: list[Path]) -> None:
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    else:
        manifest = {"version": 1, "assets": {}}
    now = datetime.now().isoformat(timespec="seconds")
    for output in outputs:
        asset_id = output.stem
        manifest.setdefault("assets", {})[asset_id] = {
            "asset_id": asset_id,
            "source_asset_id": asset_id,
            "display_name": asset_id.replace("_", " "),
            "category": "npcs",
            "status": "generated",
            "path": rel_path(output),
            "model": "local-opencv-grabcut-alpha",
            "cached": False,
            "updated_at": now,
            "call_id": f"cutout_{asset_id}",
            "input_summary": "local transparent alpha cutout from generated NPC portrait",
        }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    outputs = [make_cutout(asset_id, profile) for asset_id, profile in PROFILES.items()]
    preview = write_preview(outputs)
    update_manifest(outputs)
    for output in outputs:
        print(rel_path(output))
    print(rel_path(preview))


if __name__ == "__main__":
    main()
