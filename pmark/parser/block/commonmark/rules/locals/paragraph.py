from dataclasses import dataclass

from pmark.elements.block.commonmark.paragraph import Paragraph


@dataclass(slots=True)
class ParagraphLocals:
    current_lineno: int
    end_lineno: int
    block_element: Paragraph
