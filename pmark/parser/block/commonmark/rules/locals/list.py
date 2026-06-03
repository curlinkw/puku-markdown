from enum import Enum, auto
from dataclasses import dataclass

from pmark.persistent_list.transactional_editor import TransactionalEditor
from pmark.parser.block.line_descriptor import LineDescriptor
from pmark.elements.block.commonmark.list import ListKind


class _ListScanStep(Enum):
    INITIAL = auto()
    AFTER_PARSE_NESTED = auto()
    AFTER_LOOKAHEAD = auto()


@dataclass(slots=True)
class ListLocals:
    list_kind: ListKind
    current_after_marker_charno: int
    marker_char: str
    current_item_start_lineno: int
    current_lineno: int
    line_descriptors_editor: TransactionalEditor[LineDescriptor]
    is_tight: bool = True
    is_terminated: bool = False
    previous_item_has_trailing_blank: bool = False
    persistent_block_indent_width: int | None = None
    persistent_list_marker_indent_width: int | None = None
    step: _ListScanStep = _ListScanStep.INITIAL

    def expect_persistent_block_indent_width(self) -> int:
        """Return the persistent block indent width.

        The width must have been set previously; otherwise an exception is raised.

        Returns:
            The current block indent width as an integer.

        Raises:
            RuntimeError: If `persistent_block_indent_width` is `None` (i.e., not set).
        """
        if self.persistent_block_indent_width is None:
            raise RuntimeError("block indent width has not been set")
        return self.persistent_block_indent_width

    def expect_persistent_list_marker_indent_width(self) -> int:
        """Return the persistent list marker indent width.

        The width must have been set previously; otherwise an exception is raised.

        Returns:
            The current persistent list indent width as an integer.

        Raises:
            RuntimeError: If `persistent_list_marker_indent_width` is `None` (i.e., not set).
        """
        if self.persistent_list_marker_indent_width is None:
            raise RuntimeError("persistent list indent width has not been set")
        return self.persistent_list_marker_indent_width
