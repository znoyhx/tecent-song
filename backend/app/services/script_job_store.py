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
from app.services.quote_pool import quote_pool


STEP_DEFINITIONS = [
    ("pitch_generation", "生成案件构想", "DeepSeek 根据朝代与关键词生成案件骨架。"),
    ("script_package_generation", "生成结构化剧本", "DeepSeek 输出完整 ScriptPackage JSON 初稿。"),
    ("script_doctor_review", "编剧审稿", "DeepSeek 审核人物动机、可玩性与信息边界。"),
    ("logic_qa_review", "逻辑 QA", "DeepSeek 检查线索链、阶段推进与结局可达。"),
    ("refinement_repair", "修复合并", "DeepSeek 按审稿意见修复并合并最终剧本。"),
    ("script_supervisor", "剧本监管", "后端校验 schema、朝代、线索链、剧透与可达性。"),
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
