from puku_markdown._utils.constants import INDENTED_CODE_BLOCK_MIN_INDENT_STR
from puku_markdown.elements import Element, List
from puku_markdown.renderer.framed_element import RendererFramedElement
from puku_markdown.renderer.frames import SegmentedRendererFrame
from puku_markdown.renderer.state import RendererState
from puku_markdown.renderer.text.state import TextRendererState


def _list_init_frame_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> None:
    element = framed_element.element

    assert isinstance(element, List)

    framed_element.frame = SegmentedRendererFrame(
        segment_count=len(element.items),
        segment_child_counts=[len(item.children) for item in element.items],
    )

    return None


def _render_current_child(
    element: List, frame: SegmentedRendererFrame, state: TextRendererState
) -> Element:
    current_child = element.items[frame.current_segment_index].children[
        frame.current_child_index
    ]

    if isinstance(current_child, List):
        state.write_part(INDENTED_CODE_BLOCK_MIN_INDENT_STR)
        state.push_prefix_parts(INDENTED_CODE_BLOCK_MIN_INDENT_STR)
    else:
        marker_number = element.items[frame.current_segment_index].marker_number
        marker_number_str = "" if marker_number is None else str(marker_number)

        state.write_part(f"{marker_number_str}{element.marker_char} ")

    return current_child


def _list_enter_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element
    frame = framed_element.frame

    assert isinstance(element, List)
    assert isinstance(frame, SegmentedRendererFrame)
    assert isinstance(state, TextRendererState)

    if not frame.has_more_children:
        return None

    return RendererFramedElement(
        element=_render_current_child(element=element, frame=frame, state=state)
    )


def _list_after_child_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element
    frame = framed_element.frame

    assert isinstance(element, List)
    assert isinstance(frame, SegmentedRendererFrame)
    assert isinstance(state, TextRendererState)

    current_child = element.items[frame.current_segment_index].children[
        frame.current_child_index
    ]

    if isinstance(current_child, List):
        state.pop_prefix_parts(count=1)

    if not element.is_tight:
        state.write_part("\n", prepend_inherited_prefix=False)

    frame.advance_to_next_child()

    if not frame.has_more_children:
        return None

    return RendererFramedElement(
        element=_render_current_child(element=element, frame=frame, state=state)
    )
