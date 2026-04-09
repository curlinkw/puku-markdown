COMMONMARK_TAB_STOP: int = 4
"""Number of spaces to which a tab character expands in CommonMark parsing.

See Also:
    CommonMark Spec 0.31.2, Section 2.2 (Tabs):
    https://spec.commonmark.org/0.31.2/#tabs
"""

NULL_CHARACTER: str = "\0"

UNICODE_REPLACEMENT_CHARACTER: str = "\ufffd"

INDENTED_CODE_BLOCK_MIN: int = 4
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
