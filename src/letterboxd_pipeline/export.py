"""Export Letterboxd RSS activity and diary history to JSON."""

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .backfill import load_diary
from .rss import DEFAULT_FEED_URL, fetch_feed

# TODO: Base location for outputs should be configurable via environment variable or config file
DEFAULT_OUTPUT = Path("data/movies/raw/letterboxd/activity.json")


def _dedup_key(entry: dict) -> tuple:
    return (
        entry["title"].strip().casefold(),
        entry["year"],
        entry["watched_date"],
    )


def export_activity(
    feed_url: str = DEFAULT_FEED_URL,
    output_path: str | Path = DEFAULT_OUTPUT,
    diary_path: str | Path | None = None,
) -> dict:
    """Fetch RSS activity, merge diary history, and write JSON."""
    output_path = Path(output_path).expanduser()

    if diary_path is None:
        diary_path = output_path.parent / "export" / "diary.csv"
    diary_path = Path(diary_path).expanduser()

    entries = [
        {
            **asdict(entry),
            "watched_date": (
                entry.watched_date.isoformat()
                if isinstance(entry.watched_date, date)
                else None
            ),
        }
        for entry in fetch_feed(feed_url)
    ]

    seen = {_dedup_key(entry) for entry in entries}

    if diary_path.exists():
        for entry in load_diary(diary_path):
            key = _dedup_key(entry)
            if key not in seen:
                entries.append(entry)
                seen.add(key)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return {
        "status": "success",
        "entries": len(entries),
        "output_path": str(output_path.resolve()),
    }
