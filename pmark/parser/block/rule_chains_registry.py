from types import MappingProxyType
from typing import Final, Mapping, TYPE_CHECKING

from pmark.parser.block.type_aliases import BlockParserRuleFunc

if TYPE_CHECKING:
    from pmark.parser.block.rule_chain import BlockParserRuleChain


BLOCK_PARSER_RULE_CHAINS: Final[
    Mapping[BlockParserRuleChain, tuple[BlockParserRuleFunc, ...]]
] = MappingProxyType({})
"""
Registry mapping chain identifiers to ordered rule sequences.
"""
