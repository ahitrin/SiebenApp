from dataclasses import dataclass
from typing import Dict, Any

from siebenapp.domain import Graph, Command, EdgeType, RenderResult


@dataclass(frozen=True)
class FilterBy(Command):
    """Activate or deactivate filtering"""

    pattern: str


class FilterView(Graph):
    def __init__(self, goaltree: Graph):
        super().__init__(goaltree)
        self.pattern = ""

    def accept_FilterBy(self, event: FilterBy):
        self.pattern = event.pattern.lower()

    def settings(self, key: str) -> Any:
        if key == "filter_pattern":
            return self.pattern
        if key == "root" and self.pattern:
            goals = self.q("edge").slice("edge")
            old_root = self.goaltree.settings("root")
            return old_root if old_root in goals else -2
        return self.goaltree.settings(key)

    def reconfigure_from(self, origin: "Graph") -> None:
        super().reconfigure_from(origin)
        self.pattern = origin.settings("filter_pattern")

    def q(self, keys: str = "name") -> RenderResult:
        unfiltered = self.goaltree.q(keys).graph
        filtered = self._filter(unfiltered) if self.pattern else unfiltered
        return RenderResult(filtered, {})

    def _filter(self, unfiltered):
        accepted_nodes = [
            goal_id
            for goal_id, attrs in unfiltered.items()
            if self.pattern in attrs["name"].lower() or goal_id in self.selections()
        ]
        filtered: Dict[int, Any] = {
            -2: {
                "name": f"Filter by '{self.pattern}'",
                "edge": [],
                "select": None,
                "switchable": False,
                "open": True,
            },
        }
        for goal_id, attrs in unfiltered.items():
            if goal_id in accepted_nodes:
                attrs["edge"] = [e for e in attrs["edge"] if e[0] in accepted_nodes]
                if goal_id > 1:
                    filtered[-2]["edge"].append((goal_id, EdgeType.BLOCKER))
                else:
                    attrs["edge"].insert(0, (-2, EdgeType.BLOCKER))
                filtered[goal_id] = attrs
        return filtered
