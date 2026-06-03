from enum import Enum, auto
from dataclasses import dataclass, field

from pmark.elements.block.base import BlockElement


class ListKind(Enum):
    BULLET = auto()
    ORDERED = auto()


@dataclass(slots=True)
class ListItem:
    children: list[BlockElement] = field(default_factory=list)


@dataclass(slots=True)
class List(BlockElement):
    kind: ListKind
    marker_char: str
    is_tight: bool
    items: list[ListItem] = field(default_factory=list)
