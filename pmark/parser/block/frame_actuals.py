from dataclasses import dataclass

from pmark.parser.block.rule import BlockParserRule
from pmark.parser.block.block_stream import BlockParserBlockStream


@dataclass(slots=True, frozen=True)
class BlockParserFrameActuals:
    """
    Caller-side concrete values supplied by this frame to a `block rule`.

    Terminology (actuals / formals) originates from ALGOL 58 calling conventions:
    - *Actuals*: concrete arguments provided by the caller.
    - *Formals*: parameter placeholders in the callee.

    This class defines the formal schema: the field names and their types
    are the formals that a rule expects. Each instance stores the actual
    values for a specific frame when it calls a rule.

    Naming discipline:
    - Caller (frame) side: uses "actuals" (this class). *Storing actuals
      unambiguously marks the holder as the caller*.
    - Callee (rule) side: uses attribute grammar terminology:
      - *Inherited attributes*: values received from the parent (frame).
      - *Synthesized attributes*: values computed by the rule and returned
        to the parent (frame).
      - *Locals*: temporary values internal to the rule, not passed up or down.

      The rule never sees "actuals". It receives the content of this class
      as its *inherited attributes*.

    Thus this class belongs exclusively to the caller (frame). The rule
    interprets its content as *inherited attributes*.
    """

    parent_production: BlockParserRule | None  # parentType
    """
    The production that directly encloses this rule in the parsing hierarchy.

    `None` when this rule is invoked from the root frame (no enclosing rule).
    For nested rules, this field identifies the innermost production that
    initiated the current frame.
    """

    block_stream: BlockParserBlockStream | None
    """Stream that receives every finalized block, or `None` in speculative mode.

    Called immediately after a block is fully parsed.
    Reassignable to support nested contexts (e.g., lists intercepting children).
    When `None`, streaming is disabled (e.g., during lookahead parsing).
    """

    continuation_line_limit: int | None
    """
    Exclusive upper bound (line index) for scanning continuation lines in the current block.

    When set (e.g., for a paragraph or reference rules), the parser will not consider lines at or beyond this index
    as part of the block's continuation, even if more lines exist in the source.

    If `None` (default), the limit defaults to the total number of lines in the document (`state.line_count`),
    allowing continuation until the end of the block or file.
    """

    def expect_block_stream(self) -> BlockParserBlockStream:
        """Return the current block stream or raise if unavailable.

        Use this when streaming is mandatory (e.g., after confirming a block
        is final and not part of speculative parsing).

        Raises:
            RuntimeError: If `block_stream` is `None`, indicating that
                streaming was called in a speculative context where it
                should not occur.

        Returns:
            The non-None block stream.
        """
        if self.block_stream is None:
            raise RuntimeError(
                "Block stream is None. Streaming is disabled in speculative mode "
                "or the stream was not properly initialized."
            )
        return self.block_stream
