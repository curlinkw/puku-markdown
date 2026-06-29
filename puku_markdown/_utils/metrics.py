from puku_markdown._utils.constants import COMMONMARK_TAB_STOP, TAB_CHARACTER


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
        if character == TAB_CHARACTER
        else 1
    )


def commonmark_str_width(text: str, start_colno: int = 0) -> int:
    """
    Returns the visual width (in columns) of the given string, as defined by CommonMark.

    This function iterates over each character in the string, applying the same
    width calculation as `commonmark_char_width()`. The starting column is
    provided for correct tab expansion.

    Args:
        text: The string to measure.
        start_colno: The visual column index where the string begins (0-based).
            Defaults to 0. This affects tab expansion: the first tab's width
            depends on this starting position.

    Returns:
        The total visual width contribution of the string.

    Reference:
        https://spec.commonmark.org/0.31.2/#tabs
    """
    colno = start_colno
    for char in text:
        colno += commonmark_char_width(colno, char)
    return colno - start_colno
