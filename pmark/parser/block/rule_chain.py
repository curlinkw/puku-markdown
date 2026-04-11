from enum import Enum, auto


class BlockParserRuleChain(Enum):
    """Identifiers for ordered chains of parser rules."""

    PARAGRAPH_TERMINATION_RULE_CHAIN = auto()
    """Sequence of rules that determine when a `paragraph` block terminates."""
