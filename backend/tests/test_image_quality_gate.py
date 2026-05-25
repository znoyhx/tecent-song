from __future__ import annotations

from pathlib import Path

from app.models.script_models import ScriptPackage, VisualAsset
from app.services.image_quality_gate import image_quality_gate
from app.services.script_visual_contract import script_visual_contract
from script_generation_fixtures import stage15_script_payload


def _visual_asset() -> VisualAsset:
    return VisualAsset.model_validate(stage15_script_payload("script_quality")["visual_assets"][0])


def test_quality_gate_rejects_fallback_svg(tmp_path: Path) -> None:
    svg_path = tmp_path / "generated" / "script_a" / "asset_scene_0.svg"
    svg_path.parent.mkdir(parents=True)
    svg_path.write_text("<svg></svg>", encoding="utf-8")
    asset = _visual_asset()
    asset.generated_path = str(svg_path)

    result = image_quality_gate.review_asset(asset=asset, file_path=svg_path, script_id="script_a")

    assert result.status == "rejected"
    assert "svg_or_placeholder_not_allowed" in result.issues


def test_quality_gate_rejects_old_cache_path(tmp_path: Path) -> None:
    png_path = tmp_path / "generated" / "other_script" / "asset_scene_0.png"
    png_path.parent.mkdir(parents=True)
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 200)
    asset = _visual_asset()
    asset.generated_path = str(png_path)

    result = image_quality_gate.review_asset(asset=asset, file_path=png_path, script_id="script_a")

    assert result.status == "rejected"
    assert "image_not_owned_by_script" in result.issues


def test_quality_gate_approves_job_owned_png(tmp_path: Path) -> None:
    png_path = tmp_path / "assets" / "generated" / "visuals" / "generated" / "script_a" / "asset_scene_0.png"
    png_path.parent.mkdir(parents=True)
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 200)
    asset = _visual_asset()
    asset.generated_path = str(png_path)

    result = image_quality_gate.review_asset(asset=asset, file_path=png_path, script_id="script_a")

    assert result.status == "approved"


def test_quality_gate_rejects_scene_without_integrated_people_contract(tmp_path: Path) -> None:
    png_path = tmp_path / "assets" / "generated" / "visuals" / "generated" / "script_a" / "asset_scene_0.png"
    png_path.parent.mkdir(parents=True)
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 200)
    asset = _visual_asset()
    asset.generated_path = str(png_path)
    asset.prompt = "Northern Song rainy station, empty front hall, one dispatch on a table."
    asset.required_subjects = ["dispatch", "station"]

    result = image_quality_gate.review_asset(asset=asset, file_path=png_path, script_id="script_a")

    assert result.status == "rejected"
    assert "scene_missing_visible_npc_contract" in result.issues
    assert "scene_missing_named_npc_contract" in result.issues


def test_visual_contract_resets_old_cached_asset_without_hash() -> None:
    payload = stage15_script_payload("script_contract_reset")
    payload["visual_assets"][0]["prompt_hash"] = None
    payload["visual_assets"][0]["generated_path"] = "assets/generated/visuals/generated/script_contract_reset/asset_scene_0.png"
    payload["visual_assets"][0]["url"] = "/api/scripts/script_contract_reset/assets/asset_scene_0"

    package = script_visual_contract.apply(ScriptPackage.model_validate(payload))
    asset = package.visual_assets[0]

    assert asset.generated_path is None
    assert asset.url is None
    assert asset.generation_status == "pending"
    assert asset.prompt_hash
