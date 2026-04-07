from typing import NamedTuple


class ColumnResolution(NamedTuple):
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
