import pytest

from datetime import date
from unittest.mock import Mock, patch

from letterboxd_pipeline.rss import (
    DEFAULT_FEED_URL,
    FilmEntry,
    fetch_feed,
)

RSS_XML = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"
     xmlns:lb="https://letterboxd.com"
     xmlns:tmdb="https://themoviedb.org">
  <channel>
    <title>Letterboxd - johnwid</title>
    <item>
      <title>The Sentinel, 1977 - ★★★★</title>
      <link>https://letterboxd.com/johnwid/film/the-sentinel/</link>
      <guid isPermaLink="false">letterboxd-watch-1531262249</guid>
      <lb:watchedDate>2026-10-10</lb:watchedDate>
      <lb:rewatch>No</lb:rewatch>
      <lb:filmTitle>The Sentinel</lb:filmTitle>
      <lb:filmYear>1977</lb:filmYear>
      <lb:memberRating>4.0</lb:memberRating>
      <lb:memberLike>Yes</lb:memberLike>
      <tmdb:movieId>18196</tmdb:movieId>
    </item>
  </channel>
</rss>
"""


def mock_response(content: bytes, status_code: int = 200) -> Mock:
    response = Mock()
    response.content = content
    response.status_code = status_code
    response.raise_for_status.return_value = None
    return response


@patch("letterboxd_pipeline.rss.requests.get")
def test_fetch_feed_parses_film_entry(mock_get):
    mock_get.return_value = mock_response(RSS_XML)

    entries = fetch_feed()

    assert len(entries) == 1
    assert entries[0] == FilmEntry(
        title="The Sentinel",
        year=1977,
        watched_date=date(2026, 10, 10),
        rating=4.0,
        liked=True,
        rewatch=False,
        letterboxd_url="https://letterboxd.com/johnwid/film/the-sentinel/",
        tmdb_id=18196,
        guid="letterboxd-watch-1531262249",
    )
    mock_get.assert_called_once_with(DEFAULT_FEED_URL, timeout=20)


@patch("letterboxd_pipeline.rss.requests.get")
def test_fetch_feed_handles_missing_optional_fields(mock_get):
    xml = b"""<rss version="2.0"
        xmlns:lb="https://letterboxd.com">
      <channel>
        <item>
          <link>https://letterboxd.com/johnwid/film/example/</link>
          <guid>watch-1</guid>
          <lb:filmTitle>Example</lb:filmTitle>
        </item>
      </channel>
    </rss>"""

    mock_get.return_value = mock_response(xml)

    entry = fetch_feed()[0]

    assert entry.title == "Example"
    assert entry.year is None
    assert entry.watched_date is None
    assert entry.rating is None
    assert entry.liked is False
    assert entry.rewatch is False
    assert entry.tmdb_id is None


@patch("letterboxd_pipeline.rss.requests.get")
def test_fetch_feed_handles_empty_feed(mock_get):
    mock_get.return_value = mock_response(
        b"<rss version='2.0'><channel></channel></rss>"
    )

    assert fetch_feed() == []


@patch("letterboxd_pipeline.rss.requests.get")
def test_fetch_feed_rejects_invalid_xml(mock_get):
    mock_get.return_value = mock_response(b"<rss><channel>")

    with pytest.raises(ValueError, match="invalid RSS XML"):
        fetch_feed()


def test_fetch_feed_rejects_non_letterboxd_url():
    with pytest.raises(ValueError, match="Feed URL"):
        fetch_feed("https://example.com/feed.xml")


@patch("letterboxd_pipeline.rss.requests.get")
def test_fetch_feed_propagates_http_errors(mock_get):
    response = Mock()
    response.raise_for_status.side_effect = Exception("HTTP error")
    mock_get.return_value = response

    with pytest.raises(Exception, match="HTTP error"):
        fetch_feed()
