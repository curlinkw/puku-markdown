from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from puku_markdown.elements import Element

if TYPE_CHECKING:
    from puku_markdown.renderer.element_handler import RendererElementHandler

type RendererElementHandlerRegistry = Mapping[type[Element], "RendererElementHandler"]
