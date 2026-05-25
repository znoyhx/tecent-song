from __future__ import annotations

from app.models.script_models import ScriptPackage
from app.services.script_supervisor import script_supervisor
from script_generation_fixtures import sample_script_payload, sample_script_payload_with_broken_chain


def test_script_supervisor_accepts_valid_sample() -> None:
    package = ScriptPackage.model_validate(sample_script_payload())

    result = script_supervisor.review(package)

    assert result.passed is True


def test_script_supervisor_blocks_broken_clue_chain() -> None:
    package = ScriptPackage.model_validate(sample_script_payload_with_broken_chain())

    result = script_supervisor.review(package)

    assert result.passed is False
    assert any(issue.code == "CLUE_CHAIN_BROKEN" for issue in result.blocking_issues)


def test_script_supervisor_blocks_scene_prompt_without_location_npc() -> None:
    payload = sample_script_payload()
    payload["visual_assets"][0]["prompt"] = "北宋雨夜驿站，空荡前厅，只有桌椅和军报。"
    payload["visual_assets"][0]["required_subjects"] = ["军报", "驿站"]
    package = ScriptPackage.model_validate(payload)

    result = script_supervisor.review(package)

    assert result.passed is False
    assert any(issue.code == "SCENE_NPC_INTEGRATION_MISSING" for issue in result.blocking_issues)


def test_script_supervisor_warns_when_truth_chain_is_not_in_clue_graph() -> None:
    payload = sample_script_payload()
    payload["clue_graph"][0]["required_clue_ids"] = ["clue_0", "clue_1"]
    package = ScriptPackage.model_validate(payload)

    result = script_supervisor.review(package)

    assert result.passed is True
    assert any(issue.code == "CLUE_CHAIN_WEAK" and issue.severity == "warning" for issue in result.issues)
