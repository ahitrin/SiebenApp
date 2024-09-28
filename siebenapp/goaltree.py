from collections import deque, defaultdict
from collections.abc import Callable
from dataclasses import replace
from typing import Any

from siebenapp.domain import (
    Graph,
    EdgeType,
    Edge,
    HoldSelect,
    ToggleClose,
    Delete,
    ToggleLink,
    Add,
    Select,
    Insert,
    Rename,
    GoalId,
    RenderResult,
    RenderRow,
    Command,
)

GoalsData = list[tuple[int, str | None, bool]]
EdgesData = list[tuple[int, int, EdgeType]]
OptionsData = list[tuple[str, int]]


OPTION_SELECT = "select"
OPTION_PREV_SELECT = "prev_select"


class Selectable(Graph):
    def __init__(self, goals: Graph, data: OptionsData | None = None):
        super().__init__(goals)
        selection_dict: dict[str, int] = dict(data or [])
        original_root = int(list(goals.q().roots)[0])
        self.selection: int = selection_dict.get("selection", original_root)
        self.previous_selection: int = selection_dict.get(
            "previous_selection", original_root
        )

    def accept_Select(self, command: Select):
        goal_id: int = command.goal_id
        if self.goaltree.goals.get(goal_id, None) is not None:
            self.selection = goal_id
            self._events.append(("select", goal_id))
        self.goaltree.accept(command)

    def accept_HoldSelect(self, command: HoldSelect):
        self.previous_selection = self.selection
        self._events.append(("hold_select", self.selection))

    def accept_Rename(self, command: Rename) -> None:
        target = command.goal_id or self.selection
        self.goaltree.accept(replace(command, goal_id=target))

    def accept_ToggleClose(self, command: ToggleClose) -> None:
        target = command.goal_id or self.selection
        if self._command_approved(replace(command, goal_id=target)):
            # Change selection only when goal was successfully closed
            if target in self.goaltree.closed:
                if self.previous_selection != target:
                    self.accept_Select(Select(self.previous_selection))
                else:
                    next_selection = self._first_open_and_switchable(command.root)
                    self.accept_Select(Select(next_selection))
                    self.accept_HoldSelect(HoldSelect())

    def accept_ToggleLink(self, command: ToggleLink) -> None:
        lower = command.lower or self.previous_selection
        upper = command.upper or self.selection
        self.goaltree.accept(replace(command, lower=lower, upper=upper))

    def accept_Insert(self, command: Insert) -> None:
        lower = command.lower or self.previous_selection
        upper = command.upper or self.selection
        self.goaltree.accept(replace(command, lower=lower, upper=upper))

    def accept_Add(self, command: Add) -> None:
        target = command.add_to or self.selection
        self.goaltree.accept(replace(command, add_to=target))

    def accept_Delete(self, command: Delete) -> None:
        target = command.goal_id or self.selection
        parent: int = self.goaltree._parent(target)
        if self._command_approved(replace(command, goal_id=target)):
            self.accept_Select(Select(parent))
            self.accept_HoldSelect(HoldSelect())

    def _command_approved(self, command: Command) -> bool:
        events_before: int = len(self.events())
        self.goaltree.accept(command)
        events_after: int = len(self.events())
        return events_after > events_before

    def q(self) -> RenderResult:
        rr = self.goaltree.q()
        self.selection = self.goaltree.selection
        return replace(
            rr,
            global_opts=rr.global_opts
            | {
                OPTION_SELECT: self.selection,
                OPTION_PREV_SELECT: self.previous_selection,
            },
        )

    def settings(self, key: str) -> Any:
        selection_settings = {
            "selection": self.selection,
            "previous_selection": self.previous_selection,
        }
        if key in selection_settings:
            return selection_settings.get(key)

        return self.goaltree.settings(key)

    @staticmethod
    def export(goals: "Selectable") -> OptionsData:
        return [
            ("selection", goals.selection),
            ("previous_selection", goals.previous_selection),
        ]


