from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from puku_markdown.elements.block.base import BlockElement


class BlockParserBlockStream:
    """Callable stream that consumes finalized block elements.

    Typical usage:
        stream = BlockStream(lambda block: print(block))
        stream(block)  # prints the block
    """

    __slots__ = ("_emit",)

    def __init__(self, emit: Callable[[BlockElement], None]) -> None:
        """Create a stream that calls `emit` for every block.

        Args:
            emit: A callable that receives a `BlockElement` and does something
                  with it (e.g., appends to a parent list, writes to output).
        """
        self._emit = emit

    def __call__(self, block: BlockElement) -> None:
        """Send a finalized block through the stream."""
        self._emit(block)
