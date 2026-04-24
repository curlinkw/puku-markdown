from dataclasses import dataclass

from pmark.parser.block.line_descriptor import LineDescriptor
from pmark.persistent_list.transactional_editor import TransactionalEditor
from pmark.elements.block.commonmark.blockquote import Blockquote


@dataclass(slots=True)
class BlockquoteLocals:
    current_lineno: int
    line_descriptors_editor: TransactionalEditor[LineDescriptor]
    prev_marked_line_was_empty: bool = False
    is_terminated: bool = False
    paragraph_line_limit: int | None = None
    current_block_indent_width: int | None = None
    nested_parse_completed: bool = False
    block: Blockquote | None = None
