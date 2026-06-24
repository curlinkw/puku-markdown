from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from puku_markdown.parser.block.commonmark import (
    HTML_BLOCK_RULES,
    HTML_RULES_AS_BLOCK_TERMINATORS,
    atx_heading_rule,
    blockquote_rule,
    fenced_code_block_rule,
    indented_code_block_rule,
    link_reference_definition_rule,
    list_rule,
    list_rule_as_paragraph_terminator,
    paragraph_rule,
    setext_heading_rule,
    thematic_break_rule,
)
from puku_markdown.parser.block.rule_chain import BlockParserRuleChain
from puku_markdown.parser.block.type_aliases import BlockParserRuleFunc

_COMMON_TERMINATORS: Final[tuple[BlockParserRuleFunc, ...]] = (
    fenced_code_block_rule,
    blockquote_rule,
    thematic_break_rule,
    list_rule,
    *HTML_RULES_AS_BLOCK_TERMINATORS,
    atx_heading_rule,
)
"""
Tuple of block parser rules that can interrupt paragraphs, blockquotes,
and link reference definitions in CommonMark.

This constant is shared across multiple termination chains to avoid
duplication and ensure consistency. It includes all block types that
are considered "aggressive" interrupters according to the CommonMark
spec (excluding `table`, which is not yet implemented).
"""

_PARAGRAPH_TERMINATORS: Final[tuple[BlockParserRuleFunc, ...]] = (
    fenced_code_block_rule,
    blockquote_rule,
    thematic_break_rule,
    list_rule_as_paragraph_terminator,
    *HTML_RULES_AS_BLOCK_TERMINATORS,
    atx_heading_rule,
)
"""
Tuple of block parser rules that can interrupt a paragraph in CommonMark.

Unlike `_COMMON_TERMINATORS`, this uses `list_rule_as_paragraph_terminator`
instead of `list_rule` because list interruption of a paragraph requires
additional validation (e.g., list marker must be followed by whitespace
and the paragraph's first line must not be empty). This constant defines
the set of rules that unconditionally terminate a paragraph when matched.
"""

BLOCK_PARSER_RULE_CHAINS: Final[
    Mapping[BlockParserRuleChain, tuple[BlockParserRuleFunc, ...]]
] = MappingProxyType(
    {
        BlockParserRuleChain.PARAGRAPH_TERMINATION: _PARAGRAPH_TERMINATORS,
        BlockParserRuleChain.SETEXT_HEADING_TERMINATION: _PARAGRAPH_TERMINATORS,
        BlockParserRuleChain.BLOCKQUOTE_TERMINATION: _COMMON_TERMINATORS,
        BlockParserRuleChain.LINK_REFERENCE_DEFINITION_TERMINATION: _COMMON_TERMINATORS,
        BlockParserRuleChain.LIST_TERMINATION: (
            fenced_code_block_rule,
            blockquote_rule,
            thematic_break_rule,
        ),
        BlockParserRuleChain.FULL_COMMONMARK_RULE_CHAIN: (
            indented_code_block_rule,
            fenced_code_block_rule,
            blockquote_rule,
            thematic_break_rule,
            list_rule,
            link_reference_definition_rule,
            *HTML_BLOCK_RULES,
            atx_heading_rule,
            setext_heading_rule,
            paragraph_rule,
        ),
    }
)
"""
Registry mapping chain identifiers to ordered rule sequences.
"""
