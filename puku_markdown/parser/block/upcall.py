from enum import Enum, auto
from dataclasses import dataclass


class BlockParserUpcallKind(Enum):
    """
    Discriminant for the result data produced by the parser when processing a command.

    Each kind corresponds directly to a specific command kind and identifies
    the type of outcome delivered back to the originating rule context.
    """

    LOOKAHEAD_ANY_RULE_MATCHED = auto()
    """
    Result delivered after the parser evaluates a `LOOKAHEAD_ANY_RULE_MATCHES` command.

    Indicates whether the speculative lookahead succeeded — i.e., at least one rule
    in the tested set matched the upcoming input without consuming characters.
    Payload: `bool` — `True` if the at least one rule succeeded, `False` otherwise.
    """

    PARSE_NESTED_RESULT = auto()
    """
    Result produced after the parser processes a `PARSE_NESTED` command.

    Carries the output from parsing a nested region (e.g., a list
    item or blockquote). The payload is context-specific; currently it
    includes the `has_interblock_blank_line` flag, but may be extended.
    """


@dataclass(slots=True)
class BlockParserUpcall:
    kind: BlockParserUpcallKind
    payload: bool
