from dataclasses import replace

from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand, BlockParserCommandKind
from pmark.parser.block.rule import BlockParserRule
from pmark.parser.block.commonmark.rules.locals.blockquote import BlockquoteLocals
from pmark.parser.block.line_descriptor import LineDescriptor
from pmark.parser.block.frame_spec import BlockParserFrameSpec
from pmark.parser.block.rule_chain import BlockParserRuleChain
from pmark.parser.block.block_stream import BlockParserBlockStream
from pmark.parser.block.logger import logger
from pmark.elements.block.commonmark.blockquote import Blockquote
from pmark.persistent_list.transactional_editor import TransactionalEditor
from pmark.column_resolution import ColnoWithResolution, ColnoResolution
from pmark.line_span import LineSpan
from pmark._utils.metrics import commonmark_char_width
from pmark._utils.predicates import is_space_or_tab
from pmark._utils.constants import GREATER_THAN_CHARACTER


def _try_consume_blockquote_prefix(
    state: BlockParserState,
    line_descriptors_editor: TransactionalEditor[LineDescriptor],
    lineno: int,
) -> bool:
    current_line_descriptor = state.line_descriptors[lineno]

    if current_line_descriptor.is_blank:
        return False

    marker_charno = current_line_descriptor.current_content_start_charno
    marker = state.source[marker_charno]

    if marker != GREATER_THAN_CHARACTER:
        return False

    after_marker_charno = marker_charno + 1

    if (after_marker_charno >= current_line_descriptor.line_end_charno) or (
        not is_space_or_tab(state.source[after_marker_charno])
    ):
        line_descriptors_editor[lineno] = replace(
            current_line_descriptor,
            current_after_marker_charno=current_line_descriptor.line_end_charno,
            current_indented_marker_width=(
                current_line_descriptor.current_content_indent_width + 1
            ),
            current_content_indent_width=0,
            current_content_start_charno=current_line_descriptor.line_end_charno,
        )
        return True

    # Invariant:
    # We do have space after marker here

    after_marker_char = state.source[after_marker_charno]
    after_marker_colno = current_line_descriptor.current_content_start_colno + 1

    after_marker_char_width = commonmark_char_width(
        start_colno=after_marker_colno,
        character=after_marker_char,
    )
    is_after_marker_char_wide = after_marker_char_width > 1

    content_start_charno = after_marker_charno + 1
    content_indent_width = 0

    if is_after_marker_char_wide or (
        after_marker_charno + 1 < current_line_descriptor.line_end_charno
    ):
        resolved_indent_start = (
            ColnoWithResolution(
                colno=after_marker_colno + 1,
                resolution=ColnoResolution(
                    charno=after_marker_charno,
                    char_width=after_marker_char_width,
                    inner_colno=1,
                ),
            )
            if is_after_marker_char_wide
            else ColnoWithResolution.at_character_start(
                start_colno=after_marker_colno + 1,
                charno=after_marker_charno + 1,
                character=state.source[after_marker_charno + 1],
            )
        )
        resolved_content_start = state.resolve_next_non_space_or_tab(
            start=resolved_indent_start,
            end_charno=current_line_descriptor.line_end_charno,
        )
        content_start_charno = resolved_content_start.resolution.charno
        content_indent_width = (
            resolved_content_start.colno - resolved_indent_start.colno
        )

    line_descriptors_editor[lineno] = replace(
        current_line_descriptor,
        current_after_marker_charno=(
            after_marker_charno + (0 if is_after_marker_char_wide else 1)
        ),
        current_indented_marker_width=(
            current_line_descriptor.current_content_indent_width + 2
        ),
        current_content_indent_width=content_indent_width,
        current_content_start_charno=content_start_charno,
    )

    return True


