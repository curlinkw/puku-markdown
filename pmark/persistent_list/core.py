from typing import Generic

from pmark.persistent_list.modification import Modification
from pmark.persistent_list.type_vars import ItemT


class PersistentList(Generic[ItemT]):
    def __init__(self) -> None:
        self._modification_stack: list[Modification[ItemT]] = []
        self._transaction_stack: list[Transaction[ItemT]] = []
