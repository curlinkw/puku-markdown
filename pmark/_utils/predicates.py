from pmark._utils.constants import TAB_CHARACTER, SPACE_CHARACTER


def is_space_or_tab(character: str) -> bool:
    """
    Return True if char is ASCII space (U+0020) or tab (U+0009).

    In CommonMark, only these two characters affect indentation for block structure.
    Other Unicode whitespace characters (e.g., non-breaking space) do not count as
    leading indentation and are treated as regular content.

    Reference: https://spec.commonmark.org/0.31.2/#tabs
    """
    return character in (TAB_CHARACTER, SPACE_CHARACTER)


def is_ascii_control(character: str) -> bool:
    """
    Return True if the character is an ASCII control character.

    This includes C0 control codes (U+0000-U+001F) and DEL (U+007F).
    These characters are generally not allowed in plain text and
    terminate link destinations or titles in CommonMark.
    """
    code = ord(character)
    return code < 0x20 or code == 0x7F


def is_ascii_digit(character: str) -> bool:
    """
    Return True if the character is an ASCII digit (U+0030-U+0039).

    This is equivalent to `'0' <= character <= '9'` and is the most
    readable and performant way to test for ASCII digits.

    Reference: https://spec.commonmark.org/0.31.2/#list-items
    """
    return "0" <= character <= "9"
