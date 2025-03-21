import math
from collections.abc import Iterable
from dataclasses import replace

from siebenapp.domain import Graph, GoalId, RenderResult, RenderRow
from siebenapp.selectable import Select


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
        possible_selections: list[int] = [
            g for g in self.m if self.forward(g) == goal_id
        ]
        if len(possible_selections) == 1:
            return possible_selections[0]
        return BidirectionalIndex.NOT_FOUND


class Enumeration(Graph):
    def __init__(self, goaltree: Graph) -> None:
        super().__init__(goaltree)
        self.selection_cache: list[int] = []

    def _id_mapping(self) -> tuple[RenderResult, BidirectionalIndex]:
        render_result = self.goaltree.q()
        return render_result, BidirectionalIndex(
            [r.goal_id for r in render_result.rows]
        )

    def q(self) -> RenderResult:
        render_result, index = self._id_mapping()
        rows: list[RenderRow] = [
            replace(
                row,
                goal_id=index.forward(row.goal_id),
                edges=[(index.forward(e[0]), e[1]) for e in row.edges],
            )
            for row in render_result.rows
        ]
        new_global_opts = {
            k: index.forward(v) for k, v in render_result.global_opts.items()
        }
        return replace(
            render_result,
            rows=rows,
            roots={index.forward(goal_id) for goal_id in render_result.roots},
            global_opts=new_global_opts,
        )

    def accept_Select(self, command: Select):
        render_result, index = self._id_mapping()
        goals: set[GoalId] = {row.goal_id for row in render_result.rows}
        if (goal_id := command.goal_id) >= 10:
            self.selection_cache = []
        if self.selection_cache:
            goal_id = 10 * self.selection_cache.pop() + goal_id
            if goal_id > max(index.forward(k) for k in goals if isinstance(k, int)):
                goal_id %= int(pow(10, int(math.log(goal_id, 10))))
        if (original_id := index.backward(goal_id)) != BidirectionalIndex.NOT_FOUND:
            self.goaltree.accept(Select(original_id))
            self.selection_cache = []
        else:
            self.selection_cache.append(goal_id)
