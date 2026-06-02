from enum import Enum, auto
from dataclasses import dataclass

from pmark.elements.block.base import BlockElement


class ListKind(Enum):
    BULLET = auto()
    ORDERED = auto()
