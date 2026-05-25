from __future__ import annotations

from app.models.script_models import ScriptPackage
from app.services.script_seed_builder import compact_script_seed_builder
from app.services.script_supervisor import script_supervisor
from app.services.script_volume_gate import script_volume_gate


def test_compact_seed_builder_produces_stage15_complete_package() -> None:
    payload = compact_script_seed_builder.build(
        {
            "title": "雨夜驿铃",
            "logline": "雨夜驿站里，军报、粮草与一封密信互相牵连。",
            "surface_event": "驿卒遇害，军报失踪。",
            "hidden_truth": "有人借粮草调运遮掩军报调包，灭口只是第二层掩护。",
            "location_region": "陕西路驿道",
            "locations": [
                {"name": "甘泉驿前厅", "description": "灯火昏暗，投宿簿摊在柜上。"},
                {"name": "驿卒宿舍", "description": "湿衣和脚印留在门边。"},
                {"name": "马厩", "description": "马具被匆忙换过。"},
                {"name": "粮仓", "description": "粮袋封绳有新割痕。"},
            ],
            "npcs": [
                {"name": "赵驿丞", "public_identity": "驿站主事", "hidden_motive": "怕交接失误牵连自己。"},
                {"name": "林押粮", "public_identity": "押粮小吏", "hidden_motive": "隐瞒夜间调车。"},
                {"name": "韩旅人", "public_identity": "投宿商旅", "hidden_motive": "替人传过一封密信。"},
                {"name": "阿谨", "public_identity": "驿站杂役", "hidden_motive": "看见凶手却不敢说。"},
            ],
            "clue_themes": [
                {"title": "湿封军报", "description": "封泥受潮却仍有新压痕。"},
                {"title": "粮袋割痕", "description": "割痕方向与仓中刀具不合。"},
            ],
        },
        dynasty_id="song",
        keywords=["驿站", "军报", "雨夜", "粮草"],
        job_id="job_builder_test",
    )

    package = ScriptPackage.model_validate(payload)
    supervisor_result = script_supervisor.review(package)
    volume_result = script_volume_gate.review(package)

    assert len(package.locations) == 8
    assert sum(len(location.hotspots) for location in package.locations) == 30
    assert len(package.clues) == 30
    assert len(package.deductions) == 8
    assert len(package.chapter_sections) == 12
    assert len(package.choices) == 5
    assert len(package.endings) == 5
    assert supervisor_result.passed
    assert volume_result.passed
