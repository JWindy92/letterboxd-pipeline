"""Command-line entry point for local use."""

import getpass
import os
from pathlib import Path

from .client import DEFAULT_OUTPUT_DIR, run_export


def main() -> int:
    username = os.environ.get("LBOXD_USER") or input("Letterboxd username: ").strip()
    password = os.environ.get("LBOXD_PASS") or getpass.getpass("Letterboxd password: ")
    output_dir = Path(os.environ.get("LBOXD_OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR)))

    print("Logging in and downloading Letterboxd export...")
    try:
        result = run_export(username, password, output_dir)
    except Exception as exc:
        print(f"Export failed: {exc}")
        return 1

    print(f"Archive saved to: {result.archive_path}")
    print(f"Files extracted to: {result.extract_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
