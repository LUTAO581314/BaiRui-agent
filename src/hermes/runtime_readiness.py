from __future__ import annotations

from dataclasses import asdict, dataclass

from .avatar import avatar_engine_status
from .agents import list_agents
from .adapters.everos import status as everos_status
from .adapters.funasr import status as funasr_status
from .adapters.mineru import status as mineru_status
from .adapters.mirofish import status as mirofish_status
from .adapters.searxng import status as searxng_status
from .adapters.sonic import status as sonic_status
from .adapters.trendradar import status as trendradar_status
from .config import Settings
from .codegraph import codegraph_status


READY_STATES = {"configured"}
SOURCE_READY_STATES = {"source_ready"}
BLOCKING_STATES = {"missing_config", "missing_source", "invalid_source", "error", "http_error"}


@dataclass(frozen=True)
class RuntimeReadinessItem:
    name: str
    status: str
    required_for_usable: bool
    detail: str
    source: str
    license: str
    display_name: str
    display_detail: str
    public_source: str
    public_license: str


@dataclass(frozen=True)
class RuntimeReadiness:
    status: str
    summary: str
    items: tuple[RuntimeReadinessItem, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


def collect_runtime_readiness(settings: Settings) -> dict[str, object]:
    everos = everos_status(settings)
    funasr = funasr_status(settings)
    mineru = mineru_status(settings)
    trendradar = trendradar_status(settings)
    mirofish = mirofish_status(settings)
    searxng = searxng_status(settings)
    sonic = sonic_status(settings)
    avatar = avatar_engine_status(settings)
    codegraph = codegraph_status(settings)
    agents = list_agents(settings)

    items = (
        _item("everos_memory", everos.status, True, everos.detail, everos.source_path, everos.license),
        _item("funasr_voice_asr", funasr.status, False, funasr.detail, funasr.source, funasr.license),
        _item("mineru_document_parse", mineru.status, False, mineru.detail, mineru.source, mineru.license),
        _item("trendradar_intelligence", trendradar.status, False, trendradar.detail, trendradar.source_path, trendradar.license),
        _item("mirofish_simulation", mirofish.status, False, mirofish.detail, mirofish.source_path, mirofish.license),
        _item("searxng_metasearch", searxng.status, False, searxng.detail, searxng.source, searxng.license),
        _item("sonic_local_index", sonic.status, False, sonic.detail, sonic.source, sonic.license),
        _item("bairui_avatar_runtime", avatar.status, False, avatar.detail, avatar.source, avatar.license),
        _item("bairui_codegraph", codegraph.status, False, codegraph.detail, codegraph.root, "owned"),
        _item("bairui_agents", "ready", False, f"{len(agents)} governed agent profiles are available", "bairui", "owned"),
    )

    blockers = tuple(f"{item.display_name}: {item.display_detail}" for item in items if item.required_for_usable and item.status in BLOCKING_STATES)
    warnings = tuple(f"{item.display_name}: {item.display_detail}" for item in items if not item.required_for_usable and item.status in BLOCKING_STATES)

    if blockers:
        status = "blocked"
        summary = "Required runtime configuration is incomplete"
    elif any(item.status in SOURCE_READY_STATES for item in items):
        status = "partial"
        summary = "Required runtime source is present; optional runtimes may still need live service configuration"
    else:
        status = "ready"
        summary = "Runtime adapter configuration is complete"

    readiness = RuntimeReadiness(status=status, summary=summary, items=items, blockers=blockers, warnings=warnings)
    return asdict(readiness)


def _item(name: str, status: str, required: bool, detail: str, source: str, license_name: str) -> RuntimeReadinessItem:
    return RuntimeReadinessItem(
        name=name,
        status=status,
        required_for_usable=required,
        detail=detail,
        source=source,
        license=license_name,
        display_name=_display_name(name),
        display_detail=_public_text(detail),
        public_source=_public_source(source),
        public_license=_public_license(license_name),
    )


def _display_name(name: str) -> str:
    labels = {
        "everos_memory": "Memory runtime",
        "funasr_voice_asr": "Voice ASR",
        "mineru_document_parse": "Document parser",
        "trendradar_intelligence": "Intelligence radar",
        "mirofish_simulation": "Simulation lab",
        "searxng_metasearch": "Web search",
        "sonic_local_index": "Local index",
        "bairui_avatar_runtime": "Avatar state layer",
        "bairui_codegraph": "Code structure",
        "bairui_agents": "Multi-agent core",
    }
    return labels.get(name, name.replace("_", " ").title())


def _public_source(source: str) -> str:
    text = str(source or "")
    if not text:
        return ""
    if "vendor" in text or "runtimes" in text:
        return "managed runtime source"
    if text.startswith("http://") or text.startswith("https://"):
        return "configured runtime endpoint"
    return _public_text(text)


def _public_license(license_name: str) -> str:
    text = str(license_name or "")
    return "internal attribution required" if text and text != "owned" else text


def _public_text(value: str) -> str:
    replacements = (
        ("EverOS", "memory runtime"),
        ("FunASR", "voice ASR"),
        ("MinerU", "document parser"),
        ("TrendRadar", "intelligence radar"),
        ("MiroFish", "simulation lab"),
        ("SearXNG", "web search"),
        ("Sonic", "local index"),
        ("Obsidian", "memory vault"),
        ("Hermes", "bairui"),
        ("MOXI", "bairui"),
        ("Moxi", "bairui"),
        ("moxi", "bairui"),
        ("BaiLongma", "bairui"),
        ("Xiaobailong", "bairui"),
        ("白龙马", "bairui"),
        ("小白龙", "bairui"),
    )
    safe = str(value or "")
    for old, new in replacements:
        safe = safe.replace(old, new)
    return safe
