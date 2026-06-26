from collections.abc import Sized
from dataclasses import dataclass
from typing import Self


@dataclass(slots=True)
class RendererFrame:
    """
    Base class for all renderer traversal frames.

    In the iterative renderer, this replaces the recursive call stack.
    Each container block pushes a frame to track its position during child
    traversal. The `Renderer` prefix disambiguates these from Parser frames.

    Naming Contract (Traversing Strategy):
        Subclass names must encode the **child iteration strategy**,
        specifying how children are structured and consumed.
    """

    pass


@dataclass(slots=True)
class SequentialRendererFrame(RendererFrame):
    """
    Traversal frame for nodes with a flat, ungrouped list of children.

    Traversing Strategy:
        Linear iteration using a single integer `current_child_index`.
        The traversal assumes all children are at the same structural depth.
    """

    child_count: int
    """
    The total number of children in this node.
    Used to determine when traversal is complete (i.e., `current_child_index >= child_count`).
    """

    current_child_index: int = 0
    """
    The index of the next child to process (0-based). Incremented after
    each child is consumed.
    """

    @classmethod
    def from_children(cls, children: Sized, start_child_index: int = 0) -> Self:
        """
        Creates a sequential traversal frame from a child collection.

        Only the total length of the collection is stored as `child_count`.
        The collection itself is not retained, keeping the frame decoupled
        from the AST and minimizing memory overhead.

        Args:
            children: A collection of child elements. Only its length is used.
            start_child_index: The index from which traversal should begin.
                Defaults to 0.
        """
        return cls(child_count=len(children), current_child_index=start_child_index)


@dataclass(slots=True)
class SegmentedRendererFrame(RendererFrame):
    """
    Segmented traversal strategy (two-level, iterative descent).

    Traversing Strategy:
        The child list is divided into contiguous, non-overlapping **segments**
        (e.g., ListItems). Traversal proceeds segment-by-segment, and within
        each segment, child-by-child.
    """

    segment_count: int
    """
    The total number of segments. Traversal of the outer loop is complete
    when `current_segment_index >= segment_count`.
    """

    segment_child_counts: list[int]
    """
    The number of children for **each** segment, indexed by segment index.
    The inner loop for a segment is complete when
    `current_child_index >= segment_child_counts[current_segment_index]`.
    This list is immutable after frame creation and eliminates the need to
    query the AST for `len()` during traversal.
    """

    current_segment_index: int = 0
    """
    The index of the current segment (0-based). Represents the outer loop
    position. Incremented when all children inside the current segment are
    fully consumed.
    """

    current_child_index: int = 0
    """
    The index of the next child inside the current segment (0-based).
    Represents the inner loop position. Incremented per child consumed.
    """
