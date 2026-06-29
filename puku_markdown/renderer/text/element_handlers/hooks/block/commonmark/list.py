from puku_markdown._utils.constants import (
    EMPTY_STRING,
    INDENTED_CODE_BLOCK_MIN_INDENT,
    INDENTED_CODE_BLOCK_MIN_INDENT_STR,
    SPACE_CHARACTER,
)
from puku_markdown.elements import BlockElement, Element, IndentedCodeBlock, List
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
        segment_child_counts=[max(1, len(item.children)) for item in element.items],
        last_child_type=None,
        should_allow_cross_segment_siblings=False,
    )

    return None


def _get_marker_str(
    element: List,
    frame: SegmentedRendererFrame,
    current_child: BlockElement | None,
) -> str:
    marker_number = element.items[frame.current_segment_index].marker_number
    marker_number_str = EMPTY_STRING if marker_number is None else str(marker_number)

    if isinstance(current_child, IndentedCodeBlock | List):
        after_marker_number_str = SPACE_CHARACTER
    else:
        after_marker_number_str = INDENTED_CODE_BLOCK_MIN_INDENT_STR

    marker_str = (
        f"{SPACE_CHARACTER * (INDENTED_CODE_BLOCK_MIN_INDENT - 1)}"
        f"{marker_number_str}{element.marker_char}{after_marker_number_str}"
    )
    return marker_str


def _render_current_child(
    element: List, frame: SegmentedRendererFrame, state: TextRendererState
) -> Element:
    current_child = element.items[frame.current_segment_index].children[
        frame.current_child_index
    ]

    if frame.is_current_child_first_in_segment:
        marker_str = _get_marker_str(
            element=element, frame=frame, current_child=current_child
        )
        state.write_part(marker_str)
        state.push_prefix_parts(SPACE_CHARACTER * len(marker_str))
    elif isinstance(current_child, List) and (not element.is_tight):
        state.ensure_last_line_is_empty()
        state.write_part(EMPTY_STRING)
        state.write_empty_line()

    return current_child


def _process_empty_items(
    element: List, frame: SegmentedRendererFrame, state: TextRendererState
) -> None:
    if frame.current_segment_index >= frame.segment_count:
        return

    if element.items[frame.current_segment_index].children:
        return

    while frame.current_segment_index < frame.segment_count and (
        not element.items[frame.current_segment_index].children
    ):
        state.ensure_last_line_is_empty()

        marker_str = _get_marker_str(element=element, frame=frame, current_child=None)
        state.write_part(marker_str)

        state.write_empty_line()
        frame.current_segment_index += 1

    frame.current_child_index = 0


def _list_enter_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> RendererFramedElement | None:
    element = framed_element.element
    frame = framed_element.frame

    assert isinstance(element, List)
    assert isinstance(frame, SegmentedRendererFrame)
    assert isinstance(state, TextRendererState)

    state.enter_suppress_separators(suppress=element.is_tight)

    _process_empty_items(element=element, frame=frame, state=state)

    if state.previous_sibling_type is not None:
        state.ensure_last_line_is_empty()

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

    if frame.is_current_child_last_in_segment:
        state.pop_prefix_parts(count=1)

        state.ensure_last_line_is_empty()

    frame.advance_to_next_child()

    _process_empty_items(element=element, frame=frame, state=state)

    if not frame.has_more_children:
        return None

    if frame.is_current_child_first_in_segment and (not element.is_tight):
        # Invariant:
        # last empty line is ensured
        state.write_part(EMPTY_STRING)
        state.write_empty_line()

    return RendererFramedElement(
        element=_render_current_child(element=element, frame=frame, state=state)
    )


def _list_exit_hook(
    framed_element: RendererFramedElement, state: RendererState
) -> None:
    element = framed_element.element
    frame = framed_element.frame

    assert isinstance(element, List)
    assert isinstance(frame, SegmentedRendererFrame)
    assert isinstance(state, TextRendererState)

    state.exit_suppress_separators()
