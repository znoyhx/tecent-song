from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.routers import scripts as scripts_router
from app.models.script_models import ScriptGenerateRequest, ScriptPackage
from app.services.script_visual_contract import SCENE_STYLE_GUIDE_CONTRACT
from app.services.script_job_store import script_job_store, ScriptJobStore
from script_generation_fixtures import sample_script_payload, stage15_script_payload


client = TestClient(app)


def test_generate_api_rejects_ming() -> None:
    response = client.post("/api/scripts/generate", json={"dynasty_id": "ming", "keywords": ["书坊"]})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "AI_GENERATION_DISABLED_FOR_STABLE_DEMO"
    assert "固定 Demo" in response.json()["error"]["message"]


def test_generate_api_rejects_empty_keywords() -> None:
    response = client.post("/api/scripts/generate", json={"dynasty_id": "song", "keywords": []})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "KEYWORDS_REQUIRED"
    assert "关键词" in response.json()["error"]["message"]


def test_generate_api_rejects_encoding_damaged_keywords() -> None:
    for keywords in (["??", "????"], ["�"], ["！！！"], ["ÃÂåçé"]):
        response = client.post("/api/scripts/generate", json={"dynasty_id": "song", "keywords": keywords})

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "KEYWORDS_ENCODING_INVALID"
        assert "编码损坏" in response.json()["error"]["message"]


def test_generate_api_preserves_valid_chinese_keywords(monkeypatch) -> None:
    def fake_run_job(job_id: str) -> None:
        assert script_job_store.get_job(job_id) is not None

    monkeypatch.setattr(scripts_router.script_generation_service, "run_job", fake_run_job)

    keywords = ["驿站", "军报", "雨夜", "粮草"]
    response = client.post("/api/scripts/generate", json={"dynasty_id": "song", "keywords": keywords})

    assert response.status_code == 200
    job = script_job_store.get_job(response.json()["job_id"])
    assert job is not None
    assert job.keywords == keywords


def test_seed_prompt_requires_case_bound_deduction_blueprints() -> None:
    prompt = scripts_router.script_generation_service._seed_prompt(
        "song",
        ["粮仓"],
        {"pitch": "粮仓失火牵出官粮转运。"},
    )

    assert "deduction_blueprints" in prompt
    assert "结合本剧本真相链" in prompt
    assert "禁止使用“第几个疑点”" in prompt
    assert "correct_clue_titles 必须引用现有 clue_themes 标题" in prompt
    assert "clue_themes 视觉要求" in prompt
    assert "禁止把 title 写成“时间线”" in prompt


def test_generate_api_creates_failed_job_when_deepseek_unavailable(monkeypatch) -> None:
    def fake_run_job(job_id: str) -> None:
        job = script_job_store.get_job(job_id)
        assert job is not None
        script_job_store.set_running(job, "pitch_generation", "正在检查 DeepSeek 配置。")
        script_job_store.fail_job(job, "pitch_generation", "AI_UNAVAILABLE", "AI 服务不可用，生成已失败。")

    monkeypatch.setattr(scripts_router.script_generation_service, "run_job", fake_run_job)

    response = client.post("/api/scripts/generate", json={"dynasty_id": "song", "keywords": ["驿站"]})

    assert response.status_code == 200
    job_id = response.json()["job_id"]
    job_response = client.get(f"/api/scripts/jobs/{job_id}")

    assert job_response.status_code == 200
    job_payload = job_response.json()
    assert job_payload["status"] == "failed"
    assert job_payload["blocking_issues"][0]["code"] == "AI_UNAVAILABLE"


def test_generated_demo_library_lists_completed_playable_scripts(tmp_path, monkeypatch) -> None:
    store = ScriptJobStore(tmp_path)
    monkeypatch.setattr(scripts_router, "script_job_store", store)

    package = ScriptPackage.model_validate(stage15_script_payload("script_demo_library"))
    _write_approved_asset_files(package, tmp_path)
    store.save_script(package)
    job = store.create_job(ScriptGenerateRequest(dynasty_id="song", keywords=package.keywords))
    job.status = "completed"
    job.progress = 100
    job.current_step = "completed"
    job.ready_for_overview = True
    job.script_id = package.script_id
    store.save_job(job)

    response = client.get("/api/scripts/demos")

    assert response.status_code == 200
    demos = response.json()["demos"]
    assert len(demos) == 1
    assert demos[0]["script_id"] == package.script_id
    assert demos[0]["playable"] is True
    assert demos[0]["default_identity_id"] == "identity_inspector"
    assert demos[0]["thumbnail_url"] == "/api/scripts/script_demo_library/assets/asset_scene_0"


def test_generated_demo_library_keeps_saved_approved_scripts_after_prompt_contract_changes(tmp_path, monkeypatch) -> None:
    store = ScriptJobStore(tmp_path)
    monkeypatch.setattr(scripts_router, "script_job_store", store)

    package = ScriptPackage.model_validate(stage15_script_payload("script_demo_legacy_visual_contract"))
    for asset in package.visual_assets:
        if asset.asset_type == "scene":
            asset.prompt = asset.prompt.replace(SCENE_STYLE_GUIDE_CONTRACT, "")
    _write_approved_asset_files(package, tmp_path)
    store.save_script(package)
    job = store.create_job(ScriptGenerateRequest(dynasty_id="song", keywords=package.keywords))
    job.status = "completed"
    job.progress = 100
    job.current_step = "completed"
    job.ready_for_overview = True
    job.script_id = package.script_id
    store.save_job(job)

    response = client.get("/api/scripts/demos")

    assert response.status_code == 200
    demos = response.json()["demos"]
    assert [demo["script_id"] for demo in demos] == [package.script_id]
    assert demos[0]["gate_status"]["saved_visual_assets"] is True


def _write_approved_asset_files(package: ScriptPackage, root) -> None:
    for asset in package.visual_assets:
        if asset.asset_type not in {"scene", "npc", "clue"}:
            continue
        path = root / "assets" / "generated" / "visuals" / "generated" / package.script_id / f"{asset.asset_id}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 200)
        asset.generated_path = str(path)
        asset.url = f"/api/scripts/{package.script_id}/assets/{asset.asset_id}"
        asset.quality_gate.approved_path = str(path)
