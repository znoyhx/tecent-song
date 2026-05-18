from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture(autouse=True)
def deterministic_api_dialogue_tests():
    from app.core.config import Settings
    from app.services.dialogue_orchestrator import DialogueOrchestrator
    from app.services.game_engine import engine

    engine.dialogue_orchestrator = DialogueOrchestrator(
        runtime_settings=Settings(
            app_name="测试",
            version="0.4.0",
            use_mock_ai=True,
            ai_provider="mock",
            backend_port=8000,
            frontend_port=5173,
            deepseek_base_url="https://example.invalid",
            deepseek_model="mock",
            ai_timeout_seconds=1,
            ai_max_retries=0,
            deepseek_api_key=None,
        )
    )
    yield
