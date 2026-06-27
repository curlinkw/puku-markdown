from dataclasses import dataclass

from puku_markdown.elements import Element
from puku_markdown.renderer.frames import RendererFrame


@dataclass(slots=True)
class RendererFramedElement:
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
    The traversal frame tracking the current iteration position.

    This field may be `None` for two reasons:
    1. The element is a **leaf** (it has no children to traverse).
    2. The frame has **not yet been initialized** (the frame factory hook
       has not been called, as controlled by the traversal flow).

    In the second case, the frame will be created later during the traversal
    when the element's children are about to be processed.
    """
