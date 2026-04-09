from typing import NamedTuple, Self

from pmark.pattern_metrics import commonmark_char_width


class ColnoResolution(NamedTuple):
    """
    Result of resolving a visual column offset into a character-local position.

    In a character-based text model with variable-width characters (e.g., tabs
    expanding to multiple visual columns), a visual column coordinate cannot be
    directly mapped to a single character index. The *resolve* operation
    transforms a visual column offset into a decomposed position:
    which character contains that column, and how far into that character's
    visual span the column lies.

    This struct is the output of functions like `resolve_column_offset()`.
    It represents the architectural decision to keep the underlying model
    character-centric while exposing visual columns as a derived coordinate
    system. Using *resolve* (rather than *convert* or *map*) emphasises that
    the mapping is non-trivial due to tab expansion and may require inspecting
    character widths.
    """

    charno: int
    """
    Index of the character in the source string (0-based).
    """

    char_width: int
    """
    Visual width of that character in columns
    """

    inner_colno: int
    """
    Column offset relative to the character's left edge.
    Satisfies `0 <= inner_colno < char_width`.
    """

    @property
    def remaining_columns(self) -> int:
        """
        Number of visual columns from the current `inner_colno` (inclusive) to the end of the character.
        """
        return self.char_width - self.inner_colno


class ColnoWithResolution(NamedTuple):
    """
    A pair consisting of a visual column number and its resolved character position.

    This struct bundles the input (`colno`) together with the output
    (`ColnoResolution`) of a column-resolution operation. It is returned by
    functions that need to preserve both the original query and the mapping
    result.
    """

    colno: int
    """The original visual column number (0-based)."""

    resolution: ColnoResolution
    """The resolved character position, containing character index, width, and inner offset."""

    @classmethod
    def at_character_start(cls, start_colno: int, charno: int, character: str) -> Self:
        """
        Create a `ColnoWithResolution` positioned at the beginning of a character.

        The resolved column number (`colno`) is set to `start_colno`, and the
        character resolution (`ColnoResolution`) records the character index,
        its visual width (computed via `commonmark_char_width`), and an inner
        column offset of 0 (meaning the visual column points to the left edge
        of the character). This is useful for representing the exact start of
        a character in visual space.

        Args:
            start_colno: The visual column index where the character begins (0-based).
            charno: The index of the character in the source string (0-based).
            character: The character itself (used to compute its visual width,
                    especially for tabs).

        Returns:
            A new `ColnoWithResolution` instance with `inner_colno = 0`.
        """
        return cls(
            colno=start_colno,
            resolution=ColnoResolution(
                charno=charno,
                char_width=commonmark_char_width(
                    start_colno=start_colno,
                    character=character,
                ),
                inner_colno=0,
            ),
        )
