from puku_markdown._utils.constants import INDENTED_CODE_BLOCK_MIN_INDENT_STR
from puku_markdown.elements import IndentedCodeBlock
from puku_markdown.renderer.framed_element import RendererFramedElement
from puku_markdown.renderer.state import RendererState
from puku_markdown.renderer.text.state import TextRendererState


def _indented_code_block_enter_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element

    assert isinstance(element, IndentedCodeBlock)
    assert framed_element.frame is None
    assert isinstance(state, TextRendererState)

    state.separate_from_previous_sibling()

    if state.is_last_line_non_empty:
        state.write_part(INDENTED_CODE_BLOCK_MIN_INDENT_STR)

    with state.apply_inherited_prefix_parts(INDENTED_CODE_BLOCK_MIN_INDENT_STR):
        state.write_parts(element.content)

    state.write_empty_line()

    return None
