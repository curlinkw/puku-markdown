from collections.abc import Mapping
from types import MappingProxyType

from puku_markdown.elements import AtxHeading, Element
from puku_markdown.renderer.element_handler import RendererElementHandler
from puku_markdown.renderer.text.element_handlers.hooks import _atx_heading_enter_hook

_TEXT_RENDERER_ELEMENT_HANDLERS: dict[type[Element], RendererElementHandler] = {
    AtxHeading: RendererElementHandler(
        enter_hook=_atx_heading_enter_hook, after_child_hook=None, exit_hook=None
    )
}

TEXT_RENDERER_ELEMENT_HANDLERS: Mapping[type[Element], RendererElementHandler] = (
    MappingProxyType(_TEXT_RENDERER_ELEMENT_HANDLERS)
)
"""
Public, read-only registry for the plain-text renderer.

Maps AST element types to their corresponding `RendererElementHandler`
instances, which define the full rendering lifecycle for that specific element type.
"""
