from __future__ import annotations

from app.models.game_models import InvestigateRequest
from app.models.script_models import ScriptGenerateRequest, ScriptPackage
from app.services import script_import_service as import_module
from app.services.game_engine import engine
from app.services.script_job_store import STEP_DEFINITIONS, ScriptJobStore
from script_generation_fixtures import stage15_script_payload


def test_start_generated_session_and_investigate_hotspot(tmp_path, monkeypatch) -> None:
    store = ScriptJobStore(tmp_path)
    monkeypatch.setattr(import_module, "script_job_store", store)

    package = ScriptPackage.model_validate(stage15_script_payload("script_session_test"))
    _write_approved_asset_files(package, tmp_path)
    store.save_script(package)
    job = store.create_job(ScriptGenerateRequest(dynasty_id="song", keywords=package.keywords))
    job.script_id = package.script_id
    job.status = "completed"
    job.progress = 100
    job.ready_for_overview = True
    job.current_step = "completed"
    for step, definition in zip(job.steps, STEP_DEFINITIONS):
        step.step_id = definition[0]
        step.status = "passed"
    store.save_job(job)

    snapshot = import_module.script_import_service.start_generated_session(
        script_id=package.script_id,
        identity_id="identity_inspector",
    )

    assert snapshot["state"]["event_id"] == package.script_id
    assert snapshot["scene"]["hotspots"][0]["calibration_status"] == "approved"
    assert engine.sessions[snapshot["session_id"]]["catalog"]["deductions"]
    assert engine.sessions[snapshot["session_id"]]["catalog"]["chapter_sections"]

    result = engine.investigate(
        InvestigateRequest(
            session_id=snapshot["session_id"],
            scene_id=snapshot["scene"]["scene_id"],
            hotspot_id=snapshot["scene"]["hotspots"][0]["hotspot_id"],
        )
    )

    assert result["new_clues"]
    assert result["new_clues"][0]["clue_id"] == "clue_0"

    refreshed = engine.get_session(snapshot["session_id"])
    assert refreshed["available_deductions"]
    assert refreshed["available_deductions"][0]["deduction_id"].startswith("deduction_")


def _write_approved_asset_files(package: ScriptPackage, root) -> None:
    for asset in package.visual_assets:
        if asset.asset_type not in {"scene", "npc", "clue"}:
            continue
        path = root / "assets" / "generated" / "visuals" / "generated" / package.script_id / f"{asset.asset_id}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 200)
        asset.generated_path = str(path)
        asset.url = f"/api/scripts/{package.script_id}/assets/{asset.asset_id}"
        asset.quality_gate.approved_path = str(path)
