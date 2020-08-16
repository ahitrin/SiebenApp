# pylint: disable=too-few-public-methods
from collections import deque
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Any


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

    def __init__(self):
        self.goaltree: Graph = self

    def accept(self, command: Command) -> None:
        """React on the given command"""
        raise NotImplementedError

    def accept_all(self, *commands: Command) -> None:
        """React on the command chain"""
        for command in commands:
            self.accept(command)

    def settings(self, key: str) -> int:  # pylint: disable=unused-argument,no-self-use
        """Returns given inner value by the key"""
        return Graph.NO_VALUE

    def events(self) -> deque:
        """Returns queue of applied actions.
        Note: this queue is modifiable -- you may push new events into it. But this
        behavior may be changed in future."""
        raise NotImplementedError

    def q(self, keys: str = "name") -> Dict[int, Any]:
        """Run search query against content"""
        raise NotImplementedError

    def verify(self) -> bool:  # pylint: disable=no-self-use
        """Check all inner data for correctness"""
        return False


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

    def __str__(self):
        return f"Add['{self.name}', {self.add_to}, {self.edge_type.name}]"


class Select(Command):
    """Select a goal by its id whether it exist. Do nothing in other case"""

    def __init__(self, goal_id: int):
        self.goal_id = goal_id

    def __str__(self):
        return f"Select[{self.goal_id}]"


class Insert(Command):
    """Add an intermediate goal between two selected goals"""

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f"Insert['{self.name}']"


class HoldSelect(Command):
    """Saves current selection into the "previous selection" state"""

    def __str__(self):
        return "HoldSelect[]"


class Rename(Command):
    """Change a name of the given goal"""

    def __init__(self, new_name: str, goal_id: int = 0):
        self.new_name = new_name
        self.goal_id = goal_id

    def __str__(self):
        return f"Rename['{self.new_name}', {self.goal_id}]"


class ToggleClose(Command):
    """Close an open selected goal. Re-open a closed selected goal"""

    def __str__(self):
        return "ToggleClose[]"


class ToggleLink(Command):
    """Create or remove a link between two given goals, if possible"""

    def __init__(
        self, lower: int = 0, upper: int = 0, edge_type: EdgeType = EdgeType.BLOCKER
    ):
        self.lower = lower
        self.upper = upper
        self.edge_type = edge_type

    def __str__(self):
        return f"ToggleLink[{self.lower}, {self.upper}, {self.edge_type.name}]"


class Delete(Command):
    """Remove given or selected goal whether it exists. Do nothing in other case"""

    def __init__(self, goal_id: int = 0):
        self.goal_id = goal_id

    def __str__(self):
        return f"Delete[{self.goal_id}]"


# === Zoom layer ===
class ToggleZoom(Command):
    """Hide or show all goals blocked by the current one"""

    def __str__(self):
        return "ToggleZoom[]"


# === Enumeration layer ===
class NextView(Command):
    """Switch between different view modes in a loop"""

    def __str__(self):
        return "NextView[]"
