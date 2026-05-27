from __future__ import annotations

from dataclasses import dataclass


HOTSPOT_LAYOUT_VERSION = "hotspot_layout_contract_v2"


@dataclass(frozen=True)
class HotspotSlot:
    slot_id: str
    x: float
    y: float
    label: str


# Safe 5x4 grid for wide investigation scenes. The y range intentionally avoids
# the bottom dialogue panel, and the x range avoids the left/right tool rails.
HOTSPOT_SLOTS: tuple[HotspotSlot, ...] = (
    HotspotSlot("slot_01", 0.20, 0.34, "left upper mid-ground evidence zone"),
    HotspotSlot("slot_02", 0.35, 0.34, "center-left upper mid-ground evidence zone"),
    HotspotSlot("slot_03", 0.50, 0.34, "central upper mid-ground evidence zone"),
    HotspotSlot("slot_04", 0.65, 0.34, "center-right upper mid-ground evidence zone"),
    HotspotSlot("slot_05", 0.80, 0.34, "right upper mid-ground evidence zone"),
    HotspotSlot("slot_06", 0.20, 0.42, "left table evidence zone"),
    HotspotSlot("slot_07", 0.35, 0.42, "center-left table evidence zone"),
    HotspotSlot("slot_08", 0.50, 0.42, "central table evidence zone"),
    HotspotSlot("slot_09", 0.65, 0.42, "center-right table evidence zone"),
    HotspotSlot("slot_10", 0.80, 0.42, "right table evidence zone"),
    HotspotSlot("slot_11", 0.20, 0.50, "left mid-ground evidence zone"),
    HotspotSlot("slot_12", 0.35, 0.50, "center-left mid-ground evidence zone"),
    HotspotSlot("slot_13", 0.50, 0.50, "central mid-ground evidence zone"),
    HotspotSlot("slot_14", 0.65, 0.50, "center-right mid-ground evidence zone"),
    HotspotSlot("slot_15", 0.80, 0.50, "right mid-ground evidence zone"),
    HotspotSlot("slot_16", 0.20, 0.58, "left lower safe evidence zone"),
    HotspotSlot("slot_17", 0.35, 0.58, "lower center-left safe evidence zone"),
    HotspotSlot("slot_18", 0.50, 0.58, "lower central safe evidence zone"),
    HotspotSlot("slot_19", 0.65, 0.58, "lower center-right safe evidence zone"),
    HotspotSlot("slot_20", 0.80, 0.58, "right lower safe evidence zone"),
)

HOTSPOT_LAYOUT_VARIANTS: tuple[tuple[int, ...], ...] = (
    (7, 11, 13, 17, 6, 12),
    (6, 8, 12, 16, 11, 13),
    (5, 9, 12, 18, 7, 17),
    (11, 13, 17, 7, 6, 8),
    (8, 12, 16, 6, 11, 18),
    (6, 12, 18, 8, 11, 13),
    (7, 13, 16, 11, 8, 12),
    (11, 17, 8, 12, 6, 18),
)


def slot_for_index(index: int, location_key: str = "") -> HotspotSlot:
    variant = HOTSPOT_LAYOUT_VARIANTS[_variant_index(location_key)]
    return HOTSPOT_SLOTS[variant[index % len(variant)]]


def anchor_for_index(index: int, location_key: str = "") -> dict[str, float]:
    slot = slot_for_index(index, location_key)
    return {"x": round(slot.x, 4), "y": round(slot.y, 4)}


def bbox_from_anchor(anchor: dict[str, float], *, size: float = 0.09) -> dict[str, float]:
    x = _clamp(anchor["x"] - size / 2, 0.06, 0.90)
    y = _clamp(anchor["y"] - size / 2, 0.08, 0.64)
    return {"x": round(x, 4), "y": round(y, 4), "width": size, "height": size}


def prompt_line(index: int, title: str, location_key: str = "") -> str:
    slot = slot_for_index(index, location_key)
    return f"{title}: {slot.slot_id}, x={round(slot.x * 100)}%, y={round(slot.y * 100)}%, {slot.label}"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _variant_index(location_key: str) -> int:
    text = str(location_key or "")
    if "_" in text:
        tail = text.rsplit("_", 1)[-1]
        if tail.isdigit():
            return int(tail) % len(HOTSPOT_LAYOUT_VARIANTS)
    if text.isdigit():
        return int(text) % len(HOTSPOT_LAYOUT_VARIANTS)
    seed = sum((index + 1) * ord(char) for index, char in enumerate(text))
    return seed % len(HOTSPOT_LAYOUT_VARIANTS)
