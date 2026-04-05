from dataclasses import dataclass


@dataclass(slots=True)
class ChangeSet:
    """
    Transaction descriptor: each `Transaction` owns exactly one `ChangeSet` instance.

    Points to a contiguous slice `[start_modification_index, end_modification_index)`
    in the modification stack. Instances are stored on a separate `changeset stack`
    to mark which modifications belong to which transaction.
    """

    start_modification_index: int
    """First modification index (inclusive)."""

    end_modification_index: int
    """First index *after* the last modification (exclusive)."""

    @property
    def modification_count(self) -> int:
        """
        Return the number of modifications in this transaction's slice.

        This is equivalent to `end_modification_index - start_modification_index`.

        Returns:
            int: The total number of modifications belonging to this transaction.
        """
        return self.end_modification_index - self.start_modification_index

    def append_modification(self) -> None:
        """
        Append one modification to this transaction's slice.

        Increments `end_modification_index` by 1, expanding the half-open interval
        `[start_modification_index, end_modification_index)` to include one more
        modification at the end. This method is called after a modification has been
        added to the global modification stack.
        """
        self.end_modification_index += 1
