from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.script_models import ScriptPackage


MIN_LOCATIONS = 8
MIN_HOTSPOTS = 24
MIN_CLUES = 30
MIN_CLUE_GRAPH = 6
MIN_DEDUCTIONS = 8
MIN_CHAPTER_SECTIONS = 12
MIN_CHOICES = 5
MIN_ENDINGS = 5
MIN_SCENE_ASSETS = 8
MIN_APPROVED_HOTSPOTS = 24


@dataclass
class ScriptVolumeIssue:
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
class ScriptVolumeGateResult:
    passed: bool
    issues: list[ScriptVolumeIssue]
    counts: dict[str, int]
    missing: dict[str, int]

    @property
    def blocking_issues(self) -> list[ScriptVolumeIssue]:
        return [issue for issue in self.issues if issue.severity == "blocking"]

    def model_dump(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "counts": self.counts,
            "missing": self.missing,
            "issues": [issue.model_dump() for issue in self.issues],
            "blocking_issues": [issue.model_dump() for issue in self.blocking_issues],
        }


class ScriptVolumeGate:
    minimums = {
        "locations": MIN_LOCATIONS,
        "hotspots": MIN_HOTSPOTS,
        "clues": MIN_CLUES,
        "clue_graph": MIN_CLUE_GRAPH,
        "deductions": MIN_DEDUCTIONS,
        "chapter_sections": MIN_CHAPTER_SECTIONS,
        "choices": MIN_CHOICES,
        "endings": MIN_ENDINGS,
        "scene_assets": MIN_SCENE_ASSETS,
        "hotspot_positioning": MIN_APPROVED_HOTSPOTS,
    }

    def review(self, package: ScriptPackage) -> ScriptVolumeGateResult:
        hotspot_ids = {
            hotspot.hotspot_id
            for location in package.locations
            for hotspot in location.hotspots
        }
        location_ids = {location.location_id for location in package.locations}
        npc_ids = {npc.npc_id for npc in package.npcs}
        clue_ids = {clue.clue_id for clue in package.clues}
        section_ids = {section.section_id for section in package.chapter_sections}
        scene_asset_count = sum(1 for asset in package.visual_assets if asset.asset_type == "scene")

        counts = {
            "locations": len(package.locations),
            "hotspots": len(hotspot_ids),
            "clues": len(package.clues),
            "clue_graph": len(package.clue_graph),
            "deductions": len(package.deductions),
            "chapter_sections": len(package.chapter_sections),
            "choices": len(package.choices),
            "endings": len(package.endings),
            "scene_assets": scene_asset_count,
            "hotspot_positioning": len(package.hotspot_positioning),
        }
        missing = {
            key: max(0, minimum - counts[key])
            for key, minimum in self.minimums.items()
        }

        issues: list[ScriptVolumeIssue] = []
        self._add_count_issue(issues, missing, counts, "locations", "SCRIPT_VOLUME_TOO_SMALL", "场景数量不足。")
        self._add_count_issue(issues, missing, counts, "hotspots", "HOTSPOT_VOLUME_TOO_SMALL", "调查热点数量不足。")
        self._add_count_issue(issues, missing, counts, "clues", "CLUE_VOLUME_TOO_SMALL", "线索/证物数量不足。")
        self._add_count_issue(issues, missing, counts, "clue_graph", "SCRIPT_VOLUME_TOO_SMALL", "线索组合数量不足。")
        self._add_count_issue(issues, missing, counts, "deductions", "DEDUCTION_MISSING", "推理疑团数量不足。")
        self._add_count_issue(issues, missing, counts, "chapter_sections", "CHAPTER_SECTION_MISSING", "剧情小节数量不足。")
        self._add_count_issue(issues, missing, counts, "choices", "ENDING_VARIANTS_MISSING", "最终选择数量不足。")
        self._add_count_issue(issues, missing, counts, "endings", "ENDING_VARIANTS_MISSING", "结局数量不足。")
        self._add_count_issue(issues, missing, counts, "scene_assets", "SCRIPT_VOLUME_TOO_SMALL", "场景图数量不足。")
        self._add_count_issue(issues, missing, counts, "hotspot_positioning", "HOTSPOT_VOLUME_TOO_SMALL", "热点定位数量不足。")

        self._check_hotspot_references(issues, package, clue_ids)
        self._check_deduction_references(issues, package, clue_ids)
        self._check_section_references(issues, package, location_ids, npc_ids, hotspot_ids, clue_ids, section_ids)
        self._check_ending_references(issues, package, clue_ids)
        self._check_truth_chain_participation(issues, package)

        blocking = [issue for issue in issues if issue.severity == "blocking"]
        return ScriptVolumeGateResult(passed=not blocking, issues=issues, counts=counts, missing=missing)

    def _add_count_issue(
        self,
        issues: list[ScriptVolumeIssue],
        missing: dict[str, int],
        counts: dict[str, int],
        field_name: str,
        code: str,
        message: str,
    ) -> None:
        if missing[field_name] <= 0:
            return
        self._add(
            issues,
            code,
            "blocking",
            message,
            {
                "field": field_name,
                "actual": counts[field_name],
                "minimum": self.minimums[field_name],
                "missing": missing[field_name],
            },
        )

    def _check_hotspot_references(self, issues: list[ScriptVolumeIssue], package: ScriptPackage, clue_ids: set[str]) -> None:
        for location in package.locations:
            for hotspot in location.hotspots:
                missing_clues = sorted(set(hotspot.clue_ids).difference(clue_ids))
                if missing_clues:
                    self._add(
                        issues,
                        "VOLUME_REFERENCE_BROKEN",
                        "blocking",
                        "热点引用了不存在的线索。",
                        {"location_id": location.location_id, "hotspot_id": hotspot.hotspot_id, "missing_clue_ids": missing_clues},
                    )

    def _check_deduction_references(self, issues: list[ScriptVolumeIssue], package: ScriptPackage, clue_ids: set[str]) -> None:
        for deduction in package.deductions:
            referenced = set(deduction.required_clue_ids + deduction.correct_clue_ids)
            missing_clues = sorted(referenced.difference(clue_ids))
            if missing_clues:
                self._add(
                    issues,
                    "VOLUME_REFERENCE_BROKEN",
                    "blocking",
                    "推理疑团引用了不存在的线索。",
                    {"deduction_id": deduction.deduction_id, "missing_clue_ids": missing_clues},
                )

    def _check_section_references(
        self,
        issues: list[ScriptVolumeIssue],
        package: ScriptPackage,
        location_ids: set[str],
        npc_ids: set[str],
        hotspot_ids: set[str],
        clue_ids: set[str],
        section_ids: set[str],
    ) -> None:
        for section in package.chapter_sections:
            details: dict[str, Any] = {"section_id": section.section_id}
            if section.scene_id not in location_ids:
                details["missing_scene_id"] = section.scene_id
            missing_npcs = sorted(set(section.npc_ids).difference(npc_ids))
            missing_hotspots = sorted(set(section.hotspot_ids).difference(hotspot_ids))
            missing_clues = sorted(set(section.clue_ids).difference(clue_ids))
            missing_next = sorted(set(section.next_section_ids).difference(section_ids))
            if missing_npcs:
                details["missing_npc_ids"] = missing_npcs
            if missing_hotspots:
                details["missing_hotspot_ids"] = missing_hotspots
            if missing_clues:
                details["missing_clue_ids"] = missing_clues
            if missing_next:
                details["missing_next_section_ids"] = missing_next
            if len(details) > 1:
                self._add(issues, "VOLUME_REFERENCE_BROKEN", "blocking", "剧情小节引用了不存在的内容。", details)

    def _check_ending_references(self, issues: list[ScriptVolumeIssue], package: ScriptPackage, clue_ids: set[str]) -> None:
        choice_ids = {choice.choice_id for choice in package.choices}
        for ending in package.endings:
            missing_clues = sorted(set(ending.related_clue_ids).difference(clue_ids))
            missing_choices = sorted(set(ending.related_choice_ids).difference(choice_ids))
            if missing_clues or missing_choices:
                self._add(
                    issues,
                    "VOLUME_REFERENCE_BROKEN",
                    "blocking",
                    "结局引用了不存在的线索或选择。",
                    {"ending_id": ending.ending_id, "missing_clue_ids": missing_clues, "missing_choice_ids": missing_choices},
                )
            if not (ending.conditions or ending.required_flags or ending.related_choice_ids or ending.related_clue_ids):
                self._add(
                    issues,
                    "VOLUME_REFERENCE_BROKEN",
                    "blocking",
                    "结局缺少可触发条件。",
                    {"ending_id": ending.ending_id},
                )

    def _check_truth_chain_participation(self, issues: list[ScriptVolumeIssue], package: ScriptPackage) -> None:
        truth_chain = set(package.story.truth_chain_clue_ids)
        graph_clues = {clue_id for rule in package.clue_graph for clue_id in rule.required_clue_ids}
        deduction_clues = {
            clue_id
            for deduction in package.deductions
            for clue_id in [*deduction.required_clue_ids, *deduction.correct_clue_ids]
        }
        missing = sorted(truth_chain.difference(graph_clues | deduction_clues))
        if missing:
            self._add(
                issues,
                "VOLUME_REFERENCE_BROKEN",
                "blocking",
                "真相链线索未进入线索组合或推理疑团。",
                {"missing_truth_chain_clue_ids": missing},
            )

    def _add(self, issues: list[ScriptVolumeIssue], code: str, severity: str, message: str, details: dict[str, Any] | None = None) -> None:
        issues.append(ScriptVolumeIssue(code=code, severity=severity, message=message, details=details or {}))


script_volume_gate = ScriptVolumeGate()
