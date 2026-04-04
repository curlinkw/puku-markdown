from typing import Generic
from dataclasses import dataclass

from pmark.persistent_list.type_vars import ItemT


@dataclass(slots=True, frozen=True)
class Modification(Generic[ItemT]):
    index: int
    prior_value: ItemT
