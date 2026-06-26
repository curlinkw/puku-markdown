from dataclasses import dataclass

from puku_markdown.elements import Document
from puku_markdown.renderer.framed_element import RendererFramedElement
from puku_markdown.renderer.frames import SequentialRendererFrame
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
                frame=SequentialRendererFrame.from_children(document.root_blocks),
                element=document,
            ),
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

        framed_element_entries.append(
            _RendererFramedElementEntry(
                framed_element=next_framed_element, is_entering=True
            )
        )
