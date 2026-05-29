from dataclasses import dataclass


@dataclass(slots=True)
class ParagraphLocals:
    current_lineno: int
    end_lineno: int
    is_terminated: bool = False
