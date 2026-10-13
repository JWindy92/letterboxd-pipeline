"""Parse Letterboxd diary CSV exports."""

import csv
import re
from datetime import date
from pathlib import Path


def load_diary(path: str | Path) -> list[dict]:
    """Load diary entries from a Letterboxd CSV export."""
    entries = []

    with Path(path).expanduser().open(newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            title = row["Name"].strip()
            year = int(row["Year"]) if row["Year"].strip() else None
            watched_date = row["Watched Date"].strip() or row["Date"].strip()

            if not title or not watched_date:
                continue

            uri = row["Letterboxd URI"].strip()
            rating = row["Rating"].strip()
            rewatch = row["Rewatch"].strip().lower()

            # Stable identifier based on the source URI and watch date.
            slug = uri.rstrip("/").split("/")[-1] or re.sub(r"\W+", "-", title.lower())

            entries.append(
                {
                    "title": title,
                    "year": year,
                    "watched_date": date.fromisoformat(watched_date).isoformat(),
                    "rating": float(rating) if rating else None,
                    "liked": None,
                    "rewatch": rewatch in {"yes", "true", "1"},
                    "letterboxd_url": uri or None,
                    "tmdb_id": None,
                    "guid": f"letterboxd-diary-{watched_date}-{slug}",
                }
            )

    return entries
