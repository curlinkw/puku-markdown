from puku_markdown.elements import Blockquote
from puku_markdown.renderer.framed_element import RendererFramedElement
from puku_markdown.renderer.frames import SequentialRendererFrame
from puku_markdown.renderer.state import RendererState
from puku_markdown.renderer.text.state import TextRendererState


def _blockquote_init_frame_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> None:
    element = framed_element.element

    assert isinstance(element, Blockquote)

    framed_element.frame = SequentialRendererFrame.from_children(element.children)

    return None


def _blockquote_enter_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element
    frame = framed_element.frame

    assert isinstance(element, Blockquote)
    assert isinstance(frame, SequentialRendererFrame)
    assert isinstance(state, TextRendererState)

    if not frame.has_more_children:
        return None

    state.separate_from_previous_sibling()

    state.push_prefix_parts("> ")

    return RendererFramedElement(element=element.children[frame.current_child_index])


def _blockquote_after_child_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element
    frame = framed_element.frame

    assert isinstance(element, Blockquote)
    assert isinstance(frame, SequentialRendererFrame)
    assert isinstance(state, TextRendererState)

    frame.current_child_index += 1

    if not frame.has_more_children:
        return None

    return RendererFramedElement(element=element.children[frame.current_child_index])


def _blockquote_exit_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> None:
    element = framed_element.element
    frame = framed_element.frame

    assert isinstance(element, Blockquote)
    assert isinstance(frame, SequentialRendererFrame)
    assert isinstance(state, TextRendererState)

    state.pop_prefix_parts(count=1)

    return None
