from re import Pattern
from typing import Final

from puku_markdown.parser.block.state import BlockParserState
from puku_markdown.parser.block.frame_actuals import BlockParserFrameActuals
from puku_markdown.parser.block.rule_context import BlockParserRuleContext
from puku_markdown.parser.block.command import BlockParserCommand
from puku_markdown.parser.block.logger import logger
from puku_markdown.elements.block.commonmark.html_block import HtmlBlock, HtmlBlockKind
from puku_markdown.line_span import LineSpan
from puku_markdown._utils.constants import LESS_THAN_CHARACTER
from puku_markdown._utils.re_patterns import (
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
from puku_markdown.parser.block.type_aliases import BlockParserRuleFunc


def _find_block_end_lineno(
    state: BlockParserState, line_span: LineSpan, close_re: Pattern[str]
) -> int:
    for current_lineno in range(line_span.start_lineno, line_span.end_lineno):
        current_line_descriptor = state.line_descriptors[current_lineno]

        if current_line_descriptor.is_lazy_continuation:
            return current_lineno

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
    logger.debug(
        "Entered into _html_rule_impl at state.current_lineno=%r; line_span=%r",
        state.current_lineno,
        context.line_span,
    )

    start_lineno = context.line_span.start_lineno
    start_line_descriptor = state.line_descriptors[start_lineno]

    if (
        not start_line_descriptor.is_lazy_continuation
    ) and state.meets_indented_code_block_indent(start_lineno):
        return BlockParserCommand.with_commit_rejection_kind()

    start_line_content = state.source[
        start_line_descriptor.current_content_start_charno : start_line_descriptor.line_end_charno
    ]

    if (not start_line_content) or (start_line_content[0] != LESS_THAN_CHARACTER):
        return BlockParserCommand.with_commit_rejection_kind()

    if open_re.search(start_line_content) is None:
        return BlockParserCommand.with_commit_rejection_kind()

    if start_line_descriptor.is_lazy_continuation:
        raise RuntimeError(
            f"Internal parser error: lazy continuation line {start_lineno} "
            "was not consumed by the previous block rule."
        )

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
        kind=block_kind,
        content=state.indent_reduced_block_content(
            line_span=LineSpan(
                start_lineno=context.line_span.start_lineno, end_lineno=block_end_lineno
            ),
            reduction_width=state.current_block_indent_width,
            keep_trailing_newline=True,
        ),
    )

    inherited_attributes.expect_block_stream()(block)

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


HTML_BLOCK_RULES: Final[tuple[BlockParserRuleFunc, ...]] = (
    html_raw_text_tag_rule,
    html_comment_rule,
    html_processing_instruction_rule,
    html_markup_declaration_rule,
    html_cdata_rule,
    html_block_level_tag_rule,
    html_tag_rule,
)
"""
HTML block rule functions in the order defined by CommonMark.

This order determines precedence during block parsing. For example,
comments (`<!-- -->`) must be recognised before generic block-level
tags (`<div>`) to avoid misinterpreting comment starts as tag starts.

Rule mapping to `markdown-it-py` `HTML_SEQUENCES`:

0. `html_raw_text_tag_rule` → `<script>`, `<pre>`, `<style>`, `<textarea>`
1. `html_comment_rule` → `<!-- ... -->`
2. `html_processing_instruction_rule` → `<? ... ?>`
3. `html_markup_declaration_rule` → `<!...>` (e.g., DOCTYPE)
4. `html_cdata_rule` → `<![CDATA[ ... ]]>`
5. `html_block_level_tag_rule` → block-level HTML tags (e.g., `<div>`)
6. `html_tag_rule` → any other complete HTML tag on a single line

Note:
    Do not change this order unless you also update the underlying precedence.
"""


HTML_RULES_AS_BLOCK_TERMINATORS: Final[tuple[BlockParserRuleFunc, ...]] = (
    html_raw_text_tag_rule,
    html_comment_rule,
    html_processing_instruction_rule,
    html_markup_declaration_rule,
    html_cdata_rule,
    html_block_level_tag_rule,
)
"""
HTML rules that act as **block terminators** in the Markdown parsing context.

When any of these rules matches, the current block (paragraph, list item,
blockquote, etc.) ends immediately. The matched HTML content is then processed
as its own block.

This set excludes `html_tag_rule` because that rule matches inline‑level tags
which must **not** terminate blocks - they should be parsed as inline HTML
inside the current block.

Use this set when checking for conditions that should close a block (e.g.,
inside a paragraph rule, before heading detection).
"""