def blockquote_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Blockquote rule.
    """
    logger.debug(
        "Entered into blockquote_rule at state.current_lineno=%r; line_span=%r",
        state.current_lineno,
        context.line_span,
    )

    if not context.is_bound_to_production:
        start_lineno = context.line_span.start_lineno

        if __debug__:
            if state.line_descriptors[start_lineno].is_lazy_continuation:
                raise RuntimeError(
                    f"Internal parser error: lazy continuation line {start_lineno} "
                    "was not consumed by the previous block rule."
                )

        if state.meets_indented_code_block_indent(start_lineno):
            logger.debug(
                "Rejected blockquote_rule because of `meets_indented_code_block_indent`"
            )
            return BlockParserCommand.with_commit_rejection_kind()

        if state.is_content_start_beyond_source(start_lineno):
            logger.debug(
                "Rejected blockquote_rule because of `is_content_start_beyond_source`"
            )
            return BlockParserCommand.with_commit_rejection_kind()

        if (
            state.source[
                state.line_descriptors[start_lineno].current_content_start_charno
            ]
            != GREATER_THAN_CHARACTER
        ):
            logger.debug(
                "Rejected blockquote_rule because of `wrong marker`. With line descriptor: %r",
                state.line_descriptors[start_lineno],
            )
            return BlockParserCommand.with_commit_rejection_kind()

        if context.is_speculative_mode:
            return BlockParserCommand.with_commit_success_kind()

        start_local_attrs = BlockquoteLocals(
            line_descriptors_editor=TransactionalEditor[LineDescriptor](
                target=state.line_descriptors
            ),
            current_lineno=start_lineno + 1,
        )

        start_local_attrs.line_descriptors_editor.enter_transaction()

        _try_consume_blockquote_prefix(
            state=state,
            line_descriptors_editor=start_local_attrs.line_descriptors_editor,
            lineno=start_lineno,
        )

        start_local_attrs.prev_marked_line_was_empty |= state.is_blank_line(
            start_lineno
        )

        context.bind_production(
            production=BlockParserRule.BLOCKQUOTE,
            local_attributes=start_local_attrs,
        )

    local_attrs = context.expect_local_attributes(
        expected_production=BlockParserRule.BLOCKQUOTE,
        expected_locals_type=BlockquoteLocals,
    )

    if local_attrs.nested_parse_completed:
        state.current_block_indent_width = (
            local_attrs.expect_current_block_indent_width()
        )

        local_attrs.line_descriptors_editor.exit_transaction()

        inherited_attributes.expect_block_stream()(local_attrs.expect_block())

        return BlockParserCommand.with_commit_success_kind()

    if context.lookahead_matched is None:
        pass
    elif context.lookahead_matched:
        logger.debug("Set continuation_line_limit=%r", local_attrs.current_lineno)

        local_attrs.is_terminated = True
        local_attrs.continuation_line_limit = local_attrs.current_lineno

        if state.current_block_indent_width > 0:
            current_line_descriptor = state.line_descriptors[local_attrs.current_lineno]
            local_attrs.line_descriptors_editor[local_attrs.current_lineno] = replace(
                current_line_descriptor,
                current_content_indent_width=(
                    current_line_descriptor.current_content_indent_width
                    - state.current_block_indent_width
                ),
            )
    else:
        current_line_descriptor = state.line_descriptors[local_attrs.current_lineno]
        local_attrs.line_descriptors_editor[local_attrs.current_lineno] = replace(
            current_line_descriptor, is_lazy_continuation=True
        )

        local_attrs.current_lineno += 1

    context.lookahead_matched = None

    while (not local_attrs.is_terminated) and (
        local_attrs.current_lineno < context.line_span.end_lineno
    ):
        if state.is_blank_line(local_attrs.current_lineno):
            logger.debug(
                "Blockquote is terminated because of `blank_line` at line %r",
                state.current_lineno,
            )
            break

        if not state.is_line_outdented(local_attrs.current_lineno):
            if _try_consume_blockquote_prefix(
                state=state,
                line_descriptors_editor=local_attrs.line_descriptors_editor,
                lineno=local_attrs.current_lineno,
            ):
                logger.debug(
                    "_try_consume_blockquote_prefix success at line %r",
                    local_attrs.current_lineno,
                )
                local_attrs.current_lineno += 1
                local_attrs.prev_marked_line_was_empty |= state.is_blank_line(
                    local_attrs.current_lineno
                )
                continue

        if local_attrs.prev_marked_line_was_empty:
            logger.debug(
                "Blockquote is terminated because of `prev_marked_line_was_empty` at line %r",
                state.current_lineno,
            )
            break

        return BlockParserCommand(
            kind=BlockParserCommandKind.LOOKAHEAD_ANY_RULE_MATCHES,
            child_frame_spec=BlockParserFrameSpec(
                line_span=LineSpan(
                    start_lineno=local_attrs.current_lineno,
                    end_lineno=context.line_span.end_lineno,
                ),
                rule_chain=BlockParserRuleChain.BLOCKQUOTE_TERMINATION,
                actuals=BlockParserFrameActuals(
                    parent_production=BlockParserRule.BLOCKQUOTE,
                    block_stream=None,
                    continuation_line_limit=inherited_attributes.continuation_line_limit,
                ),
            ),
            origin_rule_context=context,
        )

    local_attrs.current_block_indent_width = state.current_block_indent_width
    state.current_block_indent_width = 0

    local_attrs.block = Blockquote()

    local_attrs.nested_parse_completed = True

    return BlockParserCommand(
        kind=BlockParserCommandKind.PARSE_NESTED,
        child_frame_spec=BlockParserFrameSpec(
            line_span=LineSpan(
                start_lineno=context.line_span.start_lineno,
                end_lineno=local_attrs.current_lineno,
            ),
            rule_chain=BlockParserRuleChain.FULL_COMMONMARK_RULE_CHAIN,
            actuals=BlockParserFrameActuals(
                parent_production=BlockParserRule.BLOCKQUOTE,
                block_stream=BlockParserBlockStream(
                    local_attrs.expect_block().children.append
                ),
                continuation_line_limit=local_attrs.continuation_line_limit,
            ),
        ),
        origin_rule_context=context,
    )
