from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from app.models.script_models import HotspotPositioning, NormalizedBBox, NormalizedPoint, ScriptPackage
from app.services.hotspot_layout_contract import anchor_for_index, bbox_from_anchor
from app.services.visual_locator_service import visual_locator_service


class HotspotCalibrationService:
    def calibrate(self, package: ScriptPackage) -> ScriptPackage:
        updated = deepcopy(package)
        asset_by_id = {asset.asset_id: asset for asset in updated.visual_assets}
        existing = {(item.location_id, item.hotspot_id): item for item in updated.hotspot_positioning}
        calibrated: list[HotspotPositioning] = []

        for location in updated.locations:
            asset = asset_by_id.get(location.visual_asset_id)
            approved = asset is not None and asset.quality_gate.status == "approved"
            image_path = self._image_path(asset) if approved else None
            located = (
                visual_locator_service.locate_hotspots(
                    image_path=image_path,
                    targets=[
                        {
                            "id": hotspot.hotspot_id,
                            "label": hotspot.label,
                            "description": hotspot.description,
                            "clue_ids": ",".join(hotspot.clue_ids),
                        }
                        for hotspot in location.hotspots
                    ],
                )
                if approved and image_path is not None
                else {}
            )
            for local_index, hotspot in enumerate(location.hotspots):
                item = existing.get((location.location_id, hotspot.hotspot_id))
                if item is None:
                    continue
                located_item = located.get(hotspot.hotspot_id)
                if located_item:
                    item.anchor_point = NormalizedPoint.model_validate(located_item["anchor_point"])
                    item.bbox = NormalizedBBox.model_validate(located_item["bbox"])
                elif not visual_locator_service.configured:
                    item.anchor_point = NormalizedPoint.model_validate(anchor_for_index(local_index, location.location_id))
                    item.bbox = NormalizedBBox.model_validate(bbox_from_anchor(item.anchor_point.model_dump(mode="json")))
                item.calibration_status = "approved" if approved and (located_item or not visual_locator_service.configured) else "blocked"
                item.calibrated_against_path = asset.quality_gate.approved_path if approved and asset else None
                if hotspot.anchor_point is None:
                    hotspot.anchor_point = item.anchor_point
                if hotspot.bbox is None:
                    hotspot.bbox = item.bbox
                calibrated.append(item)

        updated.hotspot_positioning = calibrated
        return updated

    def _image_path(self, asset) -> Path | None:
        if asset is None:
            return None
        raw_path = asset.quality_gate.approved_path or asset.generated_path
        if not raw_path:
            return None
        path = Path(raw_path)
        return path if path.exists() else None


hotspot_calibration_service = HotspotCalibrationService()
