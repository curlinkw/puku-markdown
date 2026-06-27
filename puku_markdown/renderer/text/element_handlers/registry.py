from collections.abc import Mapping
from types import MappingProxyType

from puku_markdown.elements import AtxHeading, Blockquote, Document, Element
from puku_markdown.renderer.element_handler import RendererElementHandler
from puku_markdown.renderer.text.element_handlers.hooks import (
    _atx_heading_enter_hook,
    _blockquote_after_child_hook,
    _blockquote_enter_hook,
    _blockquote_exit_hook,
    _blockquote_init_frame_hook,
    _document_after_child_hook,
    _document_enter_hook,
    _document_init_frame_hook,
)

_TEXT_RENDERER_ELEMENT_HANDLERS: dict[type[Element], RendererElementHandler] = {
    Document: RendererElementHandler(
        enter_hook=_document_enter_hook,
        after_child_hook=_document_after_child_hook,
        exit_hook=None,
        init_frame_hook=_document_init_frame_hook,
    ),
    AtxHeading: RendererElementHandler(
        enter_hook=_atx_heading_enter_hook,
        after_child_hook=None,
        exit_hook=None,
        init_frame_hook=None,
    ),
    Blockquote: RendererElementHandler(
        enter_hook=_blockquote_enter_hook,
        after_child_hook=_blockquote_after_child_hook,
        exit_hook=_blockquote_exit_hook,
        init_frame_hook=_blockquote_init_frame_hook,
    ),
}

TEXT_RENDERER_ELEMENT_HANDLERS: Mapping[type[Element], RendererElementHandler] = (
    MappingProxyType(_TEXT_RENDERER_ELEMENT_HANDLERS)
)
"""
Public, read-only registry for the plain-text renderer.

Maps AST element types to their corresponding `RendererElementHandler`
instances, which define the full rendering lifecycle for that specific element type.
"""
