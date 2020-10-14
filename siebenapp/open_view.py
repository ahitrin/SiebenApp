import collections
from dataclasses import dataclass
from typing import Dict, Any

from siebenapp.domain import Command, Graph


@dataclass(frozen=True)
class ToggleOpenView(Command):
    """Switch between "only open goals" and "all goals" views"""


class OpenView(Graph):
    """Non-persistent view layer that allows to switch
    between only-open and all goals"""

    def __init__(self, goaltree: Graph):
        super().__init__()
        self.goaltree = goaltree
        self._open: bool = True

    def accept(self, command: Command) -> None:
        if isinstance(command, ToggleOpenView):
            self._open = not self._open
        else:
            self.goaltree.accept(command)

    def events(self) -> collections.deque:
        return self.goaltree.events()

    def settings(self, key: str) -> int:
        return self.goaltree.settings(key)

    def q(self, keys: str = "name") -> Dict[int, Any]:
        skip_open = "open" not in keys
        if skip_open:
            keys = ",".join([keys, "open"])
        goals = self.goaltree.q(keys)
        result: Dict[int, Any] = {
            k: {} for k, v in goals.items() if not self._open or v["open"]
        }
        for goal_id in result:
            val = goals[goal_id]
            result[goal_id] = dict(
                (k, v) for k, v in val.items() if k not in ["edge", "open"]
            )
            if not skip_open:
                result[goal_id]["open"] = val["open"]
            if "edge" in val:
                result[goal_id]["edge"] = [
                    (edge[0], edge[1]) for edge in val["edge"] if edge[0] in result
                ]
        return result
