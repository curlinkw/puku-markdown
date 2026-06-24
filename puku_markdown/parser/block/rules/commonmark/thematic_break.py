from puku_markdown._utils.constants import (
    THEMATIC_BREAK_MARKERS,
    THEMATIC_BREAK_MIN_MARKER_COUNT,
)
from puku_markdown._utils.predicates import is_space_or_tab
from puku_markdown.elements.block.commonmark.thematic_break import ThematicBreak
from puku_markdown.parser.block.command import BlockParserCommand
from puku_markdown.parser.block.frame_actuals import BlockParserFrameActuals
from puku_markdown.parser.block.logger import logger
from puku_markdown.parser.block.rule_context import BlockParserRuleContext
from puku_markdown.parser.block.state import BlockParserState


def thematic_break_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Thematic break rule.

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
        "Entered into thematic_break_rule at state.current_lineno=%r; line_span=%r",
        state.current_lineno,
        context.line_span,
    )

    start_lineno = context.line_span.start_lineno

    if (
        not state.line_descriptors[start_lineno].is_lazy_continuation
    ) and state.meets_indented_code_block_indent(start_lineno):
        return BlockParserCommand.with_commit_rejection_kind()

    if state.is_content_start_beyond_source(start_lineno):
        return BlockParserCommand.with_commit_rejection_kind()

    marker_charno = state.line_descriptors[start_lineno].current_content_start_charno
    marker = state.source[marker_charno]

    if marker not in THEMATIC_BREAK_MARKERS:
        return BlockParserCommand.with_commit_rejection_kind()

    current_charno = marker_charno + 1
    marker_count = 1

    while current_charno < state.line_descriptors[start_lineno].line_end_charno:
        character = state.source[current_charno]
        current_charno += 1

        if character == marker:
            marker_count += 1
            continue

        if not is_space_or_tab(character):
            return BlockParserCommand.with_commit_rejection_kind()

    if marker_count < THEMATIC_BREAK_MIN_MARKER_COUNT:
        return BlockParserCommand.with_commit_rejection_kind()

    if context.is_speculative_mode:
        return BlockParserCommand.with_commit_success_kind()

    state.current_lineno = context.line_span.start_lineno + 1
    block = ThematicBreak(markup=marker * marker_count)

    inherited_attributes.expect_block_stream()(block)

    return BlockParserCommand.with_commit_success_kind()
