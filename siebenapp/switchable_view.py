import collections
from dataclasses import dataclass
from typing import Dict, Any

from siebenapp.domain import Command, Graph, with_key


@dataclass(frozen=True)
class ToggleSwitchableView(Command):
    """Switch between "only switchable goals" and "all goals" views"""


class SwitchableView(Graph):
    """Non-persistent layer that allows to
    show only switchable and/or selected goals"""

    def __init__(self, goaltree: Graph):
        super().__init__(goaltree)
        self._only_switchable: bool = False

    def verify(self) -> bool:
        return self.goaltree.verify()

    def accept_ToggleSwitchableView(self, command: ToggleSwitchableView):
        self._only_switchable = not self._only_switchable

    def events(self) -> collections.deque:
        return self.goaltree.events()

    def settings(self, key: str) -> int:
        if key == "filter_switchable":
            return self._only_switchable
        return self.goaltree.settings(key)

    @with_key("switchable")
    def q(self, keys: str = "name") -> Dict[int, Any]:
        pass_through = [
            k
            for k in [
                self.goaltree.settings("selection"),
                self.goaltree.settings("previous_selection"),
            ]
            if k is not None
        ]
        goals = self.goaltree.q(keys)
        if self._only_switchable:
            goals = {
                k: v for k, v in goals.items() if v["switchable"] or k in pass_through
            }
            for v in goals.values():
                if "edge" in v:
                    v["edge"] = []
        return goals
