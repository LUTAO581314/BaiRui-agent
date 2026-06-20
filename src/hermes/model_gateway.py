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


@dataclass(frozen=True)
class ModelProbeResult:
    status: str
    base_url: str
    model: str
    models: tuple[str, ...]
    chat_status: str
    detail: str
    error: str = ""
    secret_echo: bool = False


def model_gateway_status(settings: Settings) -> str:
    return "ready" if settings.has_model_gateway else "missing_config"


def build_chat_payload(settings: Settings, prompt: str, system: str = "", *, model: str = "") -> dict[str, Any]:
    messages: list[dict[str, str]] = []
    if system.strip():
        messages.append({"role": "system", "content": system.strip()})
    messages.append({"role": "user", "content": prompt.strip()})
    return {
        "model": model or settings.model_name,
        "messages": messages,
    }


def _chat_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/chat/completions"


def _models_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/models"


def _candidate_base_urls(base_url: str) -> tuple[str, ...]:
    normalized = base_url.strip().rstrip("/")
    if not normalized:
        return ()
    candidates = [normalized]
    if not normalized.endswith("/v1"):
        candidates.append(normalized + "/v1")
    seen: list[str] = []
    for item in candidates:
        if item not in seen:
            seen.append(item)
    return tuple(seen)


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
    open_fn = opener or urllib.request.urlopen
    last_error = ""
    for candidate_base_url in _candidate_base_urls(base_url):
        request = urllib.request.Request(_models_url(candidate_base_url), headers=headers, method="GET")
        try:
            with open_fn(request, timeout=settings.model_timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
            base_url = candidate_base_url
            break
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            _close_http_error(exc)
            last_error = str(exc)
    else:
        return ModelListResult(status="failed", base_url=base_url, models=(), error=last_error or "failed to list models")

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
    base_url: str = "",
    api_key: str = "",
    model: str = "",
    opener: Callable[[urllib.request.Request, int], Any] | None = None,
) -> ChatResult:
    if not prompt.strip():
        raise ModelGatewayError("prompt is required")
    resolved_base_url = base_url.strip() or settings.model_base_url
    resolved_api_key = api_key.strip() or settings.model_api_key
    resolved_model = model.strip() or settings.model_name
    if not (resolved_base_url.strip() and resolved_api_key.strip() and resolved_model.strip()):
        return ChatResult(
            status="missing_config",
            content="",
            model=resolved_model,
            provider=resolved_base_url,
            error="BAIRUI_MODEL_BASE_URL, BAIRUI_MODEL_API_KEY, and BAIRUI_MODEL_NAME are required.",
        )

    body = json.dumps(build_chat_payload(settings, prompt, system, model=resolved_model), ensure_ascii=False).encode("utf-8")
    open_fn = opener or urllib.request.urlopen
    payload: dict[str, Any] | None = None
    provider = resolved_base_url
    last_error = ""
    for candidate_base_url in _candidate_base_urls(resolved_base_url):
        request = urllib.request.Request(
            _chat_url(candidate_base_url),
            data=body,
            headers={
                "Authorization": f"Bearer {resolved_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with open_fn(request, timeout=settings.model_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            provider = candidate_base_url
            break
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            _close_http_error(exc)
            last_error = str(exc)
    if payload is None:
        return ChatResult(status="failed", content="", model=resolved_model, provider=provider, error=last_error or "failed to complete chat")

    try:
        content = str(payload["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        return ChatResult(status="failed", content="", model=resolved_model, provider=provider, error=f"invalid model response: {exc}")
    if not content.strip():
        finish_reason = ""
        try:
            finish_reason = str(payload["choices"][0].get("finish_reason", ""))
        except (KeyError, IndexError, TypeError, AttributeError):
            finish_reason = ""
        detail = "model returned empty content"
        if finish_reason:
            detail = f"{detail}; finish_reason={finish_reason}"
        return ChatResult(status="failed", content="", model=resolved_model, provider=provider, error=detail)

    return ChatResult(status="completed", content=content, model=resolved_model, provider=provider)


def probe_model_gateway(
    settings: Settings,
    payload: dict[str, Any] | None = None,
    *,
    opener: Callable[[urllib.request.Request, int], Any] | None = None,
) -> ModelProbeResult:
    payload = payload or {}
    base_url = str(payload.get("base_url") or settings.model_base_url or "").strip()
    api_key = str(payload.get("api_key") or settings.model_api_key or "").strip()
    requested_model = str(payload.get("model") or settings.model_name or "").strip()
    prompt = str(payload.get("prompt") or "Reply exactly: bairui-ok").strip()
    system = str(payload.get("system") or "You are a bairui model gateway connectivity probe.").strip()

    models_result = list_models(settings, {"base_url": base_url, "api_key": api_key}, opener=opener)
    model = requested_model
    if not model and models_result.models:
        model = models_result.models[0]
    if not base_url:
        return ModelProbeResult(
            status="missing_config",
            base_url="",
            model=model,
            models=models_result.models,
            chat_status="missing_config",
            detail="Base URL is required.",
            error=models_result.error,
        )
    if not api_key:
        return ModelProbeResult(
            status="missing_config",
            base_url=models_result.base_url or base_url,
            model=model,
            models=models_result.models,
            chat_status="missing_config",
            detail="API key is required.",
            error=models_result.error,
        )
    if not model:
        return ModelProbeResult(
            status="missing_config",
            base_url=models_result.base_url or base_url,
            model="",
            models=models_result.models,
            chat_status="missing_config",
            detail="Model name is required.",
            error=models_result.error,
        )

    candidate_models = _probe_candidate_models(model, models_result.models)
    chat = None
    errors: list[str] = []
    for candidate_model in candidate_models:
        chat = complete_chat(settings, prompt, system=system, base_url=base_url, api_key=api_key, model=candidate_model, opener=opener)
        if chat.status == "completed":
            model = candidate_model
            break
        errors.append(f"{candidate_model}: {chat.error or chat.status}")
    status = "ready" if chat and chat.status == "completed" else "blocked"
    diagnostic = _summarize_probe_errors(errors)
    detail = (
        "Model gateway listed models and returned non-empty chat content."
        if status == "ready"
        else diagnostic["detail"]
    )
    return ModelProbeResult(
        status=status,
        base_url=(chat.provider if chat else "") or models_result.base_url or base_url,
        model=model,
        models=models_result.models,
        chat_status=chat.status if chat else "missing_config",
        detail=detail,
        error="" if status == "ready" else diagnostic["error"] or (models_result.error or "chat probe failed"),
    )


def _summarize_probe_errors(errors: list[str]) -> dict[str, str]:
    if not errors:
        return {
            "detail": "Model list may be reachable, but chat probe did not return usable content.",
            "error": "",
        }
    upstream_unavailable = [item for item in errors if "HTTP Error 503" in item or "Service Unavailable" in item]
    if upstream_unavailable and len(upstream_unavailable) == len(errors):
        sample = "; ".join(upstream_unavailable[:3])
        suffix = f"; {len(upstream_unavailable) - 3} more models also returned 503" if len(upstream_unavailable) > 3 else ""
        return {
            "detail": "Model gateway listed models, but the upstream chat service is unavailable or overloaded.",
            "error": f"upstream_service_unavailable: {sample}{suffix}",
        }
    unauthorized = [item for item in errors if "HTTP Error 401" in item or "Unauthorized" in item or "HTTP Error 403" in item]
    if unauthorized:
        return {
            "detail": "Model gateway rejected the API key or account permission for chat completions.",
            "error": "auth_or_permission_failed: " + "; ".join(unauthorized[:3]),
        }
    sample = "; ".join(errors[:5])
    suffix = f"; {len(errors) - 5} more model errors omitted" if len(errors) > 5 else ""
    return {
        "detail": "Model list may be reachable, but chat probe did not return usable content.",
        "error": f"{sample}{suffix}",
    }


def _close_http_error(exc: BaseException) -> None:
    if isinstance(exc, urllib.error.HTTPError):
        try:
            exc.close()
        except OSError:
            pass


def _probe_candidate_models(requested_model: str, models: tuple[str, ...]) -> tuple[str, ...]:
    preferred = (
        requested_model,
        "gpt-5.5-openai-compact",
        "gpt-5.4",
        "gpt-5.2-chat-latest",
        "gpt-5-chat-latest",
        "gpt-4.1",
        "gpt-4o",
    )
    candidates: list[str] = []
    available = set(models)
    for item in preferred:
        if item and item not in candidates and (not available or item in available):
            candidates.append(item)
    for item in models:
        if item and item not in candidates:
            candidates.append(item)
    return tuple(candidates)
