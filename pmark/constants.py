"""
CommonMark constants for Markdown parsing.

Coding style note:
    Typically, names are limited to at most 4 words (e.g., `INDENTED_CODE_BLOCK_MIN_INDENT`).
    However, for constants that directly represent a CommonMark element (e.g., fenced code
    blocks, thematic breaks), the element name in the prefix (e.g., `FENCED_CODE_BLOCK_`,
    `THEMATIC_BREAK_`) is **excluded** from the word count. This allows longer, more
    precise names without violating the spirit of the rule.

    This exception is *temporary* and subject to revision.

    TODO: Re-evaluate the word-limit exception for CommonMark element prefixes.
          Consider adopting a fixed maximum total length or a different scheme.
"""

from typing import Final


COMMONMARK_TAB_STOP: Final[int] = 4
"""Number of spaces to which a tab character expands in CommonMark parsing.

See Also:
    CommonMark Spec 0.31.2, Section 2.2 (Tabs):
    https://spec.commonmark.org/0.31.2/#tabs
"""

NULL_CHARACTER: Final[str] = "\0"

HASH_CHARACTER: Final[str] = "#"
"""
Hash/number sign character used as the ATX heading marker in CommonMark.
"""

UNICODE_REPLACEMENT_CHARACTER: Final[str] = "\ufffd"

BACKTICK_CHARACTER: Final[str] = "`"

INDENTED_CODE_BLOCK_MIN_INDENT: Final[int] = 4
"""Minimum indentation required for a line to be part of an indented code block.

According to the CommonMark specification (Section 4.4), an indented chunk is a
sequence of non-blank lines, each preceded by *four or more spaces* of indentation.
Lines meeting this threshold form an indented code block.

Note:
    An indented code block cannot interrupt a paragraph. Therefore, within a
    paragraph, a line with indentation >= this value is treated as a lazy
    continuation of the paragraph, not as a new code block.

See Also:
    CommonMark Spec 0.31.2, Section 4.4:
    https://spec.commonmark.org/0.31.2/#indented-code-blocks
"""

THEMATIC_BREAK_MARKERS: Final[frozenset[str]] = frozenset({"*", "-", "_"})
"""
Immutable set of characters that can initiate a CommonMark thematic break.
"""

THEMATIC_BREAK_MIN_MARKER_COUNT: Final[int] = 3
"""
Minimum number of identical markers required for a CommonMark thematic break.

See CommonMark Spec 0.31.2, Section 4.1:
https://spec.commonmark.org/0.31.2/#thematic-breaks
"""

FENCED_CODE_BLOCK_MIN_MARKER_COUNT: Final[int] = 3
"""
Minimum number of consecutive backticks or tildes required for a fenced code block.

Per CommonMark Spec 0.31.2, Section 4.5:
https://spec.commonmark.org/0.31.2/#fenced-code-blocks
"""

FENCED_CODE_BLOCK_MARKERS: Final[frozenset[str]] = frozenset({"~", "`"})
"""
Immutable set of marker characters that can open a fenced code block.

See Also:
    CommonMark Spec 0.31.2, Section 4.5:
    https://spec.commonmark.org/0.31.2/#fenced-code-blocks
"""
