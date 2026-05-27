from __future__ import annotations

from pathlib import Path

from app.models.script_models import ScriptPackage, VisualAsset
from app.services.image_quality_gate import image_quality_gate
from app.services.script_visual_contract import (
    SCENE_CLUE_DETAIL_CONTRACT,
    SCENE_CLUE_DETAIL_MARKER,
    SCENE_STYLE_GUIDE_CONTRACT,
    script_visual_contract,
)
from app.services.visual_clue_sanitizer import scene_clue_visual_requirement
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
    assert "scene_missing_centered_full_face_contract" in result.issues


def test_quality_gate_rejects_scene_without_clue_detail_gate(tmp_path: Path) -> None:
    png_path = tmp_path / "assets" / "generated" / "visuals" / "generated" / "script_a" / "asset_scene_0.png"
    png_path.parent.mkdir(parents=True)
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 200)
    asset = _visual_asset()
    asset.generated_path = str(png_path)
    asset.prompt = asset.prompt.replace(SCENE_CLUE_DETAIL_CONTRACT, "")
    asset.prompt = asset.prompt.replace(SCENE_CLUE_DETAIL_MARKER, "scene_clue_old:")
    asset.required_subjects = [
        subject
        for subject in asset.required_subjects
        if subject != SCENE_CLUE_DETAIL_CONTRACT and not subject.startswith(SCENE_CLUE_DETAIL_MARKER)
    ]

    result = image_quality_gate.review_asset(asset=asset, file_path=png_path, script_id="script_a")

    assert result.status == "rejected"
    assert "scene_missing_clue_detail_contract" in result.issues
    assert "scene_missing_clue_detail_marker" in result.issues


def test_scene_prompt_keeps_location_and_concrete_clue_requirements() -> None:
    payload = stage15_script_payload("script_scene_contract")
    payload["locations"][0]["name"] = "沈度宅邸"
    payload["locations"][0]["description"] = "书房里有被打开的暗格，雨夜灯影压在空盒上。"
    payload["locations"][0]["scene_text"] = "桌案旁的暗格半开，盒内空无一物。"
    payload["clues"][0]["title"] = "沈度书房暗格中的空盒"
    payload["clues"][0]["display_text"] = "暗格内有一只空木盒，盒内残留墨迹。"
    payload["clues"][0]["detail"] = "空盒说明原本藏在沈度书房暗格里的东西已被提前取走。"

    package = script_visual_contract.apply(ScriptPackage.model_validate(payload), reset_assets=True)
    scene_asset = next(asset for asset in package.visual_assets if asset.asset_id == "asset_scene_0")

    assert "沈度宅邸" in scene_asset.prompt
    assert "打开的空木盒" in scene_asset.prompt
    assert "打开的暗格" in scene_asset.prompt
    assert SCENE_CLUE_DETAIL_MARKER in scene_asset.prompt
    assert SCENE_STYLE_GUIDE_CONTRACT in scene_asset.prompt


def test_scene_prompt_does_not_force_ming_demo_style() -> None:
    payload = stage15_script_payload("script_scene_style_guide")

    package = script_visual_contract.apply(ScriptPackage.model_validate(payload), reset_assets=True)
    scene_asset = next(asset for asset in package.visual_assets if asset.asset_id == "asset_scene_0")

    forbidden_style_terms = ["Ming demo", "Ming-demo", "fixed Ming demo", "明代 Demo", "明代Demo", "明代固定 Demo"]
    combined_text = f"{scene_asset.prompt} {' '.join(scene_asset.required_subjects)}"
    assert not any(term in combined_text for term in forbidden_style_terms)
    assert SCENE_STYLE_GUIDE_CONTRACT in combined_text
    assert "visual_style_guide" in scene_asset.prompt
    assert "mountains, lakes, cabins, deer, western scenery" in scene_asset.prompt


def test_scene_clue_requirement_for_corpse_and_empty_box() -> None:
    corpse = {
        "title": "沈度尸体上的刀伤",
        "display_text": "致命伤为胸口一刀。",
        "detail": "伤口形状与变法司佩刀一致。",
    }
    empty_box = {
        "title": "沈度书房暗格中的空盒",
        "display_text": "暗格内有一空木盒。",
        "detail": "盒内残留墨迹。",
    }

    assert "尸体" in scene_clue_visual_requirement(corpse, location_name="汴河码头")
    assert "刀伤" in scene_clue_visual_requirement(corpse, location_name="汴河码头")
    assert "打开的空木盒" in scene_clue_visual_requirement(empty_box, location_name="沈度宅邸")
    assert "暗格" in scene_clue_visual_requirement(empty_box, location_name="沈度宅邸")


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
