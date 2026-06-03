from pmark.parser.block.state import BlockParserState
from pmark.parser.block.command import BlockParserCommand, BlockParserCommandKind
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.commonmark.rules.locals.paragraph import ParagraphLocals
from pmark.parser.block.rule import BlockParserRule
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.frame_spec import BlockParserFrameSpec
from pmark.parser.block.rule_chain import BlockParserRuleChain
from pmark.parser.block.logger import logger
from pmark.elements.block.commonmark.paragraph import Paragraph
from pmark.line_span import LineSpan


def paragraph_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Paragraph rule.
    """
    logger.debug(
        "Entered into paragraph_rule at state.current_lineno=%r; line_span=%r",
        state.current_lineno,
        context.line_span,
    )

    if context.is_speculative_mode:
        return BlockParserCommand.with_commit_success_kind()

    if not context.is_bound_to_production:
        context.bind_production(
            production=BlockParserRule.PARAGRAPH,
            local_attributes=ParagraphLocals(
                current_lineno=context.line_span.start_lineno + 1,
                end_lineno=(
                    state.line_count
                    if inherited_attributes.continuation_line_limit is None
                    else inherited_attributes.continuation_line_limit
                ),
            ),
        )

    local_attrs = context.expect_local_attributes(
        expected_production=BlockParserRule.PARAGRAPH,
        expected_locals_type=ParagraphLocals,
    )

    if context.lookahead_matched is not None:
        if context.lookahead_matched:
            local_attrs.is_terminated = True
        else:
            local_attrs.current_lineno += 1
        context.lookahead_matched = None

    while (
        not local_attrs.is_terminated
    ) and local_attrs.current_lineno < local_attrs.end_lineno:
        if state.is_blank_line(local_attrs.current_lineno):
            break

        if state.line_descriptors[local_attrs.current_lineno].is_lazy_continuation:
            local_attrs.current_lineno += 1
            continue

        if state.meets_indented_code_block_indent(local_attrs.current_lineno):
            local_attrs.current_lineno += 1
            continue

        return BlockParserCommand(
            kind=BlockParserCommandKind.LOOKAHEAD_ANY_RULE_MATCHES,
            child_frame_spec=BlockParserFrameSpec(
                line_span=LineSpan(
                    start_lineno=local_attrs.current_lineno,
                    end_lineno=local_attrs.end_lineno,
                ),
                rule_chain=BlockParserRuleChain.PARAGRAPH_TERMINATION,
                actuals=BlockParserFrameActuals(
                    parent_production=context.production,
                    block_stream=None,
                    continuation_line_limit=inherited_attributes.continuation_line_limit,
                ),
            ),
            origin_rule_context=context,
        )

    state.current_lineno = local_attrs.current_lineno

    block = Paragraph(
        content=state.indent_reduced_block_content(
            line_span=LineSpan(
                start_lineno=context.line_span.start_lineno,
                end_lineno=local_attrs.current_lineno,
            ),
            reduction_width=state.current_block_indent_width,
            keep_trailing_newline=False,
        ).strip(),
    )

    inherited_attributes.expect_block_stream()(block)

    return BlockParserCommand.with_commit_success_kind()
