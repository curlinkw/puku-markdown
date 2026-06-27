from puku_markdown.elements import Document
from puku_markdown.renderer.framed_element import RendererFramedElement
from puku_markdown.renderer.frames import SequentialRendererFrame
from puku_markdown.renderer.state import RendererState
from puku_markdown.renderer.text.state import TextRendererState


def _document_init_frame_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> None:
    element = framed_element.element

    assert isinstance(element, Document)

    framed_element.frame = SequentialRendererFrame.from_children(element.root_blocks)

    return None


def _document_enter_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element
    frame = framed_element.frame

    assert isinstance(element, Document)
    assert isinstance(frame, SequentialRendererFrame)
    assert isinstance(state, TextRendererState)

    if not frame.has_more_children:
        return None

    return RendererFramedElement(element=element.root_blocks[frame.current_child_index])
