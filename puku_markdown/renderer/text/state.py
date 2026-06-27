from dataclasses import dataclass, field

from puku_markdown.renderer.state import RendererState


@dataclass(slots=True)
class TextRendererState(RendererState):
    """
    Mutable rendering context for sequential, iterative (non-recursive) AST traversal.
    """

    rendered_text_lines: list[str] = field(default_factory=list)
    """
    Accumulates fully rendered lines. Each entry is a complete line of output
    (including any inherited prefix). Use `'\n'.join(rendered_text_lines)` to obtain
    the final output.
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

    def write_parts(self, *parts: str, prepend_inherited_prefix: bool = True) -> None:
        """Writes string parts, handling line continuations and inherited prefixes.

        This method is the core line-builder for the renderer. It joins the input
        `parts`, splits the result by newline (``\n``), and routes each segment
        to the output buffer with the following rules:

        **First segment** (text before the first newline):
            - If the buffer is **empty**: the segment starts a new line and
            receives the inherited prefix.
            - If the buffer has a **non-empty** last line: the segment is appended
            to that line **without** adding the inherited prefix.
            - If the buffer has an **empty** last line: the segment is appended
            to that empty line, but **the inherited prefix is prepended** to it.
            (This effectively turns an existing blank line into a properly
            prefixed line.)

        **Subsequent segments** (each line after the first newline):
            - Each segment starts a new line. These new lines always receive the
            inherited prefix (if `prepend_inherited_prefix` is `True`).

        The inherited prefix (``''.join(self.inherited_prefix_parts)``) is applied
        only when a line is *newly created* (buffer empty) or *reactivated from
        a blank line* (last line empty). It is **never** applied when appending
        to an existing no-empty line.

        Args:
            *parts: Variable number of string fragments to join and write.
            prepend_inherited_prefix: If `True`, the inherited prefix is applied
                to all newly created lines (buffer empty, last line empty, or any
                line after the first newline). Defaults to `True`.

        Returns:
            None.
        """
        content = "".join(parts)

        if not content:
            return

        lines = content.split("\n")
        first_line = lines[0]

        inherited_prefix = (
            "".join(self.inherited_prefix_parts) if prepend_inherited_prefix else ""
        )

        if self.rendered_text_lines:
            prefix_for_first = "" if self.rendered_text_lines[-1] else inherited_prefix
            self.rendered_text_lines[-1] += prefix_for_first + first_line
        else:
            self.rendered_text_lines.append(inherited_prefix + first_line)

        self.rendered_text_lines.extend(inherited_prefix + line for line in lines[1:])
        return None

    def write_part(self, part: str, prepend_inherited_prefix: bool = True) -> None:
        """Writes a single string part as a logical unit.

        This is a convenience wrapper around `write_parts()` for the common case
        of writing a single fragment. See `write_parts()` for detailed behavior
        regarding line continuation, newline splitting, and prefix handling.

        Args:
            part: The string fragment to write.
            prepend_inherited_prefix: Passed through to `write_parts()`.

        Returns:
            None.

        Example:
            >>> self.write_part("Hello world")
            >>> # Equivalent to: self.write_parts("Hello world")
        """
        self.write_parts(part, prepend_inherited_prefix=prepend_inherited_prefix)

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
