from dataclasses import dataclass, field

from pmark.parser.block.line_descriptor import LineDescriptor
from pmark.persistent_list import PersistentList, Transient
from pmark.column_resolution import ColnoWithResolution, ColnoResolution
from pmark.line_span import LineSpan
from pmark.elements import Document
from pmark.pattern_metrics import commonmark_char_width
from pmark.pattern_predicates import is_space_or_tab
from pmark.constants import INDENTED_CODE_BLOCK_MIN_INDENT, LINE_FEED_CHARACTER


@dataclass(slots=True)
class BlockParserState:
    source: str
    """
    Source text.
    """

    target_document: Document
    """
    Output document under construction. Root blocks are appended as parsing progresses.
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

                        current_indent_width += commonmark_char_width(
                            start_colno=current_indent_width, character=character
                        )

                        continue
                    else:
                        in_leading_whitespaces = False

                if (
                    is_last_character := (position + 1 >= source_length)
                ) or character == LINE_FEED_CHARACTER:
                    line_descriptors_editor.append(
                        LineDescriptor(
                            line_start_charno=current_line_start_charno,
                            current_indented_marker_width=0,
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
                    current_indented_marker_width=0,
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
        """
        Return True if the specified line contains no non-whitespace characters.

        This method delegates to `LineDescriptor.is_blank`, which determines blankness
        by checking whether the content start index is at or beyond the line end index.

        A line is considered blank if it is empty or consists only of spaces/tabs.

        Args:
            lineno: Zero-based index of the line to check.

        Returns:
            True if the line is blank, False otherwise.
        """
        return self.line_descriptors[lineno].is_blank

    @property
    def is_preceded_by_blank_line(self) -> bool:
        """
        Return True if there is a previous line and it is blank.
        """
        return self.current_lineno > 0 and self.is_blank_line(self.current_lineno - 1)

    def next_non_blank_lineno(
        self, start_lineno: int, end_lineno: int | None = None
    ) -> int:
        """Return the first line index >= start_lineno that is not blank.

        The search stops at (but does not include) `end_lineno`. If no non-blank
        line is found within the range, `end_lineno` is returned (or `line_count`
        when `end_lineno` is `None`).

        Args:
            start_lineno: Index of the first line to check (inclusive).
            end_lineno:   Exclusive upper bound for the search. If `None`, the
                        search goes to the end of the document (`self.line_count`).

        Returns:
            The line index of the first non-blank line, or `end_lineno` (or
            `self.line_count`) if no such line exists in the range.

        Raises:
            ValueError: If `start_lineno` is out of the valid range
                `[0, end_lineno)`.
        """
        if end_lineno is None:
            end_lineno = self.line_count

        if not (0 <= start_lineno < end_lineno):
            raise ValueError(
                f"start_lineno {start_lineno} must be in range [0, {end_lineno})"
            )

        return next(
            (
                lineno
                for lineno in range(start_lineno, end_lineno)
                if not self.is_blank_line(lineno)
            ),
            end_lineno,
        )

    def skip_blank_lines(self, end_lineno: int | None = None) -> None:
        """Advance the current line position past consecutive blank lines.

        The scan starts at `self.current_lineno` and continues until a non-blank
        line is found or the search limit (`end_lineno`) is reached. After the
        call, `self.current_lineno` points to either:
        - The next non-blank line (if any exists within the limit)
        - `end_lineno` (or `self.line_count` when `end_lineno is None`) if no
        non-blank line is found.

        Args:
            end_lineno: Exclusive upper bound for the search. If `None`, the
                        search goes to the end of the document (`self.line_count`).

        Note:
            This method mutates `self.current_lineno`. It does not return a value.
        """
        self.current_lineno = self.next_non_blank_lineno(
            start_lineno=self.current_lineno,
            end_lineno=end_lineno,
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
        start: ColnoWithResolution,
        column_offset: int,
        keep_trailing_newline: bool,
    ) -> ColnoResolution:
        """
        Resolve a visual column offset forward from a given resolved column position.

        Starting from `start` (which contains both the absolute column number and its
        character-level resolution), this method moves `column_offset` visual columns
        to the right within the specified line. It returns the new character-level
        resolution (`ColnoResolution`) at the target position.

        The offset is applied purely in visual space, handling tab expansion correctly.
        If the offset lands exactly on a character boundary (`inner_colno == 0`), the
        returned resolution points to the start of the next character. If the offset
        lands exactly at the end of the line (or at the end of the newline when
        `keep_trailing_newline` is `True`), a sentinel `ColnoResolution` is returned
        with `charno` set to the end index, `char_width = 0`, and `inner_colno = 0`.
        This sentinel represents a virtual position after all line content.

        Args:
            lineno: Zero-based line index within the document.
            start: A resolved column position (input + resolution) marking the start.
            column_offset: Number of visual columns to move forward. Must be >= 0.
            keep_trailing_newline: If `True`, the line's trailing newline character is
                considered part of the line and can be landed on. If `False`, the newline
                is excluded and the method stops at the last visible character.

        Returns:
            A `ColnoResolution` representing the character and inner offset at the
            target visual column. If the target is exactly at the end of the line
            (including the newline when allowed), returns a sentinel resolution with
            `char_width = 0` and `inner_colno = 0`.

        Raises:
            ValueError: If `column_offset` is negative, or if `start.resolution.charno`
                lies outside the character range of line `lineno`.
            RuntimeError: If `column_offset` exceeds the total visual length of the
                line (including the newline when allowed) - current_charno.e., if the offset goes
                beyond the sentinel end position.
        """
        if column_offset < 0:
            raise ValueError(
                f"column_offset must be non-negative (got {column_offset}); negative offsets are not supported"
            )

        line_descriptor = self.line_descriptors[lineno]

        if not (
            line_descriptor.line_start_charno
            <= start.resolution.charno
            < line_descriptor.line_end_charno
        ):
            raise ValueError(
                f"start.resolution.charno ({start.resolution.charno}) not in line {lineno} "
                f"[{line_descriptor.line_start_charno}, {line_descriptor.line_end_charno})"
            )

        if start.resolution.remaining_columns > column_offset:
            return ColnoResolution(
                charno=start.resolution.charno,
                char_width=start.resolution.char_width,
                inner_colno=start.resolution.inner_colno + column_offset,
            )

        current_column_offset = start.resolution.remaining_columns
        end_charno = line_descriptor.line_end_charno + (
            1 if keep_trailing_newline else 0
        )

        for current_charno in range(
            start.resolution.charno + 1,
            end_charno,
        ):
            current_char_width = commonmark_char_width(
                start_colno=start.colno + current_column_offset,
                character=self.source[current_charno],
            )

            remaining_offset = column_offset - current_column_offset

            if current_char_width > remaining_offset:
                return ColnoResolution(
                    charno=current_charno,
                    char_width=current_char_width,
                    inner_colno=remaining_offset,
                )

            current_column_offset += current_char_width

        if current_column_offset < column_offset:
            raise RuntimeError(
                f"Column offset {column_offset} from start colno {start.colno} "
                f"exceeds line {lineno} capacity {current_column_offset}"
            )

        return ColnoResolution(charno=end_charno, char_width=0, inner_colno=0)

    def indent_reduced_line_content(
        self, lineno: int, reduction_width: int, keep_trailing_newline: bool
    ) -> str:
        """
        Return the line content after removing the marker prefix and reducing the content indent.

        This method strips the entire marker prefix (including any leading spaces before the
        marker and the marker itself) from the line, and then reduces the remaining content
        indent by `reduction_width` visual columns. The reduction is applied from the left
        edge of the content indent area; if the reduction lands inside a tab character, that
        tab is partially expanded to spaces to preserve exact visual alignment.

        Args:
            lineno: Zero-based line index within the document.
            reduction_width: Number of visual columns to reduce the content indent by.
                Must be less than or equal to the line's `current_content_indent_width`.
            keep_trailing_newline: If `True`, the returned string includes the line's
                trailing newline character; otherwise it ends before the newline.

        Returns:
            The line content starting after the removed marker prefix and the reduced content
            indent. If the reduction lands exactly on a character boundary, the returned
            string starts at that character; if it lands inside a tab, the tab is replaced by
            the appropriate number of spaces to fill the reduced portion, and the remaining
            part of the tab (if any) is kept as part of the output.

        Raises:
            ValueError: If `reduction_width` is greater than the line's
                `current_content_indent_width`. The error message includes the actual values.
        """

        line_descriptor = self.line_descriptors[lineno]
        end_charno = line_descriptor.line_end_charno + (
            1 if keep_trailing_newline else 0
        )

        if line_descriptor.current_content_indent_width < reduction_width:
            raise ValueError(
                f"Cannot reduce content indent by {reduction_width} columns on line {lineno}: "
                f"current content indent width is only {line_descriptor.current_content_indent_width}"
            )

        retained_indent_start = self.resolve_relative_column_offset(
            lineno=lineno,
            start=ColnoWithResolution.at_character_start(
                start_colno=line_descriptor.current_indented_marker_width,
                charno=line_descriptor.current_after_marker_charno,
                character=self.source[line_descriptor.current_after_marker_charno],
            ),
            column_offset=reduction_width,
            keep_trailing_newline=keep_trailing_newline,
        )

        return (
            self.source[retained_indent_start.charno : end_charno]
            if (retained_indent_start.inner_colno == 0)
            else (
                " " * retained_indent_start.remaining_columns
                + self.source[retained_indent_start.charno + 1 : end_charno]
            )
        )

    def indent_reduced_block_content(
        self, line_span: LineSpan, reduction_width: int, keep_trailing_newline: bool
    ):
        """
        Return the concatenated content of a block of lines, with marker prefixes removed
        and content indent reduced by a given width on each line.

        For each line in the span (from `line_span.start_lineno` inclusive to
        `line_span.end_lineno` exclusive), this method calls `indent_reduced_line_content`
        with the specified `reduction_width` and `keep_trailing_newline`, then joins the
        results into a single string. The reduction width applies to the content indent
        of every line individually.

        Args:
            line_span: A `LineSpan` defining the contiguous range of lines to process.
                The span is half-open: `[start_lineno, end_lineno)`.
            reduction_width: Number of visual columns to reduce the content indent by on
                each line. Must be <= each line's `current_content_indent_width`.
            keep_trailing_newline: If `True`, the trailing newline of each line is included
                in that line's result. If `False`, newlines are omitted from all lines
                (resulting in a single concatenated string without line breaks).

        Returns:
            A single string formed by concatenating the processed content of all lines
            in the specified range.

        Raises:
            ValueError: If `reduction_width` exceeds the `current_content_indent_width`
                of any line in the span. The error message identifies the problematic line.
        """
        return "".join(
            self.indent_reduced_line_content(
                lineno=lineno,
                reduction_width=reduction_width,
                keep_trailing_newline=keep_trailing_newline,
            )
            for lineno in range(line_span.start_lineno, line_span.end_lineno)
        )

    def meets_indented_code_block_indent(self, lineno: int) -> bool:
        """
        Return True if the line's content indentation exceeds the current block's
        indentation by at least `INDENTED_CODE_BLOCK_MIN_INDENT` (4 spaces).

        Indented code blocks in CommonMark are defined relative to the enclosing
        block's indentation level. For example, inside a list item that already has
        2 spaces of indentation, a line needs 6 total spaces (2 block + 4 extra) to
        start an indented code block.

        Args:
            lineno: Line index (0-based) within the current block.

        Returns:
            True if the relative indentation meets or exceeds the threshold,
            otherwise False.

        Note:
            This is a *necessary* condition only. The caller must also enforce
            that an indented code block cannot interrupt a paragraph.
        """
        return (
            self.line_descriptors[lineno].current_content_indent_width
            - self.current_block_indent_width
        ) >= INDENTED_CODE_BLOCK_MIN_INDENT

    def is_content_start_beyond_source(self, lineno: int) -> bool:
        """
        Return True if the line's content start index is at or past the end of the source string.

        Equivalent to `line.current_content_start_charno >= len(source)`. This occurs when a line
        has no parseable characters (e.g., a blank line or a line that starts after EOF).

        Args:
            lineno: Line index (0-based) within the current block.

        Returns:
            True if the line's content start is beyond the source end, otherwise False.
        """
        return self.line_descriptors[lineno].current_content_start_charno >= len(
            self.source
        )

    def count_run_of_char(
        self,
        start_charno: int,
        end_charno: int | None = None,
        character: str | None = None,
    ) -> int:
        """
        Count consecutive occurrences of `character` in `self.source[start_charno:end_charno]`.

        Scans forward from `start_charno` (inclusive) until a character different from `character`
        is found, or until `end_charno` (exclusive) is reached.
        If `character` is `None`, the character at `start_charno` is used as the match target.

        Args:
            start_charno: Start index (inclusive). Must satisfy `0 <= start_charno < len(self.source)`.
            end_charno: Exclusive upper bound. If `None`, defaults to `len(self.source)`.
                        Must satisfy `start_charno < end_charno <= len(self.source)`.
            character: The character to match. If `None`, uses `self.source[start_charno]`.

        Returns:
            Number of consecutive matching characters in the range `[start_charno, end_charno)`.
            If `character` is provided and does not equal the character at `start_charno`,
            returns `0` (because the first character already fails to match).

        Raises:
            ValueError: If the range `[start_charno, end_charno)` is invalid, i.e.:
                        - `start_charno < 0` or `start_charno >= len(self.source)`
                        - `end_charno > len(self.source)`
                        - `start_charno >= end_charno` (empty range not allowed)
        """
        source_len = len(self.source)

        if end_charno is None:
            end_charno = source_len

        if not (0 <= start_charno < end_charno <= source_len):
            raise ValueError(
                f"Invalid range: start_charno={start_charno}, end_charno={end_charno}, "
                f"source_len={source_len}. Must satisfy 0 <= start < end <= source_len"
            )

        if character is None:
            character = self.source[start_charno]

        match_count = 0
        for current_charno in range(start_charno, end_charno):
            if self.source[current_charno] != character:
                break
            match_count += 1
        return match_count

    def backward_count_run_of_char(
        self,
        start_charno: int,
        boundary_charno: int | None = None,
        character: str | None = None,
    ) -> int:
        """
        Count consecutive occurrences of `character` ending at `start_charno` in `self.source`.

        Scans backward from `start_charno` (inclusive) toward the beginning until a character
        different from `character` is found, or until `boundary_charno` (exclusive) is reached.
        If `character` is `None`, the character at `start_charno` is used as the match target.

        Args:
            start_charno: Start index (inclusive). Must satisfy `0 <= start_charno < len(self.source)`.
            boundary_charno: Exclusive lower bound. If `None`, defaults to `-1` (meaning scan
                            until before index -1, i.e., include index 0).
                            Must satisfy `-1 <= boundary_charno < start_charno`.
            character: The character to match. If `None`, uses `self.source[start_charno]`.

        Returns:
            Number of consecutive matching characters in the range `(boundary_charno, start_charno]`.
            If `character` is provided and does not equal the character at `start_charno`,
            returns `0` (the first character already fails to match).

        Raises:
            ValueError: If the range `(boundary_charno, start_charno]` is invalid, i.e.:
                        - `start_charno < 0` or `start_charno >= len(self.source)`
                        - `boundary_charno < -1` or `boundary_charno >= start_charno`
                        - `boundary_charno` is not `None` and violates the above.
        """
        source_len = len(self.source)

        if boundary_charno is None:
            boundary_charno = -1

        if not (-1 <= boundary_charno < start_charno < source_len):
            raise ValueError(
                f"Invalid range: boundary_charno={boundary_charno}, start_charno={start_charno}, "
                f"source_len={source_len}. Must satisfy -1 <= boundary < start < source_len"
            )

        if character is None:
            character = self.source[start_charno]

        match_count = 0
        for current_charno in range(start_charno, boundary_charno, -1):
            if self.source[current_charno] != character:
                break
            match_count += 1
        return match_count

    def next_non_space_or_tab_charno(
        self,
        start_charno: int,
        end_charno: int | None = None,
    ) -> int | None:
        """
        Return the index of the first character that is *not a space or tab* in `self.source[start_charno:end_charno]`.

        Scans forward from `start_charno` (inclusive) until `end_charno` (exclusive).
        If no such character is found within the range, returns `None`.

        Args:
            start_charno: Start index (inclusive). Must satisfy `0 <= start_charno < len(self.source)`.
            end_charno: Exclusive upper bound. If `None`, defaults to `len(self.source)`.
                        Must satisfy `start_charno < end_charno <= len(self.source)`.

        Returns:
            The character index (charno) of the first character that is not a space or tab,
            or `None` if all characters in the range are spaces/tabs.

        Raises:
            ValueError: If the range `[start_charno, end_charno)` is invalid, i.e.:
                        - `start_charno < 0` or `start_charno >= len(self.source)`
                        - `end_charno > len(self.source)`
                        - `start_charno >= end_charno` (empty range not allowed)
        """
        source_len = len(self.source)

        if end_charno is None:
            end_charno = source_len

        if not (0 <= start_charno < end_charno <= source_len):
            raise ValueError(
                f"Invalid range: start_charno={start_charno}, end_charno={end_charno}, "
                f"source_len={source_len}. Must satisfy 0 <= start < end <= source_len"
            )

        for current_charno in range(start_charno, end_charno):
            if not is_space_or_tab(self.source[current_charno]):
                return current_charno
        return None

    def previous_non_space_or_tab_charno(
        self,
        start_charno: int,
        boundary_charno: int | None = None,
    ) -> int | None:
        """
        Return the index of the first character that is *not a space or tab* when scanning backward in `self.source`.

        Scans backward from `start_charno` (inclusive) toward the beginning until a non-space/tab is found,
        or until `boundary_charno` (exclusive) is reached.
        If no such character is found within the range, returns `None`.

        Args:
            start_charno: Start index (inclusive). Must satisfy `0 <= start_charno < len(self.source)`.
            boundary_charno: Exclusive lower bound. If `None`, defaults to `-1` (meaning scan down to
                            and including index 0). Must satisfy `-1 <= boundary_charno < start_charno`.

        Returns:
            The character index (charno) of the first character that is not a space or tab,
            or `None` if all characters in the range `(boundary_charno, start_charno]` are spaces/tabs.

        Raises:
            ValueError: If `start_charno` is out of range, or `boundary_charno` is invalid.
        """
        source_len = len(self.source)

        if boundary_charno is None:
            boundary_charno = -1

        if not (-1 <= boundary_charno < start_charno < source_len):
            raise ValueError(
                f"Invalid range: boundary_charno={boundary_charno}, start_charno={start_charno}, "
                f"source_len={source_len}. Must satisfy -1 <= boundary < start < source_len"
            )

        for current_charno in range(start_charno, boundary_charno, -1):
            if not is_space_or_tab(self.source[current_charno]):
                return current_charno

        return None

    def resolve_next_non_space_or_tab(
        self,
        start: ColnoWithResolution,
        end_charno: int | None = None,
    ) -> ColnoWithResolution:
        """
        Advance past consecutive spaces and tabs, returning the column position after them.

        Starting from the resolved character index and column given by `start`, this method
        consumes all leading spaces and tabs up to (but not including) `end_charno`.
        It returns a new `ColnoWithResolution` whose `colno` is the original column plus
        the total visual width of the consumed whitespace, and whose `resolution` points to:

        - the first character that is neither space nor tab (if any), or
        - `end_charno` if the entire scanned range consists only of whitespace.

        If the character at the starting position is not a space or tab, the method returns
        `start` unchanged (no characters are consumed).

        Args:
            start: Starting column and character index.
            end_charno: Exclusive character index limit. If `None`, scans to the end of
                the source string.

        Returns:
            A `ColnoWithResolution` representing the column after the whitespace run,
            with a resolution that includes the character index of the first non-whitespace
            (or `end_charno`) and its visual width (0 when at the limit).

        Raises:
            ValueError: If the starting character index is out of range or not less than
                `end_charno` (when provided).
        """
        if end_charno is None:
            end_charno = len(self.source)

        start_charno = start.resolution.charno
        if not (0 <= start_charno < end_charno):
            raise ValueError(
                f"Invalid start character index {start_charno}; expected 0 <= start < {end_charno}"
            )

        if not is_space_or_tab(self.source[start_charno]):
            return start

        consumed_width = start.resolution.remaining_columns

        for current_charno in range(start_charno + 1, end_charno):
            current_char = self.source[current_charno]
            current_char_width = commonmark_char_width(
                start_colno=consumed_width + start.colno,
                character=current_char,
            )

            if not is_space_or_tab(current_char):
                return ColnoWithResolution(
                    colno=start.colno + consumed_width,
                    resolution=ColnoResolution(
                        charno=current_charno,
                        char_width=current_char_width,
                        inner_colno=0,
                    ),
                )

            consumed_width += current_char_width

        return ColnoWithResolution(
            colno=start.colno + consumed_width,
            resolution=ColnoResolution(
                charno=end_charno,
                char_width=0,
                inner_colno=0,
            ),
        )

    def get_line_content(self, lineno: int, include_end: bool = False) -> str:
        """
        Returns the source text of a specified line.

        The line is extracted using the line descriptor's
        `current_content_start_charno` (actual content start, after indentation)
        and `line_end_charno` (position of the newline or end of line).

        Args:
            lineno: Zero-based line index.
            include_end: If `True`, includes the trailing newline character
                        (if present) in the returned string.

        Returns:
            The line content as a substring of the source.
        """
        line_descriptor = self.line_descriptors[lineno]
        return self.source[
            line_descriptor.current_content_start_charno : line_descriptor.line_end_charno
            + (1 if include_end else 0)
        ]