class Goals(Graph):
    ROOT_ID = 1

    def __init__(
        self, name: str, message_fn: Callable[[str], None] | None = None
    ) -> None:
        super().__init__()
        self.goals: dict[int, str | None] = {}
        self.edges: dict[tuple[int, int], EdgeType] = {}
        self.edges_forward: dict[int, dict[int, EdgeType]] = defaultdict(
            lambda: defaultdict(lambda: EdgeType.BLOCKER)
        )
        self.edges_backward: dict[int, dict[int, EdgeType]] = defaultdict(
            lambda: defaultdict(lambda: EdgeType.BLOCKER)
        )
        self.closed: set[int] = set()
        self.selection: int = Goals.ROOT_ID
        self.previous_selection: int = Goals.ROOT_ID
        self._events: deque = deque()
        self.message_fn: Callable[[str], None] | None = message_fn
        self._add_no_link(name)

    def error(self, message: str) -> None:
        if self.message_fn:
            self.message_fn(message)

    def _has_link(self, lower: int, upper: int) -> bool:
        return upper in self.edges_forward[lower]

    def _forward_edges(self, goal: int) -> list[Edge]:
        return [Edge(goal, k, v) for k, v in self.edges_forward[goal].items()]

    def _back_edges(self, goal: int) -> list[Edge]:
        return [Edge(k, goal, v) for k, v in self.edges_backward[goal].items()]

    def _strict_parent(self, goal: int) -> int | None:
        parents: set[Edge] = {
            e for e in self._back_edges(goal) if e.type == EdgeType.PARENT
        }
        return parents.pop().source if parents else None

    def _parent(self, goal: int) -> int:
        return self._strict_parent(goal) or Goals.ROOT_ID

    def settings(self, key: str) -> Any:
        return Graph.NO_VALUE

    def events(self) -> deque:
        return self._events

    def accept_Add(self, command: Add) -> bool:
        add_to: int = command.add_to
        if add_to in self.closed:
            self.error("A new subgoal cannot be added to the closed one")
            return False
        next_id: int = self._add_no_link(command.name)
        self.accept_ToggleLink(ToggleLink(add_to, next_id, command.edge_type))
        return True

    def _add_no_link(self, name: str) -> int:
        next_id: int = max(list(self.goals.keys()) + [0]) + 1
        self.goals[next_id] = name
        self._events.append(("add", next_id, name, True))
        return next_id

    def accept_Select(self, command: Select):
        goal_id: int = command.goal_id
        if goal_id in self.goals and self.goals[goal_id] is not None:
            self.selection = goal_id

    def q(self) -> RenderResult:
        rows: list[RenderRow] = []
        for key, name in ((k, n) for k, n in self.goals.items() if n is not None):
            edges: list[tuple[GoalId, EdgeType]] = sorted(
                [(e.target, e.type) for e in self._forward_edges(key)]
            )
            rows.append(
                RenderRow(
                    key,
                    key,
                    name,
                    key not in self.closed,
                    self._switchable(key),
                    edges,
                )
            )
        return RenderResult(
            rows,
            roots={Goals.ROOT_ID},
        )

    def _switchable(self, key: int) -> bool:
        if key in self.closed:
            if back_edges := self._back_edges(key):
                return all(e.source not in self.closed for e in back_edges)
            return True
        direct_blockers = [
            e for e in self._forward_edges(key) if e.type != EdgeType.RELATION
        ]
        no_direct_blockers_or_subgoals = all(
            x.target in self.closed for x in direct_blockers
        )
        return no_direct_blockers_or_subgoals and not self._blocked_by_parent(key)

    def _blocked_by_parent(self, goal_id: int) -> bool:
        while goal_id != Goals.ROOT_ID:
            parent = self._strict_parent(goal_id)
            if not parent:
                break
            parent_blockers = [
                e
                for e in self._forward_edges(parent)
                if e.type == EdgeType.BLOCKER
                and e.target not in self.closed
                and not self._is_direct_subgoal(parent, e.target)
            ]
            if parent_blockers:
                return True

            goal_id = parent
        return False

    def _is_direct_subgoal(self, parent: int, goal_id: int) -> bool:
        while goal_id != Goals.ROOT_ID:
            goal_parent = self._strict_parent(goal_id)
            if not goal_parent:
                return False
            if goal_parent == parent:
                return True
            goal_id = goal_parent
        return False

    def accept_Insert(self, command: Insert) -> None:
        if (lower := command.lower) == (upper := command.upper):
            self.error("A new goal can be inserted only between two different goals")
            return
        edge_type: EdgeType = self.edges_forward[lower].get(upper, EdgeType.BLOCKER)
        if self.accept_Add(Add(command.name, lower, edge_type)):
            key: int = len(self.goals)
            self._create_new_link(key, upper, edge_type)
            if self._has_link(lower, upper):
                self.accept_ToggleLink(ToggleLink(lower, upper, edge_type))

    def accept_Rename(self, command: Rename) -> None:
        self.goals[command.goal_id] = command.new_name
        self._events.append(("rename", command.new_name, command.goal_id))

    def accept_ToggleClose(self, command: ToggleClose) -> None:
        target = command.goal_id
        is_closed = target in self.closed
        error_messages = {
            True: "This goal can't be reopened because other subgoals block it",
            False: "This goal can't be closed because it have open subgoals",
        }
        if not self._switchable(target):
            self.error(error_messages[is_closed])
            return

        if is_closed:
            self.closed.remove(target)
            self._events.append(("toggle_close", True, target))
        else:
            self.closed.add(target)
            self._events.append(("toggle_close", False, target))

    def _first_open_and_switchable(self, root: int) -> int:
        actual_root: int = max(root, Goals.ROOT_ID)
        front: list[int] = [actual_root]
        candidates: list[int] = []
        while front:
            next_goal: int = front.pop()
            subgoals: list[int] = [
                e.target
                for e in self._forward_edges(next_goal)
                if e.target not in self.closed and e.type == EdgeType.PARENT
            ]
            front.extend(subgoals)
            candidates.extend(g for g in subgoals if self._switchable(g))
        return min(candidates) if candidates else actual_root

    def accept_Delete(self, command: Delete) -> None:
        if (goal_id := command.goal_id) == Goals.ROOT_ID:
            self.error("Root goal can't be deleted")
            return
        self._delete_subtree(goal_id)

    def _delete_subtree(self, goal_id: int) -> None:
        parent: int = self._parent(goal_id)
        self.goals[goal_id] = None
        self.closed.add(goal_id)
        forward_edges: list[Edge] = self._forward_edges(goal_id)
        next_to_remove: set[Edge] = {
            e for e in forward_edges if e.type == EdgeType.PARENT
        }
        dangling_goals: set[Edge] = {
            e for e in forward_edges if e.type != EdgeType.PARENT
        }
        for back_edge in self._back_edges(goal_id):
            self.edges_forward[back_edge.source].pop(goal_id)
        self.edges_forward[goal_id].clear()
        for forward_edge in forward_edges:
            self.edges_backward[forward_edge.target].pop(goal_id)
        self.edges_backward[goal_id].clear()
        self.edges = {k: v for k, v in self.edges.items() if goal_id not in k}
        for g in dangling_goals:
            if not self._back_edges(g.target):
                self._create_new_link(parent, g.target, g.type)
        for next_goal in next_to_remove:
            if not self._back_edges(next_goal.target):
                self._delete_subtree(next_goal.target)
        self._events.append(("delete", goal_id))

    def accept_ToggleLink(self, command: ToggleLink) -> None:
        if (lower := command.lower) == (upper := command.upper):
            self.error("Goal can't be linked to itself")
            return
        if lower in self.closed and upper not in self.closed:
            self.error("Cannot add a blocking relation to the closed goal")
            return
        if self._has_link(lower, upper):
            self._replace_or_remove_existing_link(command, lower, upper)
        else:
            self._create_new_link(lower, upper, command.edge_type)
            if command.edge_type == EdgeType.PARENT:
                self._transform_old_parents_into_relation(lower, upper)

    def _replace_or_remove_existing_link(
        self, command: ToggleLink, lower: int, upper: int
    ) -> None:
        if (current_edge_type := self.edges_forward[lower][upper]) != command.edge_type:
            self._replace_link(lower, upper, command.edge_type)
            if command.edge_type == EdgeType.PARENT:
                self._transform_old_parents_into_relation(lower, upper)
        else:
            self._remove_existing_link(lower, upper, current_edge_type)

    def _remove_existing_link(
        self, lower: int, upper: int, edge_type: int | None = None
    ) -> None:
        if len(self._back_edges(upper)) > 1:
            self.edges.pop((lower, upper))
            self.edges_forward[lower].pop(upper)
            self.edges_backward[upper].pop(lower)
            self._events.append(("unlink", lower, upper, edge_type))
        else:
            self.error("Can't remove the last link")

    def _create_new_link(self, lower: int, upper: int, edge_type: EdgeType) -> None:
        if (
            lower in self.closed
            and upper not in self.closed
            and edge_type != EdgeType.RELATION
        ):
            self.error("An open goal can't block already closed one")
            return
        if self._lower_is_reachable_from_upper(lower, upper):
            self.error("Circular dependencies between goals are not allowed")
            return
        goal_id = upper
        while parent := self._strict_parent(goal_id):
            if self.edges.get((parent, lower)) == EdgeType.BLOCKER:
                self.error("A goal cannot block its own blocker")
                return
            goal_id = parent
        self.edges[lower, upper] = edge_type
        self.edges_forward[lower][upper] = edge_type
        self.edges_backward[upper][lower] = edge_type
        self._events.append(("link", lower, upper, edge_type))

    def _transform_old_parents_into_relation(self, lower: int, upper: int) -> None:
        old_parents: list[int] = [
            e.source
            for e in self._back_edges(upper)
            if e.type == EdgeType.PARENT and e.source != lower
        ]
        for p in old_parents:
            self._replace_link(p, upper, EdgeType.RELATION)

    def _replace_link(self, lower: int, upper: int, edge_type: EdgeType) -> None:
        old_edge_type: EdgeType = self.edges_forward[lower][upper]
        self.edges[(lower, upper)] = edge_type
        self.edges_forward[lower][upper] = edge_type
        self.edges_backward[upper][lower] = edge_type
        self._events.append(("link", lower, upper, edge_type))
        self._events.append(("unlink", lower, upper, old_edge_type))

    def _lower_is_reachable_from_upper(self, lower: int, upper: int) -> bool:
        front: set[int] = {upper}
        visited: set[int] = set()
        total: set[int] = set()
        while front:
            g = front.pop()
            visited.add(g)
            for e in self._forward_edges(g):
                total.add(e.target)
                if e not in visited:
                    front.add(e.target)
        return lower in total

    def verify(self) -> None:
        self._verify_open_goals_are_not_blocked_by_closed_goals()
        self._verify_all_subgoals_are_accessible_from_the_root_goal()
        self._verify_deleted_goals_have_no_dependencies()
        self._verify_forward_and_backward_edges_match_each_other()
        self._verify_at_most_one_parent_for_each_goal()

    def _verify_open_goals_are_not_blocked_by_closed_goals(self) -> None:
        b = all(
            e.target in self.closed
            for p in self.closed
            for e in self._forward_edges(p)
            if e.type != EdgeType.RELATION
        )
        assert b, "Open goals could not be blocked by closed ones"

    def _verify_all_subgoals_are_accessible_from_the_root_goal(self) -> None:
        queue: list[int] = [Goals.ROOT_ID]
        visited: set[int] = set()
        while queue:
            goal: int = queue.pop()
            queue.extend(
                g.target
                for g in self._forward_edges(goal)
                if g.target not in visited and self.goals[g.target] is not None
            )
            visited.add(goal)
        assert visited == {
            x for x in self.goals if self.goals[x] is not None
        }, "All subgoals must be accessible from the root goal"

    def _verify_deleted_goals_have_no_dependencies(self) -> None:
        deleted_nodes: list[int] = [g for g, v in self.goals.items() if v is None]
        assert all(
            not self._forward_edges(n) for n in deleted_nodes
        ), "Deleted goals must have no dependencies"

    def _verify_forward_and_backward_edges_match_each_other(self) -> None:
        fwd_edges: set[tuple[int, int, EdgeType]] = {
            (g1, g2, et) for g1, e in self.edges_forward.items() for g2, et in e.items()
        }
        bwd_edges: set[tuple[int, int, EdgeType]] = {
            (g1, g2, et)
            for g2, e in self.edges_backward.items()
            for g1, et in e.items()
        }
        assert (
            fwd_edges == bwd_edges
        ), "Forward and backward edges must always match each other"

    def _verify_at_most_one_parent_for_each_goal(self) -> None:
        parent_edges: list[tuple[int, int]] = [
            k for k, v in self.edges.items() if v == EdgeType.PARENT
        ]
        edges_with_parent: set[int] = {child for parent, child in parent_edges}
        assert len(parent_edges) == len(
            edges_with_parent
        ), "Each goal must have at most 1 parent"

    @staticmethod
    def build(
        goals: GoalsData,
        edges: EdgesData,
        settings: OptionsData,
        message_fn: Callable[[str], None] | None = None,
    ) -> "Goals":
        result: Goals = Goals("", message_fn)
        result._events.clear()
        goals_dict: dict[int, str | None] = {g[0]: g[1] for g in goals}
        result.goals = {
            i: goals_dict.get(i) for i in range(1, max(goals_dict.keys()) + 1)
        }

        result.closed = {g[0] for g in goals if not g[2]}.union(
            {k for k, v in result.goals.items() if v is None}
        )

        for parent, child, link_type in edges:
            result.edges[parent, child] = EdgeType(link_type)
            result.edges_forward[parent][child] = EdgeType(link_type)
            result.edges_backward[child][parent] = EdgeType(link_type)
        selection_dict: dict[str, int] = dict(settings)
        result.selection = selection_dict.get("selection", result.selection)
        result.previous_selection = selection_dict.get(
            "previous_selection", result.previous_selection
        )
        result.verify()
        return result

    @staticmethod
    def export(goals: "Goals") -> tuple[GoalsData, EdgesData]:
        nodes: GoalsData = [
            (g_id, g_name, g_id not in goals.closed)
            for g_id, g_name in goals.goals.items()
        ]

        edges: EdgesData = [(k[0], k[1], v) for k, v in goals.edges.items()]
        return nodes, edges
