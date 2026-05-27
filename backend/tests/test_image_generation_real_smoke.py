from __future__ import annotations

from pathlib import Path

import pytest

from app.services.image_generation_service import image_generation_service



def test_real_gpt_image_generation_or_explicit_blocked() -> None:

    if not image_generation_service._has_api_key():
        pytest.skip("未检测到图片生成 Key")

    result = image_generation_service.generate_asset("clue_burned_page", force=True)

    assert result["status"] in {"generated", "fallback"}
    if result["status"] == "generated":
        assert result["blocked"] is False
        assert result["generated_path"]
        assert Path(image_generation_service.workspace_dir / result["generated_path"]).exists()
        return

    assert result["blocked"] is True
    assert result["generation_status"] == "blocked"
    assert "已使用本地视觉占位" in result["message"]
