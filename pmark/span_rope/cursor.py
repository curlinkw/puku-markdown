from typing import Self

from pmark.span_rope.core import SpanRope


class SpanRopeCursor:
    """
    A cursor that traverses a `SpanRope` and provides the current source character index.
    """

    def __init__(self, rope: SpanRope, span_index: int, charno: int) -> None:
        """
        Initialize a new cursor at a specific span and source character.
        """

        self._rope: SpanRope = rope
        """
        The rope to which this cursor belongs.
        """

        self._span_index: int = span_index
        """
        Index of the span that contains the position.
        """

        self._charno: int = charno
        """
        Absolute source character index of the position.
        """

    @classmethod
    def at_span_start(cls, rope: SpanRope, span_index: int) -> Self:
        """
        Create a cursor positioned at the first character of the specified span.

        Args:
            rope: The rope containing the spans.
            span_index: Index of the target span in `rope._char_spans`.

        Returns:
            A `RopeCursor` positioned at `rope._char_spans[span_index].start_charno`.

        Raises:
            IndexError: If `span_index` is not in the range `[0, len(rope._char_spans))`.
        """
        if not (0 <= span_index < len(rope._char_spans)):
            raise IndexError(
                f"Span index {span_index} out of range (0-{len(rope._char_spans) - 1})"
            )

        return cls(
            rope=rope,
            span_index=span_index,
            charno=rope._char_spans[span_index].start_charno,
        )

    @classmethod
    def at_start(cls, rope: SpanRope) -> Self:
        """Create a cursor positioned at the first character of the rope (start of the first span).

        Equivalent to `at_span_start(rope, 0)`.

        Args:
            rope: The rope to which the cursor will belong.

        Returns:
            A `RopeCursor` at the beginning of the rope.

        Raises:
            IndexError: If the rope has no spans.
        """
        if rope.span_count == 0:
            raise IndexError("Cannot create cursor at start of empty SpanRope")
        return cls.at_span_start(rope=rope, span_index=0)

    @property
    def charno(self) -> int:
        """
        The absolute source character index of the cursor's current position.
        """
        return self._charno

    @property
    def logical_offset(self) -> int:
        """Return the cursor's position as a logical character offset from the rope's start.

        This offset is computed from the current span index and source character index,
        delegating to the rope's `logical_offset_of` method.
        """
        return self._rope.logical_offset_of(
            span_index=self._span_index, charno=self._charno
        )

    def advance_backward(self, distance: int) -> None:
        """Move the cursor backward by the given number of logical character positions.

        This method traverses spans incrementally, making it optimal for small
        backward steps (typically <= 5) in linear scanning.

        Args:
            distance: Number of characters to move backward. Must be non-negative.
                Zero has no effect.

        Raises:
            ValueError: If `distance` is negative.
            IndexError: If the cursor would move past the start of the rope
                (i.e., `self.logical_offset - distance < 0`).

        Note:
            Equivalent to `advance(-distance)` but enforces non-negative distance.
        """
        if distance < 0:
            raise ValueError(
                f"advance_backward distance must be non-negative, got {distance}"
            )

        if distance == 0:
            return

        if self.logical_offset < distance:
            raise IndexError(
                f"Cannot move backward {distance} from logical offset {self.logical_offset} "
                f"(would go below 0)"
            )

        _current_span = self._rope.get_span(self._span_index)

        # Maximum distance we can move backward without leaving the current span
        _current_span_capacity = self._charno - _current_span.start_charno

        if distance <= _current_span_capacity:
            self._charno -= distance
            return

        distance -= _current_span_capacity

        for span_index in range(self._span_index - 1, -1, -1):
            # Invariant:
            # distance > 0 here

            _current_span = self._rope.get_span(span_index)

            if distance <= _current_span.length:
                self._span_index = span_index
                self._charno = _current_span.end_charno - distance
                return

            distance -= _current_span.length

    def advance_forward(self, distance: int) -> None:
        """Move the cursor forward by the given number of logical character positions.

        This method traverses spans incrementally, making it optimal for small
        forward steps (typically ≤5) in linear scanning.

        Args:
            distance: Number of characters to move forward. Must be non-negative.
                Zero has no effect.

        Raises:
            ValueError: If `distance` is negative.
            IndexError: If the cursor would move past the end of the rope
                (i.e., `self.logical_offset + distance >= len(self._rope)`).

        Note:
            Equivalent to `advance(distance)` but enforces non-negative distance.
        """

        if distance < 0:
            raise ValueError(
                f"advance_forward distance must be non-negative, got {distance}"
            )

        if distance == 0:
            return

        if self.logical_offset + distance >= len(self._rope):
            raise IndexError(
                f"Cannot move forward {distance} from logical offset {self.logical_offset} "
                f"(rope length {len(self._rope)})"
            )

        _current_span = self._rope.get_span(self._span_index)

        # Maximum distance we can move forward without leaving the current span
        _current_span_capacity = (_current_span.end_charno - 1) - self._charno

        if distance <= _current_span_capacity:
            self._charno += distance
            return

        distance -= _current_span_capacity

        for span_index in range(self._span_index + 1, self._rope.span_count):
            # Invariant:
            # distance > 0 here

            _current_span = self._rope.get_span(span_index)

            if distance <= _current_span.length:
                self._span_index = span_index
                self._charno = _current_span.start_charno + (distance - 1)
                return

            distance -= _current_span.length
