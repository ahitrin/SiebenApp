from dataclasses import dataclass
from typing import Dict, Any, Set, List, Tuple

from siebenapp.domain import Command, Graph, with_key, EdgeType, RenderResult, GoalId


@dataclass(frozen=True)
class ToggleOpenView(Command):
    """Switch between "only open goals" and "all goals" views"""


class OpenView(Graph):
    """Non-persistent view layer that allows to switch
    between only-open (plus selected) and all goals"""

    def __init__(self, goaltree: Graph):
        super().__init__(goaltree)
        self._open: bool = True

    def accept_ToggleOpenView(self, command: ToggleOpenView):
        self._open = not self._open

    def settings(self, key: str) -> Any:
        if key == "filter_open":
            return self._open
        return self.goaltree.settings(key)

    def reconfigure_from(self, origin: "Graph") -> None:
        super().reconfigure_from(origin)
        if not origin.settings("filter_open"):
            self.accept(ToggleOpenView())

    def _is_visible(self, goal_id: int, attrs) -> bool:
        if self._open:
            # Here we know something about other layers (Zoom). I do not like it
            return attrs["open"] or goal_id in self.selections() or goal_id in {1, -1}
        return True

    @with_key("open")
    def q(self, keys: str = "name") -> RenderResult:
        goals = self.goaltree.q(keys).slice(keys)
        result: Dict[int, Any] = {
            k: {} for k, v in goals.items() if self._is_visible(k, v)
        }
        # goals without parents
        not_linked: Set[int] = set(g for g in result.keys() if g > 1)
        for goal_id in result:
            val = goals[goal_id]
            result[goal_id] = {k: v for k, v in val.items() if k != "edge"}
            if "edge" in keys:
                filtered_edges: List[Tuple[int, EdgeType]] = []
                for edge in val["edge"]:
                    if edge[0] in result:
                        filtered_edges.append(edge)
                        if edge[0] > 1:
                            not_linked.discard(edge[0])
                result[goal_id]["edge"] = filtered_edges
        if "edge" in keys:
            root_goals: Set[int] = set(result.keys()).intersection({1, -1})
            if root_goals:
                root_goal: int = root_goals.pop()
                for missing_goal in not_linked:
                    result[root_goal]["edge"].append((missing_goal, EdgeType.BLOCKER))
        repacked: Dict[GoalId, Any] = {k: v for k, v in result.items()}
        return RenderResult(repacked, {})
