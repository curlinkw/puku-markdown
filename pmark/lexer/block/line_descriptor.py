from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class LineDescriptor:
    """
    Describes a single line of a Markdown document with respect to the current block.

    The line is represented as a half-open interval `[line_start_charno, line_end_charno)`.
    The current block (e.g., a blockquote) is composed as:

    current_block = `marker_indent` (visual) + `marker` + `content_indent` (visual) + `content`

    where:
    - `marker_indent` : whitespaces before the marker (measured in visual columns)
    - `marker`        : syntactic token (e.g., '>')
    - `content_indent`: spaces between marker and content (visual columns)
    - `content`       : actual text, starting at `current_content_start_charno`

    All character indices are 0-based offsets from the line start.
    Visual column widths assume tab stops every 4 spaces (CommonMark convention).
    """

    line_start_charno: int  # Inirial bMark
    """
    Character index of the first character of the line (inclusive).
    """

    current_marker_indent_width: int  # bsCount
    """
    Visual column width of spaces preceding the marker. `0` if no marker.
    """

    current_after_marker_charno: int  # bMark
    """
    Character index of the first character *immediately after* the marker.
    If no marker, equals to current block start.
    """

    current_content_indent_width: int  # sCount
    """
    Visual column width of spaces between the marker and the content.
    If no marker, this is the visual indent of the content itself.
    """

    current_content_start_charno: int  # bMark + tShift
    """
    Character index of the first character of the actual content (after content indent).
    """

    line_end_charno: int  # eMark
    """
    Character index immediately after the last character of the line (exclusive).
    """

    is_lazy_continuation: bool = field(default=False)  # sCount = -1
    """
    Indicates that this line is a *lazy continuation* of the previous block's content.

    In CommonMark, certain block constructs (e.g., blockquotes, lists) allow subsequent lines
    to continue the same block without repeating the leading marker (e.g., `>`).
    Such lines are called lazy continuation lines.

    When `True`, this line should be parsed as if it were part of the preceding block's
    content, disregarding its own indentation and marker presence.

    This flag is set by block rules (e.g., blockquote, list) when they detect a line that
    belongs to the current block but lacks the expected marker.
    """
