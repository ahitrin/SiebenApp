from dataclasses import dataclass
from typing import Any, List, Set

from siebenapp.domain import Graph, Command, RenderResult, RenderRow, GoalId


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
        }
        all_ids: Set[GoalId] = accepted_ids.union(render_result.select)
        rows: List[RenderRow] = [
            RenderRow(
                row.goal_id,
                row.raw_id,
                row.name,
                row.is_open,
                row.is_switchable,
                [e for e in row.edges if e[0] in all_ids],
                row.attrs
                | ({"Filter": self.pattern} if row.goal_id in accepted_ids else {}),
            )
            for row in render_result.rows
            if row.goal_id in all_ids
        ]
        if not accepted_ids:
            fake_row = RenderRow(
                -2,
                -2,
                f"Filter by '{self.pattern}'",
                True,
                False,
                [],
            )
            all_ids.add(-2)
            rows.append(fake_row)
        linked_ids: Set[GoalId] = {goal_id for r in rows for goal_id, _ in r.edges}
        new_roots: Set[GoalId] = all_ids.difference(linked_ids)
        return RenderResult(rows, select=render_result.select, roots=new_roots)
