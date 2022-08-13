from dataclasses import dataclass
from typing import Dict, Any

from siebenapp.domain import Command, Graph, with_key, RenderResult, GoalId


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

    @with_key("switchable")
    def q(self, keys: str = "name") -> Dict[int, Any]:
        goals: Dict[GoalId, Any] = {k: v for k, v in self.goaltree.q(keys).items()}
        if self._only_switchable:
            goals = {
                k: v
                for k, v in goals.items()
                if v["switchable"] or k in self.selections()
            }
            for v in goals.values():
                if "edge" in v:
                    v["edge"] = []
        return RenderResult(goals, {}).slice(keys)
