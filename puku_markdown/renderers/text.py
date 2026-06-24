from functools import singledispatch

from puku_markdown.elements import Document


def render_to_text(document: Document) -> str:
    raise NotImplementedError
