from puku_markdown.elements import HtmlBlock
from puku_markdown.renderer.framed_element import RendererFramedElement
from puku_markdown.renderer.state import RendererState
from puku_markdown.renderer.text.state import TextRendererState


def _html_block_enter_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element

    assert isinstance(element, HtmlBlock)
    assert framed_element.frame is None
    assert isinstance(state, TextRendererState)

    state.write_part(element.content)
    state.write_newline()

    return None
