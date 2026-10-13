import json
from datetime import date
from unittest.mock import patch

from letterboxd_pipeline.export import export_activity
from letterboxd_pipeline.rss import FilmEntry


def test_export_activity_merges_rss_and_diary(tmp_path):
    output_path = tmp_path / "activity.json"
    diary_path = tmp_path / "export" / "diary.csv"
    diary_path.parent.mkdir()

    diary_path.write_text(
        "Date,Name,Year,Letterboxd URI,Rating,Rewatch,Tags,Watched Date\n"
        "2026-10-10,The Sentinel,1977,"
        "https://boxd.it/example,4,,"
        ",2026-10-10\n"
        "2023-01-04,The Black Phone,2021,"
        "https://boxd.it/other,3,No,,2023-01-03\n",
        encoding="utf-8",
    )

    rss_entry = FilmEntry(
        title="The Sentinel",
        year=1977,
        watched_date=date(2026, 10, 10),
        rating=4.0,
        liked=True,
        rewatch=False,
        letterboxd_url=("https://letterboxd.com/johnwid/film/the-sentinel/"),
        tmdb_id=18196,
        guid="letterboxd-watch-1531262249",
    )

    with patch(
        "letterboxd_pipeline.export.fetch_feed",
        return_value=[rss_entry],
    ):
        result = export_activity(
            output_path=output_path,
            diary_path=diary_path,
        )

    entries = json.loads(output_path.read_text(encoding="utf-8"))
    print(output_path)
    print(json.dumps(entries, indent=2))

    # RSS entry is retained; duplicate diary entry is removed.
    assert len(entries) == 2
    assert entries[0]["guid"] == "letterboxd-watch-1531262249"

    # Older diary entry is added.
    assert entries[1]["title"] == "The Black Phone"
    assert entries[1]["watched_date"] == "2023-01-03"
    assert entries[1]["rating"] == 3.0
    assert entries[1]["tmdb_id"] is None

    assert result["status"] == "success"
    assert result["entries"] == 2
    assert result["output_path"] == str(output_path.resolve())


def test_export_activity_without_diary(tmp_path):
    output_path = tmp_path / "activity.json"
    rss_entry = FilmEntry(
        title="Example",
        year=2020,
        watched_date=None,
        rating=None,
        liked=False,
        rewatch=False,
        letterboxd_url="https://letterboxd.com/film/example/",
        tmdb_id=None,
        guid="watch-1",
    )

    with patch(
        "letterboxd_pipeline.export.fetch_feed",
        return_value=[rss_entry],
    ):
        result = export_activity(output_path=output_path)

    entries = json.loads(output_path.read_text(encoding="utf-8"))

    assert len(entries) == 1
    assert entries[0]["title"] == "Example"
    assert result["entries"] == 1
