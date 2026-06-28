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

LESS_THAN_CHARACTER: Final[str] = "<"
"""
The less-than sign character '<' (Unicode U+003C).
"""

GREATER_THAN_CHARACTER: Final[str] = ">"
"""The greater-than sign character '>' (Unicode U+003E).
"""

SPACE_CHARACTER: Final[str] = " "
"""
The space character ' ' (Unicode U+0020).
"""

TAB_CHARACTER: Final[str] = "\t"
"""
The tab character '\\t' (Unicode U+0009, CHARACTER TABULATION).
"""

LEFT_SQUARE_BRACKET_CHARACTER: Final[str] = "["
"""
The left square bracket character '[' (Unicode U+005B, LEFT SQUARE BRACKET).
"""

RIGHT_SQUARE_BRACKET_CHARACTER: Final[str] = "]"
"""
The right square bracket character ']' (Unicode U+005D, RIGHT SQUARE BRACKET).
"""

LINE_FEED_CHARACTER: Final[str] = "\n"
"""
Line feed (LF), the '\n' character.
"""

BACKSLASH_CHARACTER: Final[str] = "\\"
"""
Backslash, the escape character.
"""

COLON_CHARACTER: Final[str] = ":"
"""
Colon (:), used in reference definitions after the label.
"""

LEFT_PARENTHESIS_CHARACTER: Final[str] = "("
"""
Left parenthesis '(' (U+0028).
"""

RIGHT_PARENTHESIS_CHARACTER: Final[str] = ")"
"""
Right parenthesis ')' (U+0029).
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

INDENTED_CODE_BLOCK_MIN_INDENT_STR: Final[str] = " " * INDENTED_CODE_BLOCK_MIN_INDENT
"""The string representation of the minimum indentation for an indented code block.

This constant provides the literal four-space string (`"    "`). It is
derived from `INDENTED_CODE_BLOCK_MIN_INDENT` to guarantee consistency
between the numeric threshold and the actual characters used for string
operations.

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

ATX_HEADING_MAX_LEVEL: Final[int] = 6
"""
Maximum heading level for an ATX heading, corresponding to six '#' characters.

See Also:
    CommonMark Spec 0.31.2, Section 4.2 (ATX headings):
    https://spec.commonmark.org/0.31.2/#atx-headings
"""

HTML_BLOCK_NAMES: Final[tuple[str, ...]] = (
    "address",
    "article",
    "aside",
    "base",
    "basefont",
    "blockquote",
    "body",
    "caption",
    "center",
    "col",
    "colgroup",
    "dd",
    "details",
    "dialog",
    "dir",
    "div",
    "dl",
    "dt",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "frame",
    "frameset",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "head",
    "header",
    "hr",
    "html",
    "iframe",
    "legend",
    "li",
    "link",
    "main",
    "menu",
    "menuitem",
    "nav",
    "noframes",
    "ol",
    "optgroup",
    "option",
    "p",
    "param",
    "search",
    "section",
    "summary",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "title",
    "tr",
    "track",
    "ul",
)
"""
List of HTML block-level tag names as defined by the CommonMark specification.

This list is used to construct the regex for matching block-level HTML tags
(CommonMark HTML block type 6). The tags are matched case-insensitively
(using `re.IGNORECASE` flag) because HTML tag names are case-insensitive.

Reference: https://spec.commonmark.org/0.31.2/#html-blocks
"""

SETEXT_HEADING_MARKERS: Final[frozenset[str]] = frozenset({"-", "="})
"""Markers that denote Setext headings (CommonMark section 4.2, version 0.31.2).

A line consisting entirely of `=` characters (optionally with trailing spaces)
indicates a level-1 heading. A line consisting entirely of `-` characters
indicates a level-2 heading. The marker line must appear immediately after the
heading text (with no blank line in between).

Reference: https://spec.commonmark.org/0.31.2/#setext-headings
"""

HYPHEN_MINUS_CHARACTER: Final[str] = "-"
"""
The hyphen-minus character '-' (Unicode U+002D).

This character is used as a hyphen, minus sign, or dash. In Markdown,
it appears in Setext headings (level-2), unordered lists, and horizontal rules.
"""

EQUALS_SIGN_CHARACTER: Final[str] = "="
"""
The equals sign '=' (Unicode U+003D).

In Markdown, this character is used in Setext headings (level-1) and as a
delimiter for fenced code blocks (with backticks). It also appears in
HTML attributes and link definitions.
"""

MAX_LINK_DESTINATION_PARENTHESIS_DEPTH: Final[int] = 32
"""
Maximum allowed nesting depth of parentheses inside a bare link destination
(i.e., when not enclosed in `<` `>`). Exceeding this limit invalidates the
link destination and stops scanning.

This limit is a safety measure against pathological input; it is not mandated
by the CommonMark specification, which only requires balanced parentheses.
The value 32 is high enough for all practical URLs yet low enough to prevent
excessive CPU consumption.
"""

DOUBLE_QUOTE_CHARACTER: Final[str] = '"'
"""
Double quotation mark " (U+0022).
"""

SINGLE_QUOTE_CHARACTER: Final[str] = "'"
"""
Apostrophe / single quote ' (U+0027).
"""

BULLET_LIST_MARKERS: Final[frozenset[str]] = frozenset({"*", "-", "+"})
"""Bullet list markers as defined in CommonMark section 5.2 (version 0.31.2).

A line beginning with one of these characters, followed by a space or tab,
starts a bullet list item. The marker may be preceded by up to three spaces
of indentation.

References:
- https://spec.commonmark.org/0.31.2/#list-items
- https://spec.commonmark.org/0.31.2/#bullet-list-marker
"""

ORDERED_LIST_MARKER_DELIMITERS: Final[frozenset[str]] = frozenset({".", ")"})
"""Ordered list marker delimiters as defined in CommonMark section 5.2 (version 0.31.2).

An ordered list marker consists of a positive integer followed by a delimiter
character: either a period (`.`) or a right parenthesis (`)`). This constant
holds the two allowed delimiter characters.

Reference: https://spec.commonmark.org/0.31.2/#list-items
"""

EMPTY_STRING: str = ""
"""An immutable sentinel representing the empty string.

Use this constant instead of the literal `""` when the empty string serves as
a default value, a placeholder, or a well-known marker in public APIs or
repeated logic. This improves readability and centralises the concept.
"""

MAX_ORDERED_LIST_MARKER_DIGITS: int = 9
"""
The maximum number of digits permitted in an ordered list marker.

The CommonMark Spec (0.30+) limits ordered list markers (e.g., '1.', '999999999.')
to at most 9 digits. This limit prevents integer overflows in browsers that use
signed 32-bit integers for list indexing.

Any marker exceeding this length (e.g., '1000000000.') is invalid and must not
be recognized as a list marker by a conforming implementation.

Source: CommonMark Spec 0.30, Section 5.2 - List Items.
"""

DEFAULT_SETEXT_HEADING_MARKER_LENGTH: Final[int] = 3
"""
The default number of underline characters (`=` or `-`) to emit when rendering
a Setext heading.

While the CommonMark specification permits any length (including a single
character), `3` is the conventional default used by most renderers. It is:

- **The minimum practical choice** - visually distinct enough to be clear.
- **Spec-compliant** - passes all CommonMark conformance tests.
- **Widely adopted** - matches the output of many Markdown generators.

Renderers that prefer aesthetics over brevity may opt to match the heading's
text length dynamically, but for a static default, `3` is the idiomatic value.
"""
