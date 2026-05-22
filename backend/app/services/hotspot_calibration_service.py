from __future__ import annotations

from copy import deepcopy

from app.models.script_models import HotspotPositioning, ScriptPackage


class HotspotCalibrationService:
    def calibrate(self, package: ScriptPackage) -> ScriptPackage:
        updated = deepcopy(package)
        asset_by_id = {asset.asset_id: asset for asset in updated.visual_assets}
        existing = {(item.location_id, item.hotspot_id): item for item in updated.hotspot_positioning}
        calibrated: list[HotspotPositioning] = []

        for location in updated.locations:
            asset = asset_by_id.get(location.visual_asset_id)
            for index, hotspot in enumerate(location.hotspots):
                item = existing.get((location.location_id, hotspot.hotspot_id))
                if item is None:
                    continue
                approved = asset is not None and asset.quality_gate.status == "approved"
                item.calibration_status = "approved" if approved else "blocked"
                item.calibrated_against_path = asset.quality_gate.approved_path if approved and asset else None
                if hotspot.anchor_point is None:
                    hotspot.anchor_point = item.anchor_point
                if hotspot.bbox is None:
                    hotspot.bbox = item.bbox
                calibrated.append(item)

        updated.hotspot_positioning = calibrated
        return updated


hotspot_calibration_service = HotspotCalibrationService()
