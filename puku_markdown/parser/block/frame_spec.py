from dataclasses import dataclass

from puku_markdown.line_span import LineSpan
from puku_markdown.parser.block.rule_chain import BlockParserRuleChain
from puku_markdown.parser.block.frame_actuals import BlockParserFrameActuals


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

    actuals: BlockParserFrameActuals
    """
    Concrete caller-side values supplied by this frame to a block rule.

    This field holds the actual arguments that this frame (as caller)
    provides when invoking a rule. The rule receives this data as its
    inherited attributes. Storing actuals marks this frame as the caller.
    """
