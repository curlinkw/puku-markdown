from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand
from pmark.constants import (
    FENCED_CODE_BLOCK_MARKERS,
    FENCED_CODE_BLOCK_MIN_MARKER_COUNT,
    BACKTICK_CHAR,
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
    start_line_desciptor = state.line_descriptors[start_lineno]

    if __debug__:
        if start_line_desciptor.is_lazy_continuation:
            raise RuntimeError(
                f"Internal parser error: lazy continuation line {start_lineno} "
                "was not consumed by the previous block rule."
            )

    if state.meets_indented_code_block_indent(start_lineno):
        return BlockParserCommand.with_commit_rejection_kind()

    if start_line_desciptor.current_content_length < FENCED_CODE_BLOCK_MIN_MARKER_COUNT:
        return BlockParserCommand.with_commit_rejection_kind()

    marker_charno = start_line_desciptor.current_content_start_charno
    marker = state.source[marker_charno]

    if marker not in FENCED_CODE_BLOCK_MARKERS:
        return BlockParserCommand.with_commit_rejection_kind()

    markup_length = state.count_run_of_char(
        start_charno=marker_charno, character=marker
    )

    if markup_length < FENCED_CODE_BLOCK_MIN_MARKER_COUNT:
        return BlockParserCommand.with_commit_rejection_kind()

    markup = state.source[marker_charno : marker_charno + markup_length]
    info_string = state.source[
        marker_charno + markup_length : start_line_desciptor.line_end_charno
    ]

    if (marker == BACKTICK_CHAR) and (marker in info_string):
        return BlockParserCommand.with_commit_rejection_kind()

    if context.is_speculative_mode:
        return BlockParserCommand.with_commit_success_kind()

    current_lineno = start_lineno + 1

    while current_lineno < context.line_span.end_lineno:
        if __debug__:
            if state.line_descriptors[current_lineno].is_lazy_continuation:
                raise RuntimeError(
                    f"Internal parser error: lazy continuation line {current_lineno} "
                    "was not consumed by the previous block rule."
                )
