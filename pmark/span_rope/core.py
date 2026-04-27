from pmark.char_span import CharSpan


class SpanRope:
    """A append-only rope of character spans from a source document."""

    def __init__(self) -> None:
        """Initialize an empty SpanRope."""

        self._char_spans: list[CharSpan] = []
        """List of character spans in order"""

        self._prefix_lengths: list[int] = []
        """Cumulative character length after each span"""

    def append(self, char_span: CharSpan) -> None:
        """Append a character span to the end of the rope.

        The total length of the rope increases by `len(char_span)`.

        Args:
            char_span: The span to add. Must be a valid `CharSpan`
                (non-negative start and end with start < end).

        Note:
            The rope does not validate that spans are contiguous or non-overlapping;
            that is the caller's responsibility.
        """
        self._char_spans.append(char_span)
        self._prefix_lengths.append(len(self) + char_span.length)

    def __len__(self) -> int:
        """Return the total number of characters represented by the rope.

        Returns:
            The sum of the lengths of all appended `CharSpan` objects,
            or 0 if the rope is empty.
        """
        return self._prefix_lengths[-1] if self._prefix_lengths else 0

    @property
    def start_charno(self) -> int:
        """Return the source character index of the first character in the rope.

        This is equivalent to `self._char_spans[0].start_charno`.

        Raises:
            ValueError: If the rope contains no spans (empty).
        """
        if not self._char_spans:
            raise ValueError("Cannot get start_charno of an empty SpanRope")

        return self._char_spans[0].start_charno

    @property
    def end_charno(self) -> int:
        """Return the source character index immediately after the last character in the rope.

        This is equivalent to `self._char_spans[-1].end_charno`.

        Raises:
            ValueError: If the rope contains no spans (empty).
        """
        if not self._char_spans:
            raise ValueError("Cannot get end_charno of an empty SpanRope")

        return self._char_spans[-1].end_charno

    def logical_offset_of(self, span_index: int, charno: int) -> int:
        """Return the logical character offset (0-based) within the rope's concatenated string.

        The offset corresponds to the position of the source character `charno`
        which belongs to the span at `span_index`. The method assumes:
        - `span_index` is valid (0 <= span_index < len(self._char_spans))
        - `charno` is within the half-open interval [`self._char_spans[span_index].start_charno`,
            `self._char_spans[span_index].end_charno`).

        Args:
            span_index: Index of the span containing the character.
            charno: Absolute source character index (must lie inside the specified span).

        Returns:
            The logical offset from the start of the rope (0-based).
        """
        return self._prefix_lengths[span_index] - (
            self._char_spans[span_index].end_charno - charno
        )

    def get_span(self, index: int) -> CharSpan:
        """Return the CharSpan at the given index (0-based)."""
        return self._char_spans[index]

    @property
    def span_count(self) -> int:
        """Return the number of CharSpan objects in the rope."""
        return len(self._char_spans)
