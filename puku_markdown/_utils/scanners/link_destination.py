from typing import NamedTuple

from puku_markdown._utils.constants import (
    BACKSLASH_CHARACTER,
    GREATER_THAN_CHARACTER,
    LEFT_PARENTHESIS_CHARACTER,
    LESS_THAN_CHARACTER,
    LINE_FEED_CHARACTER,
    MAX_LINK_DESTINATION_PARENTHESIS_DEPTH,
    RIGHT_PARENTHESIS_CHARACTER,
    SPACE_CHARACTER,
)
from puku_markdown._utils.predicates import is_ascii_control


class LinkDestinationScanResult(NamedTuple):
    destination: str
    next_charno: int


def scan_link_destination(
    source: str, start_charno: int, end_charno: int
) -> LinkDestinationScanResult | None:
    if not (start_charno < end_charno <= len(source)):
        return None

    current_charno = start_charno

    if source[current_charno] == LESS_THAN_CHARACTER:
        current_charno += 1

        while current_charno < end_charno:
            current_char = source[current_charno]

            if current_char == LINE_FEED_CHARACTER:
                return None

            if current_char == LESS_THAN_CHARACTER:
                return None

            if current_char == GREATER_THAN_CHARACTER:
                return LinkDestinationScanResult(
                    destination=source[start_charno + 1 : current_charno],
                    next_charno=current_charno + 1,
                )

            if (current_char == BACKSLASH_CHARACTER) and (
                current_charno + 1 < end_charno
            ):
                current_charno += 2
                continue

            current_charno += 1

        return None

    parenthesis_depth = 0
    while current_charno < end_charno:
        current_char = source[current_charno]

        if current_char == SPACE_CHARACTER:
            break

        if is_ascii_control(current_char):
            break

        if (current_char == BACKSLASH_CHARACTER) and (current_charno + 1 < end_charno):
            if source[current_charno + 1] == SPACE_CHARACTER:
                break
            current_charno += 2
            continue

        if current_char == LEFT_PARENTHESIS_CHARACTER:
            parenthesis_depth += 1

            if parenthesis_depth > MAX_LINK_DESTINATION_PARENTHESIS_DEPTH:
                return None

        if current_char == RIGHT_PARENTHESIS_CHARACTER:
            if parenthesis_depth == 0:
                break

            parenthesis_depth -= 1

        current_charno += 1

    if start_charno == current_charno:
        return None

    if parenthesis_depth != 0:
        return None

    return LinkDestinationScanResult(
        destination=source[start_charno:current_charno], next_charno=current_charno
    )
