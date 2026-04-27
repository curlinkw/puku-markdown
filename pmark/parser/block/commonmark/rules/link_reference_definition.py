from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand
from pmark.parser.block.rule import BlockParserRule
from pmark.parser.block.commonmark.rules.locals.link_reference_definition import (
    LinkReferenceDefinitionLocals,
    _LinkReferenceDefinitionStep,
)
from pmark.constants import LEFT_SQUARE_BRACKET


def _scan_label_end(
    state: BlockParserState, local_attrs: LinkReferenceDefinitionLocals
) -> BlockParserCommand | None:
    pass


def _dispatch_step(
    state: BlockParserState, local_attrs: LinkReferenceDefinitionLocals
) -> BlockParserCommand | None:
    match local_attrs.step:
        case _LinkReferenceDefinitionStep.SCAN_LABEL_END:
            command = _scan_label_end(state=state, local_attrs=local_attrs)
        case _:
            raise ValueError(
                f"Unhandled link reference definition step: {local_attrs.step!r}"
            )
    return command


def link_reference_definition_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Link reference definition rule.
    """
    if not context.is_bound_to_production:
        start_lineno = context.line_span.start_lineno
        start_line_descriptor = state.line_descriptors[start_lineno]

        if __debug__:
            if start_line_descriptor.is_lazy_continuation:
                raise RuntimeError(
                    f"Internal parser error: lazy continuation line {start_lineno} "
                    "was not consumed by the previous block rule."
                )

        if state.meets_indented_code_block_indent(start_lineno):
            return BlockParserCommand.with_commit_rejection_kind()

        if (
            state.source[start_line_descriptor.current_content_start_charno]
            != LEFT_SQUARE_BRACKET
        ):
            return BlockParserCommand.with_commit_rejection_kind()

        context.bind_production(
            production=BlockParserRule.LINK_REFERENCE_DEFINITION,
            local_attributes=LinkReferenceDefinitionLocals(
                current_lineno=start_lineno + 1
            ),
        )

    local_attrs = context.expect_local_attributes(
        expected_production=BlockParserRule.LINK_REFERENCE_DEFINITION,
        expected_locals_type=LinkReferenceDefinitionLocals,
    )

    if context.lookahead_matched is not None:
        local_attrs.is_current_line_block_terminator = context.lookahead_matched
        context.lookahead_matched = None

    while (command := _dispatch_step(state=state, local_attrs=local_attrs)) is None:
        pass

    return command
