from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand
from pmark.elements.block.commonmark.indented_code_block import IdentedCodeBlock
from pmark.line_span import LineSpan
from pmark.constants import INDENTED_CODE_BLOCK_MIN_INDENT, LINE_FEED_CHARACTER


def indented_code_block_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Indented code block rule.

    This rule is *terminal* - it never suspends or yields. It either succeeds
    (`COMMIT_SUCCESS`) or rejects (`COMMIT_REJECTION`) in the same
    call. It has no locals (no internal parsing state to resume) and does not
    bind `context` to any production, because no recursive descent is needed.

    Invariants:
        - No recursive calls to other rules.
        - No use of `context.locals` (no suspension points).
        - Returns only `COMMIT_SUCCESS` or `COMMIT_REJECTION` command kinds.
    """

    if __debug__:
        if state.line_descriptors[context.line_span.start_lineno].is_lazy_continuation:
            raise RuntimeError(
                f"Internal parser error: lazy continuation line {context.line_span.start_lineno} "
                "was not consumed by the previous block rule."
            )

    if not state.meets_indented_code_block_indent(context.line_span.start_lineno):
        return BlockParserCommand.with_commit_rejection_kind()

    if context.is_speculative_mode:
        return BlockParserCommand.with_commit_success_kind()

    last_lineno = current_lineno = context.line_span.start_lineno + 1

    while current_lineno < context.line_span.end_lineno:
        if __debug__:
            if state.line_descriptors[current_lineno].is_lazy_continuation:
                raise RuntimeError(
                    f"Internal parser error: lazy continuation line {current_lineno} "
                    "was not consumed by the previous block rule."
                )

        if state.is_blank_line(current_lineno):
            current_lineno += 1
            continue

        if state.meets_indented_code_block_indent(current_lineno):
            current_lineno += 1
            last_lineno = current_lineno
            continue

        break

    state.current_lineno = current_lineno
    block = IdentedCodeBlock(
        parent=None,
        content=state.indent_reduced_block_content(
            line_span=LineSpan(
                start_lineno=context.line_span.start_lineno, end_lineno=last_lineno
            ),
            reduction_width=INDENTED_CODE_BLOCK_MIN_INDENT
            + state.current_block_indent_width,
            keep_trailing_newline=False,
        )
        + LINE_FEED_CHARACTER,
    )

    if not inherited_attributes.try_attach_parent(block):
        state.target_document.append_root_block(block)

    return BlockParserCommand.with_commit_success_kind()
