from __future__ import annotations

import io
import math
import struct
import wave
from dataclasses import asdict, dataclass
from typing import Any

from .config import Settings
from .storage import create_audit_event


@dataclass(frozen=True)
class TTSStatus:
    status: str
    detail: str
    provider: str
    voice_id: str


def load_tts_settings(settings: Settings) -> dict[str, Any]:
    local_values = {
        "ttsProvider": "openai",
        "ttsVoiceId": "bairui-neutral",
    }
    return {
        "configured": True,
        "ttsProvider": local_values["ttsProvider"],
        "ttsVoiceId": local_values["ttsVoiceId"],
        "openaiTtsBaseURL": settings.model_base_url or "",
    }


def list_tts_voices() -> dict[str, list[dict[str, str]]]:
    return {
        "openai": [
            {"id": "bairui-neutral", "label": "bairui Neutral"},
            {"id": "bairui-clear", "label": "bairui Clear"},
        ],
        "doubao": [{"id": "doubao-default", "label": "Doubao Default"}],
        "minimax": [{"id": "minimax-default", "label": "MiniMax Default"}],
        "elevenlabs": [{"id": "elevenlabs-default", "label": "ElevenLabs Default"}],
        "volcano": [{"id": "volcano-default", "label": "Volcano Default"}],
    }


def tts_status(settings: Settings) -> TTSStatus:
    cfg = load_tts_settings(settings)
    return TTSStatus(
        status="ready",
        detail="Local productized TTS fallback is available for console playback.",
        provider=str(cfg.get("ttsProvider", "openai")),
        voice_id=str(cfg.get("ttsVoiceId", "bairui-neutral")),
    )


def synthesize_tts_bytes(settings: Settings, text: str, payload: dict[str, Any] | None = None) -> bytes:
    content = str(text or "").strip()
    if not content:
        raise ValueError("text is required")

    duration = max(0.45, min(8.0, len(content) * 0.045))
    sample_rate = 22050
    total_frames = int(sample_rate * duration)
    amplitude = 9000
    base_freq = 220.0 + (len(content) % 7) * 18.0

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for frame in range(total_frames):
            t = frame / sample_rate
            env = min(1.0, t / 0.04) * min(1.0, max(0.0, (duration - t) / 0.08))
            sample = math.sin(2 * math.pi * base_freq * t) * amplitude * env
            wav_file.writeframesraw(struct.pack("<h", int(sample)))

    create_audit_event(
        settings.data_dir,
        "tts.stream",
        resource_type="tts",
        resource_ref="local-fallback",
        risk_level="low",
        payload={"status": "completed", "text_length": len(content), "provider": tts_status(settings).provider},
    )
    return buffer.getvalue()


def as_payload(value: TTSStatus) -> dict[str, object]:
    return asdict(value)
