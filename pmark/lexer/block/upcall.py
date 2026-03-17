from enum import IntEnum, auto
from dataclasses import dataclass


class BlockLexerUpcallKind(IntEnum):
    """
    Discriminant for the result data produced by the lexer when processing a command.

    Each kind corresponds directly to a specific command kind and identifies
    the type of outcome delivered back to the originating rule context.
    """

    PROBE_TERMINATION_RESULT = auto()
    """
    Result produced after the lexer processes a `PROBE_TERMINATION` command.

    Indicates whether any termination rule matched during the probe.
    Payload: bool — `True` if at least one termination rule succeeded,
    `False` otherwise.
    """

    TOKENIZE_NESTED_RESULT = auto()
    """
    Result produced after the lexer processes a `TOKENIZE_NESTED` command.

    Carries the output from tokenizing a nested lexical region (e.g., a list
    item or blockquote). The payload is context-specific; currently it
    includes the `has_interblock_blank_line` flag, but may be extended.
    """


@dataclass(slots=True)
class BlockLexerUpcall:
    kind: BlockLexerUpcallKind
    payload: bool
