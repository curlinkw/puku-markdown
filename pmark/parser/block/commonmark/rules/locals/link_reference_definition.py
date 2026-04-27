from enum import Enum, auto
from dataclasses import dataclass


class _LinkReferenceDefinitionStep(Enum):
    SCAN_LABEL_END = auto()


@dataclass(slots=True)
class LinkReferenceDefinitionLocals:
    current_lineno: int
    step: _LinkReferenceDefinitionStep = _LinkReferenceDefinitionStep.SCAN_LABEL_END
    is_current_line_block_terminator: bool = False
