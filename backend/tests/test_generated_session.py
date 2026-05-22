from __future__ import annotations

from app.models.game_models import InvestigateRequest
from app.models.script_models import ScriptGenerateRequest, ScriptPackage
from app.services import script_import_service as import_module
from app.services.game_engine import engine
from app.services.script_job_store import STEP_DEFINITIONS, ScriptJobStore
from script_generation_fixtures import sample_script_payload


def test_start_generated_session_and_investigate_hotspot(tmp_path, monkeypatch) -> None:
    store = ScriptJobStore(tmp_path)
    monkeypatch.setattr(import_module, "script_job_store", store)

    package = ScriptPackage.model_validate(sample_script_payload("script_session_test"))
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

    result = engine.investigate(
        InvestigateRequest(
            session_id=snapshot["session_id"],
            scene_id=snapshot["scene"]["scene_id"],
            hotspot_id=snapshot["scene"]["hotspots"][0]["hotspot_id"],
        )
    )

    assert result["new_clues"]
    assert result["new_clues"][0]["clue_id"] == "clue_0"
