import re

from pmark.constants import HTML_BLOCK_NAMES


LINE_ENDINGS_RE = re.compile(r"\r\n?|\n")
"""
Per CommonMark spec 0.31.2 section 2.1, a line ending is:
- Line feed (U+000A, '\\n')
- Carriage return (U+000D, '\\r') NOT followed by a line feed
- Carriage return + line feed ('\\r\\n') as a pair
Reference: https://spec.commonmark.org/0.31.2/#line-ending
"""

_HTML_ATTRIBUTE_NAME = r"[a-zA-Z_:][a-zA-Z0-9:._-]*"
"""
Regex string for an HTML attribute name (e.g., `href`, `class`).
"""

_HTML_UNQUOTED_VALUE = r"[^\"'=<>`\x00-\x20]+"
"""
Regex string for an unquoted attribute value (no spaces or special chars).
"""

_HTML_SINGLE_QUOTED_VALUE = r"'[^']*'"
"""
Regex string for a single-quoted attribute value.
"""

_HTML_DOUBLE_QUOTED_VALUE = r'"[^"]*"'
"""
Regex string for a double-quoted attribute value.
"""

_HTML_ATTRIBUTE_VALUE = rf"(?:{_HTML_UNQUOTED_VALUE}|{_HTML_SINGLE_QUOTED_VALUE}|{_HTML_DOUBLE_QUOTED_VALUE})"
"""
Regex string for any attribute value (unquoted or quoted).
"""

_HTML_ATTRIBUTE_SPEC = (
    rf"(?:\s+{_HTML_ATTRIBUTE_NAME}(?:\s*=\s*{_HTML_ATTRIBUTE_VALUE})?)"
)
"""
Regex string for a full HTML attribute specification (whitespace + name + optional value).
"""

_HTML_OPEN_TAG = rf"<[A-Za-z][A-Za-z0-9\-]*{_HTML_ATTRIBUTE_SPEC}*\s*/?>"
"""
Regex string for an opening HTML tag (e.g., `<div>`, `<img/>`).
"""

_HTML_CLOSE_TAG = r"</[A-Za-z][A-Za-z0-9\-]*\s*>"
"""
Regex string for a closing HTML tag (e.g., `</div>`).
"""

_HTML_COMMENT = r"<!---?>|<!--(?:[^-]|-[^-]|--[^>])*-->"
"""
Regex string for an HTML comment (including the obsolete `<!-` form).
"""

_HTML_PROCESSING_INSTRUCTION = r"<[?][\s\S]*?[?]>"
"""
Regex string for an XML processing instruction (e.g., `<?php ... ?>`).
"""

_HTML_MARKUP_DECLARATION = r"<![A-Za-z][^>]*>"
"""
Regex string for a markup declaration (e.g., `<!DOCTYPE html>`).
"""

_HTML_CDATA = r"<!\[CDATA\[[\s\S]*?\]\]>"
"""
Regex string for a CDATA section.
"""

HTML_BLOCK_START_RE: re.Pattern = re.compile(
    rf"^(?:{_HTML_OPEN_TAG}|{_HTML_CLOSE_TAG}|{_HTML_COMMENT}|{_HTML_PROCESSING_INSTRUCTION}|{_HTML_MARKUP_DECLARATION}|{_HTML_CDATA})",
    re.IGNORECASE,
)
"""
Match the start of any HTML block (tag, comment, PI, declaration, CDATA).

This regex matches the beginning of a CommonMark HTML block, as defined by
the seven types in the specification. It covers:
- Opening or closing HTML tags (including self-closing)
- HTML comments (`<!-- ... -->`)
- Processing instructions (`<? ... ?>`)
- Markup declarations (`<!DOCTYPE ... >`)
- CDATA sections (`<![CDATA[ ... ]]>`)
"""

_HTML_OPEN_CLOSE_TAG: str = rf"^(?:{_HTML_OPEN_TAG}|{_HTML_CLOSE_TAG})"
"""
String pattern for opening or closing HTML tags (not compiled).
"""

HTML_OPEN_CLOSE_TAG_RE: re.Pattern = re.compile(_HTML_OPEN_CLOSE_TAG, re.IGNORECASE)
"""
Match an opening or closing HTML tag (including self-closing) at line start.

This regex matches only tags, not comments, PI, declarations, or CDATA.
It is used for the last (type 7) HTML block rule.
"""

HTML_RAW_TEXT_TAG_OPEN_RE: re.Pattern = re.compile(
    r"^<(script|pre|style|textarea)(?=(\s|>|$))", re.IGNORECASE
)
"""
Match the start of a raw text HTML block: `<script`, `<pre`, `<style`, `<textarea>`.
"""

HTML_RAW_TEXT_TAG_CLOSE_RE = re.compile(
    r"</(script|pre|style|textarea)>", re.IGNORECASE
)
"""
Match the closing tag of a raw text HTML element.
"""

HTML_COMMENT_OPEN_RE = re.compile(r"^<!--")
"""
Match the start of an HTML comment: `<!--`.
"""

HTML_COMMENT_CLOSE_RE = re.compile(r"-->")
"""
Match the end of an HTML comment: `-->`.
"""

HTML_PROCESSING_INSTRUCTION_OPEN_RE = re.compile(r"^<\?")
"""
Match the start of a processing instruction: `<?`.
"""

HTML_PROCESSING_INSTRUCTION_CLOSE_RE = re.compile(r"\?>")
"""
Match the end of a processing instruction: `?>`.
"""

HTML_MARKUP_DECLARATION_OPEN_RE = re.compile(r"^<![A-Z]")
"""
Match the start of a markup declaration: `<!` followed by an ASCII letter.
"""

HTML_MARKUP_DECLARATION_CLOSE_RE = re.compile(r">")
"""
Match the closing `>` of a markup declaration.
"""

HTML_CDATA_OPEN_RE = re.compile(r"^<!\[CDATA\[")
"""
Match the start of a CDATA section: `<![CDATA[`.
"""

HTML_CDATA_CLOSE_RE = re.compile(r"\]\]>")
"""
Match the end of a CDATA section: `]]>`.
"""

HTML_BLOCK_LEVEL_TAG_OPEN_RE = re.compile(
    r"^</?(" + "|".join(HTML_BLOCK_NAMES) + r")(?=(\s|/?>|$))", re.IGNORECASE
)
"""
Match an opening or closing block-level HTML tag at line start.
"""

HTML_BLOCK_LEVEL_TAG_CLOSE_RE = re.compile(r"^$")
"""
Match a blank line, which closes a block-level tag block.
"""

HTML_TAG_OPEN_RE = re.compile(_HTML_OPEN_CLOSE_TAG + r"\s*$", re.IGNORECASE)
"""
Match any other HTML opening or closing tag at line start (type 7).
"""

HTML_TAG_CLOSE_RE = re.compile(r"^$")
"""
Match a blank line, which closes a type-7 HTML block.
"""
