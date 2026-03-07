from enum import IntEnum, auto


class LexerRuleChain(IntEnum):
    """Identifiers for ordered chains of lexer rules."""

    pass


RULE_CHAINS: dict[LexerRuleChain, tuple] = {}  # TODO (change tuple type)
"""
Registry mapping chain identifiers to ordered rule sequences.
"""
