from enum import Enum, auto


class BlockParserRuleChain(Enum):
    """Identifiers for ordered chains of parser rules."""

    PARAGRAPH_TERMINATION = auto()
    """Sequence of rules that determine when a `paragraph` block terminates."""

    SETEXT_HEADING_TERMINATION = auto()
    """Sequence of rules that determine when a `setext heading` block terminates."""

    BLOCKQUOTE_TERMINATION = auto()
    """Sequence of rules that determine when a `blockquote` block terminates."""

    FULL_COMMONMARK_RULE_CHAIN = auto()
    """
    All CommonMark block rules.

    When assigned to a frame's `rule_chain`, this provides the complete
    CommonMark parsing behaviour.
    """
