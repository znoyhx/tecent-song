from __future__ import annotations

from datetime import datetime
import hashlib
from pathlib import Path

from app.models.script_models import ImageQualityGateResult, VisualAsset
from app.services.script_visual_contract import (
    CLUE_CLOSEUP_CONTRACT,
    CLUE_OWNER_MARKER,
    NPC_IDENTITY_MARKER,
    NPC_PORTRAIT_CONTRACT,
    SCENE_CLUE_CONTRACT,
    SCENE_CLUE_MARKER,
    SCENE_NPC_CONTRACT,
    SCENE_NPC_MARKER,
    VISUAL_CONTRACT_VERSION,
)


class ImageQualityGate:
    def review_asset(self, *, asset: VisualAsset, file_path: Path | None, script_id: str) -> ImageQualityGateResult:
        issues: list[str] = []

        if file_path is None:
            issues.append("image_file_missing")
        elif not file_path.exists():
            issues.append("image_file_not_found")
        elif file_path.suffix.lower() == ".svg":
            issues.append("svg_or_placeholder_not_allowed")
        elif file_path.stat().st_size < 128:
            issues.append("image_file_too_small")
        elif f"generated/{script_id}/" not in file_path.as_posix().replace("\\", "/"):
            issues.append("image_not_owned_by_script")
        elif not self._looks_like_raster(file_path):
            issues.append("image_not_valid_raster")

        expected_hash = hashlib.sha256(asset.prompt.encode("utf-8")).hexdigest()[:16]
        if not asset.prompt_hash:
            issues.append("prompt_hash_missing")
        elif asset.prompt_hash != expected_hash:
            issues.append("prompt_hash_mismatch")
        if not asset.era_feature_checklist:
            issues.append("era_feature_checklist_missing")
        if not asset.required_subjects:
            issues.append("required_subjects_missing")
        if asset.generation_status in {"blocked", "rejected"}:
            issues.append("generation_status_not_passed")
        if asset.generated_path and "fallback" in asset.generated_path.lower():
            issues.append("fallback_image_not_allowed")

        if asset.asset_type == "scene":
            issues.extend(self._scene_contract_issues(asset))
        elif asset.asset_type == "clue":
            issues.extend(self._clue_contract_issues(asset))
        elif asset.asset_type == "npc":
            issues.extend(self._npc_contract_issues(asset))

        combined_issues = [*asset.quality_gate.issues, *issues]
        if combined_issues:
            return ImageQualityGateResult(
                status="rejected",
                checked_at=datetime.now().isoformat(timespec="seconds"),
                attempts=max(asset.quality_gate.attempts, 1),
                prompt_hash=asset.prompt_hash,
                issues=combined_issues,
                rejected_paths=[asset.generated_path] if asset.generated_path else [],
                regenerated_count=asset.quality_gate.regenerated_count,
            )

        return ImageQualityGateResult(
            status="approved",
            checked_at=datetime.now().isoformat(timespec="seconds"),
            attempts=max(asset.quality_gate.attempts, 1),
            prompt_hash=asset.prompt_hash,
            issues=[],
            approved_path=file_path.as_posix() if file_path else asset.generated_path,
            regenerated_count=asset.quality_gate.regenerated_count,
        )

    def _scene_contract_issues(self, asset: VisualAsset) -> list[str]:
        text = self._contract_text(asset)
        subjects = asset.required_subjects
        issues: list[str] = []
        if VISUAL_CONTRACT_VERSION not in text:
            issues.append("visual_contract_version_missing")
        if SCENE_NPC_CONTRACT not in text:
            issues.append("scene_missing_visible_npc_contract")
        if SCENE_CLUE_CONTRACT not in text:
            issues.append("scene_missing_clue_object_contract")
        if not self._has_marker(subjects, SCENE_NPC_MARKER) and SCENE_NPC_MARKER not in asset.prompt:
            issues.append("scene_missing_named_npc_contract")
        if not self._has_marker(subjects, SCENE_CLUE_MARKER) and SCENE_CLUE_MARKER not in asset.prompt:
            issues.append("scene_missing_named_clue_object_contract")
        return issues

    def _clue_contract_issues(self, asset: VisualAsset) -> list[str]:
        text = self._contract_text(asset)
        subjects = asset.required_subjects
        issues: list[str] = []
        if VISUAL_CONTRACT_VERSION not in text:
            issues.append("visual_contract_version_missing")
        if CLUE_CLOSEUP_CONTRACT not in text:
            issues.append("clue_missing_object_closeup_contract")
        if not self._has_marker(subjects, CLUE_OWNER_MARKER) and CLUE_OWNER_MARKER not in asset.prompt:
            issues.append("clue_missing_owner_contract")
        if not any(token in text for token in ("no readable text", "readable body text", CLUE_CLOSEUP_CONTRACT)):
            issues.append("clue_missing_no_readable_text_guard")
        scene_like_without_closeup = any(
            token in text for token in ("wide street scene", "crowd scene", "main scene", "environment illustration")
        ) and CLUE_CLOSEUP_CONTRACT not in text
        if scene_like_without_closeup:
            issues.append("clue_looks_like_scene_contract")
        return issues

    def _npc_contract_issues(self, asset: VisualAsset) -> list[str]:
        text = self._contract_text(asset)
        subjects = asset.required_subjects
        issues: list[str] = []
        if VISUAL_CONTRACT_VERSION not in text:
            issues.append("visual_contract_version_missing")
        if NPC_PORTRAIT_CONTRACT not in text:
            issues.append("npc_missing_portrait_contract")
        if not self._has_marker(subjects, NPC_IDENTITY_MARKER) and NPC_IDENTITY_MARKER not in asset.prompt:
            issues.append("npc_missing_identity_contract")
        return issues

    def _contract_text(self, asset: VisualAsset) -> str:
        return " ".join([asset.prompt, *asset.required_subjects])

    def _has_marker(self, subjects: list[str], marker: str) -> bool:
        return any(subject.startswith(marker) for subject in subjects)

    def _looks_like_raster(self, file_path: Path) -> bool:
        try:
            header = file_path.read_bytes()[:16]
        except OSError:
            return False
        return (
            header.startswith(b"\x89PNG\r\n\x1a\n")
            or header.startswith(b"\xff\xd8\xff")
            or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
        )


image_quality_gate = ImageQualityGate()
