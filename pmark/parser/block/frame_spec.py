from dataclasses import dataclass, field

from pmark.line_span import LineSpan
from pmark.parser.block.rule_chain import BlockParserRuleChain
from pmark.parser.block.rule_context import BlockParserRuleContext


@dataclass(slots=True, frozen=True)
class BlockParserFrameSpec:
    """
    Specification for creating a new frame in the block parser.

    A `BlockParserFrameSpec` contains all rule-level information required to
    construct a full `BlockParserFrame` later in the parser. It serves as a
    blueprint that is typically created by a *parser rule* and then passed to
    the parser (via a `BlockParserCommand`) to instantiate the actual frame.

    Design Note:
        Currently, `BlockParserFrameSpec` is a single concrete class that is
        primarily instantiated from parser rules. However, the architecture is
        designed to evolve into a *discriminated union* (sum type) if multiple
        distinct kinds of frame specifications become necessary (e.g., specs
        originating from different sources). This approach would allow each
        variant to carry its own specific fields while still being uniformly
        handled as a `BlockParserFrameSpec`. The current structure intentionally
        keeps the design simple until such diversity is required.
    """

    line_span: LineSpan
    """
    The line range being processed in this frame.
    """

    rule_chain: BlockParserRuleChain
    """
    Ordered sequence of parser rules to apply for this frame.
    """

    current_rule_context: BlockParserRuleContext | None = field(default=None)
    """
    *Mutable* context for the currently active rule.
    """
