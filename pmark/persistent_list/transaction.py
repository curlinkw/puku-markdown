from typing import Generic

from pmark.persistent_list.type_vars import ItemT


class Transaction(Generic[ItemT]):
    def __init__(self) -> None:
