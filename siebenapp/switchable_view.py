from dataclasses import dataclass, replace
from typing import Any

from siebenapp.domain import Command, Graph, RenderResult, RenderRow


@dataclass(frozen=True)
class ToggleSwitchableView(Command):
    """Switch between "only switchable goals" and "all goals" views"""


class SwitchableView(Graph):
    """Non-persistent layer that allows to
    show only switchable and/or selected goals"""

    def __init__(self, goaltree: Graph):
        super().__init__(goaltree)
        self._only_switchable: bool = False

    def accept_ToggleSwitchableView(self, command: ToggleSwitchableView):
        self._only_switchable = not self._only_switchable

    def settings(self, key: str) -> Any:
        if key == "filter_switchable":
            return self._only_switchable
        return self.goaltree.settings(key)

    def reconfigure_from(self, origin: "Graph") -> None:
        super().reconfigure_from(origin)
        if origin.settings("filter_switchable"):
            self.accept(ToggleSwitchableView())

    def q(self) -> RenderResult:
        render_result = self.goaltree.q()
        if not self._only_switchable:
            return render_result
        rows: list[RenderRow] = [
            replace(row, edges=[])
            for row in render_result.rows
            if row.is_switchable or row.goal_id in list(render_result.select)
        ]
        return RenderResult(
            rows,
            select=render_result.select,
            roots={r.goal_id for r in rows},
            global_opts=render_result.global_opts,
        )
