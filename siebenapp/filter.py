import collections
from dataclasses import dataclass
from typing import Dict, Any

from siebenapp.domain import Graph, Command, with_key


@dataclass(frozen=True)
class FilterBy(Command):
    """Activate or deactivate filtering"""

    pattern: str


class FilterView(Graph):
    def __init__(self, goaltree: Graph):
        super().__init__(goaltree)
        self.pattern = ""

    def events(self) -> collections.deque:
        return self.goaltree.events()

    def verify(self) -> bool:
        return self.goaltree.verify()

    def settings(self, key: str) -> int:
        return self.goaltree.settings(key)

    def accept_FilterBy(self, event: FilterBy):
        self.pattern = event.pattern.lower()

    @with_key("name")
    @with_key("select")
    def q(self, keys: str = "name") -> Dict[int, Any]:
        unfiltered = self.goaltree.q(keys)
        return self._filter(unfiltered, keys) if self.pattern else unfiltered

    def _filter(self, unfiltered, keys):
        accepted_nodes = [
            goal_id
            for goal_id, attrs in unfiltered.items()
            if self.pattern in attrs["name"].lower()
            or attrs.get("select", None) is not None
        ]
        filtered: Dict[int, Any] = {}
        for goal_id, attrs in unfiltered.items():
            if goal_id in accepted_nodes:
                if "edge" in keys:
                    attrs["edge"] = [e for e in attrs["edge"] if e[0] in accepted_nodes]
                filtered[goal_id] = attrs
        return filtered
