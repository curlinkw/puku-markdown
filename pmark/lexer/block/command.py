from dataclasses import dataclass
from enum import IntEnum, auto


class BlockLexerCommandKind(IntEnum):
    pass


@dataclass(slots=True, frozen=True)
class BlockLexerCommand:
    kind: BlockLexerCommandKind
