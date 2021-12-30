from collections import deque
from dataclasses import dataclass
from enum import IntEnum
from functools import wraps
from typing import Dict, Any, Set


class EdgeType(IntEnum):
    BLOCKER = 1
    PARENT = 2


@dataclass(frozen=True)
class Edge:
    source: int
    target: int
    type: EdgeType


class Command:
    pass


class Graph:
    """Base interface definition"""

    NO_VALUE = -1

    def __init__(self, goaltree=None):
        self.goaltree: Graph = goaltree

    def __getattr__(self, item):
        """When method is not found, ask nested goaltree for it"""
        if self.goaltree != self:
            return getattr(self.goaltree, item)
        return None

    def accept(self, command: Command) -> None:
        """React on the given command"""
        method_name = "accept_" + command.__class__.__name__
        if method := getattr(self, method_name):
            method(command)
        elif parent := self.goaltree:
            parent.accept(command)
        else:
            raise NotImplementedError(f"Cannot find method {method_name}")

    def accept_all(self, *commands: Command) -> None:
        """React on the command chain"""
        for command in commands:
            self.accept(command)

    def settings(self, key: str) -> Any:
        """Returns given inner value by the key"""
        if self.goaltree is not None:
            return self.goaltree.settings(key)
        return Graph.NO_VALUE

    def reconfigure_from(self, origin: "Graph") -> None:
        """Synchronize *non-persistent* settings from the given origin"""
        if self.goaltree:
            self.goaltree.reconfigure_from(origin)

    def selections(self) -> Set[int]:
        """Return ids of special 'selection' goals"""
        # Doesn't look clean nevertheless
        return set(
            k
            for k in [
                self.settings("selection"),
                self.settings("previous_selection"),
            ]
            if k is not None
        )

    def events(self) -> deque:
        """Returns queue of applied actions.
        Note: this queue is modifiable -- you may push new events into it. But this
        behavior may be changed in future."""
        if self.goaltree is not None:
            return self.goaltree.events()
        raise NotImplementedError

    def q(self, keys: str = "name") -> Dict[int, Any]:
        """Run search query against content"""
        raise NotImplementedError

    def verify(self) -> bool:
        """Check all inner data for correctness"""
        if self.goaltree is not None:
            return self.goaltree.verify()
        return False


def with_key(key):
    """Wraps around Graph.q, adding given key to the request"""

    def inner(q):
        @wraps(q)
        def wrapper(self, keys="name"):
            if no_key := key not in keys:
                keys = ",".join([keys, key])
            result = q(self, keys)
            if no_key:
                for v in result.values():
                    v.pop(key)
            return result

        return wrapper

    return inner


# == Command implementations ==

# === Graph layer ===


@dataclass(frozen=True)
class Add(Command):
    """Add a new goal to the existing tree"""

    name: str
    add_to: int = 0
    edge_type: EdgeType = EdgeType.PARENT


@dataclass(frozen=True)
class Select(Command):
    """Select a goal by its id whether it exist. Do nothing in other case"""

    goal_id: int


@dataclass(frozen=True)
class Insert(Command):
    """Add an intermediate goal between two selected goals"""

    name: str


@dataclass(frozen=True)
class HoldSelect(Command):
    """Saves current selection into the "previous selection" state"""


@dataclass(frozen=True)
class Rename(Command):
    """Change a name of the given goal"""

    new_name: str
    goal_id: int = 0


@dataclass(frozen=True)
class ToggleClose(Command):
    """Close an open selected goal. Re-open a closed selected goal"""

    root: int = 0


@dataclass(frozen=True)
class ToggleLink(Command):
    """Create or remove a link between two given goals, if possible"""

    lower: int = 0
    upper: int = 0
    edge_type: EdgeType = EdgeType.BLOCKER


@dataclass(frozen=True)
class Delete(Command):
    """Remove given or selected goal whether it exists. Do nothing in other case"""

    goal_id: int = 0
