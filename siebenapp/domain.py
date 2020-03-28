# pylint: disable=too-few-public-methods
import collections
from enum import IntEnum
from typing import Dict, Any


class EdgeType(IntEnum):
    BLOCKER = 1
    PARENT = 2


class Edge(collections.namedtuple("Edge", "source target type")):
    __slots__ = ()


class Command:
    pass


class Graph:
    """Base interface definition"""

    def accept(self, command: Command) -> None:
        """React on the given command"""
        raise NotImplementedError

    def select(self, goal_id: int) -> None:
        """Select a goal by its id whether it exist. Do nothing in other case"""
        raise NotImplementedError

    def insert(self, name: str) -> None:
        """Add an intermediate goal between two selected goals"""
        raise NotImplementedError

    def rename(self, new_name: str, goal_id: int = 0) -> None:
        """Change a name of the given goal"""
        raise NotImplementedError

    def q(self, keys: str = "name") -> Dict[int, Any]:
        """Run search query against goaltree state"""
        raise NotImplementedError


# == Command implementations ==

# === Graph layer ===


class Add(Command):
    """Add a new goal to the existing tree"""

    def __init__(
        self, name: str, add_to: int = 0, edge_type: EdgeType = EdgeType.PARENT
    ):
        self.name = name
        self.add_to = add_to
        self.edge_type = edge_type


class HoldSelect(Command):
    """Saves current selection into the "previous selection" state"""


class ToggleClose(Command):
    """Close an open selected goal. Re-open a closed selected goal"""


class ToggleLink(Command):
    """Create or remove a link between two given goals, if possible"""

    def __init__(
        self, lower: int = 0, upper: int = 0, edge_type: EdgeType = EdgeType.BLOCKER
    ):
        self.lower = lower
        self.upper = upper
        self.edge_type = edge_type


class Delete(Command):
    """Remove given or selected goal whether it exists. Do nothing in other case"""

    def __init__(self, goal_id: int = 0):
        self.goal_id = goal_id
