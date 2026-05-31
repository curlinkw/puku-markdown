from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand


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
