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

    def add(
        self, name: str, add_to: int = 0, edge_type: EdgeType = EdgeType.PARENT
    ) -> bool:
        """Add a new goal to the existing tree"""
        raise NotImplementedError

    def select(self, goal_id: int) -> None:
        """Select a goal by its id whether it exist. Do nothing in other case"""
        raise NotImplementedError

    def hold_select(self) -> None:
        """Saves current selection into the "previous selection" state"""
        raise NotImplementedError

    def insert(self, name: str) -> None:
        """Add an intermediate goal between two selected goals"""
        raise NotImplementedError

    def rename(self, new_name: str, goal_id: int = 0) -> None:
        """Change a name of the given goal"""
        raise NotImplementedError

    def toggle_link(
        self, lower: int = 0, upper: int = 0, edge_type: EdgeType = EdgeType.BLOCKER
    ) -> None:
        """Create or remove a link between two given goals, if possible"""
        raise NotImplementedError

    def toggle_close(self) -> None:
        """Close an open selected goal. Re-open a closed selected goal"""
        raise NotImplementedError

    def delete(self, goal_id: int = 0) -> None:
        """Remove given or selected goal whether it exists. Do nothiung in other case"""
        raise NotImplementedError

    def q(self, keys: str = "name") -> Dict[int, Any]:
        """Run search query against goaltree state"""
        raise NotImplementedError
