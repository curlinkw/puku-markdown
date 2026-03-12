from dataclasses import dataclass
from enum import IntEnum, auto


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
    recursion in rule code.
    """

    PROBE_TERMINATION = auto()
    """
    Probe whether any termination rule matches at the current position.

    Return this command when a rule needs to check if the current lexical context
    should end. The lexer evaluates the given rule chain in *speculative mode*:
    """


@dataclass(slots=True, frozen=True)
class BlockLexerCommand:
    kind: BlockLexerCommandKind
