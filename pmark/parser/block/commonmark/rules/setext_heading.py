from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand, BlockParserCommandKind
from pmark.parser.block.rule import BlockParserRule
from pmark.parser.block.frame_spec import BlockParserFrameSpec
from pmark.parser.block.rule_chain import BlockParserRuleChain
from pmark.parser.block.line_descriptor import LineDescriptor
from pmark.parser.block.logger import logger
from pmark.parser.block.commonmark.rules.locals.setext_heading import (
    SetextHeadingLocals,
)
from pmark.elements.block.commonmark.setext_heading import SetextHeading
from pmark.line_span import LineSpan
from pmark._utils.constants import SETEXT_HEADING_MARKERS, EQUALS_SIGN_CHARACTER


def _parse_setext_underline(
    state: BlockParserState, lineno: int, line_descriptor: LineDescriptor
) -> tuple[str, int] | None:
    """
    Return (marker, heading_level) if the line is a valid Setext underline.

    A valid underline line must:
    - Not be blank.
    - Not be outdented (indentation less than block indent).
    - Start with either '=' or '-'.
    - Consist only of that same marker character, optionally followed by spaces,
      until the end of the line.

    Args:
        state: Block parser state.
        lineno: Line number (unused in implementation but kept for context).
        line_descriptor: Descriptor for the line to check.

    Returns:
        A tuple (marker, heading_level) where:
        - marker is the underline character (`'-'` or `'='`).
        - heading_level is 1 for `'='`, 2 for `'-'`.
        Returns None if the line is not a valid Setext underline.
    """

    if line_descriptor.is_blank:
        return None

    if state.is_line_outdented(lineno):
        return None

    marker_charno = line_descriptor.current_content_start_charno
    marker = state.source[marker_charno]
    heading_level = 1 if marker == EQUALS_SIGN_CHARACTER else 2

    if marker not in SETEXT_HEADING_MARKERS:
        return None

    markup_length = state.count_run_of_char(
        start_charno=marker_charno,
        end_charno=line_descriptor.line_end_charno,
        character=marker,
    )

    if marker_charno + markup_length >= line_descriptor.line_end_charno:
        return marker, heading_level

    return (
        (marker, heading_level)
        if (
            state.next_non_space_or_tab_charno(
                start_charno=marker_charno + markup_length,
                end_charno=line_descriptor.line_end_charno,
            )
            is None
        )
        else None
    )


def setext_heading_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Setext heading rule.
    """
    logger.debug(
        "Entered into setext_heading_rule at state.current_lineno=%r; line_span=%r",
        state.current_lineno,
        context.line_span,
    )

    if not context.is_bound_to_production:
        if __debug__:
            if state.line_descriptors[
                context.line_span.start_lineno
            ].is_lazy_continuation:
                raise RuntimeError(
                    f"Internal parser error: lazy continuation line {context.line_span.start_lineno} "
                    "was not consumed by the previous block rule."
                )

        if state.meets_indented_code_block_indent(context.line_span.start_lineno):
            return BlockParserCommand.with_commit_rejection_kind()

        context.bind_production(
            production=BlockParserRule.SETEXT_HEADING,
            local_attributes=SetextHeadingLocals(
                current_lineno=context.line_span.start_lineno + 1,
            ),
        )

    local_attrs = context.expect_local_attributes(
        expected_production=BlockParserRule.SETEXT_HEADING,
        expected_locals_type=SetextHeadingLocals,
    )

    if context.lookahead_matched is not None:
        if context.lookahead_matched:
            local_attrs.is_terminated = True
        else:
            local_attrs.current_lineno += 1
        context.lookahead_matched = None

    while (
        (not local_attrs.is_terminated)
        and (local_attrs.current_lineno < context.line_span.end_lineno)
        and (not state.is_blank_line(local_attrs.current_lineno))
    ):
        current_line_descriptor = state.line_descriptors[local_attrs.current_lineno]

        if current_line_descriptor.is_lazy_continuation:
            local_attrs.current_lineno += 1
            continue

        if state.meets_indented_code_block_indent(local_attrs.current_lineno):
            local_attrs.current_lineno += 1
            continue

        if (
            parsed_underline := _parse_setext_underline(
                state=state,
                lineno=local_attrs.current_lineno,
                line_descriptor=current_line_descriptor,
            )
        ) is not None:
            marker, heading_level = parsed_underline
            local_attrs.marker = marker
            local_attrs.heading_level = heading_level
            break

        return BlockParserCommand(
            kind=BlockParserCommandKind.LOOKAHEAD_ANY_RULE_MATCHES,
            child_frame_spec=BlockParserFrameSpec(
                line_span=LineSpan(
                    start_lineno=local_attrs.current_lineno,
                    end_lineno=context.line_span.end_lineno,
                ),
                rule_chain=BlockParserRuleChain.SETEXT_HEADING_TERMINATION,
                actuals=BlockParserFrameActuals(
                    parent_production=context.production,
                    block_stream=None,
                    continuation_line_limit=inherited_attributes.continuation_line_limit,
                ),
            ),
            origin_rule_context=context,
        )

    if (local_attrs.heading_level is None) or (local_attrs.marker is None):
        return BlockParserCommand.with_commit_rejection_kind()

    if context.is_speculative_mode:
        return BlockParserCommand.with_commit_success_kind()

    state.current_lineno = local_attrs.current_lineno + 1

    block = SetextHeading(
        marker=local_attrs.marker,
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
