from typing import NamedTuple

from puku_markdown.elements import Element
from puku_markdown.renderer.frames import RendererFrame


class RendererFramedElement(NamedTuple):
    """
    An AST Element paired with its associated traversal Frame.

    In the explicit stack traversal, each active container node has an associated
    frame that tracks its iteration position. This pair represents that association
    when both need to be stored together (e.g., in a stack).
    """

    element: Element
    """
    The AST element that owns this frame.
    """

    frame: RendererFrame | None = None
    """
    The traversal frame tracking the current position.

    If `None`, this indicates that the element is a **leaf** (i.e., it has no
    children to traverse). Leaf elements do not require a frame to maintain
    iteration state; they are processed immediately on entry.
    """
