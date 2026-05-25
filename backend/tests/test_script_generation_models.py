from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.script_models import ScriptPackage
from script_generation_fixtures import sample_script_payload


def test_script_package_minimal_payload_parses() -> None:
    package = ScriptPackage.model_validate(sample_script_payload())

    assert package.script_overview.title == "雨夜军报案"
    assert package.dynasty_id == "song"
    assert len(package.playable_identities) == 1
    assert len(package.hotspot_positioning) >= 6


def test_script_package_missing_required_field_reports_error() -> None:
    payload = sample_script_payload()
    payload.pop("script_overview")

    with pytest.raises(ValidationError) as exc_info:
        ScriptPackage.model_validate(payload)

    assert "script_overview" in str(exc_info.value)


def test_script_generate_request_rejects_damaged_keywords() -> None:
    payload = sample_script_payload()
    payload["keywords"] = ["??"]

    with pytest.raises(ValidationError) as exc_info:
        ScriptPackage.model_validate(payload)

    assert "关键词疑似编码损坏" in str(exc_info.value)
