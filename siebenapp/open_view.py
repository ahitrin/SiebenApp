from dataclasses import dataclass
from typing import Any

from siebenapp.domain import (
    Command,
    Graph,
    RenderResult,
    GoalId,
    RenderRow,
)


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

    def q(self) -> RenderResult:
        render_result = self.goaltree.q()
        if not self._open:
            return render_result
        visible_rows: dict[GoalId, RenderRow] = {
            row.goal_id: row
            for row in render_result.rows
            if row.is_open
            or row.goal_id in render_result.roots.union(set(render_result.select))
        }
        rows: list[RenderRow] = [
            RenderRow(
                row.goal_id,
                row.raw_id,
                row.name,
                row.is_open,
                row.is_switchable,
                [e for e in row.edges if e[0] in visible_rows],
                row.attrs,
            )
            for row in visible_rows.values()
        ]
        dangling: set[GoalId] = set(visible_rows.keys()).difference(
            set(e[0] for row in rows for e in row.edges)
        )
        return RenderResult(
            rows, select=render_result.select, roots=render_result.roots.union(dangling)
        )
