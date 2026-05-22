from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
import time
from typing import Any

from pydantic import ValidationError

from app.core.config import settings
from app.models.script_models import ScriptPackage, VisualAsset
from app.services.ai_client import AIClient
from app.services.hotspot_calibration_service import hotspot_calibration_service
from app.services.image_generation_service import image_generation_service
from app.services.image_quality_gate import image_quality_gate
from app.services.log_service import log_service
from app.services.script_import_service import script_import_service
from app.services.script_job_store import script_job_store
from app.services.script_normalizer import script_package_normalizer
from app.services.script_supervisor import script_supervisor


TERMINAL_JOB_STATUSES = {"completed", "failed", "visual_blocked"}


class ScriptGenerationService:
    def __init__(self) -> None:
        self.ai_client = AIClient(settings)

    def run_job(self, job_id: str) -> None:
        job = script_job_store.get_job(job_id)
        if job is None:
            return
        if settings.use_mock_ai or settings.ai_provider != "deepseek" or not settings.deepseek_api_key_available:
            script_job_store.set_running(job, "pitch_generation", "正在检查 DeepSeek 配置。")
            script_job_store.fail_job(
                job,
                "pitch_generation",
                "AI_UNAVAILABLE",
                "后端未启用真实 DeepSeek，生成 job 已失败，未使用 Mock 冒充完成。",
            )
            return

        try:
            pitch = self._run_ai_round(
                job,
                step_id="pitch_generation",
                module="DeepSeekScriptPitch",
                prompt=self._pitch_prompt(job.dynasty_id, job.keywords),
                schema_hint={"pitch": "中文案件构想", "constraints": []},
                max_tokens=1600,
            )
            raw_package_payload = self._run_ai_round(
                job,
                step_id="script_package_generation",
                module="DeepSeekScriptPackage",
                prompt=self._package_prompt(job.dynasty_id, job.keywords, pitch),
                schema_hint={"script_package": {}},
                max_tokens=12000,
                temperature=0.35,
            ).get("script_package", {})
            package_payload = script_package_normalizer.normalize(
                raw_package_payload,
                dynasty_id=job.dynasty_id,
                keywords=job.keywords,
                job_id=job.job_id,
            )
            review = self._run_ai_round(
                job,
                step_id="script_doctor_review",
                module="DeepSeekScriptDoctor",
                prompt=self._review_prompt(package_payload),
                schema_hint={"review_notes": [], "blocking_issues": [], "repair_instructions": []},
                max_tokens=3000,
                temperature=0.2,
            )
            qa = self._run_ai_round(
                job,
                step_id="logic_qa_review",
                module="DeepSeekLogicQA",
                prompt=self._qa_prompt(package_payload),
                schema_hint={"qa_notes": [], "blocking_issues": [], "repair_instructions": []},
                max_tokens=3000,
                temperature=0.2,
            )
            raw_repaired_payload = self._run_ai_round(
                job,
                step_id="refinement_repair",
                module="DeepSeekScriptRepair",
                prompt=self._repair_prompt(package_payload, review, qa),
                schema_hint={"script_package": {}},
                max_tokens=12000,
                temperature=0.25,
            ).get("script_package", {})
            repaired_payload = script_package_normalizer.normalize(
                raw_repaired_payload,
                dynasty_id=job.dynasty_id,
                keywords=job.keywords,
                job_id=job.job_id,
                base_payload=package_payload,
            )
            package = ScriptPackage.model_validate(repaired_payload)
        except ValidationError as exc:
            current_job = script_job_store.get_job(job_id) or job
            script_job_store.fail_job(
                current_job,
                current_job.current_step if current_job.current_step != "queued" else "refinement_repair",
                "SCRIPT_SCHEMA_INVALID",
                f"DeepSeek 返回的剧本结构无法通过校验：{str(exc)[:240]}",
            )
            return
        except RuntimeError as exc:
            current_job = script_job_store.get_job(job_id) or job
            if current_job.status not in TERMINAL_JOB_STATUSES:
                script_job_store.fail_job(current_job, current_job.current_step, "AI_UNAVAILABLE", str(exc))
            return

        job = script_job_store.get_job(job_id) or job
        script_job_store.set_running(job, "script_supervisor", "正在进行后端剧本监管。")
        supervisor_result = script_supervisor.review(package)
        if not supervisor_result.passed:
            job.blocking_issues.extend([issue.model_dump() for issue in supervisor_result.blocking_issues])
            script_job_store.fail_job(job, "script_supervisor", "SCRIPT_SUPERVISOR_BLOCKED", "剧本监管发现阻塞问题，未导入游戏。")
            return
        script_job_store.pass_step(job, "script_supervisor", "剧本监管通过。", supervisor_result.model_dump())

        package = self._generate_visuals(job_id, package)
        job = script_job_store.get_job(job_id) or job
        if any(asset.quality_gate.status != "approved" for asset in package.visual_assets if asset.asset_type in {"scene", "npc", "clue"}):
            script_job_store.save_script(package)
            job.script_id = package.script_id
            script_job_store.fail_job(job, "image_quality_gate", "VISUAL_BLOCKED", "必需图片未全部通过质量门禁。", visual_blocked=True)
            return

        script_job_store.set_running(job, "hotspot_calibration", "正在校准生成图片上的热点坐标。")
        package = hotspot_calibration_service.calibrate(package)
        if len([item for item in package.hotspot_positioning if item.calibration_status == "approved"]) < 6:
            script_job_store.save_script(package)
            script_job_store.fail_job(job, "hotspot_calibration", "HOTSPOT_CALIBRATION_BLOCKED", "approved 热点坐标不足 6 个。", visual_blocked=True)
            return
        script_job_store.pass_step(job, "hotspot_calibration", "热点坐标已校准。")

        script_job_store.set_running(job, "script_import", "正在验证生成剧本可导入现有游戏引擎。")
        if not script_import_service.required_images_approved(package):
            script_job_store.save_script(package)
            script_job_store.fail_job(job, "script_import", "VISUALS_NOT_APPROVED", "图片未全部 approved，拒绝导入。", visual_blocked=True)
            return
        script_job_store.save_script(package)
        script_job_store.pass_step(job, "script_import", "生成剧本已准备进入现有游戏引擎。")
        script_job_store.complete_job(job, package.script_id)

    def continue_visuals_for_script(self, script_id: str) -> None:
        package = script_job_store.get_script(script_id)
        job = script_job_store.find_job_by_script_id(script_id)
        if package is None or job is None:
            return
        job.blocking_issues = [issue for issue in job.blocking_issues if issue.get("code") != "VISUAL_BLOCKED"]
        package = self._generate_visuals(job.job_id, package, only_unapproved=True)
        job = script_job_store.get_job(job.job_id) or job
        if any(asset.quality_gate.status != "approved" for asset in package.visual_assets if asset.asset_type in {"scene", "npc", "clue"}):
            script_job_store.save_script(package)
            job.script_id = package.script_id
            script_job_store.fail_job(job, "image_quality_gate", "VISUAL_BLOCKED", "必需图片未全部通过质量门禁。", visual_blocked=True)
            return

        script_job_store.set_running(job, "hotspot_calibration", "正在校准生成图片上的热点坐标。")
        package = hotspot_calibration_service.calibrate(package)
        if len([item for item in package.hotspot_positioning if item.calibration_status == "approved"]) < 6:
            script_job_store.save_script(package)
            script_job_store.fail_job(job, "hotspot_calibration", "HOTSPOT_CALIBRATION_BLOCKED", "approved 热点坐标不足 6 个。", visual_blocked=True)
            return
        script_job_store.pass_step(job, "hotspot_calibration", "热点坐标已校准。")

        script_job_store.set_running(job, "script_import", "正在验证生成剧本可导入现有游戏引擎。")
        if not script_import_service.required_images_approved(package):
            script_job_store.save_script(package)
            script_job_store.fail_job(job, "script_import", "VISUALS_NOT_APPROVED", "图片未全部 approved，拒绝导入。", visual_blocked=True)
            return
        script_job_store.save_script(package)
        script_job_store.pass_step(job, "script_import", "生成剧本已准备进入现有游戏引擎。")
        script_job_store.complete_job(job, package.script_id)

    def _run_ai_round(
        self,
        job,
        *,
        step_id: str,
        module: str,
        prompt: str,
        schema_hint: dict[str, Any],
        max_tokens: int,
        temperature: float = 0.4,
    ) -> dict[str, Any]:
        job = script_job_store.get_job(job.job_id) or job
        script_job_store.set_running(job, step_id, "正在真实调用 DeepSeek。")
        response = self.ai_client.generate_json_sync(
            module=module,
            prompt=prompt,
            schema_hint=schema_hint,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        log_entry = log_service.record_ai_call(
            module=module,
            model=response.model,
            input_summary=f"{module} / {job.dynasty_id} / {','.join(job.keywords)}",
            latency_ms=response.latency_ms,
            success=response.success,
            fallback_used=response.fallback_used,
            supervisor_pass=response.success,
            issues=[] if response.success else [{"type": "AI_UNAVAILABLE", "detail": response.error_message}],
            prompt=prompt,
            raw_response=response.raw_text,
            extra_fields={"job_id": job.job_id, "provider": "deepseek", "fallback_used": response.fallback_used},
        )
        job.ai_calls.append(
            {
                "module": module,
                "provider": "deepseek",
                "model": response.model,
                "input_summary": f"{job.dynasty_id}/{','.join(job.keywords)}",
                "latency": response.latency_ms,
                "success": response.success,
                "supervisor_pass": response.success,
                "fallback_used": response.fallback_used,
                "prompt_path": log_entry.get("prompt_path"),
                "response_path": log_entry.get("response_path"),
            }
        )
        if not response.success:
            script_job_store.fail_job(job, step_id, "AI_UNAVAILABLE", response.error_message or "DeepSeek 调用失败。")
            raise RuntimeError(response.error_message or "DeepSeek 调用失败。")
        script_job_store.pass_step(job, step_id, "DeepSeek 本轮输出已解析为 JSON。", {"call_id": log_entry.get("call_id")})
        return response.parsed_json

    def _generate_visuals(self, job_id: str, package: ScriptPackage, *, only_unapproved: bool = False) -> ScriptPackage:
        updated = deepcopy(package)
        job = script_job_store.get_job(job_id)
        if job is None:
            return updated
        script_job_store.set_running(job, "visual_generation", "正在为生成剧本请求图片。")

        regenerated = 0
        rejected = 0
        blocked = 0
        approved = {"scene": 0, "npc": 0, "clue": 0}
        quality_by_type = {
            "scene": {"rejected": 0, "regenerated": 0, "blocked": 0},
            "npc": {"rejected": 0, "regenerated": 0, "blocked": 0},
            "clue": {"rejected": 0, "regenerated": 0, "blocked": 0},
        }
        next_assets: list[VisualAsset] = []
        for asset in updated.visual_assets:
            if asset.asset_type not in {"scene", "npc", "clue"}:
                next_assets.append(asset)
                continue
            if only_unapproved and asset.quality_gate.status == "approved":
                approved[asset.asset_type] += 1
                next_assets.append(asset)
                continue
            current = asset
            existing_file = image_generation_service.generated_script_asset_path(script_id=updated.script_id, asset_id=current.asset_id)
            if existing_file.exists():
                current.prompt_hash = current.prompt_hash or hashlib.sha256(current.prompt.encode("utf-8")).hexdigest()[:16]
                current.generation_status = "generated"
                current.quality_gate.issues = []
                current.quality_gate.rejected_paths = []
                current.quality_gate = image_quality_gate.review_asset(asset=current, file_path=existing_file, script_id=updated.script_id)
                current.generation_status = current.quality_gate.status
                if current.quality_gate.status == "approved":
                    current.generated_path = current.quality_gate.approved_path
                    current.url = f"/api/scripts/{updated.script_id}/assets/{current.asset_id}"
                    approved[current.asset_type] += 1
                    next_assets.append(current)
                    continue
            for attempt in range(1, 4):
                if attempt > 1:
                    regenerated += 1
                    quality_by_type[current.asset_type]["regenerated"] += 1
                    current.prompt = self._rewrite_visual_prompt(current.prompt, attempt)
                    job = script_job_store.get_job(job_id) or job
                    script_job_store.retry_step(job, "visual_generation", f"{current.title} 未通过，正在第 {attempt} 次重试。")
                    self._wait_before_image_retry(current)
                current = image_generation_service.generate_script_asset(script_id=updated.script_id, asset=current, attempt=attempt)
                file_path = image_generation_service.generated_script_asset_path(script_id=updated.script_id, asset_id=current.asset_id)
                current.quality_gate = image_quality_gate.review_asset(asset=current, file_path=file_path, script_id=updated.script_id)
                current.generation_status = current.quality_gate.status
                if current.quality_gate.status == "approved":
                    current.generated_path = current.quality_gate.approved_path
                    current.url = f"/api/scripts/{updated.script_id}/assets/{current.asset_id}"
                    approved[current.asset_type] += 1
                    break
                rejected += 1
                quality_by_type[current.asset_type]["rejected"] += 1
                if attempt < 3:
                    self._wait_after_image_failure(current)
            if current.quality_gate.status != "approved":
                blocked += 1
                quality_by_type[current.asset_type]["blocked"] += 1
            next_assets.append(current)
            self._wait_between_image_assets()

        updated.visual_assets = next_assets
        updated.quality_gate.scene_approved = approved["scene"]
        updated.quality_gate.npc_approved = approved["npc"]
        updated.quality_gate.clue_approved = approved["clue"]
        updated.quality_gate.rejected = rejected
        updated.quality_gate.regenerated = regenerated
        updated.quality_gate.blocked = blocked

        job = script_job_store.get_job(job_id) or job
        for asset_type in ("scene", "npc", "clue"):
            getattr(job.visual_quality, asset_type).update(
                {
                    "approved": approved[asset_type],
                    "rejected": quality_by_type[asset_type]["rejected"],
                    "regenerated": quality_by_type[asset_type]["regenerated"],
                    "blocked": quality_by_type[asset_type]["blocked"],
                }
            )
        script_job_store.pass_step(job, "visual_generation", "图片请求已完成，进入质量门禁。")
        script_job_store.set_running(job, "image_quality_gate", "正在汇总图片质量门禁结果。")
        if blocked > 0:
            script_job_store.save_job(job)
        else:
            script_job_store.pass_step(job, "image_quality_gate", "必需图片已全部 approved。")
        return updated

    def _rewrite_visual_prompt(self, prompt: str, attempt: int) -> str:
        return (
            f"{prompt}\n"
            f"重试要求 {attempt}: 明确呈现核心物件，避免空白、占位、现代物件、错朝代服饰和文字水印。"
        )

    def _wait_between_image_assets(self) -> None:
        delay = self._image_delay("SCRIPT_IMAGE_THROTTLE_SECONDS", 3.0)
        if delay > 0:
            time.sleep(delay)

    def _wait_after_image_failure(self, asset: VisualAsset) -> None:
        issues = " ".join(asset.quality_gate.issues)
        default_delay = 12.0 if any(code in issues for code in ("429", "503", "timeout", "Timeout")) else 4.0
        delay = self._image_delay("SCRIPT_IMAGE_RETRY_DELAY_SECONDS", default_delay)
        if delay > 0:
            time.sleep(delay)

    def _wait_before_image_retry(self, asset: VisualAsset) -> None:
        issues = " ".join(asset.quality_gate.issues)
        if any(code in issues for code in ("429", "503")):
            time.sleep(self._image_delay("SCRIPT_IMAGE_RATE_LIMIT_DELAY_SECONDS", 20.0))

    def _image_delay(self, env_name: str, default: float) -> float:
        raw = os.getenv(env_name)
        try:
            return max(0.0, float(raw)) if raw not in (None, "") else default
        except ValueError:
            return default

    def _pitch_prompt(self, dynasty_id: str, keywords: list[str]) -> str:
        dynasty_name = "北宋" if dynasty_id == "song" else "晚唐"
        return f"""
只输出 JSON。请为《史隙》生成一个 {dynasty_name} 历史悬疑案件 pitch。
关键词：{", ".join(keywords)}
字段必须为：
{{
  "pitch": "中文案件构想，包含案发地点、表面事件、调查目标",
  "constraints": ["必须符合{dynasty_name}时代", "不能出现明代书坊案", "不能提前泄露最终真相"]
}}
不要输出 Markdown，不要输出英文用户可见文案，不要泄露系统或 API 信息。
"""

    def _package_prompt(self, dynasty_id: str, keywords: list[str], pitch: dict[str, Any]) -> str:
        dynasty_name = "北宋" if dynasty_id == "song" else "晚唐"
        return f"""
只输出 JSON，顶层字段必须是 script_package。
请生成 P0 ScriptPackage，朝代只能是 {dynasty_id}（{dynasty_name}），关键词为：{", ".join(keywords)}。

字段名必须严格使用下面这些英文 key，不要改成 id/name/description 的简写：
{self._schema_contract()}

硬性要求：
1. 至少 5 个 locations，每个 location 必须有 visual_asset_id 和可调查 hotspots。
2. 至少 4 个 npcs，每个 NPC 必须有 visual_asset_id、known_info、unknown_info、forbidden_disclosure。
3. 至少 6 个核心 clues，每个 clue 必须有 source_location_id、stage_available、visual_asset_id。
4. visual_assets 必须是数组，不要分组成 scenes/npcs/clues；至少包含 5 个 scene、4 个 npc、6 个 clue。
5. hotspot_positioning 至少 6 个，anchor_point 和 bbox 使用对象格式：{{"x":0.5,"y":0.5}}、{{"x":0.4,"y":0.4,"width":0.2,"height":0.2}}。
6. stages 的 stage_id 只能是 intro、investigation、reversal、choice、ending。
7. 不得使用明代书坊案内容，不得出现现代词，不得让 NPC 早期泄露 hidden_truth。

pitch:
{json.dumps(pitch, ensure_ascii=False)}
"""

    def _review_prompt(self, package_payload: dict[str, Any]) -> str:
        return f"""
只输出 JSON。你是编剧审稿人，检查此 ScriptPackage 的人物动机、可玩性、信息边界和概览是否会剧透。
输出字段必须为：
{{"review_notes": [], "blocking_issues": [], "repair_instructions": []}}
请只写中文内容。
ScriptPackage:
{json.dumps(package_payload, ensure_ascii=False)}
"""

    def _qa_prompt(self, package_payload: dict[str, Any]) -> str:
        return f"""
只输出 JSON。你是逻辑 QA，检查线索链、阶段可达、结局可达、玩家身份权限、视觉字段和热点坐标。
输出字段必须为：
{{"qa_notes": [], "blocking_issues": [], "repair_instructions": []}}
请只写中文内容。
ScriptPackage:
{json.dumps(package_payload, ensure_ascii=False)}
"""

    def _repair_prompt(self, package_payload: dict[str, Any], review: dict[str, Any], qa: dict[str, Any]) -> str:
        return f"""
只输出 JSON，顶层字段必须是 script_package。
请根据审稿和 QA 意见修复 ScriptPackage，并保持完整结构。不要只输出摘要或差异补丁。
字段名必须继续严格使用：
{self._schema_contract()}

特别注意：
1. 必须保留 dynasty_id、keywords、script_overview、playable_identities、world、story、stages、locations、npcs、clues、visual_assets、visual_style_guide、hotspot_positioning、quality_gate。
2. visual_assets 必须是数组，不要改成 scenes/npcs/clues 分组对象。
3. hotspots、hotspot_positioning 和 clues 的 id 必须互相对应。
4. 不得输出 Markdown，不得加入英文用户可见文案。

初稿：
{json.dumps(package_payload, ensure_ascii=False)}
审稿：
{json.dumps(review, ensure_ascii=False)}
QA：
{json.dumps(qa, ensure_ascii=False)}
"""

    def _schema_contract(self) -> str:
        return """
script_package = {
  "script_id": "string",
  "dynasty_id": "song | late_tang",
  "keywords": ["1-8 个中文关键词"],
  "script_overview": {"title": "", "logline": "", "case_summary": "", "opening_location": "", "public_objective": "", "major_locations": [], "major_npcs": [], "player_briefing": ""},
  "playable_identities": [{"identity_id": "", "display_name": "", "description": "", "social_rank": "low|middle|high", "relation_to_case": "", "motive": "", "permissions": [], "limitations": [], "background": "", "tags": [], "is_default": true}],
  "world": {"dynasty_id": "song|late_tang", "dynasty_name": "", "era_name": "", "year_hint": "", "location_region": "", "rules": [], "forbidden_terms": []},
  "story": {"surface_event": "", "hidden_truth": "", "themes": [], "culprit_boundary": "", "truth_chain_clue_ids": []},
  "stages": [{"stage_id": "intro|investigation|reversal|choice|ending", "name": "", "order": 0, "goal": "", "entry_location_id": "", "unlock_conditions": [], "available_location_ids": [], "key_clue_ids": []}],
  "locations": [{"location_id": "", "name": "", "description": "", "scene_text": "", "stage_ids": [], "npc_ids": [], "hotspots": [{"hotspot_id": "", "label": "", "description": "", "clue_ids": [], "required_stage": "intro", "required_clue_ids": [], "investigation_text": "", "repeat_text": ""}], "visual_asset_id": ""}],
  "npcs": [{"npc_id": "", "name": "", "public_identity": "", "appearance": "", "personality": "", "background_suspicion": "", "case_connection": "", "event_behavior": "", "public_goal": "", "hidden_motive": "", "known_info": [], "unknown_info": [], "forbidden_disclosure": [], "speaking_style": "", "initial_trust": 0, "emotion_state": "guarded", "releasable_clue_ids": [], "stage_limits": {}, "visual_asset_id": ""}],
  "relationships": [{"source_id": "", "target_id": "", "relation": "", "public_state": "", "hidden_state": ""}],
  "clues": [{"clue_id": "", "title": "", "type": "物证", "is_key": true, "source_location_id": "", "source_npc_id": null, "highlight_text": "", "display_text": "", "detail": "", "stage_available": [], "unlock_conditions": {}, "effects": {}, "related_clue_ids": [], "ending_tags": [], "forbidden_before_stage": null, "visual_asset_id": ""}],
  "clue_graph": [{"rule_id": "", "required_clue_ids": [], "result_title": "", "result_text": "", "effects": {}}],
  "dialogue_rules": [{"dialogue_id": "", "npc_id": "", "stage": "intro", "priority": 0, "trigger_keywords": [], "presented_clue_ids": [], "response": "", "released_clue_ids": [], "suggested_questions": []}],
  "choices": [{"choice_id": "", "title": "", "description": "", "effects": {}}],
  "endings": [{"ending_id": "", "title": "", "priority": 0, "conditions": {}, "required_flags": [], "blocked_flags": [], "result_summary": "", "ending_text": "", "history_echo": "", "related_clue_ids": [], "related_choice_ids": [], "npc_fates": {}, "visual_asset_id": null}],
  "visual_assets": [{"asset_id": "", "asset_type": "scene|npc|clue|ending", "owner_id": "", "title": "", "prompt": "", "negative_prompt": "", "required_subjects": [], "era_feature_checklist": []}],
  "visual_style_guide": {"style_keywords": [], "forbidden_visuals": [], "color_script": "", "camera": "", "era_feature_checklist": [], "appearance_lock": {}},
  "hotspot_positioning": [{"location_id": "", "hotspot_id": "", "visual_asset_id": "", "clue_id": "", "anchor_point": {"x": 0.5, "y": 0.5}, "bbox": {"x": 0.4, "y": 0.4, "width": 0.2, "height": 0.2}, "calibration_status": "pending"}],
  "quality_gate": {"required_scene_count": 5, "required_npc_count": 4, "required_clue_count": 6}
}
"""


script_generation_service = ScriptGenerationService()
