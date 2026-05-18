from __future__ import annotations

import asyncio

import pytest

from app.core.config import load_settings
from app.services.ai_client import AIClient


SCHEMA_HINT = {
    "npc_dialogue": "中文字符串",
    "npc_action": "中文字符串",
    "emotion": "fearful|calm|angry|hesitant|defensive",
    "released_clue_ids": [],
    "highlight_clues": [],
    "suggested_questions": ["中文问题"],
    "state_update_suggestion": {},
}


def test_deepseek_connection_returns_parseable_json() -> None:
    runtime_settings = load_settings()
    if runtime_settings.use_mock_ai or runtime_settings.ai_provider != "deepseek":
        pytest.skip("真实 AI 模式未开启：请设置 USE_MOCK_AI=false 且 AI_PROVIDER=deepseek 后再运行。")
    if not runtime_settings.deepseek_api_key_available:
        pytest.skip("未检测到 DeepSeek Key：请在安全环境变量或本机后端配置中补齐后再运行。")

    prompt = """
只输出一个 JSON 对象，用中文回答。字段必须包含：npc_dialogue、npc_action、emotion、released_clue_ids、highlight_clues、suggested_questions、state_update_suggestion。
场景：明代书坊雨夜。NPC：阿沈。玩家问：你昨夜三更后到底听见了什么？
不要剧透幕后身份。
"""
    response = asyncio.run(
        AIClient(runtime_settings).generate_json(
            module="NPCDialogueAgent",
            prompt=prompt,
            schema_hint=SCHEMA_HINT,
        )
    )

    assert response.success is True, response.error_message
    assert response.fallback_used is False
    assert isinstance(response.parsed_json, dict)
    assert set(SCHEMA_HINT.keys()).issubset(response.parsed_json.keys())
    assert isinstance(response.parsed_json["npc_dialogue"], str)
    assert "幕后上级" not in response.parsed_json["npc_dialogue"]
