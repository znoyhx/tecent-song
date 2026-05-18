from __future__ import annotations

import json

from app.core.config import settings
from app.models.game_models import SupervisorIssue
from app.services.log_service import LogService


def test_log_service_redacts_keys_and_records_observability_fields(tmp_path) -> None:
    log_service = LogService(tmp_path)
    env_secret = settings.deepseek_api_key or "sk-testsecret000000"

    entry = log_service.record_ai_call(
        module="NPCDialogueAgent",
        model="deepseek-chat",
        input_summary=f"Bearer {env_secret} sk-summary000000",
        latency_ms=12,
        success=True,
        fallback_used=False,
        supervisor_pass=False,
        issues=[SupervisorIssue(type="role_permission", severity="high", detail=f"Bearer {env_secret}")],
        prompt=f"Authorization: Bearer {env_secret}\nsource_id=ming_worker_third_watch_001",
        raw_response=f'{{"text":"sk-response000000 {env_secret}"}}',
        extra_fields={
            "rag_hit_count": 2,
            "rag_source_ids": ["ming_worker_third_watch_001", "ming_jinyiwei_permission_001"],
            "rag_material_types": ["clue_boundary", "hard_rule"],
            "repair_attempted": True,
            "repair_success": False,
            "fallback_used": False,
            "nested": {
                "authorization": f"Bearer {env_secret}",
                "items": [{"secret": f"sk-nested000000 {env_secret}"}],
            },
        },
    )

    assert entry["rag_hit_count"] == 2
    assert "ming_worker_third_watch_001" in entry["rag_source_ids"]
    assert "hard_rule" in entry["rag_material_types"]
    assert "role_permission" in entry["supervisor_issue_types"]
    assert entry["repair_attempted"] is True
    assert entry["repair_success"] is False
    assert entry["fallback_used"] is False
    assert entry["ai_mode"] in {"mock", "real"}

    log_text = (tmp_path / "ai_calls.jsonl").read_text(encoding="utf-8")
    prompt_text = (tmp_path / "prompts" / f"{entry['call_id']}.txt").read_text(encoding="utf-8")
    response_text = (tmp_path / "responses" / f"{entry['call_id']}.json").read_text(encoding="utf-8")
    combined = "\n".join([log_text, prompt_text, response_text, json.dumps(entry, ensure_ascii=False)])

    assert env_secret not in combined
    assert "Bearer " not in combined or "Bearer [已隐藏密钥]" in combined
    assert "sk-summary000000" not in combined
    assert "sk-response000000" not in combined
    assert "sk-nested000000" not in combined
    assert f"Authorization: Bearer {env_secret}" not in combined

