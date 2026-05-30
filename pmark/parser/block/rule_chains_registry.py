from types import MappingProxyType
from typing import Final, Mapping

from pmark.parser.block.commonmark import (
    HTML_BLOCK_RULES,
    atx_heading_rule,
    blockquote_rule,
    fenced_code_block_rule,
    indented_code_block_rule,
    link_reference_definition_rule,
    list_rule,
    paragraph_rule,
    setext_heading_rule,
    thematic_break_rule,
)
from pmark.parser.block.type_aliases import BlockParserRuleFunc
from pmark.parser.block.rule_chain import BlockParserRuleChain


_COMMON_TERMINATORS: Final[tuple[BlockParserRuleFunc, ...]] = (
    fenced_code_block_rule,
    blockquote_rule,
    thematic_break_rule,
    list_rule,
    *HTML_BLOCK_RULES,
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

BLOCK_PARSER_RULE_CHAINS: Final[
    Mapping[BlockParserRuleChain, tuple[BlockParserRuleFunc, ...]]
] = MappingProxyType(
    {
        BlockParserRuleChain.PARAGRAPH_TERMINATION: _COMMON_TERMINATORS,
        BlockParserRuleChain.SETEXT_HEADING_TERMINATION: _COMMON_TERMINATORS,
        BlockParserRuleChain.BLOCKQUOTE_TERMINATION: _COMMON_TERMINATORS,
        BlockParserRuleChain.LINK_REFERENCE_DEFINITION_TERMINATION: _COMMON_TERMINATORS,
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
