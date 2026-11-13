"""Shared state store with declared reads/writes and taint tracking.

Contract
- State is a table of cells: `key -> place_id -> scalar` (int, float, str, bool).
  Only scalars are stored, so nobody can change state behind the store's back.
- A domain touches state through a `StateView` built from its declared
  `reads` and `writes`. Any other access raises `UndeclaredAccessError`.
- Taint (see ADR-005): a cell is "tainted" when its value may have been
  influenced by a player action. The taint is the id of a tainted event.
  Within a scope (`begin_scope`), reading a tainted cell taints the scope, and
  every later write in the scope carries the scope's taint. A write from an
  untainted scope clears the cell's taint. Domains must therefore (1) call
  `begin_scope` before working on a place, (2) keep all information flow inside
  the store, and (3) write cells unconditionally (write the same value rather
  than skip the write).
"""

from __future__ import annotations

from collections.abc import Iterable

Scalar = int | float | str | bool


class UndeclaredAccessError(Exception):
    """A domain read or wrote a state key it did not declare."""


class StateStore:
    """All mutable simulation state."""

    def __init__(self) -> None:
        self._values: dict[str, dict[str, Scalar]] = {}
        self._taint: dict[str, dict[str, int]] = {}

    def view(self, owner: str, reads: Iterable[str], writes: Iterable[str]) -> StateView:
        """A view restricted to the declared keys of one domain."""
        return StateView(self, owner, frozenset(reads), frozenset(writes), False)

    def player_view(self) -> StateView:
        """An unrestricted view for player action effects (existing keys only)."""
        return StateView(self, "player", frozenset(), frozenset(), True)

    def keys(self) -> list[str]:
        """All state keys, sorted."""
        return sorted(self._values)

    def places(self, key: str) -> list[str]:
        """Place ids that have a cell for `key`, sorted."""
        return sorted(self._values[key])

    def has(self, key: str, place_id: str) -> bool:
        """True if the cell exists."""
        return key in self._values and place_id in self._values[key]

    def peek(self, key: str, place_id: str) -> Scalar:
        """Read a cell without access checks or taint tracking (tests, scoring, UI)."""
        return self._values[key][place_id]

    def snapshot(self) -> dict[str, dict[str, Scalar]]:
        """Deep copy of all values, keys and places sorted."""
        return {key: dict(sorted(self._values[key].items())) for key in sorted(self._values)}

    def tainted_cells(self) -> frozenset[tuple[str, str]]:
        """Cells whose value may have been influenced by a player action."""
        return frozenset((key, place) for key, cells in self._taint.items() for place in cells)

    def totals(self) -> dict[str, float]:
        """Sum over places of every numeric key (used for per-tick metrics)."""
        result: dict[str, float] = {}
        for key in sorted(self._values):
            cells = self._values[key]
            numbers = [v for v in cells.values() if isinstance(v, (int, float))]
            if len(numbers) == len(cells):
                result[key] = float(sum(numbers))
        return result


class StateView:
    """Checked, taint-tracking access to the store for one owner."""

    def __init__(self, store: StateStore, owner: str, reads: frozenset[str],
                 writes: frozenset[str], unrestricted: bool) -> None:
        self._values = store._values
        self._taint = store._taint
        self.owner = owner
        self._readable = reads | writes
        self._writable = writes
        self._unrestricted = unrestricted
        self._scope_taint: int | None = None

    def begin_scope(self, inherited: int | None = None) -> None:
        """Start a new unit of work; `inherited` is a tainted event id or None."""
        self._scope_taint = inherited

    def mark(self, event_id: int) -> None:
        """Make `event_id` the taint carried by later writes in this scope."""
        self._scope_taint = event_id

    @property
    def scope_taint(self) -> int | None:
        """Tainted event id for the current scope, or None."""
        return self._scope_taint

    def define(self, key: str, place_id: str, value: Scalar) -> None:
        """Create a cell (used by `init_state`)."""
        self._check_write(key)
        self._values.setdefault(key, {})[place_id] = value
        self._taint.setdefault(key, {})

    def get(self, key: str, place_id: str) -> Scalar:
        """Read a cell. Raises on undeclared keys and on missing cells."""
        if key not in self._readable and not self._unrestricted:
            raise UndeclaredAccessError(f"{self.owner} reads undeclared key {key!r}")
        taint = self._taint[key].get(place_id)
        if taint is not None and (self._scope_taint is None or taint > self._scope_taint):
            self._scope_taint = taint
        return self._values[key][place_id]

    def get_or(self, key: str, place_id: str, default: Scalar) -> Scalar:
        """Like `get`, but returns `default` when the cell does not exist.

        Use only for keys owned by another domain that may not be loaded.
        """
        if key not in self._readable and not self._unrestricted:
            raise UndeclaredAccessError(f"{self.owner} reads undeclared key {key!r}")
        if key not in self._values or place_id not in self._values[key]:
            return default
        return self.get(key, place_id)

    def count(self, key: str, place_id: str) -> int:
        """Read a cell that holds an int."""
        value = self.get(key, place_id)
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{key}[{place_id}] is not an int: {value!r}")
        return value

    def num(self, key: str, place_id: str) -> float:
        """Read a cell that holds a number."""
        value = self.get(key, place_id)
        if isinstance(value, (bool, str)):
            raise TypeError(f"{key}[{place_id}] is not a number: {value!r}")
        return float(value)

    def set(self, key: str, place_id: str, value: Scalar) -> None:
        """Write an existing cell, carrying the scope taint."""
        self._check_write(key)
        cells = self._values[key]
        if place_id not in cells:
            raise KeyError(f"no cell {key}[{place_id}]")
        cells[place_id] = value
        if self._scope_taint is None:
            self._taint[key].pop(place_id, None)
        else:
            self._taint[key][place_id] = self._scope_taint

    def add(self, key: str, place_id: str, amount: float, lo: float | None = None,
            hi: float | None = None) -> None:
        """Read-modify-write: add `amount`, then clamp to [lo, hi] if given."""
        current = self.get(key, place_id)
        if isinstance(current, (bool, str)):
            raise TypeError(f"{key}[{place_id}] is not a number: {current!r}")
        updated = current + amount
        if lo is not None:
            updated = max(updated, lo)
        if hi is not None:
            updated = min(updated, hi)
        if isinstance(current, int) and float(updated).is_integer():
            updated = int(updated)
        self.set(key, place_id, updated)

    def _check_write(self, key: str) -> None:
        if self._unrestricted:
            if key not in self._values:
                raise KeyError(f"player effect targets unknown state key {key!r}")
            return
        if key not in self._writable:
            raise UndeclaredAccessError(f"{self.owner} writes undeclared key {key!r}")
