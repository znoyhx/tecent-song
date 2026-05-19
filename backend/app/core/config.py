from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = BACKEND_ROOT.parent


@dataclass(frozen=True)
class Settings:
    app_name: str
    version: str
    use_mock_ai: bool
    ai_provider: str
    backend_port: int
    frontend_port: int
    deepseek_base_url: str
    deepseek_model: str
    ai_timeout_seconds: int
    ai_max_retries: int
    deepseek_api_key: str | None = field(default=None, repr=False)
    music_provider: str = "tianpuyue"
    music_generate_endpoint: str = "https://api.tianpuyue.cn/open-apis/v1/instrumental/generate"
    music_query_endpoint: str = "https://api.tianpuyue.cn/open-apis/v1/instrumental/query"
    music_model: str = "TemPolor i3.5"
    music_timeout_seconds: int = 30
    music_api_key: str | None = field(default=None, repr=False)
    music_tos_bucket: str = ""
    music_callback_url: str = ""

    @property
    def deepseek_api_key_available(self) -> bool:
        return bool(self.deepseek_api_key)

    @property
    def music_api_key_available(self) -> bool:
        return bool(self.music_api_key)

    @property
    def allowed_origins(self) -> list[str]:
        return [
            f"http://127.0.0.1:{self.frontend_port}",
            f"http://localhost:{self.frontend_port}",
        ]


def _read_env_file(env_path: Path) -> dict[str, str]:
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _read_backend_env_file() -> dict[str, str]:
    values: dict[str, str] = {}
    for env_path in (WORKSPACE_ROOT / ".env", BACKEND_ROOT / ".env"):
        values.update(_read_env_file(env_path))
    return values


def _env_value(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is not None and value != "":
        return value
    return _read_backend_env_file().get(name, default)


def _env_bool(name: str, default: bool) -> bool:
    value = _env_value(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = _env_value(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def load_settings() -> Settings:
    backend_port = _env_int("BACKEND_PORT", 8000)
    frontend_port = _env_int("FRONTEND_PORT", 5173)
    api_key = _env_value("DEEPSEEK_API_KEY")
    use_mock_ai = _env_bool("USE_MOCK_AI", True)
    ai_provider = (_env_value("AI_PROVIDER", "mock") or "mock").strip().lower()
    if use_mock_ai and ai_provider == "deepseek":
        ai_provider = "mock"
    music_api_key = (
        _env_value("TIANPUYUEKEY")
        or _env_value("TIANPUYUE_API_KEY")
        or _env_value("MUSIC_API_KEY")
        or _env_value("MUSIC_AUTHORIZATION")
    )

    music_public_base_url = (
        _env_value("MUSIC_PUBLIC_BASE_URL")
        or _env_value("BACKEND_PUBLIC_URL")
        or f"http://127.0.0.1:{backend_port}"
    ).rstrip("/")
    music_callback_url = _env_value("MUSIC_CALLBACK_URL") or f"{music_public_base_url}/api/music/callback"

    return Settings(
        app_name="史隙阶段四真实 AI NPC 后端",
        version="0.11.0",
        use_mock_ai=use_mock_ai,
        ai_provider=ai_provider,
        backend_port=backend_port,
        frontend_port=frontend_port,
        deepseek_base_url=(_env_value("DEEPSEEK_BASE_URL", "https://api.deepseek.com") or "https://api.deepseek.com").rstrip("/"),
        deepseek_model=_env_value("DEEPSEEK_MODEL", "deepseek-chat") or "deepseek-chat",
        ai_timeout_seconds=max(1, _env_int("AI_TIMEOUT_SECONDS", 20)),
        ai_max_retries=max(0, _env_int("AI_MAX_RETRIES", 1)),
        deepseek_api_key=api_key,
        music_provider=(_env_value("MUSIC_PROVIDER", "tianpuyue") or "tianpuyue").strip().lower(),
        music_generate_endpoint=(
            _env_value("MUSIC_GENERATE_ENDPOINT", "https://api.tianpuyue.cn/open-apis/v1/instrumental/generate")
            or "https://api.tianpuyue.cn/open-apis/v1/instrumental/generate"
        ).rstrip("/"),
        music_query_endpoint=(
            _env_value("MUSIC_QUERY_ENDPOINT", "https://api.tianpuyue.cn/open-apis/v1/instrumental/query")
            or "https://api.tianpuyue.cn/open-apis/v1/instrumental/query"
        ).rstrip("/"),
        music_model=_env_value("MUSIC_MODEL", "TemPolor i3.5") or "TemPolor i3.5",
        music_timeout_seconds=max(1, _env_int("MUSIC_TIMEOUT_SECONDS", 30)),
        music_api_key=music_api_key,
        music_tos_bucket=_env_value("MUSIC_TOS_BUCKET", "") or "",
        music_callback_url=music_callback_url,
    )


settings = load_settings()

