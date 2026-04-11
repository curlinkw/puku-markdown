from pmark.parser.block.state import BlockParserState
from pmark.parser.block.command import BlockParserCommand, BlockParserCommandKind
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.commonmark.rules.locals.paragraph import ParagraphLocals
from pmark.parser.block.rule import BlockParserRule


def paragraph_rule(
    state: BlockParserState, context: BlockParserRuleContext
) -> BlockParserCommand:
    if not context.is_bound_to_production:
        context.bind_production(
            production=BlockParserRule.PARAGRAPH_RULE,
            local_attributes=ParagraphLocals(),
        )

    local_attrs = context.expect_local_attributes(
        expected_production=BlockParserRule.PARAGRAPH_RULE,
        expected_locals_type=ParagraphLocals,
    )

    return BlockParserCommand()
