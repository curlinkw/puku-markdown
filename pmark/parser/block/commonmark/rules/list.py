from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand
from pmark.parser.block.rule import BlockParserRule
from pmark.parser.block.commonmark.rules.locals.list import ListLocals
from pmark._utils.predicates import is_space_or_tab
from pmark._utils.constants import BULLET_LIST_MARKERS


def skipBulletListMarker(state: BlockParserState, lineno: int) -> int | None:
    if state.is_content_start_beyond_source(lineno):
        return None

    line_descriptor = state.line_descriptors[lineno]

    marker_charno = line_descriptor.current_content_start_charno
    marker = state.source[marker_charno]
    after_marker_charno = marker_charno + 1

    if marker not in BULLET_LIST_MARKERS:
        return None

    if after_marker_charno < line_descriptor.line_end_charno:
        after_marker_char = state.source[after_marker_charno]

        if not is_space_or_tab(after_marker_char):
            return None

    return after_marker_charno


def list_block_paragraph_terminator(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    start_lineno = context.line_span.start_lineno
    start_line_descriptor = state.line_descriptors[start_lineno]

    if not (
        context.is_speculative_mode
        and inherited_attributes.parent_production
        in (BlockParserRule.PARAGRAPH, BlockParserRule.SETEXT_HEADING)
    ):
        raise RuntimeError(
            (
                f"Internal parser error: list_block_paragraph_terminator called in invalid context: "
                f"speculative={context.is_speculative_mode}, "
                f"parent={inherited_attributes.parent_production}"
            )
        )

    if start_line_descriptor.is_lazy_continuation:
        raise RuntimeError(
            f"Internal parser error: lazy continuation line {start_lineno} "
            "was not consumed by the previous block rule."
        )

    if state.meets_indented_code_block_indent(start_lineno):
        return BlockParserCommand.with_commit_rejection_kind()

    is_start_line_outdented = state.is_line_outdented(start_lineno)

    if (
        (state.current_list_marker_indent is not None)
        and state.meets_indented_code_block_indent(
            lineno=start_lineno, relative_to_current_list_marker=True
        )
        and is_start_line_outdented
    ):
        return BlockParserCommand.with_commit_rejection_kind()


def list_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Link reference definition rule.
    """

    if not context.is_bound_to_production:
        start_lineno = context.line_span.start_lineno

        if state.meets_indented_code_block_indent(start_lineno):
            return BlockParserCommand.with_commit_rejection_kind()

        if (
            (state.current_list_marker_indent is not None)
            and state.meets_indented_code_block_indent(
                lineno=start_lineno, relative_to_current_list_marker=True
            )
            and state.is_line_outdented(start_lineno)
        ):
            return BlockParserCommand.with_commit_rejection_kind()

        context.bind_production(
            production=BlockParserRule.LIST, local_attributes=ListLocals()
        )

    local_attrs = context.expect_local_attributes(
        expected_production=BlockParserRule.LIST,
        expected_locals_type=ListLocals,
    )

    return BlockParserCommand.with_commit_rejection_kind()
