from __future__ import annotations

from pathlib import Path

from app.models.script_models import ImageQualityGateResult, VisualAsset


class ImageQualityGate:
    def review_asset(self, *, asset: VisualAsset, file_path: Path | None, script_id: str) -> ImageQualityGateResult:
        issues: list[str] = []
        if file_path is None:
            issues.append("未找到图片文件")
        elif not file_path.exists():
            issues.append("图片文件不存在")
        elif file_path.suffix.lower() == ".svg":
            issues.append("SVG 或占位图不能计入通过")
        elif file_path.stat().st_size < 128:
            issues.append("图片文件为空或过小")
        elif f"generated{Path('/').as_posix()}{script_id}" not in file_path.as_posix().replace("\\", "/"):
            issues.append("图片不是本次生成剧本的资产")
        elif not self._looks_like_raster(file_path):
            issues.append("图片格式不是可验收的 PNG/JPEG/WebP")

        if not asset.prompt_hash:
            issues.append("缺少 prompt_hash")
        if not asset.era_feature_checklist:
            issues.append("缺少朝代视觉检查清单")
        if not asset.required_subjects:
            issues.append("缺少核心主体声明")
        if asset.generation_status in {"blocked", "rejected"}:
            issues.append("图片生成状态未通过")
        if asset.generated_path and "fallback" in asset.generated_path.lower():
            issues.append("fallback 图不能计入通过")

        from datetime import datetime

        previous_issues = list(asset.quality_gate.issues)
        combined_issues = [*previous_issues, *issues]

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
