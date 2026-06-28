from puku_markdown.elements import FencedCodeBlock
from puku_markdown.renderer.framed_element import RendererFramedElement
from puku_markdown.renderer.state import RendererState
from puku_markdown.renderer.text.state import TextRendererState


def _fenced_code_block_enter_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element

    assert isinstance(element, FencedCodeBlock)
    assert framed_element.frame is None
    assert isinstance(state, TextRendererState)

    state.separate_from_previous_sibling()
    state.write_parts(
        element.markup,
        element.info_string,
        "\n",
        element.content,
        element.markup,
    )
    state.write_empty_line()

    return None
