from dataclasses import dataclass, replace
from typing import Any

from siebenapp.domain import Graph, Command, EdgeType, GoalId, RenderResult, RenderRow


@dataclass(frozen=True)
class ToggleProgress(Command):
    pass


def _progress_status(
    row: RenderRow, progress_cache: dict[GoalId, tuple[int, int]]
) -> str:
    dividend = progress_cache[row.goal_id][0]
    divisor = progress_cache[row.goal_id][1]
    percent = int(100.0 * dividend / divisor)
    return f"{percent}% ({dividend}/{divisor})"


class ProgressView(Graph):
    def __init__(self, goaltree: Graph):
        super().__init__(goaltree)
        self.show_progress = False

    def accept_ToggleProgress(self, command: ToggleProgress) -> None:
        self.show_progress = not self.show_progress

    def settings(self, key: str) -> Any:
        if key == "filter_progress":
            return self.show_progress
        return self.goaltree.settings(key)

    def reconfigure_from(self, origin: "Graph") -> None:
        super().reconfigure_from(origin)
        self.show_progress = origin.settings("filter_progress")

    def q(self) -> RenderResult:
        render_result = self.goaltree.q()
        if not self.show_progress:
            return render_result
        progress_cache: dict[GoalId, tuple[int, int]] = {}
        rows = render_result.rows
        queue: list[RenderRow] = list(rows)
        while queue:
            row = queue.pop(0)
            children = [x[0] for x in row.edges if x[1] == EdgeType.PARENT]
            open_count = 0 if row.is_open else 1
            if not children:
                progress_cache[row.goal_id] = (open_count, 1)
            elif all(g in progress_cache for g in children):
                progress_cache[row.goal_id] = (
                    sum(progress_cache[x][0] for x in children) + open_count,
                    sum(progress_cache[x][1] for x in children) + 1,
                )
            else:
                queue.append(row)

        result_rows: list[RenderRow] = [
            replace(
                row,
                attrs=row.attrs
                | {
                    "Progress": _progress_status(row, progress_cache),
                    "Id": str(row.goal_id),
                },
            )
            for row in rows
        ]

        return RenderResult(
            result_rows, select=render_result.select, roots=render_result.roots
        )
