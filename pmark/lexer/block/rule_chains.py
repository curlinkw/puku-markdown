from enum import IntEnum, auto


from pmark.lexer.block.type_aliases import BlockLexerRule


class BlockLexerRuleChain(IntEnum):
    """Identifiers for ordered chains of lexer rules."""

    pass


RULE_CHAINS: dict[BlockLexerRuleChain, tuple[BlockLexerRule, ...]] = {}
"""
Registry mapping chain identifiers to ordered rule sequences.
"""
