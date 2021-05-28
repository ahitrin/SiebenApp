# coding: utf-8
import collections
from typing import Callable, Dict, Optional, List, Set, Any, Tuple

from siebenapp.domain import (
    Graph,
    EdgeType,
    Edge,
    Command,
    HoldSelect,
    ToggleClose,
    Delete,
    ToggleLink,
    Add,
    Select,
    Insert,
    Rename,
)

GoalsData = List[Tuple[int, Optional[str], bool]]
EdgesData = List[Tuple[int, int, EdgeType]]
OptionsData = List[Tuple[str, int]]


class Goals(Graph):
    ROOT_ID = 1

    def __init__(self, name: str, message_fn: Callable[[str], None] = None) -> None:
        super().__init__()
        self.goals: Dict[int, Optional[str]] = {}
        self.edges: Dict[Tuple[int, int], EdgeType] = {}
        self.closed: Set[int] = set()
        self.selection = Goals.ROOT_ID
        self.previous_selection = Goals.ROOT_ID
        self._events: collections.deque = collections.deque()
        self.message_fn = message_fn
        self._add_no_link(name)

    def _msg(self, message: str) -> None:
        if self.message_fn:
            self.message_fn(message)

    def _has_link(self, lower: int, upper: int) -> bool:
        return (lower, upper) in self.edges

    def _forward_edges(self, goal: int) -> List[Edge]:
        return [Edge(goal, k[1], v) for k, v in self.edges.items() if k[0] == goal]

    def _back_edges(self, goal: int) -> List[Edge]:
        return [Edge(k[0], goal, v) for k, v in self.edges.items() if k[1] == goal]

    def _parent(self, goal: int) -> int:
        parents = {e for e in self._back_edges(goal) if e.type == EdgeType.PARENT}
        return parents.pop().source if parents else Goals.ROOT_ID

    def accept(self, command: Command) -> None:
        if isinstance(command, Add):
            self._add(command)
        elif isinstance(command, Insert):
            self._insert(command)
        elif isinstance(command, Select):
            self._select(command)
        elif isinstance(command, HoldSelect):
            self._hold_select()
        elif isinstance(command, Rename):
            self._rename(command)
        elif isinstance(command, ToggleClose):
            self._toggle_close(command)
        elif isinstance(command, ToggleLink):
            self._toggle_link(command)
        elif isinstance(command, Delete):
            self._delete(command)

    def settings(self, key: str) -> int:
        return {
            "selection": self.selection,
            "previous_selection": self.previous_selection,
        }.get(key, 0)

    def events(self) -> collections.deque:
        return self._events

    def _add(self, command: Add) -> bool:
        add_to = command.add_to if command.add_to != 0 else self.selection
        if add_to in self.closed:
            self._msg("A new subgoal cannot be added to the closed one")
            return False
        next_id = self._add_no_link(command.name)
        self._toggle_link(ToggleLink(add_to, next_id, command.edge_type))
        return True

    def _add_no_link(self, name: str) -> int:
        next_id = max(list(self.goals.keys()) + [0]) + 1
        self.goals[next_id] = name
        self._events.append(("add", next_id, name, True))
        return next_id

    def _select(self, command: Select):
        goal_id = command.goal_id
        if goal_id in self.goals and self.goals[goal_id] is not None:
            self.selection = goal_id
            self._events.append(("select", goal_id))

    def _hold_select(self):
        self.previous_selection = self.selection
        self._events.append(("hold_select", self.selection))

    def q(self, keys: str = "name") -> Dict[int, Any]:
        def sel(x: int) -> Optional[str]:
            if x == self.selection:
                return "select"
            if x == self.previous_selection:
                return "prev"
            return None

        keys_list = keys.split(",")
        result: Dict[int, Any] = dict()
        for key, name in ((k, n) for k, n in self.goals.items() if n is not None):
            value = {
                "edge": sorted([(e.target, e.type) for e in self._forward_edges(key)]),
                "name": name,
                "open": key not in self.closed,
                "select": sel(key),
                "switchable": self._switchable(key),
            }
            result[key] = {k: v for k, v in value.items() if k in keys_list}
        return result

    def _switchable(self, key: int) -> bool:
        if key in self.closed:
            has_parents = False
            for k in self.edges.keys():
                if k[1] == key:
                    has_parents = True
                    if k[0] not in self.closed:
                        return True
            return not has_parents
        return all(x.target in self.closed for x in self._forward_edges(key))

    def _insert(self, command: Insert):
        if (lower := self.previous_selection) == (upper := self.selection):
            self._msg("A new goal can be inserted only between two different goals")
            return
        edge_type = self.edges.get((lower, upper), EdgeType.BLOCKER)
        if self._add(Add(command.name, lower, edge_type)):
            key = len(self.goals)
            self._toggle_link(ToggleLink(key, upper, edge_type))
            if self._has_link(lower, upper):
                self._toggle_link(ToggleLink(lower, upper))

    def _rename(self, command: Rename):
        goal_id = command.goal_id if command.goal_id != 0 else self.selection
        self.goals[goal_id] = command.new_name
        self._events.append(("rename", command.new_name, goal_id))

    def _toggle_close(self, command: ToggleClose) -> None:
        if self.selection in self.closed:
            if self._may_be_reopened():
                self.closed.remove(self.selection)
                self._events.append(("toggle_close", True, self.selection))
            else:
                self._msg("This goal can't be reopened because other subgoals block it")
        else:
            if self._may_be_closed():
                self.closed.add(self.selection)
                self._events.append(("toggle_close", False, self.selection))
                self._select(Select(self._first_open_and_switchable(command.root)))
                self.accept(HoldSelect())
            else:
                self._msg("This goal can't be closed because it have open subgoals")

    def _may_be_closed(self) -> bool:
        return all(g.target in self.closed for g in self._forward_edges(self.selection))

    def _may_be_reopened(self) -> bool:
        return all(
            k[0] not in self.closed
            for k, v in self.edges.items()
            if k[1] == self.selection
        )

    def _first_open_and_switchable(self, root: int) -> int:
        root = max(root, Goals.ROOT_ID)
        front = [root]
        candidates: List[int] = []
        while front:
            next_goal = front.pop()
            subgoals = [
                e.target
                for e in self._forward_edges(next_goal)
                if e.target not in self.closed and e.type == EdgeType.PARENT
            ]
            front.extend(subgoals)
            candidates.extend(g for g in subgoals if self._switchable(g))
        return min(candidates) if candidates else root

    def _delete(self, command: Delete) -> None:
        goal_id = command.goal_id if command.goal_id != 0 else self.selection
        if goal_id == Goals.ROOT_ID:
            self._msg("Root goal can't be deleted")
            return
        parent = self._parent(goal_id)
        self._delete_subtree(goal_id)
        self._select(Select(parent))
        self.accept(HoldSelect())

    def _delete_subtree(self, goal_id: int) -> None:
        parent = self._parent(goal_id)
        self.goals[goal_id] = None
        self.closed.add(goal_id)
        forward_edges = self._forward_edges(goal_id)
        next_to_remove = {e for e in forward_edges if e.type == EdgeType.PARENT}
        blockers = {e for e in forward_edges if e.type == EdgeType.BLOCKER}
        self.edges = {k: v for k, v in self.edges.items() if goal_id not in k}
        for old_blocker in blockers:
            if not self._back_edges(old_blocker.target):
                self._create_new_link(parent, old_blocker.target, EdgeType.BLOCKER)
        for next_goal in next_to_remove:
            if not self._back_edges(next_goal.target):
                self._delete_subtree(next_goal.target)
        self._events.append(("delete", goal_id))

    def _toggle_link(self, command: ToggleLink):
        lower = self.previous_selection if command.lower == 0 else command.lower
        upper = self.selection if command.upper == 0 else command.upper
        if lower == upper:
            self._msg("Goal can't be linked to itself")
            return
        if self._has_link(lower, upper):
            if (current_edge_type := self.edges[(lower, upper)]) != command.edge_type:
                self._replace_link(lower, upper, command.edge_type)
                self._transform_old_parents_into_blocked(lower, upper)
            else:
                self._remove_existing_link(lower, upper, current_edge_type)
        else:
            self._create_new_link(lower, upper, command.edge_type)

    def _replace_link(self, lower: int, upper: int, edge_type: EdgeType) -> None:
        old_edge_type = self.edges[(lower, upper)]
        self.edges[(lower, upper)] = edge_type
        self._events.append(("link", lower, upper, edge_type))
        self._events.append(("unlink", lower, upper, old_edge_type))

    def _remove_existing_link(
        self, lower: int, upper: int, edge_type: int = None
    ) -> None:
        if len(self._back_edges(upper)) > 1:
            self.edges.pop((lower, upper))
            self._events.append(("unlink", lower, upper, edge_type))
        else:
            self._msg("Can't remove the last link")

    def _create_new_link(self, lower: int, upper: int, edge_type: EdgeType) -> None:
        if lower in self.closed and upper not in self.closed:
            self._msg("An open goal can't block already closed one")
            return
        if self._has_circular_dependency(lower, upper):
            self._msg("Circular dependencies between goals are not allowed")
            return
        if edge_type == EdgeType.PARENT:
            self._transform_old_parents_into_blocked(lower, upper)
        self.edges[lower, upper] = edge_type
        self._events.append(("link", lower, upper, edge_type))

    def _transform_old_parents_into_blocked(self, lower, upper):
        old_parents = [
            e.source
            for e in self._back_edges(upper)
            if e.type == EdgeType.PARENT and e.source != lower
        ]
        for p in old_parents:
            self._replace_link(p, upper, EdgeType.BLOCKER)

    def _has_circular_dependency(self, lower: int, upper: int) -> bool:
        front: Set[int] = {upper}
        visited: Set[int] = set()
        total: Set[int] = set()
        while front:
            g = front.pop()
            visited.add(g)
            for e in self._forward_edges(g):
                total.add(e.target)
                if e not in visited:
                    front.add(e.target)
        return lower in total

    def verify(self) -> bool:
        assert all(
            g.target in self.closed for p in self.closed for g in self._forward_edges(p)
        ), "Open goals could not be blocked by closed ones"

        queue: List[int] = [Goals.ROOT_ID]
        visited: Set[int] = set()
        while queue:
            goal = queue.pop()
            queue.extend(
                g.target
                for g in self._forward_edges(goal)
                if g.target not in visited and self.goals[g.target] is not None
            )
            visited.add(goal)
        assert visited == {
            x for x in self.goals if self.goals[x] is not None
        }, "All subgoals must be accessible from the root goal"

        deleted_nodes = [g for g, v in self.goals.items() if v is None]
        assert all(
            not self._forward_edges(n) for n in deleted_nodes
        ), "Deleted goals must have no dependencies"

        parent_edges = [k for k, v in self.edges.items() if v == EdgeType.PARENT]
        edges_with_parent = {child for parent, child in parent_edges}
        assert len(parent_edges) == len(
            edges_with_parent
        ), "Each goal must have at most 1 parent"

        return True

    @staticmethod
    def build(goals, edges, settings, message_fn=None):
        # type: (GoalsData, EdgesData, OptionsData, Callable[[str], None]) -> Goals
        result = Goals("", message_fn)
        result._events.clear()  # pylint: disable=protected-access
        goals_dict = {g[0]: g[1] for g in goals}
        result.goals = {
            i: goals_dict.get(i) for i in range(1, max(goals_dict.keys()) + 1)
        }

        result.closed = {g[0] for g in goals if not g[2]}.union(
            {k for k, v in result.goals.items() if v is None}
        )

        for parent, child, link_type in edges:
            result.edges[parent, child] = EdgeType(link_type)
        selection_dict = dict(settings)
        result.selection = selection_dict.get("selection", result.selection)
        result.previous_selection = selection_dict.get(
            "previous_selection", result.previous_selection
        )
        result.verify()
        return result

    @staticmethod
    def export(goals):
        # type: (Goals) -> Tuple[GoalsData, EdgesData, OptionsData]
        nodes = [
            (g_id, g_name, g_id not in goals.closed)
            for g_id, g_name in goals.goals.items()
        ]

        edges = [(k[0], k[1], v) for k, v in goals.edges.items()]
        settings = [
            ("selection", goals.selection),
            ("previous_selection", goals.previous_selection),
        ]
        return nodes, edges, settings
