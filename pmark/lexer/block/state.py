from dataclasses import dataclass, field

from pmark.tokens import Token
from pmark.lexer.block.line_descriptor import LineDescriptor
from pmark.persistent_list import PersistentList, Transient
from pmark.lexer.block.column_resolution import ColumnResolution
from pmark.pattern_metrics import char_width
from pmark.pattern_predicates import is_space_or_tab


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

    line_descriptors: PersistentList[LineDescriptor] = field(
        init=False, default_factory=PersistentList
    )
    """
    `LineDescriptor`'s for the source, computed relative to the current block.
    Indexed by line number (0-based).
    """

    line_count: int = field(init=False)  # lineMax
    """
    Total number of real lines in the source (excluding the final fake entry).
    """

    def _compute_line_descriptors(self) -> None:
        """
        Compute line descriptors.
        """

        source_length = len(self.source)

        in_leading_whitespaces = True
        current_line_start_charno = 0

        # length: character count (raw spaces/tabs as characters, not expanded)
        # width: visual column width (tabs expanded to spaces)
        current_indent_length = 0
        current_indent_width = 0

        with Transient(self.line_descriptors) as line_descriptors_editor:
            for position, character in enumerate(self.source):
                if in_leading_whitespaces:
                    if is_space_or_tab(character):
                        current_indent_length += 1

                        current_indent_width += char_width(
                            current_column=current_indent_width, character=character
                        )

                        continue
                    else:
                        in_leading_whitespaces = False

                if (
                    is_last_character := (position + 1 >= source_length)
                ) or character == "\n":
                    line_descriptors_editor.append(
                        LineDescriptor(
                            line_start_charno=current_line_start_charno,
                            current_marker_indent_width=0,
                            current_after_marker_charno=current_line_start_charno,
                            current_content_indent_width=current_indent_width,
                            current_content_start_charno=current_line_start_charno
                            + current_indent_length,
                            line_end_charno=(
                                source_length if is_last_character else position
                            ),
                        )
                    )

                    in_leading_whitespaces = True
                    current_line_start_charno = position + 1
                    current_indent_length = 0
                    current_indent_width = 0

            line_descriptors_editor.append(
                LineDescriptor(
                    line_start_charno=source_length,
                    current_marker_indent_width=0,
                    current_after_marker_charno=source_length,
                    current_content_indent_width=0,
                    current_content_start_charno=source_length,
                    line_end_charno=source_length,
                )
            )

        # exclude the final fake entry
        self.line_count = len(self.line_descriptors) - 1

    def __post_init__(self):
        """Just compute line boundaries."""
        self._compute_line_descriptors()

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
            self.line_descriptors[lineno].current_content_start_charno
            >= self.line_descriptors[lineno].line_end_charno
        )

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
        return (
            self.line_descriptors[lineno].current_content_indent_width
            < self.current_block_indent_width
        )

    def resolve_relative_column_offset(
        self,
        lineno: int,
        start: ColumnResolution,
        column_offset: int,
        keep_trailing_newline: bool,
    ) -> ColumnResolution:
        if start.remaining_columns > column_offset:
            return ColumnResolution(
                charno=start.charno,
                char_width=start.char_width,
                inner_colno=start.inner_colno + column_offset,
            )

        column_offset -= start.remaining_columns
        for charno in range(
            self.line_descriptors[lineno].current_after_marker_charno,
            self.line_descriptors[lineno].line_end_charno
            + (1 if keep_trailing_newline else 0),
        ):
            character = self.source[charno]
