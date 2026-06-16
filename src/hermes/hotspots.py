from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters.searxng import build_search_payload, search as searxng_search, status as searxng_status
from .adapters.trendradar import project_root as trendradar_project_root, status as trendradar_status
from .config import Settings


HOTSPOT_PLATFORM_MAP = {
    "douyin": ("douyin", "douyin_hot"),
    "xiaohongshu": ("xiaohongshu", "xhs"),
    "wechat": ("wechat", "wechat-hot", "wechat-hot-search"),
    "weibo": ("weibo",),
}
FALLBACK_PLATFORM_ORDER = ("baidu", "toutiao", "bilibili-hot-search", "zhihu", "wallstreetcn-hot")
HOTSPOT_SEARCH_QUERIES = {
    "douyin": "site:douyin.com 热点",
    "xiaohongshu": "site:xiaohongshu.com 热点",
    "wechat": "微信 热点",
    "weibo": "site:weibo.com 热搜",
}


@dataclass(frozen=True)
class HotspotItem:
    rank: int
    text: str
    heat: str
    trend: str = "same"
    isNew: bool = False
    url: str = ""
    source: str = ""


def build_hotspots(settings: Settings, *, force_refresh: bool = False) -> dict[str, Any]:
    trend_state = trendradar_status(settings)
    search_state = searxng_status(settings)
    platforms = {name: [] for name in HOTSPOT_PLATFORM_MAP}
    statuses: dict[str, dict[str, Any]] = {}

    trend_payload = _read_trendradar_hotspots(settings)
    for platform in platforms:
        items = trend_payload["platforms"].get(platform, [])
        platforms[platform] = items
        statuses[platform] = {
            "ok": bool(items),
            "source": "bairui intelligence" if items else "bairui intelligence unavailable",
            "detail": trend_payload["status"].get(platform, {}).get("detail", trend_state.detail),
        }

    if search_state.status == "configured":
        _merge_searxng_supplements(settings, platforms, statuses)

    fetched_at = trend_payload["fetchedAt"] or datetime.now(timezone.utc).isoformat()
    return {
        "service": "bairui",
        "source": "bairui-intelligence",
        "fetchedAt": fetched_at,
        "stale": trend_payload["stale"],
        "refreshMinutes": 30,
        "forceRefresh": force_refresh,
        "platforms": platforms,
        "status": statuses,
        "runtimes": {
            "primary_intelligence": {
                "status": trend_state.status,
                "detail": trend_state.detail,
                "license": trend_state.license,
            },
            "search_intelligence": {
                "status": search_state.status,
                "detail": search_state.detail,
                "license": search_state.license,
            },
        },
    }


def _read_trendradar_hotspots(settings: Settings) -> dict[str, Any]:
    db_path = _latest_trendradar_db(settings)
    payload = {
        "platforms": {name: [] for name in HOTSPOT_PLATFORM_MAP},
        "status": {},
        "fetchedAt": "",
        "stale": True,
    }
    if db_path is None:
        for platform in HOTSPOT_PLATFORM_MAP:
            payload["status"][platform] = {"ok": False, "detail": "TrendRadar output database not found"}
        return payload

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            available = _available_platform_ids(conn)
            for target, preferred_ids in HOTSPOT_PLATFORM_MAP.items():
                selected = next((pid for pid in preferred_ids if pid in available), "")
                if not selected:
                    selected = next((pid for pid in FALLBACK_PLATFORM_ORDER if pid in available), "")
                items = _read_platform_items(conn, selected) if selected else []
                payload["platforms"][target] = [item.__dict__ for item in items]
                payload["status"][target] = {
                    "ok": bool(items),
                    "source": "bairui intelligence",
                    "platformId": selected,
                    "detail": f"Loaded from {db_path.name}" if items else "No matching TrendRadar source data",
                }
            payload["fetchedAt"] = _latest_crawl_time(conn, db_path)
            payload["stale"] = True
    except sqlite3.Error as exc:
        for platform in HOTSPOT_PLATFORM_MAP:
            payload["status"][platform] = {"ok": False, "detail": f"TrendRadar SQLite read failed: {exc}"}
    return payload


