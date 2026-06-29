from puku_markdown._utils.constants import SPACE_CHARACTER
from puku_markdown.elements import AtxHeading
from puku_markdown.renderer.framed_element import RendererFramedElement
from puku_markdown.renderer.state import RendererState
from puku_markdown.renderer.text.state import TextRendererState


def _atx_heading_enter_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element

    assert isinstance(element, AtxHeading)
    assert framed_element.frame is None
    assert isinstance(state, TextRendererState)

    state.separate_from_previous_sibling()
    state.write_parts("#" * element.level, SPACE_CHARACTER, element.content)
    state.write_empty_line()

    return None
