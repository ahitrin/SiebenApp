import math
from typing import List, Dict, Tuple, Any, Iterable

from siebenapp.domain import Graph, Select, GoalId, RenderResult


class BidirectionalIndex:
    NOT_FOUND = -2

    def __init__(self, goals: Iterable[GoalId]):
        self.m = {
            g: i + 1
            for i, g in enumerate(
                sorted(g for g in goals if isinstance(g, int) and g > 0)
            )
        }
        self.length = len(self.m)

    def forward(self, goal_id: GoalId) -> int:
        if isinstance(goal_id, str):
            return BidirectionalIndex.NOT_FOUND
        if goal_id < 0:
            return goal_id
        goal_id = self.m[goal_id]
        new_id = goal_id % 10
        if self.length > 10:
            new_id += 10 * ((goal_id - 1) // 10 + 1)
        if self.length > 90:
            new_id += 100 * ((goal_id - 1) // 100 + 1)
        if self.length > 900:
            new_id += 1000 * ((goal_id - 1) // 1000 + 1)
        return new_id

    def backward(self, goal_id: int) -> int:
        possible_selections: List[int] = [
            g for g in self.m if self.forward(g) == goal_id
        ]
        if len(possible_selections) == 1:
            return possible_selections[0]
        return BidirectionalIndex.NOT_FOUND


class Enumeration(Graph):
    def __init__(self, goaltree: Graph) -> None:
        super().__init__(goaltree)
        self.selection_cache: List[int] = []

    def _id_mapping(self) -> Tuple[Dict[GoalId, Any], BidirectionalIndex]:
        goals = self.goaltree.q().graph
        return goals, BidirectionalIndex(goals)

    def settings(self, key: str) -> Any:
        if key == "root":
            goals, index = self._id_mapping()
            return index.forward(self.goaltree.settings("root"))
        return self.goaltree.settings(key)

    def q(self) -> RenderResult:
        result: Dict[GoalId, Any] = dict()
        goals, index = self._id_mapping()
        for old_id, val in goals.items():
            new_id = index.forward(old_id)
            result[new_id] = {k: v for k, v in val.items() if k != "edge"}
            if "edge" in val:
                result[new_id]["edge"] = [
                    (index.forward(edge[0]), edge[1]) for edge in val["edge"]
                ]
        return RenderResult(result)

    def accept_Select(self, command: Select):
        goals, index = self._id_mapping()
        if (goal_id := command.goal_id) >= 10:
            self.selection_cache = []
        if self.selection_cache:
            goal_id = 10 * self.selection_cache.pop() + goal_id
            if goal_id > max(
                index.forward(k) for k in goals.keys() if isinstance(k, int)
            ):
                goal_id %= int(pow(10, int(math.log(goal_id, 10))))
        if (original_id := index.backward(goal_id)) != BidirectionalIndex.NOT_FOUND:
            self.goaltree.accept(Select(original_id))
            self.selection_cache = []
        else:
            self.selection_cache.append(goal_id)
