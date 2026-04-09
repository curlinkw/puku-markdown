from pmark.constants import COMMONMARK_TAB_STOP


def commonmark_char_width(start_colno: int, character: str) -> int:
    """
    Return the visual width (in columns) of a character, as defined by CommonMark.

    For a tab character, the width is the number of spaces required to advance
    the visual column from `start_colno` to the next tab stop (every 4 columns).
    For any other character, the width is 1.

    Args:
        start_colno: The visual column index where the character begins (0-based).
        character: The character to measure.

    Returns:
        The visual width increment that the character contributes.

    Reference:
        https://spec.commonmark.org/0.31.2/#tabs
    """
    return (
        (COMMONMARK_TAB_STOP - (start_colno % COMMONMARK_TAB_STOP))
        if character == "\t"
        else 1
    )
