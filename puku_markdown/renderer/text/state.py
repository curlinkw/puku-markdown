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

    inherited_prefix: str = ""
    """
    String reconstruction of all ancestor block markers on the current line.

    Parser Counterpart (`LineDescriptor`):
        For the current block, the ancestors' markers occupy the source
        characters *immediately preceding* `line_start_charno`.

        While the parser uses `line_start_charno` to numerically skip these
        characters and isolate the current block's marker/content, the renderer
        uses `inherited_prefix` to literally re-insert that skipped text at the
        beginning of every output line generated for this block.

    Note:
        This prefix contains only ancestors. The current block's own marker
        (e.g., `"1. "`) is NOT included here; it is added separately when
        the renderer processes the current block's frame.
    """

    def write_parts(self, *parts: str) -> None:
        """
        Writes one or more string parts to the output buffer.

        If `inherited_prefix` is non-empty, it is automatically prepended as the
        first part of this write operation. The prefix is **not** consumed or
        cleared; it will be prepended again on every subsequent call to
        `write_parts` or `write_part`.

        This method is designed for writing a complete logical unit (typically
        a single line of output). Use it for block-level content.
        """
        if self.inherited_prefix:
            self.rendered_text_parts.append(self.inherited_prefix)
        self.rendered_text_parts.extend(parts)

    def write_part(self, part: str) -> None:
        """
        Writes a single string part to the output buffer.

        If `inherited_prefix` is non-empty, it is automatically prepended.
        The prefix is **not** consumed or cleared.
        """
        self.write_parts(part)
