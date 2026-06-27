from puku_markdown.elements import Paragraph
from puku_markdown.renderer.framed_element import RendererFramedElement
from puku_markdown.renderer.state import RendererState
from puku_markdown.renderer.text.state import TextRendererState


def _paragraph_enter_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element

    assert isinstance(element, Paragraph)
    assert framed_element.frame is None
    assert isinstance(state, TextRendererState)

    state.write_parts(element.content)
    state.write_newline()

    return None
