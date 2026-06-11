from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .config import Settings
from .storage import create_audit_event, utc_now


ALLOWED_AVATAR_STATES = ("idle", "thinking", "speaking", "approval_required", "error", "done", "hidden")
DEFAULT_STATE_MOTIONS = {
    "idle": "idle",
    "thinking": "thinking",
    "speaking": "talk",
    "approval_required": "attention",
    "error": "worried",
    "done": "happy",
    "hidden": "",
}


@dataclass(frozen=True)
class AvatarEngineStatus:
    status: str
    detail: str
    package: str
    version: str
    license: str
    source: str
    browser_runtime: str
    install_hint: str
    supports: tuple[str, ...]
    fallback_package: str


@dataclass(frozen=True)
class AvatarValidationResult:
    status: str
    model_path: str
    model_format: str
    missing_files: tuple[str, ...]
    warnings: tuple[str, ...]
    detected: dict[str, Any]


def avatar_engine_status(settings: Settings) -> AvatarEngineStatus:
    if settings.avatar_engine_package != "pixi-live2d-display-advanced":
        status = "custom_engine"
        detail = "Custom browser avatar engine is configured"
    else:
        status = "source_ready"
        detail = "Default browser avatar engine contract is ready for frontend integration"
    return AvatarEngineStatus(
        status=status,
        detail=detail,
        package=settings.avatar_engine_package,
        version=settings.avatar_engine_version,
        license="MIT",
        source="https://github.com/GuangChen2333/pixi-live2d-display-advanced",
        browser_runtime="PixiJS/WebGL",
        install_hint=f"npm install {settings.avatar_engine_package}@{settings.avatar_engine_version}",
        supports=("live2d_model3", "motions", "expressions", "audio_lipsync", "multi_motion", "state_mapping"),
        fallback_package="pixi-live2d-display",
    )


def _public_url(settings: Settings, path: Path) -> str:
    try:
        relative = path.resolve().relative_to(settings.avatar_assets_dir.resolve()).as_posix()
    except ValueError:
        relative = path.name
    if settings.avatar_public_base_url.strip():
        return f"{settings.avatar_public_base_url.rstrip('/')}/{relative}"
    return f"/avatars/assets/{relative}"


def _safe_model_path(settings: Settings, model_path: str) -> Path:
    raw = Path(model_path)
    if not raw.is_absolute():
        raw = settings.avatar_assets_dir / raw
    return raw.resolve()


def validate_avatar_model(settings: Settings, model_path: str) -> AvatarValidationResult:
    path = _safe_model_path(settings, model_path)
    warnings: list[str] = []
    missing_files: list[str] = []
    detected: dict[str, Any] = {"motions": (), "expressions": (), "textures": ()}

    if path.suffix not in {".json"}:
        warnings.append("model_manifest_should_be_json")
    if not path.exists():
        return AvatarValidationResult(
            status="not_found",
            model_path=str(path),
            model_format="unknown",
            missing_files=(str(path),),
            warnings=tuple(warnings),
            detected=detected,
        )

    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return AvatarValidationResult(
            status="invalid_manifest",
            model_path=str(path),
            model_format="unknown",
            missing_files=(),
            warnings=tuple(warnings),
            detected=detected,
        )

    model_format = "model3" if "FileReferences" in manifest or str(path.name).endswith(".model3.json") else "legacy"
    refs = manifest.get("FileReferences", {}) if isinstance(manifest.get("FileReferences"), dict) else {}
    moc = refs.get("Moc")
    if isinstance(moc, str) and not (path.parent / moc).exists():
        missing_files.append(moc)
    textures = tuple(str(item) for item in refs.get("Textures", ()) if isinstance(item, str))
    motions = refs.get("Motions", {}) if isinstance(refs.get("Motions"), dict) else {}
    expressions = tuple(str(item.get("File")) for item in refs.get("Expressions", ()) if isinstance(item, dict) and item.get("File"))

    for texture in textures:
        if not (path.parent / texture).exists():
            missing_files.append(texture)
    for motion_group in motions.values():
        if not isinstance(motion_group, list):
            continue
        for motion in motion_group:
            if isinstance(motion, dict) and motion.get("File") and not (path.parent / str(motion["File"])).exists():
                missing_files.append(str(motion["File"]))
    for expression in expressions:
        if not (path.parent / expression).exists():
            missing_files.append(expression)

    detected = {
        "motions": tuple(sorted(motions.keys())),
        "expressions": expressions,
        "textures": textures,
    }
    status = "valid" if not missing_files else "missing_assets"
    return AvatarValidationResult(
        status=status,
        model_path=str(path),
        model_format=model_format,
        missing_files=tuple(missing_files),
        warnings=tuple(warnings),
        detected=detected,
    )


def build_avatar_manifest(settings: Settings, avatar_id: str = "default", model_path: str = "") -> dict[str, Any]:
    model_ref = model_path or settings.avatar_default_model
    engine = avatar_engine_status(settings)
    validation: AvatarValidationResult | None = None
    model_url = ""
    if model_ref.strip():
        validation = validate_avatar_model(settings, model_ref)
        model_url = _public_url(settings, Path(validation.model_path))

    return {
        "avatar_id": avatar_id or "default",
        "brand": "bairui",
        "engine": asdict(engine),
        "model": {
            "configured": bool(model_ref.strip()),
            "path": str(_safe_model_path(settings, model_ref)) if model_ref.strip() else "",
            "url": model_url,
            "validation": asdict(validation) if validation else None,
        },
        "runtime": {
            "renderer": "browser",
            "webgl_required": True,
            "backend_renders_live2d": False,
            "audio_lipsync": {"enabled": True, "driver": "web_audio_amplitude"},
        },
        "state_map": {
            state: {"motion": motion, "expression": state if state not in {"hidden", "thinking"} else ""}
            for state, motion in DEFAULT_STATE_MOTIONS.items()
        },
        "created_at": utc_now(),
    }


def set_avatar_state(settings: Settings, payload: dict[str, Any]) -> dict[str, Any]:
    avatar_id = str(payload.get("avatar_id", "default") or "default")
    state = str(payload.get("state", "idle") or "idle")
    if state not in ALLOWED_AVATAR_STATES:
        return {
            "status": "invalid_state",
            "avatar_id": avatar_id,
            "state": state,
            "allowed_states": ALLOWED_AVATAR_STATES,
        }

    result = {
        "status": "accepted",
        "avatar_id": avatar_id,
        "state": state,
        "motion": str(payload.get("motion", DEFAULT_STATE_MOTIONS[state]) or DEFAULT_STATE_MOTIONS[state]),
        "expression": str(payload.get("expression", "") or ""),
        "text": str(payload.get("text", "") or ""),
        "audio_url": str(payload.get("audio_url", "") or ""),
        "lip_sync": bool(payload.get("lip_sync", state == "speaking")),
        "created_at": utc_now(),
    }
    create_audit_event(
        settings.data_dir,
        "avatar.state_changed",
        resource_type="avatar",
        resource_ref=avatar_id,
        risk_level="low",
        payload=result,
    )
    return result


def as_payload(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    return value
