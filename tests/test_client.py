from pathlib import Path
import zipfile

import pytest

from letterboxd_pipeline.client import _export_filename, extract_export


def test_export_filename_uses_safe_basename():
    assert _export_filename('attachment; filename="../export.zip"') == "export.zip"


def test_export_filename_falls_back_for_non_zip():
    assert _export_filename('attachment; filename="export.html"') == "letterboxd-export.zip"


def test_extract_export_extracts_files(tmp_path: Path):
    archive_path = tmp_path / "letterboxd-export.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("diary.csv", "Date,Name\n2025-01-01,Example\n")

    extract_dir = extract_export(archive_path)

    assert (extract_dir / "diary.csv").read_text() == "Date,Name\n2025-01-01,Example\n"


def test_extract_export_rejects_path_traversal(tmp_path: Path):
    archive_path = tmp_path / "letterboxd-export.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", "unsafe")

    with pytest.raises(RuntimeError, match="unsafe file path"):
        extract_export(archive_path)

    assert not (tmp_path / "outside.txt").exists()
