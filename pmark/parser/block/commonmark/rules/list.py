from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand
from pmark.parser.block.rule import BlockParserRule
from pmark.parser.block.commonmark.rules.locals.list import ListLocals
from pmark.parser.block.line_descriptor import LineDescriptor
from pmark.elements.block.commonmark.list import ListKind
from pmark._utils.predicates import is_space_or_tab, is_ascii_digit
from pmark._utils.constants import BULLET_LIST_MARKERS, ORDERED_LIST_MARKER_DELIMITERS


def _get_after_bullet_marker_charno(
    state: BlockParserState, line_descriptor: LineDescriptor
) -> int | None:
    # is_content_start_beyond_source
    if line_descriptor.current_content_start_charno >= len(state.source):
        return None

    marker_charno = line_descriptor.current_content_start_charno
    marker = state.source[marker_charno]

    if marker not in BULLET_LIST_MARKERS:
        return None

    after_marker_charno = marker_charno + 1

    if after_marker_charno < line_descriptor.line_end_charno and (
        not is_space_or_tab(state.source[after_marker_charno])
    ):
        return None

    return after_marker_charno


def _get_after_ordered_marker_charno(
    state: BlockParserState, line_descriptor: LineDescriptor
) -> int | None:
    # marker_number + marker_delimiter
    if line_descriptor.current_content_length < 2:
        return None

    marker_number_start_charno = line_descriptor.current_content_start_charno

    if not is_ascii_digit(state.source[marker_number_start_charno]):
        return None

    marker_delimiter_charno = next(
        (
            current_charno
            for current_charno in range(
                marker_number_start_charno + 1, line_descriptor.line_end_charno
            )
            if not is_ascii_digit(state.source[current_charno])
        ),
        None,
    )

    if (marker_delimiter_charno is None) or (
        state.source[marker_delimiter_charno] not in ORDERED_LIST_MARKER_DELIMITERS
    ):
        return None

    after_marker_charno = marker_delimiter_charno + 1

    if after_marker_charno < line_descriptor.line_end_charno and (
        not is_space_or_tab(state.source[after_marker_charno])
    ):
        return None

    return after_marker_charno


def _scan_marker(
    state: BlockParserState,
    line_descriptor: LineDescriptor,
    require_ordered_list_starts_with_one: bool,
) -> tuple[int, ListKind] | None:
    # is_terminating_paragraph = (not is_start_line_outdented)
    if (
        after_marker_charno := _get_after_bullet_marker_charno(
            state=state, line_descriptor=line_descriptor
        )
    ) is not None:
        return (after_marker_charno, ListKind.BULLET)

    if (
        after_marker_charno := _get_after_ordered_marker_charno(
            state=state, line_descriptor=line_descriptor
        )
    ) is not None:
        if (
            require_ordered_list_starts_with_one
            and int(
                state.source[
                    line_descriptor.current_content_start_charno : after_marker_charno
                    - 1
                ]
            )
            != 1
        ):
            return None

        return (after_marker_charno, ListKind.ORDERED)

    return None


def list_rule_as_terminator(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    start_lineno = context.line_span.start_lineno
    start_line_descriptor = state.line_descriptors[start_lineno]

    if not (
        context.is_speculative_mode
        and inherited_attributes.parent_production
        in (BlockParserRule.PARAGRAPH, BlockParserRule.SETEXT_HEADING)
    ):
        raise RuntimeError(
            (
                f"Internal parser error: list_block_paragraph_terminator called in invalid context: "
                f"speculative={context.is_speculative_mode}, "
                f"parent={inherited_attributes.parent_production}"
            )
        )

    if start_line_descriptor.is_lazy_continuation:
        # must be handled in parent
        raise RuntimeError(
            f"Internal parser error: lazy continuation line {start_lineno} "
            "was not consumed by the previous block rule."
        )

    if state.meets_indented_code_block_indent(start_lineno):
        return BlockParserCommand.with_commit_rejection_kind()

    is_start_line_outdented = state.is_line_outdented(start_lineno)

    if (
        (state.current_list_marker_indent is not None)
        and state.meets_indented_code_block_indent(
            lineno=start_lineno, relative_to_current_list_marker=True
        )
        and is_start_line_outdented
    ):
        return BlockParserCommand.with_commit_rejection_kind()

    is_terminating_paragraph = not is_start_line_outdented

    if (
        scanned_marker := _scan_marker(
            state=state,
            line_descriptor=start_line_descriptor,
            require_ordered_list_starts_with_one=is_terminating_paragraph,
        )
    ) is None:
        return BlockParserCommand.with_commit_rejection_kind()

    after_marker_charno, _ = scanned_marker

    # If we're starting a new unordered list right after
    # a paragraph, first line should not be empty.
    if is_terminating_paragraph and (
        (after_marker_charno >= start_line_descriptor.line_end_charno)
        or state.next_non_space_or_tab_charno(
            start_charno=after_marker_charno,
            end_charno=start_line_descriptor.line_end_charno,
        )
        is None
    ):
        return BlockParserCommand.with_commit_rejection_kind()

    return BlockParserCommand.with_commit_success_kind()


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
