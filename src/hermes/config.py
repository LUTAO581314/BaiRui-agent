from __future__ import annotations

import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    product_name: str
    brand_key: str
    trademark_name: str
    logo_text: str
    env: str
    host: str
    port: int
    database_url: str
    data_dir: Path
    log_dir: Path
    obsidian_vault_dir: Path
    license_file: Path
    license_secret: str
    platform_base_url: str
    server_id: str
    vendor_dir: Path
    model_base_url: str
    model_api_key: str
    model_name: str
    model_timeout_seconds: int
    everos_base_url: str
    everos_memory_root: Path
    everos_timeout_seconds: int
    trendradar_project_root: Path | None
    trendradar_mcp_url: str
    trendradar_timeout_seconds: int
    mirofish_project_root: Path | None
    mirofish_backend_base_url: str
    mirofish_frontend_base_url: str
    mirofish_timeout_seconds: int
    searxng_base_url: str
    searxng_public_base_url: str
    searxng_timeout_seconds: int
    sonic_host: str
    sonic_port: int
    sonic_password: str
    sonic_timeout_seconds: int
    funasr_project_root: Path | None
    funasr_base_url: str
    funasr_public_base_url: str
    funasr_model: str
    funasr_timeout_seconds: int
    mineru_project_root: Path | None
    mineru_output_dir: Path
    mineru_backend: str
    mineru_device: str
    mineru_timeout_seconds: int
    avatar_assets_dir: Path
    avatar_public_base_url: str
    avatar_default_model: str
    avatar_engine_package: str
    avatar_engine_version: str
    codegraph_root: Path
    codegraph_max_file_bytes: int
    owner_token: str
    discord_bot_token: str
    feishu_verification_token: str
    feishu_app_id: str
    feishu_app_secret: str
    wechat_official_token: str
    wechat_official_app_id: str
    wechat_official_app_secret: str
    wecom_incoming_token: str
    wecom_bot_key: str
    qq_napcat_base_url: str
    qq_napcat_token: str

    @property
    def has_database(self) -> bool:
        return bool(self.database_url.strip())

    @property
    def has_model_gateway(self) -> bool:
        return bool(self.model_base_url.strip() and self.model_api_key.strip() and self.model_name.strip())


