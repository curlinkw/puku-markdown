from dataclasses import dataclass

from pmark.tokens import Token
from pmark.utils import is_tab, is_space_or_tab, is_line_ending


@dataclass(slots=True)
class BlockLexerState:
    source: str
    """
    Source text.
    """

    tokens: list[Token]
    """
    The list of tokens produced so far.
    """

    # Pre-computed line boundaries.

    line_start_indices: list[int]  # bMark
    """
    For each line, the index in `source` where the line begins.
    A fake entry is added at the end for safe bounds checks.
    """

    line_end_indices: list[int]  # eMark
    """
    For each line, the index in `source` just after the line's content
    (i.e. the position of the newline character or the end of the string).
    A fake entry is added at the end for safe bounds checks.
    """

    leading_whitespace_counts: list[int]  # tShift
    """
    Number of leading whitespace characters (spaces and tabs) before the
    first non-space character on each line. Tabs count as **one** whitespace
    character (raw count, not expanded).
    """

    leading_indent_space_counts: list[int]  # sCount
    """
    The indentation level of each line expressed in **spaces**, with tabs
    expanded to the next multiple of 4. This is the effective visual indent.
    """

    base_indent_space_counts: list[int]  # bsCount
    """
    Virtual indentation (in spaces) used to adjust tab expansion when the
    beginning of a line has been logically moved (e.g. by blockquote markers).
    Initially zero for every line; mutated during parsing to preserve
    correct tab expansion when `line_start_indices` is overridden.
    """

    line_count: int  # lineMax
    """
    Total number of real lines in the source (excluding the final fake entry).
    """

    def _precompute_lines(self) -> None:
        """
        Precompute line boundaries and indentation.
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
                        (4 - leading_indent_space_count % 4) if is_tab(character) else 1
                    )

                    continue
                else:
                    in_leading_whitespaces = False

            if (is_last_character := (position + 1 >= source_length)) or is_line_ending(
                character, self.source[position + 1]
            ):
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
