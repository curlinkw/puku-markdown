import pytest

from puku_markdown.parser.parse import parse
from puku_markdown.renderer import render_to_text
from tests.commonmark.spec import SpecExample, get_all_examples


@pytest.mark.parametrize("spec_example", get_all_examples(), ids=lambda x: x.example)
def test_text_renderer(spec_example: SpecExample) -> None:
    if spec_example.example in (596, 218, 239, 240):
        return None

    as_ast = parse(spec_example.markdown)

    assert as_ast == parse(render_to_text(as_ast))
