from dataclasses import dataclass, field

from pmark.tokens import Token
from pmark.pattern_predicates import is_space_or_tab
from pmark.constants import COMMONMARK_TAB_STOP


@dataclass(slots=True)
class BlockLexerState:
    source: str
    """
    Source text.
    """

    tokens: list[Token] = field(default_factory=list)
    """
    The list of tokens produced so far.
    """

    current_lineno: int = field(default=0)
    """
    Current line number being processed.
    """

    current_block_indent_width: int = field(default=0)
    """
    Visual column width (tabs expanded to spaces) that represents the indentation
    level of the current block. Lines with indentation less than this value are
    considered outdented and terminate the block.
    """

    line_starts_charno: list[int] = field(default_factory=list, init=False)  # bMark
    """
    For each line, the index in `source` where the line begins.
    A fake entry is added at the end for safe bounds checks.
    """

    line_ends_charno: list[int] = field(default_factory=list, init=False)  # eMark
    """
    For each line, the index in `source` just after the line's content
    (i.e. the position of the newline character or the end of the string).
    A fake entry is added at the end for safe bounds checks.
    """

    current_positions_charno: list[int] = field(
        default_factory=list, init=False
    )  # tShift
    """
    For each line, character offset from the start of the line to the current
    parsing position. Points to the character that is about to be
    processed. After indentation and block markers have been consumed, this
    points to the first non-indent, non-marker character (i.e., the actual
    content).
    """

    current_indents_width: list[int] = field(default_factory=list, init=False)  # sCount
    """
    For each line, *visual* column width (tabs expanded to spaces) of the indentation that appears
    *before* the actual content on the current line, *after* any block marker has
    been consumed.

    - For blocks with a marker (blockquotes, lists), this is the number of spaces
    between the marker and the first non-space content character (i.e., the indent
    after the marker). The marker itself is *excluded* from this width.
    - For blocks without a marker (paragraphs, code blocks), this is simply the
    visual indent.
    """

    current_initial_indents_width: list[int] = field(
        default_factory=list, init=False
    )  # bsCount
    """
    For each line, total visual column width (tabs expanded to spaces) of the marker region for
    the current block. This includes:

    - Any initial indent before the marker,
    - The marker character itself (e.g., `>` for blockquotes),
    - An optional single space after the marker (e.g., for blockquotes).

    That is, for:
    - *Blocks with a marker* (e.g., blockquotes, lists): this value is the combined width
    of the initial indent, marker, and (e.g., for blockquotes) an optional following space.
    - *Blocks without a marker* (e.g., paragraphs, code blocks, etc.): this field is `0`
    and should be ignored.
    """

    line_count: int = field(init=False)  # lineMax
    """
    Total number of real lines in the source (excluding the final fake entry).
    """

    def _compute_line_boundaries(self) -> None:
        """
        Compute line boundaries.
        """

        source_length = len(self.source)

        in_leading_whitespaces = True
        current_line_start_charno = 0

        # length: character count (raw spaces/tabs as characters, not expanded)
        # width: visual column width (tabs expanded to spaces)
        current_indent_length = 0
        current_indent_width = 0

        for position, character in enumerate(self.source):
            if in_leading_whitespaces:
                if is_space_or_tab(character):
                    current_indent_length += 1

                    # For indentation purposes, tabs behave as if replaced by spaces
                    # with tab stops every 4 characters.
                    # https://spec.commonmark.org/0.31.2/#tabs
                    current_indent_width += (
                        (
                            COMMONMARK_TAB_STOP
                            - current_indent_width % COMMONMARK_TAB_STOP
                        )
                        if character == "\t"
                        else 1
                    )

                    continue
                else:
                    in_leading_whitespaces = False

            #
            if (
                is_last_character := (position + 1 >= source_length)
            ) or character == "\n":
                self.line_starts_charno.append(current_line_start_charno)
                self.line_ends_charno.append(
                    source_length if is_last_character else position
                )
                self.current_positions_charno.append(current_indent_length)
                self.current_indents_width.append(current_indent_width)
                self.current_initial_indents_width.append(0)

                in_leading_whitespaces = True
                current_line_start_charno = position + 1
                current_indent_length = 0
                current_indent_width = 0

        self.line_starts_charno.append(source_length)
        self.line_ends_charno.append(source_length)
        self.current_positions_charno.append(0)
        self.current_indents_width.append(0)
        self.current_initial_indents_width.append(0)

        # exclude the final fake entry
        self.line_count = len(self.line_starts_charno) - 1

    def __post_init__(self):
        """Just compute line boundaries."""
        self._compute_line_boundaries()

    def is_blank_line(self, lineno: int) -> bool:
        """Determine if a line contains only whitespace or is completely empty.

        A line is considered blank if, after skipping all leading whitespace characters,
        there are no remaining characters before the line ends. This includes lines that
        are completely empty as well as lines containing only spaces and/or tabs.

        Args:
            lineno: Zero-based index of the line to check.

        Returns:
            True if the line consists solely of whitespace or is empty, False if it
            contains any non-whitespace characters.
        """
        return (
            self.line_starts_charno[lineno] + self.current_positions_charno[lineno]
        ) >= self.line_ends_charno[lineno]

    @property
    def is_preceded_by_blank_line(self) -> bool:
        """
        Return True if there is a previous line and it is blank.
        """
        return self.current_lineno > 0 and self.is_blank_line(self.current_lineno - 1)

    def next_non_blank_lineno(self, start_lineno: int) -> int:
        """Find the next line index (>= start_lineno) that is not blank.

        Args:
            start_lineno: The line index from which to start searching (inclusive).

        Returns:
            The index of the next non-blank line, or `line_count` if none found.
        """
        return next(
            (
                lineno
                for lineno in range(start_lineno, self.line_count)
                if not self.is_blank_line(lineno)
            ),
            self.line_count,
        )

    def skip_blank_lines(self) -> None:
        """Advance current line position past any consecutive blank lines.

        Moves `current_lineno` forward until a non-blank line is found or the
        end of document is reached.

        Note:
            This is a state-changing operation. After calling this method,
            `current_lineno` will point to either:
            - The next non-blank line (if any exists)
            - `self.line_count` (if no non-blank lines remain)
        """
        self.current_lineno = self.next_non_blank_lineno(
            start_lineno=self.current_lineno
        )

    def is_line_outdented(self, lineno: int) -> bool:
        """Determine if a line is outdented relative to the current block.

        A line is considered outdented when its visual indentation (after tab
        expansion) is less than the current block's required base indentation.
        This condition marks the boundary where a block container (blockquote,
        list item, etc.) ends and content returns to a outer level.

        Args:
            lineno: Zero-based index of the line to check.

        Returns:
            True if the line's indentation is strictly less than the current
            block's base indentation; otherwise False.
        """
        return self.current_indents_width[lineno] < self.current_block_indent_width
