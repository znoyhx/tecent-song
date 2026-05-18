from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
from uuid import uuid4
from typing import Any

from app.core.config import settings


class LogService:
    def __init__(self, base_dir: Path | None = None) -> None:
        backend_root = Path(__file__).resolve().parents[2]
        self.base_dir = base_dir or backend_root / "logs"
        self.prompt_dir = self.base_dir / "prompts"
        self.response_dir = self.base_dir / "responses"

    def record_ai_call(
        self,
        *,
        module: str,
        model: str,
        input_summary: str,
        latency_ms: int,
        success: bool,
        fallback_used: bool,
        supervisor_pass: bool,
        issues: list[Any],
        prompt: str | None = None,
        raw_response: str | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        self.prompt_dir.mkdir(parents=True, exist_ok=True)
        self.response_dir.mkdir(parents=True, exist_ok=True)
        call_id = f"call_{uuid4().hex[:10]}"

        prompt_path = None
        response_path = None
        if prompt is not None:
            prompt_path = self.prompt_dir / f"{call_id}.txt"
            prompt_path.write_text(self._redact(prompt), encoding="utf-8")
        if raw_response is not None:
            response_path = self.response_dir / f"{call_id}.json"
            response_path.write_text(self._redact(raw_response), encoding="utf-8")

        issue_payload = [self._issue_to_dict(issue) for issue in issues]
        entry = {
            "call_id": call_id,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "module": module,
            "provider": settings.ai_provider,
            "model": model,
            "ai_mode": "mock" if settings.use_mock_ai or settings.ai_provider == "mock" else "real",
            "input_summary": self._redact(input_summary),
            "prompt_path": str(prompt_path) if prompt_path else None,
            "response_path": str(response_path) if response_path else None,
            "latency_ms": latency_ms,
            "success": success,
            "fallback_used": fallback_used,
            "supervisor_pass": supervisor_pass,
            "supervisor_issue_types": [str(issue.get("type")) for issue in issue_payload if issue.get("type")],
            "issues": issue_payload,
        }

        if extra_fields:
            entry.update(self._redact_extra_fields(extra_fields))

        self.base_dir.mkdir(parents=True, exist_ok=True)

        with (self.base_dir / "ai_calls.jsonl").open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def _issue_to_dict(self, issue: Any) -> dict[str, Any]:
        if hasattr(issue, "model_dump"):
            payload = issue.model_dump()
        elif isinstance(issue, dict):
            payload = issue
        else:
            payload = {"detail": str(issue)}
        return self._redact_value(payload)

    def _redact_extra_fields(self, fields: dict[str, Any]) -> dict[str, Any]:
        return self._redact_value(fields)

    def _redact_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._redact(value)
        if isinstance(value, list):
            return [self._redact_value(item) for item in value]
        if isinstance(value, dict):
            return {str(key): self._redact_value(item) for key, item in value.items()}
        return value


    def _redact(self, text: str) -> str:
        redacted = text
        if settings.deepseek_api_key:
            redacted = redacted.replace(settings.deepseek_api_key, "[已隐藏密钥]")
        redacted = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [已隐藏密钥]", redacted)
        redacted = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "[已隐藏密钥]", redacted)
        return redacted



log_service = LogService()
