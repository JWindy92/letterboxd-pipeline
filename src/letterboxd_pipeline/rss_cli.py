"""CLI for exporting Letterboxd RSS activity as JSON."""

import os
import sys

from .export import DEFAULT_OUTPUT, export_activity
from .rss import DEFAULT_FEED_URL


def main() -> int:
    feed_url = os.environ.get("LBOXD_RSS_URL", DEFAULT_FEED_URL)
    output_path = os.environ.get("LBOXD_RSS_OUTPUT", str(DEFAULT_OUTPUT))

    try:
        result = export_activity(feed_url, output_path)
    except Exception as exc:
        print(f"RSS export failed: {exc}", file=sys.stderr)
        return 1

    print(f"Saved {result['entries']} entries to: {result['output_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
