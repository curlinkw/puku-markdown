from pmark.parser.block.state import BlockParserState
from pmark.parser.block.command import BlockParserCommand, BlockParserCommandKind
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.commonmark.rules.locals.paragraph import ParagraphLocals
from pmark.parser.block.rule import BlockParserRule
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.frame_spec import BlockParserFrameSpec
from pmark.parser.block.rule_chain import BlockParserRuleChain
from pmark.elements.block.commonmark.paragraph import Paragraph
from pmark.line_span import LineSpan


def _finalize(
    state: BlockParserState,
    local_attrs: ParagraphLocals,
    context: BlockParserRuleContext,
) -> None:
    state.current_lineno = local_attrs.current_lineno

    local_attrs.block_element.content = state.indent_reduced_block_content(
        line_span=LineSpan(
            start_lineno=context.line_span.start_lineno,
            end_lineno=local_attrs.current_lineno,
        ),
        reduction_width=state.current_block_indent_width,
        keep_trailing_newline=False,
    ).strip()


def paragraph_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    if not context.is_bound_to_production:
        context.bind_production(
            production=BlockParserRule.PARAGRAPH_RULE,
            local_attributes=ParagraphLocals(
                current_lineno=context.line_span.start_lineno + 1,
                end_lineno=(
                    state.line_count
                    if inherited_attributes.paragraph_line_limit is None
                    else inherited_attributes.paragraph_line_limit
                ),
                block_element=Paragraph(),
            ),
        )

    local_attrs = context.expect_local_attributes(
        expected_production=BlockParserRule.PARAGRAPH_RULE,
        expected_locals_type=ParagraphLocals,
    )

    # Invariant:
    # We always come here
    if not inherited_attributes.try_attach_parent(local_attrs.block_element):
        state.target_document.append_root_block(local_attrs.block_element)

    if context.lookahead_matched is not None:
        if context.lookahead_matched:
            _finalize(state=state, local_attrs=local_attrs, context=context)
            return BlockParserCommand(kind=BlockParserCommandKind.COMMIT_SUCCESS)
        else:
            local_attrs.current_lineno += 1
        context.lookahead_matched = None

    while local_attrs.current_lineno < local_attrs.end_lineno:
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
                rule_chain=BlockParserRuleChain.PARAGRAPH_TERMINATION_RULE_CHAIN,
                actuals=BlockParserFrameActuals(
                    parent_production=context.production,
                    parent_block=local_attrs.block_element,
                ),
                current_rule_context=context,
            ),
        )

    _finalize(state=state, local_attrs=local_attrs, context=context)

    return BlockParserCommand(kind=BlockParserCommandKind.COMMIT_SUCCESS)
