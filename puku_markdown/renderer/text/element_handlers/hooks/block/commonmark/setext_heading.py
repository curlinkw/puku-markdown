from puku_markdown._utils.constants import DEFAULT_SETEXT_HEADING_MARKER_LENGTH
from puku_markdown.elements import SetextHeading
from puku_markdown.renderer.framed_element import RendererFramedElement
from puku_markdown.renderer.state import RendererState
from puku_markdown.renderer.text.state import TextRendererState


def _setext_heading_enter_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element

    assert isinstance(element, SetextHeading)
    assert framed_element.frame is None
    assert isinstance(state, TextRendererState)

    state.write_parts(
        "\n",
        element.content,
        "\n",
        element.marker * DEFAULT_SETEXT_HEADING_MARKER_LENGTH,
    )
    state.write_newline()

    return None
