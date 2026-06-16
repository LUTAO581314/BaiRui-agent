from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Settings


WIKILINK_RE = re.compile(r"(?<!!)\[\[([^\]\n]+)\]\]")
FRONTMATTER_TITLE_RE = re.compile(r"(?m)^title:\s*[\"']?(.+?)[\"']?\s*$")


@dataclass(frozen=True)
class ObsidianGraphNode:
    id: str
    mem_id: str
    title: str
    content: str
    kind: str
    event_type: str
    entities: tuple[str, ...]
    path: str
    unresolved: bool = False


@dataclass(frozen=True)
class ObsidianGraphLink:
    source: str
    target: str
    relation: str
    label: str


def build_obsidian_graph(settings: Settings, *, limit: int = 240) -> dict[str, Any]:
    """Build a frontend graph from the Obsidian vault's native Markdown wiki links."""

    root = settings.obsidian_vault_dir.expanduser().resolve(strict=False)
    if not root.exists():
        return {
            "status": "missing_config",
            "root": str(root),
            "nodes": [],
            "links": [],
            "note_count": 0,
            "link_count": 0,
            "detail": "Obsidian vault directory does not exist",
        }

    files = sorted(
        (path for path in root.rglob("*.md") if path.is_file() and ".obsidian" not in path.parts),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )[: max(1, limit)]

    nodes: dict[str, ObsidianGraphNode] = {}
    stem_index: dict[str, str] = {}
    path_index: dict[str, str] = {}

    for path in files:
        relative = path.relative_to(root).as_posix()
        node_id = _node_id(relative)
        title = _note_title(path)
        nodes[node_id] = ObsidianGraphNode(
            id=node_id,
            mem_id=node_id,
            title=title,
            content=relative,
            kind="obsidian_note",
            event_type="obsidian_note",
            entities=("obsidian:vault", "memory:note"),
            path=relative,
        )
        stem_index.setdefault(path.stem.lower(), node_id)
        path_index.setdefault(relative.removesuffix(".md").lower(), node_id)

    links: list[ObsidianGraphLink] = []
    seen_links: set[tuple[str, str, str]] = set()

    for path in files:
        source_id = _node_id(path.relative_to(root).as_posix())
        text = _safe_read(path)
        for raw_target in _extract_wikilinks(text):
            target_id = _resolve_link(raw_target, stem_index, path_index)
            if target_id is None:
                target_id = _unresolved_id(raw_target)
                nodes.setdefault(
                    target_id,
                    ObsidianGraphNode(
                        id=target_id,
                        mem_id=target_id,
                        title=raw_target,
                        content="unresolved Obsidian wikilink",
                        kind="obsidian_unresolved",
                        event_type="obsidian_unresolved",
                        entities=("obsidian:vault", "memory:unresolved"),
                        path="",
                        unresolved=True,
                    ),
                )
            link_key = (source_id, target_id, "wikilink")
            if source_id == target_id or link_key in seen_links:
                continue
            seen_links.add(link_key)
            links.append(ObsidianGraphLink(source=source_id, target=target_id, relation="wikilink", label=raw_target))

    node_rows = [node.__dict__ for node in nodes.values()]
    link_rows = [link.__dict__ for link in links]
    return {
        "status": "ready" if node_rows else "empty",
        "root": str(root),
        "nodes": node_rows,
        "links": link_rows,
        "note_count": len(files),
        "link_count": len(link_rows),
        "detail": "Obsidian vault wikilink graph",
    }


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _note_title(path: Path) -> str:
    text = _safe_read(path)[:2000]
    match = FRONTMATTER_TITLE_RE.search(text)
    if match:
        return match.group(1).strip()[:120] or path.stem
    return path.stem


def _extract_wikilinks(text: str) -> list[str]:
    targets: list[str] = []
    for match in WIKILINK_RE.finditer(text):
        raw = match.group(1).split("|", 1)[0].split("#", 1)[0].strip()
        if raw:
            targets.append(raw.removesuffix(".md"))
    return targets


def _resolve_link(target: str, stem_index: dict[str, str], path_index: dict[str, str]) -> str | None:
    normalized = target.strip().replace("\\", "/").removesuffix(".md").lower()
    return path_index.get(normalized) or stem_index.get(Path(normalized).name)


def _node_id(relative: str) -> str:
    return "obsidian:" + relative.removesuffix(".md").replace("\\", "/")


def _unresolved_id(target: str) -> str:
    normalized = re.sub(r"\s+", " ", target.strip())[:160]
    return "obsidian:unresolved:" + normalized
