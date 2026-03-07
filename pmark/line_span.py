from typing import NamedTuple


class LineSpan(NamedTuple):
    """A line-based span within a source document."""

    start_lineno: int
    end_lineno: int