def load_settings() -> Settings:
    root = Path(__file__).resolve().parents[2]
    data_dir_value = os.getenv("HERMES_DATA_DIR", "./data/hermes")
    local_overrides = _load_local_config(Path(data_dir_value))

    def env(name: str, default: str = "") -> str:
        override = local_overrides.get(name)
        if override not in {None, ""}:
            return str(override)
        value = os.getenv(name)
        if value:
            return value
        if override is not None:
            return str(override)
        return default

    return Settings(
        product_name=env("BAIRUI_PRODUCT_NAME", os.getenv("MOXI_PRODUCT_NAME", "bairui Agent OS")),
        brand_key=env("BAIRUI_BRAND_KEY", "bairui"),
        trademark_name=env("BAIRUI_TRADEMARK_NAME", "bairui"),
        logo_text=env("BAIRUI_LOGO_TEXT", "bairui"),
        env=env("HERMES_ENV", "development"),
        host=env("HERMES_HOST", "127.0.0.1"),
        port=int(env("HERMES_PORT", "8787")),
        database_url=env("HERMES_DATABASE_URL", ""),
        data_dir=Path(env("HERMES_DATA_DIR", data_dir_value)),
        log_dir=Path(env("HERMES_LOG_DIR", "./logs/hermes")),
        obsidian_vault_dir=Path(env("HERMES_OBSIDIAN_VAULT_DIR", "./obsidian-vault")),
        license_file=Path(env("BAIRUI_LICENSE_FILE", os.getenv("MOXI_LICENSE_FILE", "./license/bairui-license.json"))),
        license_secret=env("BAIRUI_LICENSE_SECRET", ""),
        platform_base_url=env("BAIRUI_PLATFORM_BASE_URL", os.getenv("MOXI_PLATFORM_BASE_URL", "")),
        server_id=env("BAIRUI_SERVER_ID", os.getenv("MOXI_SERVER_ID", "")),
        vendor_dir=root / "vendor" / "runtimes",
        model_base_url=env("BAIRUI_MODEL_BASE_URL", ""),
        model_api_key=env("BAIRUI_MODEL_API_KEY", ""),
        model_name=env("BAIRUI_MODEL_NAME", ""),
        model_timeout_seconds=int(env("BAIRUI_MODEL_TIMEOUT_SECONDS", "60")),
        everos_base_url=env("EVEROS_BASE_URL", ""),
        everos_memory_root=Path(env("EVEROS_MEMORY_ROOT", "./data/everos")),
        everos_timeout_seconds=int(env("EVEROS_TIMEOUT_SECONDS", "30")),
        trendradar_project_root=Path(env("TRENDRADAR_PROJECT_ROOT")) if env("TRENDRADAR_PROJECT_ROOT") else None,
        trendradar_mcp_url=env("TRENDRADAR_MCP_URL", ""),
        trendradar_timeout_seconds=int(env("TRENDRADAR_TIMEOUT_SECONDS", "30")),
        mirofish_project_root=Path(env("MIROFISH_PROJECT_ROOT")) if env("MIROFISH_PROJECT_ROOT") else None,
        mirofish_backend_base_url=env("MIROFISH_BACKEND_BASE_URL", ""),
        mirofish_frontend_base_url=env("MIROFISH_FRONTEND_BASE_URL", ""),
        mirofish_timeout_seconds=int(env("MIROFISH_TIMEOUT_SECONDS", "30")),
        searxng_base_url=env("SEARXNG_BASE_URL", ""),
        searxng_public_base_url=env("SEARXNG_PUBLIC_BASE_URL", ""),
        searxng_timeout_seconds=int(env("SEARXNG_TIMEOUT_SECONDS", "30")),
        sonic_host=env("SONIC_HOST", ""),
        sonic_port=int(env("SONIC_PORT", "1491")),
        sonic_password=env("SONIC_PASSWORD", ""),
        sonic_timeout_seconds=int(env("SONIC_TIMEOUT_SECONDS", "10")),
        funasr_project_root=Path(env("FUNASR_PROJECT_ROOT")) if env("FUNASR_PROJECT_ROOT") else None,
        funasr_base_url=env("FUNASR_BASE_URL", ""),
        funasr_public_base_url=env("FUNASR_PUBLIC_BASE_URL", ""),
        funasr_model=env("FUNASR_MODEL", "fun-asr-nano"),
        funasr_timeout_seconds=int(env("FUNASR_TIMEOUT_SECONDS", "120")),
        mineru_project_root=Path(env("MINERU_PROJECT_ROOT")) if env("MINERU_PROJECT_ROOT") else None,
        mineru_output_dir=Path(env("MINERU_OUTPUT_DIR", "./data/mineru-output")),
        mineru_backend=env("MINERU_BACKEND", "pipeline"),
        mineru_device=env("MINERU_DEVICE", "cpu"),
        mineru_timeout_seconds=int(env("MINERU_TIMEOUT_SECONDS", "600")),
        avatar_assets_dir=Path(env("BAIRUI_AVATAR_ASSETS_DIR", "./data/avatars")),
        avatar_public_base_url=env("BAIRUI_AVATAR_PUBLIC_BASE_URL", ""),
        avatar_default_model=env("BAIRUI_AVATAR_DEFAULT_MODEL", ""),
        avatar_engine_package=env("BAIRUI_AVATAR_ENGINE_PACKAGE", "pixi-live2d-display-advanced"),
        avatar_engine_version=env("BAIRUI_AVATAR_ENGINE_VERSION", "^1.1.0"),
        codegraph_root=Path(env("BAIRUI_CODEGRAPH_ROOT", "./data/codegraph")),
        codegraph_max_file_bytes=int(env("BAIRUI_CODEGRAPH_MAX_FILE_BYTES", "300000")),
        owner_token=env("BAIRUI_OWNER_TOKEN", ""),
        discord_bot_token=env("DISCORD_BOT_TOKEN", ""),
        feishu_verification_token=env("FEISHU_VERIFICATION_TOKEN", ""),
        feishu_app_id=env("FEISHU_APP_ID", ""),
        feishu_app_secret=env("FEISHU_APP_SECRET", ""),
        wechat_official_token=env("WECHAT_OFFICIAL_TOKEN", ""),
        wechat_official_app_id=env("WECHAT_OFFICIAL_APP_ID", ""),
        wechat_official_app_secret=env("WECHAT_OFFICIAL_APP_SECRET", ""),
        wecom_incoming_token=env("WECOM_INCOMING_TOKEN", ""),
        wecom_bot_key=env("WECOM_BOT_KEY", ""),
        qq_napcat_base_url=env("QQ_NAPCAT_BASE_URL", ""),
        qq_napcat_token=env("QQ_NAPCAT_TOKEN", ""),
    )


def ensure_runtime_dirs(settings: Settings) -> None:
    for path in (settings.data_dir, settings.log_dir, settings.obsidian_vault_dir, settings.everos_memory_root, settings.avatar_assets_dir, settings.codegraph_root):
        path.mkdir(parents=True, exist_ok=True)


def local_config_path(data_dir: Path | None = None) -> Path:
    base = data_dir or Path(os.getenv("HERMES_DATA_DIR", "./data/hermes"))
    return base / "local-config.json"


def _load_local_config(data_dir: Path) -> dict[str, Any]:
    path = local_config_path(data_dir)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    values = payload.get("values", {})
    return values if isinstance(values, dict) else {}
