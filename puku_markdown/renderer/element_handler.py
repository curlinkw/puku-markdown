from collections.abc import Callable
from dataclasses import dataclass

from puku_markdown.renderer.framed_element import RendererFramedElement
from puku_markdown.renderer.state import RendererState


@dataclass(slots=True)
class RendererElementHandler:
    """
    Handles the full rendering lifecycle for a single AST element type.

    The renderer maintains a mapping: `type(element) -> RendererElementHandler`.
    When the core traversal loop encounters an element of this type, it delegates
    to this handler's three callbacks in sequence.
    """

    enter_hook: Callable[
        [RendererFramedElement, RendererState], RendererFramedElement | None
    ]
    """
    Called during the **enter** phase. Returns the next framed element to be
    processed (typically the first child of the current node), or `None` if
    there is no such element (i.e., the node is a leaf).
    This hook is mandatory (must be provided).
    """

    after_child_hook: (
        Callable[[RendererFramedElement, RendererState], RendererFramedElement | None]
        | None
    ) = None
    """
    Called during the **after-child** phase. Returns the next child framed
    element to process, or `None` if all children have been consumed.
    This hook is optional; if `None`, the node is treated as a leaf with no
    children to iterate over.
    """

    exit_hook: Callable[[RendererFramedElement, RendererState], None] | None = None
    """
    Called during the **exit** phase. Performs finalization and rendering.
    This hook is optional; if `None`, the node does nothing on exit.
    """

    init_frame_hook: Callable[[RendererFramedElement, RendererState], None] | None = (
        None
    )
    """
    Initializes the `frame` field of the provided `RendererFramedElement`.

    Based on the element's AST structure, constructs the appropriate frame type
    and assigns it to `framed_element.frame`. If the element is a leaf, it may
    set `framed_element.frame = None` (or leave the existing `None`).
    """

    def call_enter_hook(
        self, framed_element: RendererFramedElement, state: RendererState
    ) -> RendererFramedElement | None:
        """
        Calls the mandatory `enter_hook`.

        Returns the next framed element to process, or `None` if there is none.
        This is the first step in traversing a node's children.
        """
        return self.enter_hook(framed_element, state)

    def try_call_after_child_hook(
        self, framed_element: RendererFramedElement, state: RendererState
    ) -> RendererFramedElement | None:
        """
        Attempts to call the optional `after_child_hook`.

        If the hook is registered, it is invoked to retrieve the next child
        framed element to process. If no hook is provided, this method returns
        `None`, signaling that traversal of this node's children is complete.
        """
        if self.after_child_hook is not None:
            return self.after_child_hook(framed_element, state)
        return None

    def try_call_exit_hook(
        self, framed_element: RendererFramedElement, state: RendererState
    ) -> None:
        """
        Attempts to call the optional `exit_hook`.

        If the hook is registered, it is invoked for finalization
        (e.g., rendering accumulated output). If no hook is provided,
        this method does nothing.
        """
        if self.exit_hook is not None:
            self.exit_hook(framed_element, state)

    def try_call_init_frame_hook(
        self, framed_element: RendererFramedElement, state: RendererState
    ) -> None:
        """
        Attempts to call the optional `init_frame_hook`.

        If the hook is registered, it is invoked to initialize the `frame` field
        of the provided framed element. If no hook is provided, this method does
        nothing.
        """
        if self.init_frame_hook is not None:
            self.init_frame_hook(framed_element, state)
