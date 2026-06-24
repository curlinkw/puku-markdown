from dataclasses import dataclass


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

    current_child_index: int = 0
    """
    The index of the next child to process (0-based). Incremented after
    each child is consumed.
    """


@dataclass(slots=True)
class SegmentedRendererFrame(RendererFrame):
    """
    Segmented traversal strategy (two-level, iterative descent).

    Traversing Strategy:
        The child list is divided into contiguous, non-overlapping **segments**
        (e.g., ListItems). Traversal proceeds segment-by-segment, and within
        each segment, child-by-child.
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
