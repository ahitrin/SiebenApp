from dataclasses import dataclass, replace
from typing import Any

from siebenapp.domain import (
    Command,
    Graph,
    RenderResult,
    GoalId,
    RenderRow,
)
from siebenapp.goaltree import OPTION_SELECT, OPTION_PREV_SELECT


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
            or row.goal_id
            in render_result.roots.union(
                goal_id
                for goal_id in {
                    render_result.global_opts.get(OPTION_SELECT, 0),
                    render_result.global_opts.get(OPTION_PREV_SELECT, 0),
                }
                if goal_id != 0
            )
        }
        rows: list[RenderRow] = [
            replace(row, edges=[e for e in row.edges if e[0] in visible_rows])
            for row in visible_rows.values()
        ]
        dangling: set[GoalId] = set(visible_rows.keys()).difference(
            {e[0] for row in rows for e in row.edges}
        )
        return replace(
            render_result, rows=rows, roots=render_result.roots.union(dangling)
        )
