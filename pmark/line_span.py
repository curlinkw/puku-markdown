from typing import NamedTuple


class LineSpan(NamedTuple):
    """A line-based span within a source document using half-open intervals."""

    start_lineno: int
    """First line number in the span (inclusive)"""

    end_lineno: int
    """Line number marking the end of the span (exclusive)"""

    def __contains__(self, lineno: object) -> bool:
        """Check if line number falls within this span.

        The span uses half-open intervals: [start_lineno, end_lineno)

        Args:
            lineno: Line number to check. Must be an int - non-int values
                will return False without raising TypeError.

        Returns:
            True if lineno is an int and start_lineno <= lineno < end_lineno,
            False otherwise (including when lineno is not an int).

        Note:
            This method explicitly checks for int type and returns False for
            non-int inputs rather than raising TypeError, making it safe to
            use with heterogeneous containers.
        """
        return isinstance(lineno, int) and self.start_lineno <= lineno < self.end_lineno
