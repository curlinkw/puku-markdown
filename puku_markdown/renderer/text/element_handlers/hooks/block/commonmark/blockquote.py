from puku_markdown.elements import Blockquote, Paragraph
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

    current_element = element.children[frame.current_child_index]

    if frame.is_current_child_last and isinstance(current_element, Paragraph):
        state.write_part("> ")
    else:
        state.push_prefix_parts("> ")

    return RendererFramedElement(element=current_element)


def _blockquote_after_child_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element
    frame = framed_element.frame

    assert isinstance(element, Blockquote)
    assert isinstance(frame, SequentialRendererFrame)
    assert isinstance(state, TextRendererState)

    frame.current_child_index += 1

    state.ensure_last_line_is_empty()

    if not frame.has_more_children:
        return None

    current_element = element.children[frame.current_child_index]

    if frame.is_current_child_last and isinstance(current_element, Paragraph):
        state.pop_prefix_parts(count=1)
        state.write_part("> ")
        state.write_empty_line()
        state.write_part("> ")
        frame.last_child_type = None

    return RendererFramedElement(element=current_element)


def _blockquote_exit_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> None:
    element = framed_element.element
    frame = framed_element.frame

    assert isinstance(element, Blockquote)
    assert isinstance(frame, SequentialRendererFrame)
    assert isinstance(state, TextRendererState)

    if not isinstance(element.children[-1], Paragraph):
        state.pop_prefix_parts(count=1)

    return None
