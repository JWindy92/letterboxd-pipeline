"""Download and extract a Letterboxd account data export."""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://letterboxd.com"
DEFAULT_OUTPUT_DIR = Path("data/movies/raw/letterboxd")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/147.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class ExportResult:
    """Paths produced by a successful export run."""

    archive_path: Path
    extract_dir: Path


def get_csrf_token(session: requests.Session) -> str:
    """Fetch the login page and extract the hidden CSRF token."""
    response = session.get(f"{BASE_URL}/sign-in/", timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    token_input = soup.find("input", {"name": "__csrf"})
    if not token_input or not token_input.get("value"):
        raise RuntimeError("Could not find CSRF token on Letterboxd login page.")
    return str(token_input["value"])


def login(session: requests.Session, username: str, password: str) -> None:
    """Authenticate the session using Letterboxd's sign-in endpoint."""
    csrf = get_csrf_token(session)
    response = session.post(
        f"{BASE_URL}/user/login.do",
        data={"__csrf": csrf, "username": username, "password": password},
        headers={
            "Referer": f"{BASE_URL}/sign-in/",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
        },
        allow_redirects=True,
        timeout=15,
    )
    response.raise_for_status()

    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"Unexpected non-JSON login response (status {response.status_code})."
        ) from exc

    if result.get("result") != "success":
        # Do not include credentials or session details in the error.
        raise RuntimeError(f"Letterboxd login failed: {result.get('messages', 'unknown error')}")


def _export_filename(content_disposition: str) -> str:
    """Extract a safe basename from Content-Disposition, with a fallback."""
    match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', content_disposition, re.I)
    filename = unquote(match.group(1).strip()) if match else "letterboxd-export.zip"
    filename = Path(filename.replace("\\", "/")).name
    if not filename.lower().endswith(".zip"):
        filename = "letterboxd-export.zip"
    return filename or "letterboxd-export.zip"


def download_export(session: requests.Session, output_dir: Path) -> Path:
    """Download the export ZIP into output_dir."""
    response = session.get(
        f"{BASE_URL}/data/export/",
        headers={"Referer": f"{BASE_URL}/settings/data/"},
        stream=True,
        timeout=60,
    )
    response.raise_for_status()

    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / _export_filename(
        response.headers.get("content-disposition", "")
    )
    try:
        with destination.open("wb") as archive_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    archive_file.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    # Check the response was actually a ZIP rather than a login/error HTML page.
    if not zipfile.is_zipfile(destination):
        destination.unlink(missing_ok=True)
        raise RuntimeError("Letterboxd export response was not a valid ZIP archive.")

    return destination


def extract_export(archive_path: Path) -> Path:
    """Safely extract a ZIP, rejecting paths that escape the destination."""
    extract_dir = archive_path.parent / archive_path.stem
    extract_dir.mkdir(parents=True, exist_ok=True)
    base = extract_dir.resolve()

    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            target = (extract_dir / member.filename).resolve()
            if target != base and base not in target.parents:
                raise RuntimeError("Export archive contains an unsafe file path.")
        archive.extractall(extract_dir)

    return extract_dir


def run_export(
    username: str,
    password: str,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
) -> ExportResult:
    """Log in, download the export, and extract it.

    Credentials are supplied by the caller so this function can run from a CLI,
    tests, or an orchestrator such as Windmill without prompting.
    """
    if not username.strip():
        raise ValueError("Letterboxd username must not be empty.")
    if not password:
        raise ValueError("Letterboxd password must not be empty.")

    destination_dir = Path(output_dir).expanduser()
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    try:
        login(session, username, password)
        archive_path = download_export(session, destination_dir)
        extract_dir = extract_export(archive_path)
        return ExportResult(archive_path=archive_path, extract_dir=extract_dir)
    finally:
        session.close()
