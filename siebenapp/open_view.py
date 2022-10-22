from dataclasses import dataclass
from typing import Dict, Any, Set, List

from siebenapp.domain import (
    Command,
    Graph,
    EdgeType,
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

    def _is_visible(self, row: RenderRow) -> bool:
        # Here we know something about other layers (Zoom). I do not like it
        return row.is_open or row.goal_id in self.selections() or row.goal_id in {1, -1}

    def q(self) -> RenderResult:
        render_result = self.goaltree.q()
        if not self._open:
            return render_result
        visible_rows: Dict[GoalId, RenderRow] = {
            row.goal_id: row for row in render_result.rows if self._is_visible(row)
        }
        rows: List[RenderRow] = [
            RenderRow(
                row.goal_id,
                row.raw_id,
                row.name,
                row.is_open,
                row.is_switchable,
                row.select,
                [e for e in row.edges if e[0] in visible_rows],
            )
            for row in visible_rows.values()
        ]
        dangling: Set[GoalId] = (
            set(visible_rows.keys())
            .difference(set(e[0] for row in rows for e in row.edges))
            .difference({1, -1})
        )
        root_id: GoalId = min(visible_rows)
        result = RenderResult(rows=rows, select=render_result.select)
        result.by_id(root_id).edges.extend(
            [(goal_id, EdgeType.BLOCKER) for goal_id in dangling]
        )
        return result
