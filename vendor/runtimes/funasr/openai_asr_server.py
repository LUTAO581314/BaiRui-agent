from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse
import whisper


def _env(name: str, default: str) -> str:
    value = os.getenv(name, "").strip()
    return value or default


MODEL_NAME = _env("ASR_MODEL", "tiny")
DEVICE = _env("ASR_DEVICE", "cpu")
COMPUTE_TYPE = _env("ASR_COMPUTE_TYPE", "int8")
DEFAULT_LANGUAGE = os.getenv("ASR_LANGUAGE", "").strip()
BEAM_SIZE = int(_env("ASR_BEAM_SIZE", "1"))

_MODEL_ALIASES = {
    "fun-asr-nano": "tiny",
    "sensevoice": "tiny",
    "paraformer": "tiny",
    "whisper-tiny": "tiny",
    "whisper-base": "base",
    "whisper-small": "small",
}

_LANGUAGE_ALIASES = {
    "zh-cn": "zh",
    "zh-tw": "zh",
    "zh-hans": "zh",
    "zh-hant": "zh",
    "en-us": "en",
    "en-gb": "en",
    "pt-br": "pt",
    "pt-pt": "pt",
}

app = FastAPI(title="bairui OpenAI-compatible ASR")
_whisper_model: Any | None = None


def _resolved_model_name(requested: str | None) -> str:
    value = (requested or MODEL_NAME).strip().lower()
    return _MODEL_ALIASES.get(value, value or "tiny")


def _get_model(requested: str | None = None) -> Any:
    global _whisper_model
    resolved = _resolved_model_name(requested)
    if _whisper_model is None or getattr(_whisper_model, "_bairui_model_name", None) != resolved:
        model = whisper.load_model(resolved, device=DEVICE)
        setattr(model, "_bairui_model_name", resolved)
        _whisper_model = model
    return _whisper_model


def _normalize_language_tag(value: str | None) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    normalized = raw.replace("_", "-").lower()
    if normalized in _LANGUAGE_ALIASES:
        return _LANGUAGE_ALIASES[normalized]
    if "-" in normalized:
        primary = normalized.split("-", 1)[0].strip()
        if primary:
            return _LANGUAGE_ALIASES.get(primary, primary)
    return normalized


@app.get("/health")
def health() -> dict[str, Any]:
    model = _get_model()
    return {
        "status": "ok",
        "engine": "openai-whisper",
        "model": getattr(model, "_bairui_model_name", MODEL_NAME),
        "device": DEVICE,
        "compute_type": COMPUTE_TYPE,
    }


@app.post("/v1/audio/transcriptions", response_model=None)
async def create_transcription(
    file: UploadFile = File(...),
    model: str = Form(""),
    language: str = Form(""),
    prompt: str = Form(""),
    response_format: str = Form("json"),
):
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(prefix="bairui-asr-", suffix=suffix, delete=False) as tmp:
        temp_path = Path(tmp.name)
        tmp.write(await file.read())

    try:
        whisper = _get_model(model)
        requested_language = _normalize_language_tag(language or DEFAULT_LANGUAGE)
        result = whisper.transcribe(
            str(temp_path),
            language=requested_language,
            initial_prompt=(prompt or None),
            beam_size=BEAM_SIZE,
        )
        text = str(result.get("text", "")).strip()
        rows = result.get("segments") or []
        resolved_model = getattr(whisper, "_bairui_model_name", _resolved_model_name(model))
        if response_format == "text":
            return PlainTextResponse(text)
        payload: dict[str, Any] = {
            "text": text,
            "language": result.get("language", ""),
            "duration": result.get("duration"),
            "model": resolved_model,
            "engine": "openai-whisper",
        }
        if response_format == "verbose_json":
            payload["segments"] = [
                {
                    "id": segment.get("id", index),
                    "start": segment.get("start"),
                    "end": segment.get("end"),
                    "text": segment.get("text", ""),
                }
                for index, segment in enumerate(rows)
            ]
        return JSONResponse(payload)
    except ValueError as exc:
        return JSONResponse(
            {
                "error": {
                    "type": "transcription_value_error",
                    "message": str(exc),
                    "language": _normalize_language_tag(language or DEFAULT_LANGUAGE) or "",
                    "model": _resolved_model_name(model),
                    "engine": "openai-whisper",
                }
            },
            status_code=400,
        )
    except Exception as exc:
        return JSONResponse(
            {
                "error": {
                    "type": "transcription_failed",
                    "message": str(exc),
                    "language": _normalize_language_tag(language or DEFAULT_LANGUAGE) or "",
                    "model": _resolved_model_name(model),
                    "engine": "openai-whisper",
                }
            },
            status_code=500,
        )
    finally:
        temp_path.unlink(missing_ok=True)
