from collections.abc import Mapping
from types import MappingProxyType

from puku_markdown.elements import (
    AtxHeading,
    Blockquote,
    Document,
    Element,
    FencedCodeBlock,
    HtmlBlock,
    IndentedCodeBlock,
    LinkReferenceDefinition,
    List,
    Paragraph,
    SetextHeading,
    ThematicBreak,
)
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
    _fenced_code_block_enter_hook,
    _html_block_enter_hook,
    _indented_code_block_enter_hook,
    _link_reference_definition_block_enter_hook,
    _list_after_child_hook,
    _list_enter_hook,
    _list_init_frame_hook,
    _paragraph_enter_hook,
    _setext_heading_enter_hook,
    _thematic_break_enter_hook,
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
    FencedCodeBlock: RendererElementHandler(
        enter_hook=_fenced_code_block_enter_hook,
        after_child_hook=None,
        exit_hook=None,
        init_frame_hook=None,
    ),
    HtmlBlock: RendererElementHandler(
        enter_hook=_html_block_enter_hook,
        after_child_hook=None,
        exit_hook=None,
        init_frame_hook=None,
    ),
    IndentedCodeBlock: RendererElementHandler(
        enter_hook=_indented_code_block_enter_hook,
        after_child_hook=None,
        exit_hook=None,
        init_frame_hook=None,
    ),
    LinkReferenceDefinition: RendererElementHandler(
        enter_hook=_link_reference_definition_block_enter_hook,
        after_child_hook=None,
        exit_hook=None,
        init_frame_hook=None,
    ),
    List: RendererElementHandler(
        enter_hook=_list_enter_hook,
        after_child_hook=_list_after_child_hook,
        exit_hook=None,
        init_frame_hook=_list_init_frame_hook,
    ),
    Paragraph: RendererElementHandler(
        enter_hook=_paragraph_enter_hook,
        after_child_hook=None,
        exit_hook=None,
        init_frame_hook=None,
    ),
    SetextHeading: RendererElementHandler(
        enter_hook=_setext_heading_enter_hook,
        after_child_hook=None,
        exit_hook=None,
        init_frame_hook=None,
    ),
    ThematicBreak: RendererElementHandler(
        enter_hook=_thematic_break_enter_hook,
        after_child_hook=None,
        exit_hook=None,
        init_frame_hook=None,
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
