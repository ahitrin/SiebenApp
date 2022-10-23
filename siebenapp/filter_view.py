from dataclasses import dataclass
from typing import Any, List, Set

from siebenapp.domain import Graph, Command, RenderResult, blocker, RenderRow, GoalId


@dataclass(frozen=True)
class FilterBy(Command):
    """Activate or deactivate filtering"""

    pattern: str


class FilterView(Graph):
    def __init__(self, goaltree: Graph):
        super().__init__(goaltree)
        self.pattern = ""

    def accept_FilterBy(self, event: FilterBy):
        self.pattern = event.pattern.lower()

    def settings(self, key: str) -> Any:
        if key == "filter_pattern":
            return self.pattern
        if key == "root" and self.pattern:
            goals: Set[GoalId] = {row.goal_id for row in self.q().rows}
            old_root = self.goaltree.settings("root")
            return old_root if old_root in goals else -2
        return self.goaltree.settings(key)

    def reconfigure_from(self, origin: "Graph") -> None:
        super().reconfigure_from(origin)
        self.pattern = origin.settings("filter_pattern")

    def q(self) -> RenderResult:
        render_result = self.goaltree.q()
        if not self.pattern:
            return render_result
        accepted_ids: Set[GoalId] = {
            row.goal_id
            for row in render_result.rows
            if self.pattern in row.name.lower()
            or row.goal_id in list(render_result.select)
        }
        rows: List[RenderRow] = [
            RenderRow(
                row.goal_id,
                row.raw_id,
                row.name,
                row.is_open,
                row.is_switchable,
                [e for e in row.edges if e[0] in accepted_ids]
                + ([blocker(-2)] if row.goal_id in {1, -1} else []),
                row.attrs,
            )
            for row in render_result.rows
            if row.goal_id in accepted_ids
        ]
        fake_rows: List[RenderRow] = [
            RenderRow(
                -2,
                -2,
                f"Filter by '{self.pattern}'",
                True,
                False,
                [
                    blocker(goal_id)
                    for goal_id in accepted_ids
                    if isinstance(goal_id, int) and goal_id > 1
                ],
            ),
        ]
        return RenderResult(rows=rows + fake_rows, select=render_result.select)