def _latest_trendradar_db(settings: Settings) -> Path | None:
    root = trendradar_project_root(settings)
    news_dir = root / "output" / "news"
    if not news_dir.exists():
        return None
    dbs = sorted(news_dir.glob("*.db"), key=lambda path: path.stat().st_mtime, reverse=True)
    return dbs[0] if dbs else None


def _available_platform_ids(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT id FROM platforms WHERE is_active = 1").fetchall()
    return {str(row["id"]) for row in rows}


def _read_platform_items(conn: sqlite3.Connection, platform_id: str, *, limit: int = 10) -> list[HotspotItem]:
    if not platform_id:
        return []
    rows = conn.execute(
        """
        SELECT n.title, n.rank, n.url, n.crawl_count, n.first_crawl_time, n.last_crawl_time,
               p.name AS platform_name
        FROM news_items n
        JOIN platforms p ON p.id = n.platform_id
        WHERE n.platform_id = ?
        ORDER BY CASE WHEN n.rank > 0 THEN n.rank ELSE 9999 END ASC, n.updated_at DESC
        LIMIT ?
        """,
        (platform_id, limit),
    ).fetchall()
    items: list[HotspotItem] = []
    for idx, row in enumerate(rows):
        rank = int(row["rank"] or idx + 1)
        first_time = str(row["first_crawl_time"] or "")
        last_time = str(row["last_crawl_time"] or "")
        items.append(
            HotspotItem(
                rank=rank,
                text=str(row["title"] or ""),
                heat=f"{int(row['crawl_count'] or 1)}次",
                trend=_rank_trend(conn, str(row["title"] or ""), platform_id, rank),
                isNew=bool(first_time and first_time == last_time),
                url=str(row["url"] or ""),
                source=str(row["platform_name"] or platform_id),
            )
        )
    return items


def _rank_trend(conn: sqlite3.Connection, title: str, platform_id: str, current_rank: int) -> str:
    rows = conn.execute(
        """
        SELECT rh.rank
        FROM rank_history rh
        JOIN news_items n ON n.id = rh.news_item_id
        WHERE n.title = ? AND n.platform_id = ?
        ORDER BY rh.id DESC
        LIMIT 2
        """,
        (title, platform_id),
    ).fetchall()
    if len(rows) < 2:
        return "same"
    previous = int(rows[1]["rank"] or current_rank)
    if current_rank < previous:
        return "up"
    if current_rank > previous:
        return "down"
    return "same"


def _latest_crawl_time(conn: sqlite3.Connection, db_path: Path) -> str:
    row = conn.execute("SELECT crawl_time FROM crawl_records ORDER BY id DESC LIMIT 1").fetchone()
    value = str(row["crawl_time"]) if row and row["crawl_time"] else ""
    if value:
        normalized = value.replace("-", ":")
        return f"{db_path.stem}T{normalized}:00+08:00" if len(normalized) == 5 else normalized
    return datetime.fromtimestamp(db_path.stat().st_mtime, timezone.utc).isoformat()


def _merge_searxng_supplements(
    settings: Settings,
    platforms: dict[str, list[dict[str, Any]]],
    statuses: dict[str, dict[str, Any]],
) -> None:
    for platform, query in HOTSPOT_SEARCH_QUERIES.items():
        if len(platforms.get(platform, [])) >= 10:
            continue
        result = searxng_search(settings, build_search_payload(query=query, categories="general", page=1))
        if result.status != "completed" or not result.response:
            statuses.setdefault(platform, {})["search"] = result.status
            continue
        rows = result.response.get("results", [])
        if not isinstance(rows, list):
            continue
        existing = {item.get("text") for item in platforms.get(platform, [])}
        for row in rows:
            if not isinstance(row, dict):
                continue
            title = str(row.get("title") or "").strip()
            if not title or title in existing:
                continue
            platforms[platform].append(
                HotspotItem(
                    rank=len(platforms[platform]) + 1,
                    text=title,
                    heat="搜索",
                    trend="same",
                    url=str(row.get("url") or ""),
                    source="bairui search",
                ).__dict__
            )
            existing.add(title)
            if len(platforms[platform]) >= 10:
                break
        statuses.setdefault(platform, {})["search"] = "completed"
