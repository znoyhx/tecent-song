from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RAGQuery:
    dynasty_id: str
    current_stage: str
    current_scene_id: str
    npc_id: str
    player_message: str
    presented_clue_ids: list[str]
    discovered_clue_ids: list[str]
    material_type: set[str]
    keywords: list[str]
    source_level: set[str]
    severity: set[str]


class RAGRetriever:
    """轻量 JSON 检索器；仅为 Prompt 提供约束上下文，不更新游戏状态。"""

    def __init__(self, source_path: Path | None = None, source_paths: list[Path] | None = None) -> None:
        backend_root = Path(__file__).resolve().parents[2]
        self.source_dir = backend_root / "data" / "rag_sources"
        self.source_paths = self._resolve_source_paths(source_path=source_path, source_paths=source_paths)
        self._sources = self._load_sources()

    def retrieve(
        self,
        *,
        dynasty_id: str,
        current_stage: str,
        current_scene_id: str = "",
        npc_id: str = "",
        player_message: str = "",
        presented_clue_ids: list[str] | None = None,
        discovered_clue_ids: list[str] | None = None,
        material_type: str | list[str] | None = None,
        keywords: list[str] | None = None,
        source_level: str | list[str] | None = None,
        severity: str | list[str] | None = None,
        top_k: int = 8,
    ) -> list[dict[str, Any]]:
        query = RAGQuery(
            dynasty_id=dynasty_id,
            current_stage=current_stage,
            current_scene_id=current_scene_id,
            npc_id=npc_id,
            player_message=player_message,
            presented_clue_ids=presented_clue_ids or [],
            discovered_clue_ids=discovered_clue_ids or [],
            material_type=self._as_filter_set(material_type),
            keywords=keywords or [],
            source_level=self._as_filter_set(source_level, upper=True),
            severity=self._as_filter_set(severity, lower=True),
        )
        best_by_id: dict[str, tuple[int, dict[str, Any]]] = {}
        for source in self._sources:
            if source.get("dynasty_id") != query.dynasty_id:
                continue
            if query.material_type and str(source.get("material_type", "")) not in query.material_type:
                continue
            if query.source_level and str(source.get("source_level", "")).upper() not in query.source_level:
                continue
            if query.severity and str(source.get("severity", "")).lower() not in query.severity:
                continue

            score = self._score(source, query)
            if score <= 0:
                continue
            source_id = str(source.get("source_id", ""))
            if not source_id:
                continue
            previous = best_by_id.get(source_id)
            if previous is None or score > previous[0]:
                best_by_id[source_id] = (score, source)

        scored = list(best_by_id.values())
        scored.sort(
            key=lambda item: (
                item[0],
                self._material_type_weight(str(item[1].get("material_type", ""))),
                self._severity_weight(str(item[1].get("severity", ""))),
                self._source_level_weight(str(item[1].get("source_level", ""))),
            ),
            reverse=True,
        )
        return [self._public_source(source, score) for score, source in scored[: max(0, top_k)]]

    def group_by_type(self, hits: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for hit in hits:
            grouped.setdefault(str(hit.get("material_type") or "unknown"), []).append(hit)
        return grouped

    def preview(
        self,
        *,
        dynasty_id: str,
        current_stage: str,
        current_scene_id: str = "",
        npc_id: str = "",
        player_message: str = "",
        presented_clue_ids: list[str] | None = None,
        discovered_clue_ids: list[str] | None = None,
        top_k: int = 8,
        content_limit: int = 100,
    ) -> dict[str, Any]:
        safe_top_k = min(max(int(top_k), 0), 20)
        safe_content_limit = min(max(int(content_limit), 0), 120)
        hits = self.retrieve(
            dynasty_id=dynasty_id,
            current_stage=current_stage,
            current_scene_id=current_scene_id,
            npc_id=npc_id,
            player_message=player_message,
            presented_clue_ids=presented_clue_ids or [],
            discovered_clue_ids=discovered_clue_ids or [],
            top_k=safe_top_k,
        )
        preview_hits = [self._debug_source(hit, safe_content_limit) for hit in hits]
        return {
            "hit_count": len(preview_hits),
            "source_ids": [hit["source_id"] for hit in preview_hits if hit.get("source_id")],
            "material_types": sorted({hit["material_type"] for hit in preview_hits if hit.get("material_type")}),
            "hits": preview_hits,
            "grouped": self._debug_grouped(preview_hits),
        }

    def _resolve_source_paths(self, *, source_path: Path | None, source_paths: list[Path] | None) -> list[Path]:

        if source_paths is not None:
            return list(source_paths)
        if source_path is None:
            return sorted(self.source_dir.glob("*.json")) if self.source_dir.exists() else []
        if source_path.is_dir():
            return sorted(source_path.glob("*.json"))
        return [source_path]

    def _load_sources(self) -> list[dict[str, Any]]:
        loaded: list[dict[str, Any]] = []
        seen: set[str] = set()
        for path in self.source_paths:
            if not path.exists() or not path.is_file():
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            sources = payload.get("sources", [])
            if not isinstance(sources, list):
                continue
            for source in sources:
                if not isinstance(source, dict):
                    continue
                source_id = str(source.get("source_id", ""))
                if not source_id or source_id in seen:
                    continue
                seen.add(source_id)
                loaded.append(source)
        return loaded

    def _score(self, source: dict[str, Any], query: RAGQuery) -> int:
        score = 0
        matched_anchor = False
        stages = {str(item) for item in source.get("stage") or []}
        scene_ids = {str(item) for item in source.get("scene_ids") or []}
        npc_ids = {str(item) for item in source.get("npc_ids") or []}
        source_keywords = [str(keyword) for keyword in source.get("keywords") or []]
        query_keywords = [str(keyword) for keyword in query.keywords]
        query_text = " ".join(
            [
                query.player_message,
                query.current_scene_id,
                query.current_stage,
                query.npc_id,
                " ".join(query.presented_clue_ids),
                " ".join(query.discovered_clue_ids),
                " ".join(query_keywords),
            ]
        ).lower()

        if query.current_stage and query.current_stage in stages:
            score += 3
            matched_anchor = True
        if query.current_scene_id and query.current_scene_id in scene_ids:
            score += 3
            matched_anchor = True
        if query.npc_id and query.npc_id in npc_ids:
            score += 4
            matched_anchor = True
        for keyword in [*source_keywords, *query_keywords]:
            normalized = keyword.lower()
            if normalized and normalized in query_text:
                score += 3
                matched_anchor = True
        topic = str(source.get("topic") or "")
        if topic and any(part and part.lower() in query_text for part in topic.replace("/", " ").split()):
            score += 1
            matched_anchor = True

        if not matched_anchor:
            return 0
        score += self._material_type_weight(str(source.get("material_type", "")))
        score += self._source_level_weight(str(source.get("source_level", "")))
        score += self._severity_weight(str(source.get("severity", "")))
        return score

    def _public_source(self, source: dict[str, Any], score: int) -> dict[str, Any]:
        return {
            "source_id": str(source.get("source_id", "")),
            "dynasty_id": str(source.get("dynasty_id", "")),
            "material_type": str(source.get("material_type", "")),
            "stage": list(source.get("stage") or []),
            "scene_ids": list(source.get("scene_ids") or []),
            "npc_ids": list(source.get("npc_ids") or []),
            "topic": str(source.get("topic", "")),
            "source_level": str(source.get("source_level", "")),
            "severity": str(source.get("severity", "")),
            "keywords": list(source.get("keywords") or []),
            "content": str(source.get("content", "")),
            "usage_rule": str(source.get("usage_rule", "")),
            "score": score,
        }

    def _debug_source(self, hit: dict[str, Any], content_limit: int) -> dict[str, Any]:
        content = str(hit.get("content", ""))
        if content_limit and len(content) > content_limit:
            content = f"{content[:content_limit]}……"
        return {
            "source_id": str(hit.get("source_id", "")),
            "material_type": str(hit.get("material_type", "")),
            "topic": str(hit.get("topic", "")),
            "source_level": str(hit.get("source_level", "")),
            "severity": str(hit.get("severity", "")),
            "usage_rule": str(hit.get("usage_rule", "")),
            "score": int(hit.get("score", 0)),
            "content": content,
        }

    def _debug_grouped(self, hits: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        grouped = {material_type: [] for material_type in [
            "hard_rule",
            "clue_boundary",
            "institution",
            "space_detail",
            "object_detail",
            "daily_life",
            "occupation",
            "scene_atmosphere",
            "dialogue_lexicon",
            "forbidden_content",
        ]}
        for hit in hits:
            material_type = str(hit.get("material_type") or "unknown")
            grouped.setdefault(material_type, []).append(hit)
        return grouped

    def _as_filter_set(self, value: str | list[str] | None, *, upper: bool = False, lower: bool = False) -> set[str]:

        if value is None:
            return set()
        values = [value] if isinstance(value, str) else value
        result = set()
        for item in values:
            normalized = str(item)
            if upper:
                normalized = normalized.upper()
            if lower:
                normalized = normalized.lower()
            if normalized:
                result.add(normalized)
        return result

    def _material_type_weight(self, material_type: str) -> int:
        return {
            "hard_rule": 10,
            "forbidden_content": 10,
            "clue_boundary": 8,
            "institution": 5,
            "occupation": 3,
            "dialogue_lexicon": 3,
            "space_detail": 2,
            "object_detail": 2,
            "daily_life": 2,
            "scene_atmosphere": 2,
        }.get(material_type, 0)


    def _source_level_weight(self, source_level: str) -> int:
        return {"S": 4, "A": 3, "B": 2, "C": 1}.get(source_level.upper(), 0)

    def _severity_weight(self, severity: str) -> int:
        return {"high": 3, "medium": 2, "low": 1}.get(severity.lower(), 0)
