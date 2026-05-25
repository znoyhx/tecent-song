from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.models.script_models import (
    ScriptGenerateRequest,
    ScriptJob,
    ScriptJobStep,
    ScriptPackage,
)
from app.services.image_quality_gate import image_quality_gate
from app.services.quote_pool import quote_pool
from app.services.script_supervisor import script_supervisor
from app.services.script_volume_gate import script_volume_gate


STEP_DEFINITIONS = [
    ("pitch_generation", "生成案件构想", "DeepSeek 根据朝代与关键词生成案件骨架。"),
    ("script_package_generation", "生成结构化剧本", "DeepSeek 输出完整 ScriptPackage JSON 初稿。"),
    ("script_doctor_review", "编剧审稿", "DeepSeek 审核人物动机、可玩性与信息边界。"),
    ("logic_qa_review", "逻辑 QA", "DeepSeek 检查线索链、阶段推进与结局可达。"),
    ("refinement_repair", "修复合并", "DeepSeek 按审稿意见修复并合并最终剧本。"),
    ("script_supervisor", "剧本监管", "后端校验 schema、朝代、线索链、剧透与可达性。"),
    ("volume_gate_review", "体量门禁", "后端校验场景、热点、线索、推理、章节、选择和结局数量。"),
    ("visual_generation", "生成视觉资产", "后端生成场景图、人物图和核心线索图。"),
    ("image_quality_gate", "图片质量门禁", "拒绝占位、空白、错风格、错朝代或缺核心物件的图片。"),
    ("hotspot_calibration", "热点坐标校准", "基于 approved 图片生成 0-1 归一化坐标。"),
    ("script_import", "导入游戏引擎", "把生成剧本导入现有调查、对话、线索和结局系统。"),
]


class ScriptJobStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        backend_root = Path(__file__).resolve().parents[2]
        self.base_dir = base_dir or backend_root / "data" / "generated_scripts"
        self.jobs_dir = self.base_dir / "jobs"
        self.scripts_dir = self.base_dir / "scripts"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.scripts_dir.mkdir(parents=True, exist_ok=True)

    def create_job(self, request: ScriptGenerateRequest) -> ScriptJob:
        job = ScriptJob(
            job_id=f"job_{uuid4().hex[:12]}",
            dynasty_id=request.dynasty_id,
            keywords=request.keywords,
            steps=[
                ScriptJobStep(step_id=step_id, title=title, description=description)
                for step_id, title, description in STEP_DEFINITIONS
            ],
            transitional_quote=quote_pool.next_quote(),
        )
        self.save_job(job)
        return job

    def get_job(self, job_id: str) -> ScriptJob | None:
        path = self._job_path(job_id)
        if not path.exists():
            return None
        return ScriptJob.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def save_job(self, job: ScriptJob) -> None:
        job.updated_at = self._now()
        path = self._job_path(job.job_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(job.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")

    def save_script(self, package: ScriptPackage) -> None:
        script_dir = self._script_dir(package.script_id)
        script_dir.mkdir(parents=True, exist_ok=True)
        (script_dir / "script_package.json").write_text(
            json.dumps(package.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_script(self, script_id: str) -> ScriptPackage | None:
        path = self._script_dir(script_id) / "script_package.json"
        if not path.exists():
            return None
        return ScriptPackage.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def find_job_by_script_id(self, script_id: str) -> ScriptJob | None:
        for path in self.jobs_dir.glob("*.json"):
            try:
                job = ScriptJob.model_validate(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, ValueError):
                continue
            if job.script_id == script_id:
                return job
        return None

    def list_demo_scripts(self, *, playable_only: bool = True) -> list[dict[str, Any]]:
        jobs_by_script_id = self._jobs_by_script_id()
        demos: list[dict[str, Any]] = []
        for script_path in self.scripts_dir.glob("*/script_package.json"):
            try:
                package = ScriptPackage.model_validate(json.loads(script_path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, ValueError):
                continue
            job = jobs_by_script_id.get(package.script_id)
            playability = self.script_playability(package, job=job)
            approved_counts = playability["visual_quality"]
            playable = bool(playability["playable"])
            if playable_only and not playable:
                continue
            demos.append(
                {
                    "script_id": package.script_id,
                    "job_id": job.job_id if job else package.job_id,
                    "dynasty_id": package.dynasty_id,
                    "title": package.script_overview.title,
                    "logline": package.script_overview.logline,
                    "case_summary": package.script_overview.case_summary,
                    "opening_location": package.script_overview.opening_location,
                    "keywords": package.keywords,
                    "generated_at": package.generated_at,
                    "updated_at": job.updated_at if job else package.generated_at,
                    "ready_for_overview": playability["completed"],
                    "playable": playable,
                    "default_identity_id": self._default_identity_id(package),
                    "thumbnail_url": self._thumbnail_url(package),
                    "counts": {
                        "locations": len(package.locations),
                        "hotspots": sum(len(location.hotspots) for location in package.locations),
                        "clues": len(package.clues),
                        "npcs": len(package.npcs),
                        "deductions": len(package.deductions),
                        "chapter_sections": len(package.chapter_sections),
                        "choices": len(package.choices),
                        "endings": len(package.endings),
                    },
                    "visual_quality": approved_counts,
                    "gate_status": playability["gate_status"],
                }
            )
        return sorted(demos, key=lambda item: str(item.get("updated_at") or item.get("generated_at") or ""), reverse=True)

    def script_playability(self, package: ScriptPackage, *, job: ScriptJob | None = None) -> dict[str, Any]:
        completed = job is not None and job.status == "completed" and job.ready_for_overview
        gate_status = self.script_package_gate_status(package)
        playable = completed and all(gate_status.values())
        return {
            "completed": completed,
            "playable": playable,
            "gate_status": gate_status,
            "visual_quality": self._approved_asset_counts(package),
        }

    def package_passes_demo_gates(self, package: ScriptPackage) -> bool:
        return all(self.script_package_gate_status(package).values())

    def script_package_gate_status(self, package: ScriptPackage) -> dict[str, bool]:
        approved_counts = self._approved_asset_counts(package)
        supervisor_ready = script_supervisor.review(package).passed
        volume_ready = script_volume_gate.review(package).passed
        required_images_ready = self._required_images_ready(package, approved_counts)
        visual_contract_ready = self._strict_visuals_ready(package)
        return {
            "script_supervisor": supervisor_ready,
            "script_volume_gate": volume_ready,
            "required_images": required_images_ready,
            "strict_visual_contract": visual_contract_ready,
        }

    def _jobs_by_script_id(self) -> dict[str, ScriptJob]:
        jobs: dict[str, ScriptJob] = {}
        for path in self.jobs_dir.glob("*.json"):
            try:
                job = ScriptJob.model_validate(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, ValueError):
                continue
            if job.script_id:
                jobs[job.script_id] = job
        return jobs

    def _approved_asset_counts(self, package: ScriptPackage) -> dict[str, int]:
        return {
            "scene": sum(1 for asset in package.visual_assets if asset.asset_type == "scene" and asset.quality_gate.status == "approved"),
            "npc": sum(1 for asset in package.visual_assets if asset.asset_type == "npc" and asset.quality_gate.status == "approved"),
            "clue": sum(1 for asset in package.visual_assets if asset.asset_type == "clue" and asset.quality_gate.status == "approved"),
        }

    def _required_images_ready(self, package: ScriptPackage, approved_counts: dict[str, int]) -> bool:
        required_assets = [asset for asset in package.visual_assets if asset.asset_type in {"scene", "npc", "clue"}]
        all_required_approved = all(asset.quality_gate.status == "approved" for asset in required_assets)
        required_scene_count = max(8, package.quality_gate.required_scene_count)
        required_npc_count = max(4, package.quality_gate.required_npc_count)
        required_clue_count = max(6, package.quality_gate.required_clue_count)
        return (
            approved_counts["scene"] >= required_scene_count
            and approved_counts["npc"] >= required_npc_count
            and approved_counts["clue"] >= required_clue_count
            and all_required_approved
        )

    def _package_ready_for_demo(self, package: ScriptPackage) -> bool:
        return script_supervisor.review(package).passed and script_volume_gate.review(package).passed

    def _strict_visuals_ready(self, package: ScriptPackage) -> bool:
        for asset in package.visual_assets:
            if asset.asset_type not in {"scene", "npc", "clue"}:
                continue
            if asset.quality_gate.status != "approved" or not asset.url:
                return False
            result = image_quality_gate.review_asset(
                asset=asset,
                file_path=self._visual_file_path(asset.generated_path),
                script_id=package.script_id,
            )
            if result.status != "approved":
                return False
        return True

    def _visual_file_path(self, generated_path: str | None) -> Path | None:
        if not generated_path:
            return None
        path = Path(generated_path)
        if path.is_absolute():
            return path
        workspace_root = Path(__file__).resolve().parents[3]
        return workspace_root / path

    def _default_identity_id(self, package: ScriptPackage) -> str | None:
        default_identity = next((identity for identity in package.playable_identities if identity.is_default), None)
        return (default_identity or package.playable_identities[0]).identity_id if package.playable_identities else None

    def _thumbnail_url(self, package: ScriptPackage) -> str | None:
        asset = next(
            (
                item
                for item in package.visual_assets
                if item.asset_type == "scene" and item.quality_gate.status == "approved"
            ),
            None,
        )
        if asset is None:
            return None
        return f"/api/scripts/{package.script_id}/assets/{asset.asset_id}"

    def set_running(self, job: ScriptJob, step_id: str, message: str = "") -> ScriptJob:
        job.status = "running"
        job.current_step = step_id
        for index, step in enumerate(job.steps):
            if step.step_id == step_id:
                step.status = "running"
                step.attempts += 1
                step.started_at = step.started_at or self._now()
                step.message = message
                job.progress = max(job.progress, int(index / max(len(job.steps), 1) * 100))
                break
        self.save_job(job)
        return job

    def pass_step(self, job: ScriptJob, step_id: str, message: str = "", metadata: dict[str, Any] | None = None) -> ScriptJob:
        for index, step in enumerate(job.steps):
            if step.step_id == step_id:
                step.status = "passed"
                step.completed_at = self._now()
                step.message = message
                if metadata:
                    step.metadata.update(metadata)
                job.progress = max(job.progress, int(((index + 1) / max(len(job.steps), 1)) * 100))
                break
        self.save_job(job)
        return job

    def retry_step(self, job: ScriptJob, step_id: str, message: str = "") -> ScriptJob:
        for step in job.steps:
            if step.step_id == step_id:
                step.status = "retrying"
                step.message = message
                step.attempts += 1
                break
        job.current_step = step_id
        self.save_job(job)
        return job

    def fail_job(self, job: ScriptJob, step_id: str, code: str, message: str, *, visual_blocked: bool = False) -> ScriptJob:
        job.status = "visual_blocked" if visual_blocked else "failed"
        job.current_step = step_id
        job.ready_for_overview = False
        job.blocking_issues.append({"code": code, "message": message})
        for step in job.steps:
            if step.step_id == step_id:
                step.status = "blocked" if visual_blocked else "failed"
                step.message = message
                step.completed_at = self._now()
                break
        self.save_job(job)
        return job

    def complete_job(self, job: ScriptJob, script_id: str) -> ScriptJob:
        job.status = "completed"
        job.progress = 100
        job.current_step = "completed"
        job.script_id = script_id
        job.ready_for_overview = True
        job.blocking_issues = []
        self.save_job(job)
        return job

    def _job_path(self, job_id: str) -> Path:
        return self.jobs_dir / f"{job_id}.json"

    def _script_dir(self, script_id: str) -> Path:
        return self.scripts_dir / script_id

    def script_dir(self, script_id: str) -> Path:
        return self._script_dir(script_id)

    def _now(self) -> str:
        from datetime import datetime

        return datetime.now().isoformat(timespec="seconds")


script_job_store = ScriptJobStore()
