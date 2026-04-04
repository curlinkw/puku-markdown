from pmark.lexer.block.state import BlockLexerState
from pmark.lexer.block.command import BlockLexerCommand, BlockLexerCommandKind
from pmark.lexer.block.rule_context import BlockLexerRuleContext
from pmark.lexer.block.commonmark.rules.locals.paragraph import ParagraphLocals
from pmark.lexer.block.rule import BlockLexerRule


def paragraph_rule(
    state: BlockLexerState, context: BlockLexerRuleContext
) -> BlockLexerCommand:
    if not context.is_bound_to_production:
        context.bind_production(
            production=BlockLexerRule.PARAGRAPH_RULE, local_attributes=ParagraphLocals()
        )

    local_attrs = context.expect_local_attributes(
        expected_production=BlockLexerRule.PARAGRAPH_RULE,
        expected_locals_type=ParagraphLocals,
    )

    return BlockLexerCommand()
