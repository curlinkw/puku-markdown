#!/usr/bin/env python3
"""Download CommonMark spec (JSON and plain text) for a given version."""

import argparse
import sys
from pathlib import Path
import requests

from tests.commonmark.spec import (
    _DEFAULT_VERSION,
    _DEFAULT_JSON_PATH,
    _DEFAULT_TEXT_PATH,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download CommonMark spec JSON and plain text"
    )
    parser.add_argument(
        "version",
        nargs="?",
        default=_DEFAULT_VERSION,
        help=f"CommonMark spec version (default: {_DEFAULT_VERSION})",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=_DEFAULT_JSON_PATH,
        help=f"Output path for JSON spec (default: {_DEFAULT_JSON_PATH})",
    )
    parser.add_argument(
        "--output-text",
        type=Path,
        default=_DEFAULT_TEXT_PATH,
        help=f"Output path for plain text spec (default: {_DEFAULT_TEXT_PATH})",
    )
    return parser.parse_args()


def download_if_changed(url: str, output_path: Path) -> None:
    """Download content from `url` and write to `output_path` only if different.

    Raises:
        requests.RequestException: on download error
        OSError: on write error
    """
    print(f"Downloading {url}")
    response = requests.get(url)
    response.raise_for_status()
    new_content = response.text

    if output_path.exists() and output_path.read_text() == new_content:
        print(f"File {output_path} is up to date, not overwriting")
    else:
        output_path.write_text(new_content)
        print(f"Updated {output_path}")


def main() -> None:
    args = parse_arguments()
    json_url = f"https://spec.commonmark.org/{args.version}/spec.json"
    text_url = f"https://raw.githubusercontent.com/commonmark/commonmark-spec/refs/tags/{args.version}/spec.txt"

    try:
        download_if_changed(json_url, args.output_json)
        download_if_changed(text_url, args.output_text)
    except (requests.RequestException, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)  # Success, regardless of whether files were updated


if __name__ == "__main__":
    main()
