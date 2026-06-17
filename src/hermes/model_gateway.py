from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from .config import Settings


class ModelGatewayError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChatResult:
    status: str
    content: str
    model: str
    provider: str
    error: str = ""


@dataclass(frozen=True)
class ModelListResult:
    status: str
    base_url: str
    models: tuple[str, ...]
    error: str = ""


def model_gateway_status(settings: Settings) -> str:
    return "ready" if settings.has_model_gateway else "missing_config"


def build_chat_payload(settings: Settings, prompt: str, system: str = "") -> dict[str, Any]:
    messages: list[dict[str, str]] = []
    if system.strip():
        messages.append({"role": "system", "content": system.strip()})
    messages.append({"role": "user", "content": prompt.strip()})
    return {
        "model": settings.model_name,
        "messages": messages,
    }


def _chat_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/chat/completions"


def _models_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/models"


def list_models(
    settings: Settings,
    payload: dict[str, Any] | None = None,
    *,
    opener: Callable[[urllib.request.Request, int], Any] | None = None,
) -> ModelListResult:
    payload = payload or {}
    base_url = str(payload.get("base_url") or settings.model_base_url or "").strip()
    api_key = str(payload.get("api_key") or settings.model_api_key or "").strip()
    if not base_url:
        return ModelListResult(status="missing_config", base_url="", models=(), error="base_url is required")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(_models_url(base_url), headers=headers, method="GET")
    open_fn = opener or urllib.request.urlopen
    try:
        with open_fn(request, settings.model_timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return ModelListResult(status="failed", base_url=base_url, models=(), error=str(exc))

    raw_models = data.get("data", []) if isinstance(data, dict) else []
    models: list[str] = []
    for item in raw_models:
        if isinstance(item, dict):
            model_id = str(item.get("id") or "").strip()
        else:
            model_id = str(item or "").strip()
        if model_id and model_id not in models:
            models.append(model_id)
    return ModelListResult(status="completed", base_url=base_url, models=tuple(models))


def complete_chat(
    settings: Settings,
    prompt: str,
    *,
    system: str = "",
    opener: Callable[[urllib.request.Request, int], Any] | None = None,
) -> ChatResult:
    if not prompt.strip():
        raise ModelGatewayError("prompt is required")
    if not settings.has_model_gateway:
        return ChatResult(
            status="missing_config",
            content="",
            model=settings.model_name,
            provider=settings.model_base_url,
            error="BAIRUI_MODEL_BASE_URL, BAIRUI_MODEL_API_KEY, and BAIRUI_MODEL_NAME are required.",
        )

    body = json.dumps(build_chat_payload(settings, prompt, system), ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        _chat_url(settings.model_base_url),
        data=body,
        headers={
            "Authorization": f"Bearer {settings.model_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    open_fn = opener or urllib.request.urlopen
    try:
        with open_fn(request, settings.model_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return ChatResult(status="failed", content="", model=settings.model_name, provider=settings.model_base_url, error=str(exc))

    try:
        content = str(payload["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        return ChatResult(status="failed", content="", model=settings.model_name, provider=settings.model_base_url, error=f"invalid model response: {exc}")

    return ChatResult(status="completed", content=content, model=settings.model_name, provider=settings.model_base_url)
