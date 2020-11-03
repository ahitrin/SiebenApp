import collections
from dataclasses import dataclass
from typing import Dict, Any

from siebenapp.domain import Command, Graph, Select, HoldSelect


@dataclass(frozen=True)
class ToggleSwitchableView(Command):
    """Switch between "only switchable goals" and "all goals" views"""


class SwitchableView(Graph):
    """Non-persistent layer that allows to
    show only switchable goals"""

    def __init__(self, goaltree: Graph):
        super().__init__()
        self.goaltree = goaltree
        self._only_switchable: bool = False

    def accept(self, command: Command) -> None:
        if isinstance(command, ToggleSwitchableView):
            self._only_switchable = not self._only_switchable
            if not self._only_switchable:
                return
            ids = [
                k for k, v in self.goaltree.q("switchable").items() if v["switchable"]
            ]
            if ids and self.goaltree.settings("selection") not in ids:
                self.goaltree.accept(Select(min(ids)))
            if ids and self.goaltree.settings("previous_selection") not in ids:
                self.goaltree.accept(HoldSelect())
        else:
            self.goaltree.accept(command)

    def events(self) -> collections.deque:
        return self.goaltree.events()

    def settings(self, key: str) -> int:
        if key == "only_switchable":
            return self._only_switchable
        return self.goaltree.settings(key)

    def verify(self) -> bool:
        return self.goaltree.verify()

    def q(self, keys: str = "name") -> Dict[int, Any]:
        skip_switchable = "switchable" not in keys
        if skip_switchable:
            keys = ",".join([keys, "switchable"])
        goals = self.goaltree.q(keys)
        if self._only_switchable:
            goals = {k: v for k, v in goals.items() if v["switchable"]}
            for v in goals.values():
                if "edge" in v:
                    v["edge"] = []
        if skip_switchable:
            for v in goals.values():
                v.pop("switchable")
        return goals
