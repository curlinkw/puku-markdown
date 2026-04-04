from enum import Enum, auto


class BlockLexerRuleChain(Enum):
    """Identifiers for ordered chains of lexer rules."""

    PARAGRAPH_TERMINATION_RULE_CHAIN = auto()
    """Sequence of rules that determine when a `paragraph` block terminates."""
