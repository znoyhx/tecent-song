from __future__ import annotations

import json
from typing import Any

from app.core.config import Settings
from app.services.ai_client import AIResponse
from app.services.dialogue_orchestrator import NPC_DIALOGUE_SCHEMA_HINT
from app.services.repair_agent import RepairAgent


class FakeRepairAIClient:
    def __init__(self) -> None:
        self.last_prompt = ""

    def generate_json_sync(self, *, module: str, prompt: str, schema_hint: dict[str, Any]) -> AIResponse:
        self.last_prompt = prompt
        payload = {
            "npc_dialogue": "阿沈压低声音说：我只听见后院有人提到那只旧箱，旁的我不敢乱说。",
            "npc_action": "他把袖口往身后藏，避开门外的脚步声。",
            "emotion": "fearful",
            "released_clue_ids": [],
            "highlight_clues": [],
            "suggested_questions": ["你为何不敢说？", "那只旧箱在哪里？"],
            "state_update_suggestion": {
                "npc_trust_delta": 0,
                "truth_score_delta": 0,
                "order_score_delta": 0,
                "survival_score_delta": 0,
                "risk_level_delta": 0,
                "new_flags": [],
            },
        }
        return AIResponse(
            success=True,
            parsed_json=payload,
            raw_text=json.dumps(payload, ensure_ascii=False),
            latency_ms=5,
            fallback_used=False,
            error_message=None,
            model="fake-repair-model",
        )


def build_settings() -> Settings:
    return Settings(
        app_name="测试",
        version="0.5.0",
        use_mock_ai=False,
        ai_provider="deepseek",
        backend_port=8000,
        frontend_port=5173,
        deepseek_base_url="https://example.invalid",
        deepseek_model="fake-repair-model",
        ai_timeout_seconds=1,
        ai_max_retries=0,
        deepseek_api_key="测试密钥占位",
    )


def test_repair_agent_removes_modern_term_and_illegal_clue() -> None:
    fake_client = FakeRepairAIClient()
    agent = RepairAgent(ai_client=fake_client, runtime_settings=build_settings())

    response = agent.repair_dialogue_json(
        original_response={
            "npc_dialogue": "我用手机拍下了完整真相。",
            "npc_action": "阿沈交出官府密档。",
            "emotion": "fearful",
            "released_clue_ids": ["clue_jinyiwei_gag_order"],
        },
        supervisor_issues=[{"type": "modern_term", "detail": "出现手机"}],
        repair_instruction="移除现代词、剧透和非法线索。",
        context_summary={
            "npc_name": "阿沈",
            "current_stage": "investigation",
            "allowed_released_clue_ids": ["clue_worker_lie"],
        },
        schema_hint=NPC_DIALOGUE_SCHEMA_HINT,
    )

    assert response.success is True
    payload = response.parsed_json
    assert "手机" not in payload["npc_dialogue"]
    assert "完整真相" not in payload["npc_dialogue"]
    assert payload["released_clue_ids"] == []
    assert isinstance(payload, dict)
    assert all(key in payload for key in NPC_DIALOGUE_SCHEMA_HINT)
    assert "阿沈" in payload["npc_dialogue"]
    assert "clue_jinyiwei_gag_order" in fake_client.last_prompt
