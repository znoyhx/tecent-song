from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.script_models import ScriptPackage


@dataclass
class ScriptSupervisorIssue:
    code: str
    severity: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def model_dump(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class ScriptSupervisorResult:
    passed: bool
    issues: list[ScriptSupervisorIssue]

    @property
    def blocking_issues(self) -> list[ScriptSupervisorIssue]:
        return [issue for issue in self.issues if issue.severity == "blocking"]

    def model_dump(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "issues": [issue.model_dump() for issue in self.issues],
            "blocking_issues": [issue.model_dump() for issue in self.blocking_issues],
        }


class ScriptSupervisor:
    modern_terms = {"手机", "电话", "电报", "火车", "报纸", "警察", "公司", "咖啡"}
    song_conflicts = {"锦衣卫", "东厂", "西厂", "军机处", "巡捕"}
    late_tang_conflicts = {"锦衣卫", "东厂", "西厂", "军机处", "殿试"}

    def review(self, package: ScriptPackage) -> ScriptSupervisorResult:
        issues: list[ScriptSupervisorIssue] = []
        location_ids = {item.location_id for item in package.locations}
        npc_ids = {item.npc_id for item in package.npcs}
        clue_ids = {item.clue_id for item in package.clues}
        asset_ids = {item.asset_id for item in package.visual_assets}
        stage_ids = {item.stage_id for item in package.stages}

        if package.dynasty_id not in {"song", "late_tang"}:
            self._add(issues, "DYNASTY_NOT_SUPPORTED", "blocking", "P0 只支持北宋和晚唐。")

        conflict_terms = self.song_conflicts if package.dynasty_id == "song" else self.late_tang_conflicts
        corpus = self._corpus(package)
        found_modern = sorted(term for term in self.modern_terms if term in corpus)
        found_conflicts = sorted(term for term in conflict_terms if term in corpus)
        if found_modern:
            self._add(issues, "ERA_MODERN_TERM_CONFLICT", "blocking", "剧本含明显现代词。", {"terms": found_modern})
        if found_conflicts:
            self._add(issues, "ERA_DYNASTY_TERM_CONFLICT", "blocking", "剧本含朝代冲突称谓或制度。", {"terms": found_conflicts})

        for stage in package.stages:
            if stage.entry_location_id not in location_ids:
                self._add(issues, "STAGE_ENTRY_LOCATION_MISSING", "blocking", "阶段入口场景不存在。", {"stage_id": stage.stage_id})
            if not stage.available_location_ids:
                self._add(issues, "STAGE_UNREACHABLE", "blocking", "阶段没有可进入场景。", {"stage_id": stage.stage_id})
            missing_locations = sorted(set(stage.available_location_ids).difference(location_ids))
            if missing_locations:
                self._add(issues, "STAGE_LOCATION_MISSING", "blocking", "阶段引用了不存在的场景。", {"stage_id": stage.stage_id, "location_ids": missing_locations})

        truth_chain = [clue_id for clue_id in package.story.truth_chain_clue_ids if clue_id]
        missing_truth = sorted(set(truth_chain).difference(clue_ids))
        if len(truth_chain) < 3 or missing_truth:
            self._add(issues, "CLUE_CHAIN_BROKEN", "blocking", "核心线索不能串成真相链。", {"missing_clue_ids": missing_truth})

        referenced_in_graph: set[str] = set()
        for graph in package.clue_graph:
            missing = sorted(set(graph.required_clue_ids).difference(clue_ids))
            if missing:
                self._add(issues, "CLUE_CHAIN_BROKEN", "blocking", "线索组合引用了不存在的线索。", {"rule_id": graph.rule_id, "missing_clue_ids": missing})
            referenced_in_graph.update(graph.required_clue_ids)
        if package.clue_graph and not set(truth_chain).issubset(referenced_in_graph.union(set(truth_chain))):
            self._add(issues, "CLUE_CHAIN_WEAK", "warning", "核心线索链未全部参与组合推理。")

        if not package.choices:
            self._add(issues, "CHOICE_MISSING", "blocking", "生成剧本缺少最终抉择。")
        if not package.endings:
            self._add(issues, "ENDING_MISSING", "blocking", "生成剧本缺少结局。")
        if package.endings and not any(ending.conditions or ending.required_flags or ending.priority == 0 for ending in package.endings):
            self._add(issues, "ENDING_UNREACHABLE", "blocking", "所有结局都缺少可判定条件。")

        for location in package.locations:
            if location.visual_asset_id not in asset_ids:
                self._add(issues, "VISUAL_FIELD_MISSING", "blocking", "场景缺少视觉资产。", {"location_id": location.location_id})
            missing_npcs = sorted(set(location.npc_ids).difference(npc_ids))
            if missing_npcs:
                self._add(issues, "NPC_REFERENCE_MISSING", "blocking", "场景引用了不存在的人物。", {"location_id": location.location_id, "npc_ids": missing_npcs})
            for hotspot in location.hotspots:
                missing_clues = sorted(set(hotspot.clue_ids).difference(clue_ids))
                if missing_clues:
                    self._add(issues, "HOTSPOT_CLUE_MISSING", "blocking", "热点引用了不存在的线索。", {"hotspot_id": hotspot.hotspot_id, "clue_ids": missing_clues})

        for npc in package.npcs:
            if npc.visual_asset_id not in asset_ids:
                self._add(issues, "VISUAL_FIELD_MISSING", "blocking", "人物缺少视觉资产。", {"npc_id": npc.npc_id})
            if not npc.forbidden_disclosure:
                self._add(issues, "NPC_PERMISSION_WEAK", "blocking", "NPC 缺少信息边界，可能早期剧透。", {"npc_id": npc.npc_id})
            forbidden_text = " ".join(npc.forbidden_disclosure)
            if package.story.hidden_truth and package.story.hidden_truth in forbidden_text:
                self._add(issues, "EARLY_SPOILER_RISK", "blocking", "NPC 信息边界直接包含最终真相。", {"npc_id": npc.npc_id})

        for clue in package.clues:
            if clue.visual_asset_id not in asset_ids:
                self._add(issues, "VISUAL_FIELD_MISSING", "blocking", "线索缺少视觉资产。", {"clue_id": clue.clue_id})
            if not set(clue.stage_available).intersection(stage_ids):
                self._add(issues, "CLUE_STAGE_UNREACHABLE", "blocking", "线索没有可达阶段。", {"clue_id": clue.clue_id})

        if len(package.playable_identities) < 1:
            self._add(issues, "PLAYABLE_IDENTITY_MISSING", "blocking", "缺少可选玩家身份。")
        for identity in package.playable_identities:
            if not identity.motive or not identity.permissions:
                self._add(issues, "PLAYER_IDENTITY_PERMISSION_MISSING", "blocking", "玩家身份缺少调查动机或行动权限。", {"identity_id": identity.identity_id})

        scene_assets = [asset for asset in package.visual_assets if asset.asset_type == "scene"]
        npc_assets = [asset for asset in package.visual_assets if asset.asset_type == "npc"]
        clue_assets = [asset for asset in package.visual_assets if asset.asset_type == "clue"]
        if len(scene_assets) < 5 or len(npc_assets) < 4 or len(clue_assets) < 6:
            self._add(issues, "VISUAL_REQUIRED_ASSETS_MISSING", "blocking", "必需图片数量不足。", {
                "scene": len(scene_assets),
                "npc": len(npc_assets),
                "clue": len(clue_assets),
            })
        for asset in package.visual_assets:
            if not asset.prompt or not asset.era_feature_checklist or not asset.required_subjects:
                self._add(issues, "IMAGE_GATE_FIELDS_MISSING", "blocking", "图片质量门禁字段不完整。", {"asset_id": asset.asset_id})

        positioned_hotspots = [item for item in package.hotspot_positioning if item.anchor_point and item.bbox]
        if len(positioned_hotspots) < 6:
            self._add(issues, "HOTSPOT_COORDINATE_MISSING", "blocking", "至少 6 个核心热点需要 anchor_point 与 bbox。", {"positioned": len(positioned_hotspots)})
        for item in package.hotspot_positioning:
            if item.location_id not in location_ids:
                self._add(issues, "HOTSPOT_LOCATION_MISSING", "blocking", "热点定位引用了不存在的场景。", {"location_id": item.location_id})
            if item.visual_asset_id not in asset_ids:
                self._add(issues, "HOTSPOT_VISUAL_MISSING", "blocking", "热点定位引用了不存在的图片资产。", {"visual_asset_id": item.visual_asset_id})

        return ScriptSupervisorResult(passed=not any(issue.severity == "blocking" for issue in issues), issues=issues)

    def _add(self, issues: list[ScriptSupervisorIssue], code: str, severity: str, message: str, details: dict[str, Any] | None = None) -> None:
        issues.append(ScriptSupervisorIssue(code=code, severity=severity, message=message, details=details or {}))

    def _corpus(self, package: ScriptPackage) -> str:
        return " ".join(
            [
                package.script_overview.title,
                package.script_overview.case_summary,
                package.story.surface_event,
                package.story.hidden_truth,
                *[location.description for location in package.locations],
                *[npc.public_identity + npc.hidden_motive for npc in package.npcs],
                *[clue.detail for clue in package.clues],
            ]
        )


script_supervisor = ScriptSupervisor()
