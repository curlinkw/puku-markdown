from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand
from pmark.elements.block.commonmark.fenced_code_block import FencedCodeBlock
from pmark.line_span import LineSpan
from pmark.common.constants import (
    FENCED_CODE_BLOCK_MARKERS,
    FENCED_CODE_BLOCK_MIN_MARKER_COUNT,
    BACKTICK_CHARACTER,
)


def fenced_code_block_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Fenced code block rule.

    This rule is *terminal* - it never suspends or yields. It either succeeds
    (`COMMIT_SUCCESS`) or rejects (`COMMIT_REJECTION`) in the same
    call. It has no locals (no internal parsing state to resume) and does not
    bind `context` to any production, because no recursive descent is needed.

    Invariants:
        - No recursive calls to other rules.
        - No use of `context.locals` (no suspension points).
        - Returns only `COMMIT_SUCCESS` or `COMMIT_REJECTION` command kinds.
    """

    start_lineno = context.line_span.start_lineno
    start_line_descriptor = state.line_descriptors[start_lineno]

    if __debug__:
        if start_line_descriptor.is_lazy_continuation:
            raise RuntimeError(
                f"Internal parser error: lazy continuation line {start_lineno} "
                "was not consumed by the previous block rule."
            )

    if state.meets_indented_code_block_indent(start_lineno):
        return BlockParserCommand.with_commit_rejection_kind()

    if (
        start_line_descriptor.current_content_length
        < FENCED_CODE_BLOCK_MIN_MARKER_COUNT
    ):
        return BlockParserCommand.with_commit_rejection_kind()

    start_marker_charno = start_line_descriptor.current_content_start_charno
    start_marker = state.source[start_marker_charno]

    if start_marker not in FENCED_CODE_BLOCK_MARKERS:
        return BlockParserCommand.with_commit_rejection_kind()

    start_markup_length = state.count_run_of_char(
        start_charno=start_marker_charno,
        end_charno=start_line_descriptor.line_end_charno,
        character=start_marker,
    )

    if start_markup_length < FENCED_CODE_BLOCK_MIN_MARKER_COUNT:
        return BlockParserCommand.with_commit_rejection_kind()

    start_markup = state.source[
        start_marker_charno : start_marker_charno + start_markup_length
    ]
    start_info_string = state.source[
        start_marker_charno
        + start_markup_length : start_line_descriptor.line_end_charno
    ]

    if (start_marker == BACKTICK_CHARACTER) and (start_marker in start_info_string):
        return BlockParserCommand.with_commit_rejection_kind()

    if context.is_speculative_mode:
        return BlockParserCommand.with_commit_success_kind()

    current_lineno = start_lineno + 1
    has_closing_fence: bool = False

    while current_lineno < context.line_span.end_lineno:
        current_line_descriptor = state.line_descriptors[current_lineno]

        if __debug__:
            if current_line_descriptor.is_lazy_continuation:
                raise RuntimeError(
                    f"Internal parser error: lazy continuation line {current_lineno} "
                    "was not consumed by the previous block rule."
                )

        if state.is_line_outdented(current_lineno) and (
            not current_line_descriptor.is_blank
        ):
            break

        if state.is_content_start_beyond_source(current_lineno):
            break

        if current_line_descriptor.is_blank:
            current_lineno += 1
            continue

        current_marker_charno = current_line_descriptor.current_content_start_charno
        current_marker = state.source[current_marker_charno]

        if current_marker != start_marker:
            current_lineno += 1
            continue

        if state.meets_indented_code_block_indent(current_lineno):
            current_lineno += 1
            continue

        current_markup_length = state.count_run_of_char(
            start_charno=current_marker_charno,
            end_charno=current_line_descriptor.line_end_charno,
            character=current_marker,
        )

        if current_markup_length < start_markup_length:
            current_lineno += 1
            continue

        if (
            current_marker_charno + current_markup_length
            >= current_line_descriptor.line_end_charno
        ):
            has_closing_fence = True
            break

        next_non_space_or_tab = state.next_non_space_or_tab_charno(
            start_charno=current_marker_charno + current_markup_length,
            end_charno=current_line_descriptor.line_end_charno,
        )

        if next_non_space_or_tab is not None:
            current_lineno += 1
            continue

        has_closing_fence = True
        break

    state.current_lineno = current_lineno + (1 if has_closing_fence else 0)

    block = FencedCodeBlock(
        parent=None,
        markup=start_markup,
        info_string=start_info_string,
        content=state.indent_reduced_block_content(
            line_span=LineSpan(
                start_lineno=start_lineno + 1, end_lineno=current_lineno
            ),
            reduction_width=start_line_descriptor.current_content_indent_width,
            keep_trailing_newline=True,
        ),
    )

    if not inherited_attributes.try_attach_parent(block):
        state.target_document.append_root_block(block)

    return BlockParserCommand.with_commit_success_kind()
