"""Export Letterboxd RSS activity to JSON."""

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .rss import DEFAULT_FEED_URL, fetch_feed

DEFAULT_OUTPUT = Path("data/movies/raw/letterboxd/activity.json")


def export_activity(
    feed_url: str = DEFAULT_FEED_URL,
    output_path: str | Path = DEFAULT_OUTPUT,
) -> dict:
    """Fetch Letterboxd activity and write it to a JSON file."""
    output_path = Path(output_path).expanduser()
    entries = fetch_feed(feed_url)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = [
        {
            **asdict(entry),
            "watched_date": (
                entry.watched_date.isoformat()
                if isinstance(entry.watched_date, date)
                else None
            ),
        }
        for entry in entries
    ]

    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return {
        "status": "success",
        "entries": len(entries),
        "output_path": str(output_path.resolve()),
    }
