import re


# Per CommonMark spec 0.31.2 section 2.1, a line ending is:
# - Line feed (U+000A, '\\n')
# - Carriage return (U+000D, '\\r') NOT followed by a line feed
# - Carriage return + line feed ('\\r\\n') as a pair
# Reference: https://spec.commonmark.org/0.31.2/#line-ending
LINE_ENDINGS_RE = re.compile(r"\r\n?|\n")
