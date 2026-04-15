from enum import Enum, auto


class BlockParserRuleChain(Enum):
    """Identifiers for ordered chains of parser rules."""

    PARAGRAPH_TERMINATION = auto()
    """Sequence of rules that determine when a `paragraph` block terminates."""
