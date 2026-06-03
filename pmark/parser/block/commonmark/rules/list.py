from dataclasses import replace

from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand, BlockParserCommandKind
from pmark.parser.block.rule import BlockParserRule
from pmark.parser.block.commonmark.rules.locals.list import ListLocals, _ListScanStep
from pmark.parser.block.frame_spec import BlockParserFrameSpec
from pmark.parser.block.line_descriptor import LineDescriptor
from pmark.parser.block.rule_chain import BlockParserRuleChain
from pmark.parser.block.block_stream import BlockParserBlockStream
from pmark.line_span import LineSpan
from pmark.persistent_list.transactional_editor import TransactionalEditor
from pmark.elements.block.commonmark.list import ListKind, List, ListItem
from pmark.column_resolution import ColnoWithResolution
from pmark._utils.predicates import is_space_or_tab, is_ascii_digit
from pmark._utils.constants import (
    BULLET_LIST_MARKERS,
    ORDERED_LIST_MARKER_DELIMITERS,
    INDENTED_CODE_BLOCK_MIN_INDENT,
)


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


def list_rule_as_paragraph_terminator(
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
        raise RuntimeError(
            f"Internal parser error: lazy continuation line {start_lineno} "
            "was not consumed by the previous block rule."
        )

    if state.meets_indented_code_block_indent(start_lineno):
        return BlockParserCommand.with_commit_rejection_kind()

    is_start_line_outdented = state.is_line_outdented(start_lineno)

    if (
        (state.current_list_marker_indent_width is not None)
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


def _lookahead_after_item_command(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
    local_attrs: ListLocals,
    end_lineno: int,
    should_exit_transaction: bool,
) -> BlockParserCommand | None:
    # Item become loose if finish with empty line,
    # but we should filter last element, because it means list finish
    local_attrs.previous_item_has_trailing_blank = (
        state.current_lineno > (local_attrs.current_item_start_lineno + 1)
    ) and state.is_preceded_by_blank_line

    # Rollback
    state.current_block_indent_width = (
        local_attrs.expect_persistent_block_indent_width()
    )
    state.current_list_marker_indent_width = (
        local_attrs.persistent_list_marker_indent_width
    )

    if should_exit_transaction:
        local_attrs.line_descriptors_editor.exit_transaction()

    # Move to state.current_lineno
    local_attrs.current_lineno = state.current_lineno
    local_attrs.current_item_start_lineno = state.current_lineno

    if local_attrs.current_lineno >= end_lineno:
        return None

    if state.line_descriptors[local_attrs.current_lineno].is_lazy_continuation:
        return None

    if state.is_line_outdented(local_attrs.current_lineno):
        return None

    if state.meets_indented_code_block_indent(local_attrs.current_lineno):
        return None

    return BlockParserCommand(
        kind=BlockParserCommandKind.LOOKAHEAD_ANY_RULE_MATCHES,
        child_frame_spec=BlockParserFrameSpec(
            line_span=LineSpan(
                start_lineno=local_attrs.current_lineno, end_lineno=end_lineno
            ),
            rule_chain=BlockParserRuleChain.LIST_TERMINATION,
            actuals=BlockParserFrameActuals(
                parent_production=BlockParserRule.LIST,
                block_stream=None,
                continuation_line_limit=inherited_attributes.continuation_line_limit,
            ),
        ),
        origin_rule_context=context,
    )


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
        start_line_descriptor = state.line_descriptors[start_lineno]

        if start_line_descriptor.is_lazy_continuation:
            # must be handled in parent
            raise RuntimeError(
                f"Internal parser error: lazy continuation line {start_lineno} "
                "was not consumed by the previous block rule."
            )

        if state.meets_indented_code_block_indent(start_lineno):
            return BlockParserCommand.with_commit_rejection_kind()

        if (
            (state.current_list_marker_indent_width is not None)
            and state.meets_indented_code_block_indent(
                lineno=start_lineno, relative_to_current_list_marker=True
            )
            and state.is_line_outdented(start_lineno)
        ):
            return BlockParserCommand.with_commit_rejection_kind()

        if (
            scanned_marker := _scan_marker(
                state=state,
                line_descriptor=start_line_descriptor,
                require_ordered_list_starts_with_one=False,
            )
        ) is None:
            return BlockParserCommand.with_commit_rejection_kind()

        if context.is_speculative_mode:
            return BlockParserCommand.with_commit_success_kind()

        after_marker_charno, list_kind = scanned_marker

        marker_char = state.source[after_marker_charno - 1]

        context.bind_production(
            production=BlockParserRule.LIST,
            local_attributes=ListLocals(
                list_kind=list_kind,
                current_after_marker_charno=after_marker_charno,
                marker_char=marker_char,
                current_item_start_lineno=start_lineno,
                current_lineno=start_lineno,
                line_descriptors_editor=TransactionalEditor[LineDescriptor](
                    target=state.line_descriptors
                ),
            ),
        )

    local_attrs = context.expect_local_attributes(
        expected_production=BlockParserRule.LIST,
        expected_locals_type=ListLocals,
    )

    end_lineno = context.line_span.end_lineno

    match local_attrs.step:
        case _ListScanStep.INITIAL:
            pass
        case _ListScanStep.AFTER_PARSE_NESTED:
            if (
                context.expect_has_interblock_blank_line()
                or local_attrs.previous_item_has_trailing_blank
            ):
                local_attrs.is_tight = False

            context.has_interblock_blank_line = None

            lookahead_command = _lookahead_after_item_command(
                state=state,
                inherited_attributes=inherited_attributes,
                context=context,
                local_attrs=local_attrs,
                end_lineno=end_lineno,
                should_exit_transaction=True,
            )

            if lookahead_command is not None:
                local_attrs.step = _ListScanStep.AFTER_LOOKAHEAD
                return lookahead_command

            local_attrs.is_terminated = True

        case _ListScanStep.AFTER_LOOKAHEAD:
            if context.expect_lookahead_matched():
                local_attrs.is_terminated = True

            context.lookahead_matched = None

            current_line_descriptor = state.line_descriptors[local_attrs.current_lineno]

            match local_attrs.list_kind:
                case ListKind.BULLET:
                    after_marker_charno = _get_after_bullet_marker_charno(
                        state=state,
                        line_descriptor=current_line_descriptor,
                    )

                case ListKind.ORDERED:
                    after_marker_charno = _get_after_ordered_marker_charno(
                        state=state,
                        line_descriptor=current_line_descriptor,
                    )

                case _:
                    raise ValueError(f"Wrong {local_attrs.list_kind}")

            if (after_marker_charno is None) or (
                local_attrs.marker_char != state.source[after_marker_charno - 1]
            ):
                local_attrs.is_terminated = True
            else:
                local_attrs.current_after_marker_charno = after_marker_charno

    while (not local_attrs.is_terminated) and local_attrs.current_lineno < end_lineno:
        current_line_descriptor = state.line_descriptors[local_attrs.current_lineno]
        current_item_start_line_descriptor = state.line_descriptors[
            local_attrs.current_item_start_lineno
        ]
        block_item = ListItem()
        local_attrs.block_items.append(block_item)

        if current_line_descriptor.is_lazy_continuation:
            raise RuntimeError(
                f"Internal parser error: lazy continuation line {local_attrs.current_lineno} "
                "was not consumed by the previous block rule."
            )

        indented_marker_width = current_line_descriptor.current_content_indent_width + (
            local_attrs.current_after_marker_charno
            - current_item_start_line_descriptor.current_content_start_charno
        )

        if (
            local_attrs.current_after_marker_charno
            >= current_line_descriptor.line_end_charno
        ):
            resolved_content_start = ColnoWithResolution.at_zero_width_character_start(
                colno=indented_marker_width,
                charno=local_attrs.current_after_marker_charno,
            )
        else:
            resolved_content_start = state.resolve_next_non_space_or_tab(
                start=ColnoWithResolution.at_character_start(
                    start_colno=indented_marker_width,
                    charno=local_attrs.current_after_marker_charno,
                    character=state.source[local_attrs.current_after_marker_charno],
                ),
                end_charno=current_line_descriptor.line_end_charno,
            )

        after_marker_indent_width = (
            1
            if resolved_content_start.resolution.charno
            >= current_line_descriptor.line_end_charno
            else resolved_content_start.colno - indented_marker_width
        )

        if after_marker_indent_width > INDENTED_CODE_BLOCK_MIN_INDENT:
            after_marker_indent_width = 1

        local_attrs.persistent_list_marker_indent_width = (
            state.current_list_marker_indent_width
        )
        state.current_list_marker_indent_width = state.current_block_indent_width

        local_attrs.persistent_block_indent_width = state.current_block_indent_width
        state.current_block_indent_width = (
            after_marker_indent_width + indented_marker_width
        )

        if (
            resolved_content_start.resolution.charno
            >= current_line_descriptor.line_end_charno
            and state.is_blank_line(local_attrs.current_item_start_lineno + 1)
        ):
            # workaround for this case
            # (list item is empty, list terminates before "foo"):
            # ~~~~~~~~
            #   -
            #
            #     foo
            # ~~~~~~~~
            state.current_lineno = min(state.current_lineno + 2, end_lineno)
        else:
            local_attrs.line_descriptors_editor.enter_transaction()

            local_attrs.line_descriptors_editor[
                local_attrs.current_item_start_lineno
            ] = replace(
                current_item_start_line_descriptor,
                current_content_start_charno=resolved_content_start.resolution.charno,
                current_content_indent_width=resolved_content_start.colno,
            )

            local_attrs.step = _ListScanStep.AFTER_PARSE_NESTED

            return BlockParserCommand(
                kind=BlockParserCommandKind.PARSE_NESTED,
                child_frame_spec=BlockParserFrameSpec(
                    line_span=LineSpan(
                        start_lineno=local_attrs.current_item_start_lineno,
                        end_lineno=end_lineno,
                    ),
                    rule_chain=BlockParserRuleChain.FULL_COMMONMARK_RULE_CHAIN,
                    actuals=BlockParserFrameActuals(
                        parent_production=BlockParserRule.LIST,
                        block_stream=BlockParserBlockStream(block_item.children.append),
                        continuation_line_limit=inherited_attributes.continuation_line_limit,
                    ),
                ),
                origin_rule_context=context,
            )

        if local_attrs.previous_item_has_trailing_blank:
            local_attrs.is_tight = False

        lookahead_command = _lookahead_after_item_command(
            state=state,
            inherited_attributes=inherited_attributes,
            context=context,
            local_attrs=local_attrs,
            end_lineno=end_lineno,
            should_exit_transaction=False,
        )

        if lookahead_command is not None:
            local_attrs.step = _ListScanStep.AFTER_LOOKAHEAD
            return lookahead_command

        local_attrs.is_terminated = True

    block = List(
        kind=local_attrs.list_kind,
        marker_char=local_attrs.marker_char,
        items=local_attrs.block_items,
    )

    inherited_attributes.expect_block_stream()(block)

    return BlockParserCommand.with_commit_success_kind()
