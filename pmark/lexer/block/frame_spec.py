from dataclasses import dataclass, field

from pmark.line_span import LineSpan
from pmark.lexer.block.rule_chain import BlockLexerRuleChain
from pmark.lexer.block.rule_context import BlockLexerRuleContext


@dataclass(slots=True, frozen=True)
class BlockLexerFrameSpec:
    """
    Specification for creating a new frame in the block lexer.

    A `BlockLexerFrameSpec` contains all rule-level information required to
    construct a full `BlockLexerFrame` later in the lexer. It serves as a
    blueprint that is typically created by a *lexer rule* and then passed to
    the lexer (via a `BlockLexerCommand`) to instantiate the actual frame.

    Design Note:
        Currently, `BlockLexerFrameSpec` is a single concrete class that is
        primarily instantiated from lexer rules. However, the architecture is
        designed to evolve into a *discriminated union* (sum type) if multiple
        distinct kinds of frame specifications become necessary (e.g., specs
        originating from different sources). This approach would allow each
        variant to carry its own specific fields while still being uniformly
        handled as a `BlockLexerFrameSpec`. The current structure intentionally
        keeps the design simple until such diversity is required.
    """

    line_span: LineSpan
    """
    The line range being processed in this frame.
    """

    rule_chain: BlockLexerRuleChain
    """
    Ordered sequence of lexer rules to apply for this frame.
    """

    current_rule_context: BlockLexerRuleContext | None = field(default=None)
    """
    *Mutable* context for the currently active rule.
    """
