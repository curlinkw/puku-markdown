from dataclasses import dataclass, field

from puku_markdown.renderer.state import RendererState


@dataclass(slots=True)
class TextRendererState(RendererState):
    """
    Mutable rendering context for sequential, iterative (non-recursive) AST traversal.
    """

    rendered_text_parts: list[str] = field(default_factory=list)
    """
    Accumulates rendered string parts. Joining these parts at the end of the
    render pass yields the final output text. Use `''.join(rendered_text_parts)`
    for O(n) performance instead of repeated `str +=` concatenation.
    """

    inherited_prefix_parts: list[str] = field(default_factory=list)
    """
    Accumulates string parts representing all ancestor block markers.

    This replaces a single `str` prefix to avoid repeated string concatenation
    when entering/exiting nested blocks. Each block appends its marker part
    (e.g., `"> "`, `"1. "`) on enter, and pops it on exit.

    Parser Counterpart (`LineDescriptor`):
        For the current block, the ancestors' markers occupy the source
        characters *immediately preceding* `line_start_charno`.

        While the parser uses `line_start_charno` to numerically skip these
        characters, the renderer accumulates them as parts to be prepended
        to every output line generated for this block.

    Note:
        This list contains only ancestor markers. The current block's own marker
        (e.g., `"1. "`) is handled separately by the block's own rendering logic.
    """

    def write_parts(self, *parts: str) -> None:
        """
        Writes one or more string parts to the output buffer.

        If `inherited_prefix_parts` is non-empty, its parts are automatically
        prepended as the first parts of this write operation. The prefix parts
        are **not** consumed or cleared; they are prepended on every call.

        This method is designed for writing a complete logical unit (typically
        a single line of output). Use it for block-level content.

        Example:
            state.write_parts("#", " ", "Hello")
            # If inherited_prefix_parts == ["> "], outputs "> # Hello"
        """
        if self.inherited_prefix_parts:
            self.rendered_text_parts.extend(self.inherited_prefix_parts)
        self.rendered_text_parts.extend(parts)

    def write_part(self, part: str) -> None:
        """
        Writes a single string part to the output buffer.

        If `inherited_prefix` is non-empty, it is automatically prepended.
        """
        self.write_parts(part)

    def push_prefix_parts(self, *parts: str) -> None:
        """
        Pushes one or more prefix parts onto the `inherited_prefix_parts` stack.

        Called when entering a block that contributes to the line prefix
        (e.g., blockquote adds `"> "`, ordered list adds `"1. "`).

        Example:
            state.push_prefix_parts("> ")          # Enter blockquote
            state.push_prefix_parts("1. ", " ")    # Enter ordered list item
        """
        self.inherited_prefix_parts.extend(parts)

    def pop_prefix_parts(self, count: int = 1) -> list[str]:
        """
        Pops `count` parts from the `inherited_prefix_parts` stack.

        Called when exiting blocks that contributed to the line prefix.
        The number of parts popped must match the number passed to the
        corresponding `push_prefix_parts` call for that block.

        Args:
            count: The number of parts to pop. Defaults to 1.

        Returns:
            The removed prefix parts, in LIFO order (last pushed first).

        Raises:
            IndexError: If the stack does not contain at least `count` elements.
            ValueError: If `count` is less than 1.

        Example:
            state.push_prefix_parts("1.", " ")   # Push 2 parts.
            ...
            state.pop_prefix_parts(2)            # Pop exactly 2 parts.
        """
        if count < 1:
            raise ValueError("count must be >= 1")
        if len(self.inherited_prefix_parts) < count:
            raise IndexError(
                f"Cannot pop {count} parts; only {len(self.inherited_prefix_parts)} available."
            )

        popped = self.inherited_prefix_parts[-count:]
        del self.inherited_prefix_parts[-count:]
        return popped
