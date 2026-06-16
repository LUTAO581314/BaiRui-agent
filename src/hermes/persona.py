from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .config import Settings


DEFAULT_DISPLAY_NAME = "bairui"
DATA_URL_RE = re.compile(r"^data:image/(png|jpeg|jpg|webp|gif);base64,[A-Za-z0-9+/=\s]+$")


def persona_path(settings: Settings) -> Path:
    return settings.data_dir / "persona.json"


def load_persona(settings: Settings) -> dict[str, Any]:
    path = persona_path(settings)
    payload: dict[str, Any] = {}
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                payload = raw
        except (OSError, json.JSONDecodeError):
            payload = {}
    display_name = _normalize_display_name(payload.get("display_name", DEFAULT_DISPLAY_NAME))
    image_data_url = str(payload.get("image_data_url", "") or "")
    if image_data_url and not _valid_image_data_url(image_data_url):
        image_data_url = ""
    return {
        "brand": "bairui",
        "display_name": display_name,
        "image_data_url": image_data_url,
        "customized": display_name != DEFAULT_DISPLAY_NAME or bool(image_data_url),
        "storage": "server",
        "path": str(path.expanduser().resolve(strict=False)),
        "policy": "display_name and image only affect assistant persona; product brand remains bairui",
    }


def save_persona(settings: Settings, payload: dict[str, Any]) -> dict[str, Any]:
    display_name = _normalize_display_name(payload.get("display_name", DEFAULT_DISPLAY_NAME))
    image_data_url = str(payload.get("image_data_url", "") or "")
    if image_data_url and not _valid_image_data_url(image_data_url):
        return {
            "status": "invalid_request",
            "message": "image_data_url must be a png, jpeg, webp, or gif data URL",
            "brand": "bairui",
        }
    path = persona_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    saved = {
        "display_name": display_name,
        "image_data_url": image_data_url,
    }
    path.write_text(json.dumps(saved, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {"status": "saved", "persona": load_persona(settings)}


def _normalize_display_name(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if not text:
        return DEFAULT_DISPLAY_NAME
    return text[:24]


def _valid_image_data_url(value: str) -> bool:
    if len(value) > 1_200_000:
        return False
    return bool(DATA_URL_RE.match(value.strip()))
