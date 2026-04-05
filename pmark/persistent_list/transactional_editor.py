from typing import Generic, overload, Union, Self

from pmark.persistent_list.core import PersistentList
from pmark.persistent_list.change_set import ChangeSet
from pmark.persistent_list.modification import Modification
from pmark.persistent_list.type_vars import ItemT


class TransactionalEditor(Generic[ItemT]):
    def __init__(self, target: PersistentList[ItemT]) -> None:
        self._target: PersistentList[ItemT] = target
        self._changeset: ChangeSet | None = None

    @overload
    def __getitem__(self, index: int) -> ItemT: ...

    @overload
    def __getitem__(self, index: slice) -> list[ItemT]: ...

    def __getitem__(self, index: Union[int, slice]) -> Union[ItemT, list[ItemT]]:
        """
        Return the item(s) at the given index or slice.

        - For an integer index, returns the single element at that position.
        - For a slice, returns a *new plain Python list* containing a shallow copy
        of the selected elements. This breaks persistence intentionally - slices
        are ephemeral and not tracked as persistent versions.

        Raises:
            IndexError: If an integer index is out of range.
        """
        return self._target[index]

    def enter_transaction(self) -> None:
        """
        Enter the transactional context, creating and activating a new transaction.
        """
        modification_count = len(self._target._changeset_stack)
        self._changeset = ChangeSet(
            start_modification_index=modification_count,
            end_modification_index=modification_count,
        )
        self._target._changeset_stack.append(self._changeset)

    @property
    def is_transaction_active(self) -> bool:
        """Return True if the transaction has been entered but not yet exited."""
        return self._changeset is not None

    def is_top_transaction(self) -> bool:
        """
        Return `True` if this editor's transaction is the top (most recent) on the changeset stack.

        Only the top transaction can accept new modifications. This method assumes
        the transaction is active (i.e., between __enter__ and __exit__). If called
        outside a transaction, it returns False.

        Returns:
            bool: True if the transaction is both active and at the stack top.
        """
        return (
            self.is_transaction_active
            and self._changeset is self._target._changeset_stack[-1]
        )

    def _expect_changeset(self) -> ChangeSet:
        """
        Return the active transaction's ChangeSet, or raise if none exists.

        Returns:
            ChangeSet: The current `_changeset` object.

        Raises:
            ValueError: If `self._changeset` is `None`, meaning the editor is not
                currently inside a transaction context.
        """
        if self._changeset is None:
            raise ValueError("No active transaction.")
        return self._changeset

    def __setitem__(self, index: int, value: ItemT) -> None:
        """
        Assign a value to an element in the persistent list within this transaction.

        The assignment is recorded as a modification; it becomes part of the persistent
        state only when the transaction commits. The change is immediately visible to
        reads inside the same transaction (via `__getitem__`).

        This operation is only allowed when the editor's transaction is the top of the
        changeset stack. Nested transactions (if any) must be closed before writing.

        Args:
            index: Zero-based position to modify (negative indices count from the end).
            value: New element to place at the specified index.

        Raises:
            RuntimeError: If this editor's transaction is not the top transaction.
            IndexError: If `index` is out of range for the current list.
            ValueError: If the editor has no active transaction (defensive check).
        """
        if not self.is_top_transaction():
            raise RuntimeError("Cannot write to a non-top transaction.")

        self._target._modification_stack.append(
            Modification(index=index, prior_value=self._target._items[index])
        )
        self._target._items[index] = value
        self._expect_changeset().append_modification()

    def exit_transaction(self) -> None:
        """
        Exit the current transaction and roll back all its modifications.

        All modifications made during this transaction are undone in reverse order,
        the transaction's change set is removed from the stack, and the editor
        becomes inactive. After this call, any further write operations will raise
        an error until a new transaction is started.

        Raises:
            RuntimeError: If this editor's transaction is not the top of the stack.
            ValueError: If no transaction is active.
        """
        if not self.is_top_transaction():
            raise RuntimeError("Cannot exit a non-top transaction.")

        changeset = self._expect_changeset()

        for _ in range(changeset.modification_count):
            self._target._modification_stack.pop().rollback(self._target._items)

        self._target._changeset_stack.pop()
        self._changeset = None
