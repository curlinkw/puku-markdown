from dataclasses import dataclass

from puku_markdown.parser.block.line_descriptor import LineDescriptor
from puku_markdown.persistent_list.transactional_editor import TransactionalEditor
from puku_markdown.elements.block.commonmark.blockquote import Blockquote


@dataclass(slots=True)
class BlockquoteLocals:
    current_lineno: int
    line_descriptors_editor: TransactionalEditor[LineDescriptor]
    prev_marked_line_was_empty: bool = False
    is_terminated: bool = False
    continuation_line_limit: int | None = None
    current_block_indent_width: int | None = None
    nested_parse_completed: bool = False
    block: Blockquote | None = None

    def expect_block(self) -> Blockquote:
        """Return the current blockquote or raise if unavailable.

        Use this when a blockquote must exist (e.g., after parsing has started
        and before termination).

        Raises:
            RuntimeError: If ``block`` is ``None``, indicating that no
                blockquote has been initialized or it was already finalized.

        Returns:
            The non-None Blockquote instance.
        """
        if self.block is None:
            raise RuntimeError(
                "Blockquote block is None. Ensure blockquote parsing has "
                "started and the block is initialized before expecting it."
            )
        return self.block

    def expect_current_block_indent_width(self) -> int:
        """Return the current block indent width or raise if not set.

        Raises:
            RuntimeError: If ``current_block_indent_width`` is ``None``, meaning
                no block is actively being parsed (e.g., outside a continuation line).

        Returns:
            The indent width in spaces.
        """
        if self.current_block_indent_width is None:
            raise RuntimeError(
                "No active block indent width. This method should only be called "
                "when parsing a continuation line of a lazy block inside a blockquote."
            )
        return self.current_block_indent_width
