from dataclasses import dataclass
from enum import IntEnum, auto

from pmark.lexer.block.frame_spec import BlockLexerFrameSpec


class BlockLexerCommandKind(IntEnum):
    """
    Discriminant for lexer commands that control the explicit stack machine's
    flow and state transitions.
    """

    COMMIT_SUCCESS = auto()
    """
    The rule has successfully matched the input and reached a final accepting
    state.
    """

    COMMIT_REJECTION = auto()
    """
    The rule has definitively failed to match the input and reached a final
    rejecting state.
    """

    TOKENIZE_NESTED = auto()
    """
    Tokenize a nested lexical region (e.g., the content of a list item or blockquote).

    Return this command when a rule needs to recursively process a subordinate part
    of the source with its own rule chain. The lexer will suspend the current rule,
    tokenize the specified region independently, and then resume the original rule,
    making the nested result available for further processing.

    This enables clean handling of arbitrarily nested structures without explicit
    recursion in rule code. When this kind is used, the `frame_spec`
    field must contain a `BlockLexerFrameSpec` that defines the nested context.
    """

    PROBE_TERMINATION = auto()
    """
    Probe whether any termination rule matches at the current position.

    Return this command when a rule needs to check if the current lexical context
    should end. The lexer evaluates the given rule chain in *speculative mode*.
    When this kind is used, the `frame_spec` field must contain a `BlockLexerFrameSpec`
    whose `rule_chain` defines the termination rules to probe.
    """


@dataclass(slots=True, frozen=True)
class BlockLexerCommand:
    """
    Instruction returned by a lexer rule to control the lexer's next action.

    A `BlockLexerCommand` encapsulates a directive that tells the block lexer
    how to proceed after a rule has finished its work. It is the primary
    communication channel from lexer rules to the lexer engine.

    Design Note:
        Currently, `BlockLexerCommand` is a single class with an optional
        `frame_spec` field that serves multiple purposes. This design is
        sufficient for the present set of command kinds. However, the
        architecture anticipates the possibility of evolving into a
        *discriminated union* (sum type) if future command variants require
        significantly different payloads. The current structure keeps the design
        simple until the need for more varied payloads arises.
    """

    kind: BlockLexerCommandKind
    """
    The specific action the lexer should perform. See `BlockLexerCommandKind` for details.
    """

    frame_spec: BlockLexerFrameSpec | None = None
    """
    A frame specification used by certain command kinds
    (`TOKENIZE_NESTED` and `PROBE_TERMINATION`). For other kinds, this field must be `None`.
    """
