from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand
from pmark.parser.block.rule import BlockParserRule
from pmark.parser.block.commonmark.rules.locals.list import ListLocals


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
