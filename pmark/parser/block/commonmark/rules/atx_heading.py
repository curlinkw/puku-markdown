from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand
from pmark.parser.block.line_descriptor import LineDescriptor
from pmark.parser.block.logger import logger
from pmark.elements.block.commonmark.atx_heading import AtxHeading
from pmark._utils.predicates import is_space_or_tab
from pmark._utils.constants import HASH_CHARACTER, ATX_HEADING_MAX_LEVEL


def _trailing_markup_start(
    state: BlockParserState,
    line_desciptor: LineDescriptor,
    after_markup_charno: int,
) -> int | None:
    if after_markup_charno + 1 >= line_desciptor.line_end_charno:
        return None

    last_non_space_or_tab_charno = state.previous_non_space_or_tab_charno(
        start_charno=line_desciptor.line_end_charno - 1,
        boundary_charno=after_markup_charno,
    )

    if last_non_space_or_tab_charno is None:
        return None

    trailing_markup_length = state.backward_count_run_of_char(
        start_charno=last_non_space_or_tab_charno,
        boundary_charno=after_markup_charno,
        character=HASH_CHARACTER,
    )

    return (
        last_non_space_or_tab_charno - trailing_markup_length + 1
        if (
            trailing_markup_length > 0
            and is_space_or_tab(
                state.source[last_non_space_or_tab_charno - trailing_markup_length]
            )
        )
        else None
    )


def atx_heading_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    ATX heading rule.

    This rule is *terminal* - it never suspends or yields. It either succeeds
    (`COMMIT_SUCCESS`) or rejects (`COMMIT_REJECTION`) in the same
    call. It has no locals (no internal parsing state to resume) and does not
    bind `context` to any production, because no recursive descent is needed.

    Invariants:
        - No recursive calls to other rules.
        - No use of `context.locals` (no suspension points).
        - Returns only `COMMIT_SUCCESS` or `COMMIT_REJECTION` command kinds.
    """
    logger.debug(
        "Entered into atx_heading_rule at state.current_lineno=%r; line_span=%r",
        state.current_lineno,
        context.line_span,
    )

    start_lineno = context.line_span.start_lineno
    start_line_descriptor = state.line_descriptors[start_lineno]

    if start_line_descriptor.is_lazy_continuation:
        raise RuntimeError(
            f"Internal parser error: lazy continuation line {start_lineno} "
            "was not consumed by the previous block rule."
        )

    if state.meets_indented_code_block_indent(start_lineno):
        logger.debug(
            "atx_heading_rule is rejected because of `meets_indented_code_block_indent`"
        )
        return BlockParserCommand.with_commit_rejection_kind()

    if start_line_descriptor.is_blank:
        logger.debug("atx_heading_rule is rejected because of `is_blank`")
        return BlockParserCommand.with_commit_rejection_kind()

    marker_charno = start_line_descriptor.current_content_start_charno
    marker = state.source[marker_charno]

    if marker != HASH_CHARACTER:
        logger.debug("atx_heading_rule is rejected because of `wrong marker`")
        return BlockParserCommand.with_commit_rejection_kind()

    markup_length = state.count_run_of_char(
        start_charno=marker_charno,
        end_charno=min(
            marker_charno + ATX_HEADING_MAX_LEVEL, start_line_descriptor.line_end_charno
        ),
        character=HASH_CHARACTER,
    )

    after_markup_charno = marker_charno + markup_length

    if (after_markup_charno < start_line_descriptor.line_end_charno) and (
        not is_space_or_tab(state.source[after_markup_charno])
    ):
        return BlockParserCommand.with_commit_rejection_kind()

    # Invariant:
    # after_markup_charno = line_end_charno, or
    # state.source[after_markup_charno] is space or tab

    logger.debug(
        "AtxHeading: matched with is_speculative_mode=%r", context.is_speculative_mode
    )

    if context.is_speculative_mode:
        return BlockParserCommand.with_commit_success_kind()

    trailing_markup_start = _trailing_markup_start(
        state=state,
        line_desciptor=start_line_descriptor,
        after_markup_charno=after_markup_charno,
    )

    block = AtxHeading(
        level=markup_length,
        content=state.source[
            after_markup_charno : start_line_descriptor.line_end_charno
            if trailing_markup_start is None
            else trailing_markup_start
        ].strip(),
    )

    inherited_attributes.expect_block_stream()(block)

    state.current_lineno = start_lineno + 1

    return BlockParserCommand.with_commit_success_kind()
