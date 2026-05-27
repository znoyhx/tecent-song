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


def test_compact_seed_builder_uses_ai_deduction_blueprints() -> None:
    payload = compact_script_seed_builder.build(
        {
            "title": "粮仓夜痕",
            "surface_event": "粮仓夜半失火，守仓人失踪。",
            "hidden_truth": "有人借火势调走官粮，又用旧账掩盖车队去向。",
            "locations": [
                {"name": "仓门", "description": "雪泥里留着深车辙。"},
                {"name": "账房", "description": "账册被新墨涂过。"},
                {"name": "后巷", "description": "夜车曾在此停靠。"},
            ],
            "npcs": [
                {"name": "周仓吏", "public_identity": "守仓官吏"},
                {"name": "何车头", "public_identity": "脚车头目"},
                {"name": "卢掌柜", "public_identity": "粮行掌柜"},
                {"name": "阿季", "public_identity": "更夫"},
            ],
            "clue_themes": [
                {"title": "半截封绳", "description": "封绳切口新鲜。"},
                {"title": "新墨账页", "description": "亏空数字被改过。"},
                {"title": "深车辙", "description": "车辙通向后巷。"},
            ],
            "deduction_blueprints": [
                {
                    "question": "「半截封绳」「新墨账页」「深车辙」能证明粮车在失火前走过哪条转运路线？",
                    "correct_clue_titles": ["半截封绳", "新墨账页", "深车辙"],
                    "answer_summary": "封绳、账页和车辙互相印证，粮车在火起前已从后巷转出。",
                    "wrong_feedback": "还没把封绳、账页和车辙串成同一条路线。",
                }
            ],
        },
        dynasty_id="song",
        keywords=["粮仓", "夜火", "转运"],
        job_id="job_deduction_blueprint",
    )

    package = ScriptPackage.model_validate(payload)
    first = package.deductions[0]

    assert first.question == "「半截封绳」「新墨账页」「深车辙」能证明粮车在失火前走过哪条转运路线？"
    assert first.correct_clue_ids == ["clue_00", "clue_01", "clue_02"]
    assert first.required_clue_ids == ["clue_00"]
    assert "粮车在火起前已从后巷转出" in first.success_text


def test_compact_seed_builder_rewrites_abstract_clues_for_visuals() -> None:
    payload = compact_script_seed_builder.build(
        {
            "title": "粮仓暗账",
            "surface_event": "粮仓盘点时发现封仓文书与实粮不合。",
            "hidden_truth": "有人提前调走官粮，再用假盘点遮掩。",
            "locations": [
                {"name": "仓门", "description": "封锁的仓门边有新泥。"},
                {"name": "账房", "description": "账册被压在灯下。"},
            ],
            "npcs": [
                {"name": "孙掌柜", "public_identity": "粮行掌柜"},
                {"name": "周仓吏", "public_identity": "仓吏"},
                {"name": "何车头", "public_identity": "脚车头目"},
                {"name": "阿季", "public_identity": "更夫"},
            ],
            "clue_themes": [
                {"title": "时间线", "description": "更点与车声对不上。"},
                {"title": "证言-孙掌柜", "description": "孙掌柜对夜间开门说法含糊。"},
            ],
        },
        dynasty_id="song",
        keywords=["粮仓", "官粮"],
        job_id="job_visual_clues",
    )

    package = ScriptPackage.model_validate(payload)

    assert package.clues[0].title == "粮仓更筹铜签"
    assert package.clues[1].title == "孙掌柜口供记录"
    clue_prompt = next(asset.prompt for asset in package.visual_assets if asset.asset_id == "asset_clue_00")
    scene_prompt = next(asset.prompt for asset in package.visual_assets if asset.asset_id == "asset_scene_00")
    assert "一个具体可见物证" in clue_prompt
    assert "禁止把抽象线索画成时间线" in clue_prompt
    assert "完整露出整脸和上半身" in scene_prompt
    assert "线索物件必须真实出现在场景里并靠近画面中部" in scene_prompt
    assert "明代 Demo" not in scene_prompt
    assert "明代Demo" not in scene_prompt
    assert "明代固定 Demo" not in scene_prompt
    assert "visual_style_guide" in scene_prompt
