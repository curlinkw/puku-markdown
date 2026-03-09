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

    block_indent_space_count: int = field(default=0)
    """
    Current block's base indentation level measured in spaces.

    This value represents the minimum indentation required for content to be
    considered part of the current block container (blockquote, list item, etc.).
    Lines with indentation less than this value terminate the block.
    """

    # Pre-computed line boundaries.

    line_start_indices: list[int] = field(default_factory=list, init=False)  # bMark
    """
    For each line, the index in `source` where the line begins.
    A fake entry is added at the end for safe bounds checks.
    """

    line_end_indices: list[int] = field(default_factory=list, init=False)  # eMark
    """
    For each line, the index in `source` just after the line's content
    (i.e. the position of the newline character or the end of the string).
    A fake entry is added at the end for safe bounds checks.
    """

    leading_whitespace_counts: list[int] = field(
        default_factory=list, init=False
    )  # tShift
    """
    Number of leading whitespace characters (spaces and tabs) before the
    first non-space character on each line. Tabs count as **one** whitespace
    character (raw count, not expanded).
    """

    leading_indent_space_counts: list[int] = field(
        default_factory=list, init=False
    )  # sCount
    """
    The indentation level of each line expressed in **spaces**, with tabs
    expanded to the next multiple of 4. This is the effective visual indent.
    """

    base_indent_space_counts: list[int] = field(
        default_factory=list, init=False
    )  # bsCount
    """
    Virtual indentation (in spaces) used to adjust tab expansion when the
    beginning of a line has been logically moved (e.g. by blockquote markers).
    Initially zero for every line; mutated during parsing to preserve
    correct tab expansion when `line_start_indices` is overridden.
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
        line_start_index = 0
        leading_whitespace_count = 0
        leading_indent_space_count = 0

        for position, character in enumerate(self.source):
            if in_leading_whitespaces:
                if is_space_or_tab(character):
                    leading_whitespace_count += 1

                    # For indentation purposes, tabs behave as if replaced by spaces
                    # with tab stops every 4 characters.
                    # https://spec.commonmark.org/0.31.2/#tabs
                    leading_indent_space_count += (
                        (
                            COMMONMARK_TAB_STOP
                            - leading_indent_space_count % COMMONMARK_TAB_STOP
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
                self.line_start_indices.append(line_start_index)
                self.line_end_indices.append(
                    source_length if is_last_character else position
                )
                self.leading_whitespace_counts.append(leading_whitespace_count)
                self.leading_indent_space_counts.append(leading_indent_space_count)
                self.base_indent_space_counts.append(0)

                in_leading_whitespaces = True
                line_start_index = position + 1
                leading_whitespace_count = 0
                leading_indent_space_count = 0

        self.line_start_indices.append(source_length)
        self.line_end_indices.append(source_length)
        self.leading_whitespace_counts.append(0)
        self.leading_indent_space_counts.append(0)
        self.base_indent_space_counts.append(0)

        # exclude the final fake entry
        self.line_count = len(self.line_start_indices) - 1

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
            self.line_start_indices[lineno] + self.leading_whitespace_counts[lineno]
        ) >= self.line_end_indices[lineno]

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
        return self.leading_indent_space_counts[lineno] < self.block_indent_space_count
