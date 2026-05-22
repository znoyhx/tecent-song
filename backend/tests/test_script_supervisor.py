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
