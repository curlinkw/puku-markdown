from puku_markdown.elements import Document
from puku_markdown.renderer.render import render
from puku_markdown.renderer.text.element_handlers import TEXT_RENDERER_ELEMENT_HANDLERS
from puku_markdown.renderer.text.state import TextRendererState


def render_to_text(
    document: Document,
) -> str:
    state = TextRendererState()
    render(
        document=document,
        state=state,
        element_handler_registry=TEXT_RENDERER_ELEMENT_HANDLERS,
    )
    return "".join(state.rendered_text_parts)
