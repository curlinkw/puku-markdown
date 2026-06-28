from puku_markdown.elements import LinkReferenceDefinition
from puku_markdown.renderer.framed_element import RendererFramedElement
from puku_markdown.renderer.state import RendererState
from puku_markdown.renderer.text.state import TextRendererState


def _link_reference_definition_block_enter_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element

    assert isinstance(element, LinkReferenceDefinition)
    assert framed_element.frame is None
    assert isinstance(state, TextRendererState)

    state.separate_from_previous_sibling()
    state.write_parts(
        f"[{element.label}]: ", f"<{element.href}> ", f'"{element.title}"'
    )
    state.write_empty_line()

    return None
