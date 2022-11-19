from collections import deque
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Any, Union, Tuple, List, Optional


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


# GoalId for real nodes is integer: -1, 4, 34, etc
# GoalId for fake nodes (used to build edges) is str: '3_5', '1_1', etc
GoalId = Union[str, int]


def child(goal_id: int) -> Tuple[GoalId, EdgeType]:
    """A more compact way of writing (goal_id, EdgeType.PARENT)"""
    return goal_id, EdgeType.PARENT


def blocker(goal_id: int) -> Tuple[GoalId, EdgeType]:
    """A more compact way of writing (goal_id, EdgeType.BLOCKER)"""
    return goal_id, EdgeType.BLOCKER


@dataclass(frozen=True)
class RenderRow:
    """Strongly typed rendered representation of a single goal."""

    goal_id: GoalId
    raw_id: int
    name: str
    is_open: bool
    is_switchable: bool
    edges: List[Tuple[GoalId, EdgeType]]
    attrs: Dict[str, str] = field(default_factory=lambda: {})


@dataclass
class RenderResult:
    graph: Dict[GoalId, Any]
    edge_opts: Dict[str, Tuple[int, int, int]]
    rows: List[RenderRow]
    select: Tuple[GoalId, GoalId]

    def __init__(
        self,
        graph: Optional[Dict[GoalId, Any]] = None,
        edge_opts: Optional[Dict[str, Tuple[int, int, int]]] = None,
        rows: Optional[List[RenderRow]] = None,
        select: Optional[Tuple[GoalId, GoalId]] = None,
    ):
        self.graph = graph or {}
        self.edge_opts = edge_opts or {}
        self.rows = rows or []
        self.select = select or (0, 0)

    def goals(self):
        return [
            (goal_id, attrs)
            for goal_id, attrs in self.graph.items()
            if isinstance(goal_id, int)
        ]

    def by_id(self, goal_id: GoalId) -> RenderRow:
        result = [r for r in self.rows if r.goal_id == goal_id]
        assert len(result) == 1
        return result[0]


class Graph:
    """Base interface definition"""

    NO_VALUE = "no value"

    def __init__(self, goaltree: Optional["Graph"] = None):
        self.goaltree: Graph = goaltree or self

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
        if self.goaltree != self:
            return self.goaltree.settings(key)
        return Graph.NO_VALUE

    def reconfigure_from(self, origin: "Graph") -> None:
        """Synchronize *non-persistent* settings from the given origin"""
        if self.goaltree != self:
            self.goaltree.reconfigure_from(origin)

    def events(self) -> deque:
        """Returns queue of applied actions.
        Note: this queue is modifiable -- you may push new events into it. But this
        behavior may be changed in future."""
        if self.goaltree != self:
            return self.goaltree.events()
        raise NotImplementedError

    def q(self) -> RenderResult:
        """Run search query against content"""
        raise NotImplementedError

    def error(self, message: str) -> None:
        """Show error message"""
        if self.goaltree != self:
            self.goaltree.error(message)

    def verify(self) -> None:
        """Check all inner data for correctness. Raise exception on violations."""
        if self.goaltree != self:
            return self.goaltree.verify()


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
