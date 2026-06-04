# puku-markdown

[![PyPI version](https://img.shields.io/pypi/v/puku-markdown.svg)](https://pypi.org/project/puku-markdown/)
[![Python Versions](https://img.shields.io/pypi/pyversions/puku-markdown.svg)](https://pypi.org/project/puku-markdown/)
[![Test Status](https://github.com/curlinkw/puku-markdown/actions/workflows/pytest.yaml/badge.svg)](https://github.com/curlinkw/puku-markdown/actions/workflows/pytest.yaml)
[![License](https://img.shields.io/github/license/curlinkw/puku-markdown.svg)](https://github.com/curlinkw/puku-markdown/blob/main/LICENSE)

A **CommonMark‑compliant** Markdown parser for block elements, written in pure Python with an **explicit stack** – no recursion, no hidden state, and a strong focus on readability and maintainability. Requires **Python 3.12 or higher**.

## Motivation

While `markdown-it-py` is a solid parser, its codebase has several pain points that this project addresses:

- **Recursive descent → explicit stack** – `puku-markdown` uses an explicit stack, eliminating recursion limits and improving portability (e.g., to C). For example, `markdown-it-py` relies on recursion and a mutable `state.tight` flag that becomes inconsistent across nested lists; `puku-markdown` stores per‑level state on an explicit stack instead.
- **No obscure quirks** – Removes confusing state flags like `sCount = -1` for continuation.
- **Readability first** – Clean variable names, thorough comments, and a well‑structured codebase.
- **Designed for long‑term maintenance** – Every internal detail is documented and intentional.

> This library was born from a deep refactoring attempt of `markdown-it-py`. Instead of fighting the original code, we built a fresh, cleaner implementation.

## Features

- ✅ **CommonMark block elements** – headings, code blocks, lists, blockquotes, HTML blocks, thematic breaks, and more.
- ✅ **Explicit stack** – no recursion, easy to reason about and port.
- ✅ **Pure Python** – no external runtime dependencies.
- ✅ **Tested against `markdown-it-py`** – we reuse their extensive test suite for compliance.

> **Current status:** Block elements are fully supported. Inline elements (emphasis, links, images, etc.) are planned.

## Installation

```bash
pip install puku-markdown
```

Or with `uv` (recommended):

```bash
uv add puku-markdown
```

## Quick Usage

```python
from puku_markdown import parse

document = parse("""
# Heading

- List item 1
- List item 2

> A blockquote.
""")
print(document)
```

## Development

Clone the repository and set up the environment:

```bash
git clone https://github.com/curlinkw/puku-markdown.git
cd puku-markdown
uv sync --group test
```

Run tests:

```bash
uv run pytest
```

## Contributing

Issues and pull requests are welcome. Please ensure that changes pass the CommonMark test suite and maintain 100% compatibility for the supported block elements.

## License

MIT License. See [LICENSE](LICENSE) for details.
