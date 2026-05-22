from __future__ import annotations

from pathlib import Path

from app.models.script_models import VisualAsset
from app.services.image_quality_gate import image_quality_gate
from script_generation_fixtures import sample_script_payload


def _visual_asset() -> VisualAsset:
    return VisualAsset.model_validate(sample_script_payload()["visual_assets"][0])


def test_quality_gate_rejects_fallback_svg(tmp_path: Path) -> None:
    svg_path = tmp_path / "generated" / "script_a" / "asset_scene_0.svg"
    svg_path.parent.mkdir(parents=True)
    svg_path.write_text("<svg></svg>", encoding="utf-8")
    asset = _visual_asset()
    asset.generated_path = str(svg_path)

    result = image_quality_gate.review_asset(asset=asset, file_path=svg_path, script_id="script_a")

    assert result.status == "rejected"
    assert any("SVG" in issue for issue in result.issues)


def test_quality_gate_rejects_old_cache_path(tmp_path: Path) -> None:
    png_path = tmp_path / "generated" / "other_script" / "asset_scene_0.png"
    png_path.parent.mkdir(parents=True)
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 200)
    asset = _visual_asset()
    asset.generated_path = str(png_path)

    result = image_quality_gate.review_asset(asset=asset, file_path=png_path, script_id="script_a")

    assert result.status == "rejected"
    assert any("本次生成剧本" in issue for issue in result.issues)


def test_quality_gate_approves_job_owned_png(tmp_path: Path) -> None:
    png_path = tmp_path / "assets" / "generated" / "visuals" / "generated" / "script_a" / "asset_scene_0.png"
    png_path.parent.mkdir(parents=True)
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 200)
    asset = _visual_asset()
    asset.generated_path = str(png_path)

    result = image_quality_gate.review_asset(asset=asset, file_path=png_path, script_id="script_a")

    assert result.status == "approved"
