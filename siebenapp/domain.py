# pylint: disable=too-few-public-methods
import collections
from enum import IntEnum
from typing import Dict, Any


class EdgeType(IntEnum):
    BLOCKER = 1
    PARENT = 2


class Edge(collections.namedtuple("Edge", "source target type")):
    __slots__ = ()


class Graph:
    """Base interface definition"""

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

    def q(self, keys: str = "name") -> Dict[int, Any]:
        """Run search query against goaltree state"""
        raise NotImplementedError
