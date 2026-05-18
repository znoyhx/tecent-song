from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import Settings, settings
from app.services.ai_client import AIClient, AIResponse


class RepairAgent:
    def __init__(self, *, ai_client: AIClient | None = None, runtime_settings: Settings | None = None) -> None:
        self.settings = runtime_settings or settings
        self.ai_client = ai_client or AIClient(self.settings)
        backend_root = Path(__file__).resolve().parents[2]
        self.prompt_path = backend_root / "data" / "prompts" / "repair_dialogue.md"
        self.last_prompt: str | None = None

    def repair_dialogue_json(
        self,
        *,
        original_response: dict[str, Any],
        supervisor_issues: list[Any],
        repair_instruction: str,
        context_summary: dict[str, Any],
        schema_hint: dict[str, Any],
    ) -> AIResponse:
        prompt = self._build_prompt(
            original_response=original_response,
            supervisor_issues=supervisor_issues,
            repair_instruction=repair_instruction,
            context_summary=context_summary,
            schema_hint=schema_hint,
        )
        self.last_prompt = prompt
        return self.ai_client.generate_json_sync(
            module="RepairAgent",
            prompt=prompt,
            schema_hint=schema_hint,
        )

    def _build_prompt(
        self,
        *,
        original_response: dict[str, Any],
        supervisor_issues: list[Any],
        repair_instruction: str,
        context_summary: dict[str, Any],
        schema_hint: dict[str, Any],
    ) -> str:
        template = self.prompt_path.read_text(encoding="utf-8")
        issue_payload = [self._issue_to_dict(issue) for issue in supervisor_issues]
        replacements = {
            "{original_response_json}": json.dumps(original_response, ensure_ascii=False),
            "{supervisor_issues_json}": json.dumps(issue_payload, ensure_ascii=False),
            "{repair_instruction}": repair_instruction,
            "{context_summary_json}": json.dumps(context_summary, ensure_ascii=False),
            "{schema_hint_json}": json.dumps(schema_hint, ensure_ascii=False),
        }
        prompt = template
        for placeholder, value in replacements.items():
            prompt = prompt.replace(placeholder, value)
        return prompt

    def _issue_to_dict(self, issue: Any) -> dict[str, Any]:
        if hasattr(issue, "model_dump"):
            return issue.model_dump()
        if isinstance(issue, dict):
            return issue
        return {"detail": str(issue)}
