from re import Pattern

from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand
from pmark.elements.block.commonmark.html_block import HtmlBlock, HtmlBlockKind
from pmark.line_span import LineSpan
from pmark._utils.constants import LESS_THAN_CHARACTER
from pmark._utils.re_patterns import (
    HTML_RAW_TEXT_TAG_OPEN_RE,
    HTML_RAW_TEXT_TAG_CLOSE_RE,
    HTML_COMMENT_OPEN_RE,
    HTML_COMMENT_CLOSE_RE,
    HTML_PROCESSING_INSTRUCTION_OPEN_RE,
    HTML_PROCESSING_INSTRUCTION_CLOSE_RE,
    HTML_MARKUP_DECLARATION_OPEN_RE,
    HTML_MARKUP_DECLARATION_CLOSE_RE,
    HTML_CDATA_OPEN_RE,
    HTML_CDATA_CLOSE_RE,
    HTML_BLOCK_LEVEL_TAG_OPEN_RE,
    HTML_BLOCK_LEVEL_TAG_CLOSE_RE,
    HTML_TAG_OPEN_RE,
    HTML_TAG_CLOSE_RE,
)


def _find_block_end_lineno(
    state: BlockParserState, line_span: LineSpan, close_re: Pattern[str]
) -> int:
    for current_lineno in range(line_span.start_lineno, line_span.end_lineno):
        current_line_descriptor = state.line_descriptors[current_lineno]

        if __debug__:
            if current_line_descriptor.is_lazy_continuation:
                raise RuntimeError(
                    f"Internal parser error: lazy continuation line {current_lineno} "
                    "was not consumed by the previous block rule."
                )

        if state.is_line_outdented(current_lineno):
            return current_lineno

        current_line_content = state.source[
            current_line_descriptor.current_content_start_charno : current_line_descriptor.line_end_charno
        ]

        if close_re.search(current_line_content):
            return current_lineno + 1 if current_line_content else current_lineno
    return line_span.end_lineno


def _html_rule_impl(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
    open_re: Pattern[str],
    close_re: Pattern[str],
    block_kind: HtmlBlockKind,
) -> BlockParserCommand:
    """
    Html rules implementation.

    This rules are *terminal* - they never suspend or yield. They either succeed
    (`COMMIT_SUCCESS`) or reject (`COMMIT_REJECTION`) in the same
    call. They have no locals (no internal parsing state to resume) and do not
    bind `context` to any production, because no recursive descent is needed.

    Invariants:
        - No recursive calls to other rules.
        - No use of `context.locals` (no suspension points).
        - Returns only `COMMIT_SUCCESS` or `COMMIT_REJECTION` command kinds.
    """

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

    start_line_content = state.source[
        start_line_descriptor.current_content_start_charno : start_line_descriptor.line_end_charno
    ]

    if (not start_line_content) or (start_line_content[0] != LESS_THAN_CHARACTER):
        return BlockParserCommand.with_commit_rejection_kind()

    if open_re.search(start_line_content) is None:
        return BlockParserCommand.with_commit_rejection_kind()

    if context.is_speculative_mode:
        return BlockParserCommand.with_commit_success_kind()

    block_end_lineno = (
        start_lineno + 1
        if close_re.search(start_line_content) is not None
        else _find_block_end_lineno(
            state=state,
            line_span=LineSpan(
                start_lineno=start_lineno + 1, end_lineno=context.line_span.end_lineno
            ),
            close_re=close_re,
        )
    )

    state.current_lineno = block_end_lineno

    block = HtmlBlock(
        parent=None,
        kind=block_kind,
        content=state.indent_reduced_block_content(
            line_span=LineSpan(
                start_lineno=context.line_span.start_lineno, end_lineno=block_end_lineno
            ),
            reduction_width=state.current_block_indent_width,
            keep_trailing_newline=True,
        ),
    )

    if not inherited_attributes.try_attach_parent(block):
        state.target_document.append_root_block(block)

    return BlockParserCommand.with_commit_success_kind()


def html_raw_text_tag_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Html raw text tag rule.
    """
    return _html_rule_impl(
        state=state,
        inherited_attributes=inherited_attributes,
        context=context,
        open_re=HTML_RAW_TEXT_TAG_OPEN_RE,
        close_re=HTML_RAW_TEXT_TAG_CLOSE_RE,
        block_kind=HtmlBlockKind.RAW_TEXT_TAG,
    )


def html_comment_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Html comment rule.
    """
    return _html_rule_impl(
        state=state,
        inherited_attributes=inherited_attributes,
        context=context,
        open_re=HTML_COMMENT_OPEN_RE,
        close_re=HTML_COMMENT_CLOSE_RE,
        block_kind=HtmlBlockKind.COMMENT,
    )


def html_processing_instruction_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Html processing instruction rule.
    """
    return _html_rule_impl(
        state=state,
        inherited_attributes=inherited_attributes,
        context=context,
        open_re=HTML_PROCESSING_INSTRUCTION_OPEN_RE,
        close_re=HTML_PROCESSING_INSTRUCTION_CLOSE_RE,
        block_kind=HtmlBlockKind.PROCESSING_INSTRUCTION,
    )


def html_markup_declaration_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Html markup declaration rule.
    """
    return _html_rule_impl(
        state=state,
        inherited_attributes=inherited_attributes,
        context=context,
        open_re=HTML_MARKUP_DECLARATION_OPEN_RE,
        close_re=HTML_MARKUP_DECLARATION_CLOSE_RE,
        block_kind=HtmlBlockKind.MARKUP_DECLARATION,
    )


def html_cdata_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Html cdata rule.
    """
    return _html_rule_impl(
        state=state,
        inherited_attributes=inherited_attributes,
        context=context,
        open_re=HTML_CDATA_OPEN_RE,
        close_re=HTML_CDATA_CLOSE_RE,
        block_kind=HtmlBlockKind.CDATA,
    )


def html_block_level_tag_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Html block level tag rule.
    """
    return _html_rule_impl(
        state=state,
        inherited_attributes=inherited_attributes,
        context=context,
        open_re=HTML_BLOCK_LEVEL_TAG_OPEN_RE,
        close_re=HTML_BLOCK_LEVEL_TAG_CLOSE_RE,
        block_kind=HtmlBlockKind.BLOCK_LEVEL_TAG,
    )


def html_tag_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Html tag rule.
    """
    return _html_rule_impl(
        state=state,
        inherited_attributes=inherited_attributes,
        context=context,
        open_re=HTML_TAG_OPEN_RE,
        close_re=HTML_TAG_CLOSE_RE,
        block_kind=HtmlBlockKind.TAG,
    )
