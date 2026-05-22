from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import re
import time
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.core.config import Settings, settings


class AIResponse(BaseModel):
    success: bool
    parsed_json: dict[str, Any] = Field(default_factory=dict)
    raw_text: str = ""
    latency_ms: int = 0
    fallback_used: bool = False
    error_message: str | None = None
    model: str


class AIClient:
    def __init__(self, runtime_settings: Settings | None = None) -> None:
        self.settings = runtime_settings or settings

    async def generate_json(
        self,
        *,
        module: str,
        prompt: str,
        schema_hint: dict[str, Any],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AIResponse:
        started_at = time.perf_counter()
        if self.settings.use_mock_ai:
            return self._failure("当前处于 Mock 模式，未调用真实 AI。", started_at)
        if self.settings.ai_provider != "deepseek":
            return self._failure("当前 AI 提供方不是 DeepSeek，已回退到失败状态。", started_at)
        if not self.settings.deepseek_api_key_available or not self.settings.deepseek_api_key:
            return self._failure("未检测到 DeepSeek Key，已回退到失败状态。", started_at)

        token_limit = 900 if max_tokens is None else max_tokens
        payload = {
            "model": self.settings.deepseek_model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是受控 JSON 生成器。必须只返回一个合法 JSON 对象，不要输出 Markdown、解释或多余文字。",
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.4 if temperature is None else temperature,
            "max_tokens": token_limit,
        }
        url = f"{self.settings.deepseek_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }

        attempts = max(1, self.settings.ai_max_retries + 1)
        if token_limit >= 6000:
            attempts = max(attempts, 2)
        last_error = "AI 调用失败，已回退到失败状态。"
        raw_text = ""
        for _ in range(attempts):
            try:
                timeout = self._timeout_for_tokens(token_limit)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, headers=headers, json=payload)
                if response.status_code >= 400:
                    last_error = f"AI 服务返回状态 {response.status_code}，已回退到失败状态。"
                    continue
                response_json = response.json()
                raw_text = response_json["choices"][0]["message"]["content"]
                parsed = self._extract_json(raw_text)
                missing = [key for key in schema_hint.keys() if key not in parsed]
                if missing:
                    return self._failure(f"AI JSON 缺少字段：{', '.join(missing)}。", started_at, raw_text=raw_text)
                return AIResponse(
                    success=True,
                    parsed_json=parsed,
                    raw_text=raw_text,
                    latency_ms=self._latency_ms(started_at),
                    fallback_used=False,
                    error_message=None,
                    model=self.settings.deepseek_model,
                )
            except (httpx.TimeoutException, httpx.TransportError):
                last_error = "AI 网络请求超时或不可达，已回退到失败状态。"
                await asyncio.sleep(4)
            except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
                last_error = "AI 返回格式无法解析，已回退到失败状态。"
            except Exception as exc:  # noqa: BLE001
                last_error = self._sanitize_error(str(exc)) or "AI 调用异常，已回退到失败状态。"
        return self._failure(last_error, started_at, raw_text=raw_text)

    def generate_json_sync(
        self,
        *,
        module: str,
        prompt: str,
        schema_hint: dict[str, Any],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AIResponse:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self.generate_json(
                    module=module,
                    prompt=prompt,
                    schema_hint=schema_hint,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            )

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                lambda: asyncio.run(
                    self.generate_json(
                        module=module,
                        prompt=prompt,
                        schema_hint=schema_hint,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                )
            )
            return future.result()

    def _timeout_for_tokens(self, max_tokens: int) -> httpx.Timeout:
        # Long structured ScriptPackage rounds routinely take 40-90 seconds.
        dynamic_timeout = max(self.settings.ai_timeout_seconds, min(240, int(max_tokens / 70) + 10))
        return httpx.Timeout(float(dynamic_timeout))

    def _extract_json(self, raw_text: str) -> dict[str, Any]:
        text = raw_text.strip()
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
        if fenced:
            parsed = json.loads(fenced.group(1))
            if isinstance(parsed, dict):
                return parsed

        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            parsed = json.loads(text[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        raise ValueError("未找到合法 JSON 对象")

    def _failure(self, message: str, started_at: float, raw_text: str = "") -> AIResponse:
        return AIResponse(
            success=False,
            parsed_json={},
            raw_text=raw_text,
            latency_ms=self._latency_ms(started_at),
            fallback_used=True,
            error_message=self._sanitize_error(message),
            model=self.settings.deepseek_model,
        )

    def _latency_ms(self, started_at: float) -> int:
        return int((time.perf_counter() - started_at) * 1000)

    def _sanitize_error(self, message: str) -> str:
        redacted = message
        if self.settings.deepseek_api_key:
            redacted = redacted.replace(self.settings.deepseek_api_key, "[已隐藏密钥]")
        redacted = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [已隐藏密钥]", redacted)
        redacted = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "[已隐藏密钥]", redacted)
        return redacted
