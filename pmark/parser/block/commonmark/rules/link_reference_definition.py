from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand, BlockParserCommandKind
from pmark.parser.block.rule import BlockParserRule
from pmark.parser.block.rule_chain import BlockParserRuleChain
from pmark.parser.block.frame_spec import BlockParserFrameSpec
from pmark.parser.block.commonmark.rules.locals.link_reference_definition import (
    LinkReferenceDefinitionLocals,
    _LinkReferenceDefinitionStep,
)
from pmark.line_span import LineSpan
from pmark.common.predicates import is_space_or_tab
from pmark.common.constants import (
    LEFT_SQUARE_BRACKET_CHARACTER,
    RIGHT_SQUARE_BRACKET_CHARACTER,
    LINE_FEED_CHARACTER,
    BACKSLASH_CHARACTER,
    COLON_CHARACTER,
)

# https://chat.deepseek.com/share/gff9f7dvr76bzge04n


def _assess_is_current_line_terminator(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
    local_attrs: LinkReferenceDefinitionLocals,
) -> BlockParserCommand | None:
    if local_attrs.is_current_line_terminator is not None:
        return None

    if local_attrs.current_lineno >= local_attrs.end_lineno:
        local_attrs.is_current_line_terminator = True
        return None

    if state.is_blank_line(local_attrs.current_lineno):
        local_attrs.is_current_line_terminator = True
        return None

    if state.line_descriptors[local_attrs.current_lineno].is_lazy_continuation:
        local_attrs.is_current_line_terminator = False
        return None

    if state.meets_indented_code_block_indent(local_attrs.current_lineno):
        local_attrs.is_current_line_terminator = False
        return None

    return BlockParserCommand(
        kind=BlockParserCommandKind.LOOKAHEAD_ANY_RULE_MATCHES,
        child_frame_spec=BlockParserFrameSpec(
            line_span=LineSpan(
                start_lineno=local_attrs.current_lineno,
                end_lineno=local_attrs.end_lineno,
            ),
            rule_chain=BlockParserRuleChain.LINK_REFERENCE_DEFINITION_TERMINATION,
            actuals=BlockParserFrameActuals(
                parent_production=BlockParserRule.LINK_REFERENCE_DEFINITION,
                parent_block=None,
                continuation_line_limit=inherited_attributes.continuation_line_limit,
            ),
        ),
        origin_rule_context=context,
    )


def _scan_label(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
    local_attrs: LinkReferenceDefinitionLocals,
) -> BlockParserCommand | None:
    # Invariant:
    # We do handle resuming correctly here
    # Cause we do nothing in _assess_is_current_line_terminator
    # If local_attrs.is_current_line_terminator is not None

    while local_attrs.current_charno < len(local_attrs.content_buffer):
        current_char = local_attrs.content_buffer[local_attrs.current_charno]

        if current_char == LEFT_SQUARE_BRACKET_CHARACTER:
            return BlockParserCommand.with_commit_rejection_kind()

        if current_char == RIGHT_SQUARE_BRACKET_CHARACTER:
            local_attrs.label_end = local_attrs.current_charno
            break

        if current_char not in (LINE_FEED_CHARACTER, BACKSLASH_CHARACTER):
            local_attrs.current_charno += 1
            continue

        if current_char == BACKSLASH_CHARACTER:
            local_attrs.current_charno += 1

            if local_attrs.current_charno >= len(local_attrs.content_buffer):
                local_attrs.current_charno += 1
                continue

            current_char = local_attrs.content_buffer[local_attrs.current_charno]

        if current_char == LINE_FEED_CHARACTER:
            if (
                command := _assess_is_current_line_terminator(
                    state=state,
                    inherited_attributes=inherited_attributes,
                    context=context,
                    local_attrs=local_attrs,
                )
            ) is not None:
                return command

            if not local_attrs.expect_is_current_line_terminator():
                local_attrs.consume_line_and_advance(
                    line_content=state.get_line_content(
                        lineno=local_attrs.current_lineno, include_end=True
                    )
                )

        local_attrs.current_charno += 1

    if (
        (local_attrs.label_end is None)
        or (local_attrs.label_end + 1 >= len(local_attrs.content_buffer))
        or (local_attrs.content_buffer[local_attrs.label_end + 1] != COLON_CHARACTER)
    ):
        return BlockParserCommand.with_commit_rejection_kind()

    local_attrs.current_charno = local_attrs.label_end + 2

    return None


def _skip_whitespace_with_continuation(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
    local_attrs: LinkReferenceDefinitionLocals,
) -> BlockParserCommand | None:
    # Invariant:
    # We do handle resuming correctly here
    # Cause we do nothing in _assess_is_current_line_terminator
    # If local_attrs.is_current_line_terminator is not None

    while local_attrs.current_charno < len(local_attrs.content_buffer):
        current_char = local_attrs.content_buffer[local_attrs.current_charno]

        if is_space_or_tab(current_char):
            local_attrs.current_charno += 1
            continue

        if current_char == LINE_FEED_CHARACTER:
            if (
                command := _assess_is_current_line_terminator(
                    state=state,
                    inherited_attributes=inherited_attributes,
                    context=context,
                    local_attrs=local_attrs,
                )
            ) is not None:
                return command

            if not local_attrs.expect_is_current_line_terminator():
                local_attrs.consume_line_and_advance(
                    line_content=state.get_line_content(
                        lineno=local_attrs.current_lineno, include_end=True
                    )
                )

            local_attrs.current_charno += 1
        else:
            break

    return None


def _scan_destination(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
    local_attrs: LinkReferenceDefinitionLocals,
) -> BlockParserCommand | None:
    pass


def _dispatch_step(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
    local_attrs: LinkReferenceDefinitionLocals,
) -> BlockParserCommand | None:
    match local_attrs.step:
        case _LinkReferenceDefinitionStep.SCAN_LABEL:
            command = _scan_label(
                state=state,
                inherited_attributes=inherited_attributes,
                context=context,
                local_attrs=local_attrs,
            )
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
            != LEFT_SQUARE_BRACKET_CHARACTER
        ):
            return BlockParserCommand.with_commit_rejection_kind()

        context.bind_production(
            production=BlockParserRule.LINK_REFERENCE_DEFINITION,
            local_attributes=LinkReferenceDefinitionLocals(
                current_lineno=start_lineno + 1,
                content_buffer=state.source[
                    start_line_descriptor.current_content_start_charno : start_line_descriptor.line_end_charno
                    + 1
                ],
                end_lineno=(
                    state.line_count
                    if inherited_attributes.continuation_line_limit is None
                    else inherited_attributes.continuation_line_limit
                ),
            ),
        )

    local_attrs = context.expect_local_attributes(
        expected_production=BlockParserRule.LINK_REFERENCE_DEFINITION,
        expected_locals_type=LinkReferenceDefinitionLocals,
    )

    if context.lookahead_matched is not None:
        local_attrs.is_current_line_terminator = context.lookahead_matched
        context.lookahead_matched = None

    while (
        command := _dispatch_step(
            state=state,
            inherited_attributes=inherited_attributes,
            context=context,
            local_attrs=local_attrs,
        )
    ) is None:
        pass

    return command
