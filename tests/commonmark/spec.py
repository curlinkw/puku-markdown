"""Access to CommonMark specification test data.

This module loads the official CommonMark spec examples from a JSON file
(commonmark.json) and provides immutable, typed access to the test cases.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_DEFAULT_VERSION = "0.31.2"
_DEFAULT_JSON_PATH = Path(__file__).parent / "spec.json"
_DEFAULT_TEXT_PATH = Path(__file__).parent / "spec.md"


@dataclass(slots=True, frozen=True)
class SpecExample:
    """A single test example from the CommonMark specification.

    Attributes:
        markdown: The input Markdown text.
        html: The expected HTML output.
        example: The example number (unique identifier).
        start_line: Line number in the spec where the example starts.
        end_line: Line number in the spec where the example ends.
        section: The specification section name (e.g., "Tabs", "Code spans").
    """

    markdown: str
    html: str
    example: int
    start_line: int
    end_line: int
    section: str


@lru_cache(maxsize=1)
def _load_raw_examples(json_path: Path) -> list[dict]:
    """Load the raw JSON list from the given path.

    Args:
        json_path: Path to the commonmark.json file.

    Returns:
        List of dictionaries as read from the JSON file.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with json_path.open(encoding="utf-8") as f:
        return json.load(f)


def _create_example_from_dict(raw: dict) -> SpecExample:
    """Convert a raw dictionary to a SpecExample dataclass."""
    return SpecExample(
        markdown=raw["markdown"],
        html=raw["html"],
        example=raw["example"],
        start_line=raw["start_line"],
        end_line=raw["end_line"],
        section=raw["section"],
    )


# ----------------------------------------------------------------------
# Public API
def get_all_examples(json_path: Path | None = None) -> tuple[SpecExample, ...]:
    """Return all spec examples as an immutable tuple of frozen dataclasses.

    The result is cached after the first call. Use `json_path` to override
    the default JSON location for this call only.

    Args:
        json_path: Optional path to the commonmark.json file. If omitted,
            the module's default path is used (can be set via environment
            variable COMMONMARK_SPEC_JSON).

    Returns:
        A tuple of SpecExample objects, one per example in the spec.

    Example:
        >>> from tests.spec import get_all_examples
        >>> examples = get_all_examples()
        >>> len(examples)
        650
        >>> examples[0].markdown
        '\\tfoo\\tbaz\\t\\tbim\\n'
    """
    path = json_path if json_path is not None else _DEFAULT_JSON_PATH
    raw_list = _load_raw_examples(path)
    return tuple(_create_example_from_dict(raw) for raw in raw_list)
