from dataclasses import dataclass

from puku_markdown.renderer.state import RendererState


@dataclass(slots=True)
class TextRendererState(RendererState):
    """
    Mutable rendering context for sequential, iterative (non-recursive) AST traversal.
    """

    rendered_text: str
    """
    The accumulated rendered output text.
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
