from pmark.constants import COMMONMARK_TAB_STOP


def char_width(current_column: int, character: str) -> int:
    """
    Return the visual width (in columns) of a character, as defined by CommonMark.

    For a tab character, the width is the number of spaces required to advance
    to the next tab stop, which occurs every 4 columns.
    For any other character, the width is 1.

    Args:
        current_column: The visual column index before the character (0-based).
        character: The character to measure.

    Returns:
        The visual width increment that the character contributes.

    Reference:
        https://spec.commonmark.org/0.31.2/#tabs
    """
    return (
        (COMMONMARK_TAB_STOP - (current_column % COMMONMARK_TAB_STOP))
        if character == "\t"
        else 1
    )
