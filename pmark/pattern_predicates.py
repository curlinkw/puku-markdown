from pmark.constants import TAB_CHARACTER, SPACE_CHARACTER


def is_space_or_tab(character: str) -> bool:
    """
    Return True if char is ASCII space (U+0020) or tab (U+0009).

    In CommonMark, only these two characters affect indentation for block structure.
    Other Unicode whitespace characters (e.g., non-breaking space) do not count as
    leading indentation and are treated as regular content.

    Reference: https://spec.commonmark.org/0.31.2/#tabs
    """
    return character in (TAB_CHARACTER, SPACE_CHARACTER)
