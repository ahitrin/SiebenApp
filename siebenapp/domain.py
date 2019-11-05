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

    def q(self, keys: str = "name") -> Dict[int, Any]:
        """Run search query against goaltree state"""
        raise NotImplementedError
