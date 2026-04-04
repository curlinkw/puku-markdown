from types import MappingProxyType
from typing import Final, Mapping, TYPE_CHECKING

from pmark.lexer.block.type_aliases import BlockLexerRuleFunc

if TYPE_CHECKING:
    from pmark.lexer.block.rule_chain import BlockLexerRuleChain


BLOCK_LEXER_RULE_CHAINS: Final[
    Mapping[BlockLexerRuleChain, tuple[BlockLexerRuleFunc, ...]]
] = MappingProxyType({})
"""
Registry mapping chain identifiers to ordered rule sequences.
"""
