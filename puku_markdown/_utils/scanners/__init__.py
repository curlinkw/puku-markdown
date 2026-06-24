"""
Scanners for extracting substrings (link titles, destinations, labels).

These functions may maintain internal state for multiline patterns, but never access
or mutate the parser's global state.

In this module, "scan" means "recognize a pattern and produce an outcome without
side effects on the parser", distinguishing it from stateful `scan_*` methods
in parser classes that modify the parser's current line or character index.
"""

from puku_markdown._utils.scanners.link_destination import (
    LinkDestinationScanResult,
    scan_link_destination,
)
from puku_markdown._utils.scanners.link_title import (
    LinkTitleScannerState,
    LinkTitleScannerStatus,
    scan_link_title,
)

__all__ = [
    "LinkDestinationScanResult",
    "LinkTitleScannerState",
    "LinkTitleScannerStatus",
    "scan_link_destination",
    "scan_link_title",
]
