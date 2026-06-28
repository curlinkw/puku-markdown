from dataclasses import dataclass

from puku_markdown.elements import Document, Element
from puku_markdown.renderer.framed_element import RendererFramedElement
from puku_markdown.renderer.state import RendererState
from puku_markdown.renderer.type_aliases import RendererElementHandlerRegistry


@dataclass(slots=True)
class _RendererFramedElementEntry:
    """
    Internal stack entry for the iterative renderer traversal.

    This class is an implementation detail of the explicit-stack loop
    and is not part of the public API. It should not be imported or used
    outside this module.
    """

    framed_element: RendererFramedElement
    """
    The framed element currently active on the stack.
    """

    previous_sibling_type: type[Element] | None
    """
    The class of the immediately preceding sibling block, or `None` if none exists.

    Used to determine whether a separator (e.g., a blank line) is needed before
    the next block.
    """

    is_entering: bool = True
    """
    `True`  if this is the first entry into the framed element
    (must retrieve the first child).

    `False` if this is a re-entry after a child has been processed
    (must retrieve the next child).
    """

    def consume_is_entering(self) -> bool:
        """
        Returns the current `is_entering` state and sets it to `False`.

        This encapsulates the standard "peek + consume" pattern:
        read the flag, then immediately mark the entry as ready for re-entry
        after the current phase completes.
        """
        entering = self.is_entering
        self.is_entering = False
        return entering


def render(
    document: Document,
    state: RendererState,
    element_handler_registry: RendererElementHandlerRegistry,
) -> None:
    framed_element_entries: list[_RendererFramedElementEntry] = [
        _RendererFramedElementEntry(
            framed_element=RendererFramedElement(
                element=document,
            ),
            previous_sibling_type=None,
            is_entering=True,
        )
    ]

    while framed_element_entries:
        current_framed_element_entry = framed_element_entries[-1]
        current_framed_element = current_framed_element_entry.framed_element
        is_entering = current_framed_element_entry.consume_is_entering()
        current_element_handler = element_handler_registry[
            type(current_framed_element.element)
        ]
        state.previous_sibling_type = current_framed_element_entry.previous_sibling_type

        if is_entering:
            current_element_handler.try_call_init_frame_hook(
                framed_element=current_framed_element, state=state
            )

        if (
            next_framed_element := (
                current_element_handler.call_enter_hook(
                    framed_element=current_framed_element, state=state
                )
                if is_entering
                else current_element_handler.try_call_after_child_hook(
                    framed_element=current_framed_element, state=state
                )
            )
        ) is None:
            current_element_handler.try_call_exit_hook(
                framed_element=current_framed_element, state=state
            )
            framed_element_entries.pop()
            continue

        current_frame = current_framed_element.frame

        if current_frame is None:
            raise RuntimeError("Cannot enter child: no active renderer frame.")

        framed_element_entries.append(
            _RendererFramedElementEntry(
                framed_element=next_framed_element,
                previous_sibling_type=current_frame.last_child_type,
                is_entering=True,
            )
        )
        current_frame.record_rendered_child_type(type(next_framed_element.element))
