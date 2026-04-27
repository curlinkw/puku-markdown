from typing import NamedTuple


class CharSpan(NamedTuple):
    """A character-based span within a source document using half-open intervals."""

    start_charno: int
    """First character index in the span (inclusive)"""

    end_charno: int
    """Character index marking the end of the span (exclusive)"""

    @property
    def length(self) -> int:
        """
        Return the number of characters in this span (end_charno - start_charno).
        """
        return self.end_charno - self.start_charno

    def __contains__(self, charno: object) -> bool:
        """Check if character index falls within this span.

        The span uses half-open intervals: [start_charno, end_charno)

        Args:
            charno: Character index to check. Must be an int - non-int values
                will return False without raising TypeError.

        Returns:
            True if charno is an int and start_charno <= charno < end_charno,
            False otherwise (including when charno is not an int).

        Note:
            This method explicitly checks for int type and returns False for
            non-int inputs rather than raising TypeError, making it safe to
            use with heterogeneous containers.
        """
        return isinstance(charno, int) and self.start_charno <= charno < self.end_charno
