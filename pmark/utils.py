def is_space_or_tab(character: str) -> bool:
    """
    Return True if char is ASCII space (U+0020) or tab (U+0009).

    In CommonMark, only these two characters affect indentation for block structure.
    Other Unicode whitespace characters (e.g., non-breaking space) do not count as
    leading indentation and are treated as regular content.

    Reference: https://spec.commonmark.org/0.31.2/#tabs
    """
    return character in ("\t", " ")


def is_tab(character: str) -> bool:
    """
    Return True if char is ASCII tab (U+0009).
    """
    return character == "\t"


def is_line_ending(character: str, next_character: str | None = None) -> bool:
    """
    Detect if a character (and optionally the next) forms a CommonMark line ending.

    Per CommonMark spec 0.31.2 section 2.1, a line ending is:
    - Line feed (U+000A, '\\n')
    - Carriage return (U+000D, '\\r') NOT followed by a line feed
    - Carriage return + line feed ('\\r\\n') as a pair

    Args:
        character: Current character to check
        next_character: Next character (if any) for detecting CRLF pairs

    Returns:
        True if the character(s) form a valid CommonMark line ending

    Reference: https://spec.commonmark.org/0.31.2/#characters-and-lines
    """
    if character == "\n":
        return True

    if character == "\r":
        # CR is a line ending UNLESS it's part of CRLF
        # If next char is '\n', this CR is NOT the end (the pair is)
        # If no next char or next isn't '\n', this CR IS the end
        return next_character != "\n"

    return False
