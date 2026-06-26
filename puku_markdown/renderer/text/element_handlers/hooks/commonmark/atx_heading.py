from puku_markdown.elements import AtxHeading
from puku_markdown.renderer.framed_element import RendererFramedElement
from puku_markdown.renderer.state import RendererState
from puku_markdown.renderer.text.state import TextRendererState


def _render_atx_heading(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element

    assert isinstance(element, AtxHeading)
    assert framed_element.frame is None
    assert isinstance(state, TextRendererState)

    state.rendered_text_parts.extend(("#" * element.level, " ", element.content))

    return None
