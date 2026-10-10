"""Fetch and parse a Letterboxd user's RSS activity feed."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlparse

import requests

LETTERBOXD_NS = "https://letterboxd.com"
TMDB_NS = "https://themoviedb.org"
DEFAULT_FEED_URL = "https://letterboxd.com/johnwid/rss/"


@dataclass(frozen=True)
class FilmEntry:
    title: str
    year: int | None
    watched_date: date | None
    rating: float | None
    liked: bool
    rewatch: bool
    letterboxd_url: str
    tmdb_id: int | None
    guid: str


def _text(item: ET.Element, tag: str) -> str | None:
    element = item.find(tag)
    return element.text.strip() if element is not None and element.text else None


def _integer(value: str | None) -> int | None:
    return int(value) if value else None


def _rating(value: str | None) -> float | None:
    return float(value) if value else None


def fetch_feed(
    feed_url: str = DEFAULT_FEED_URL,
    timeout: int = 20,
) -> list[FilmEntry]:
    """Fetch and parse recent activity from a Letterboxd RSS feed."""
    parsed_url = urlparse(feed_url)
    if parsed_url.scheme != "https" or parsed_url.hostname != "letterboxd.com":
        raise ValueError("Feed URL must use HTTPS on letterboxd.com.")

    response = requests.get(feed_url, timeout=timeout)
    response.raise_for_status()

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        raise ValueError("Letterboxd returned invalid RSS XML.") from exc

    entries = []
    for item in root.findall("./channel/item"):
        title = _text(item, f"{{{LETTERBOXD_NS}}}filmTitle")
        link = _text(item, "link")
        guid = _text(item, "guid")

        if not title or not link or not guid:
            continue

        watched = _text(item, f"{{{LETTERBOXD_NS}}}watchedDate")
        rating = _text(item, f"{{{LETTERBOXD_NS}}}memberRating")
        year = _text(item, f"{{{LETTERBOXD_NS}}}filmYear")
        liked = _text(item, f"{{{LETTERBOXD_NS}}}memberLike")
        rewatch = _text(item, f"{{{LETTERBOXD_NS}}}rewatch")
        tmdb_id = _text(item, f"{{{TMDB_NS}}}movieId")

        entries.append(
            FilmEntry(
                title=title,
                year=_integer(year),
                watched_date=date.fromisoformat(watched) if watched else None,
                rating=_rating(rating),
                liked=liked == "Yes",
                rewatch=rewatch == "Yes",
                letterboxd_url=link,
                tmdb_id=_integer(tmdb_id),
                guid=guid,
            )
        )

    return entries
