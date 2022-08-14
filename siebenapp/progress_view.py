from dataclasses import dataclass
from typing import Dict, Any, Tuple, List

from siebenapp.domain import Graph, Command, EdgeType, GoalId, RenderResult


@dataclass(frozen=True)
class ToggleProgress(Command):
    pass


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
        if not self.show_progress:
            return self.goaltree.q()
        progress_cache: Dict[GoalId, Tuple[int, int]] = {}
        result = self.goaltree.q().graph
        queue: List[GoalId] = list(result.keys())
        while queue:
            goal_id = queue.pop(0)
            children = [
                x[0] for x in result[goal_id]["edge"] if x[1] == EdgeType.PARENT
            ]
            open_count = 0 if result[goal_id]["open"] else 1
            if not children:
                progress_cache[goal_id] = (open_count, 1)
            elif all(g in progress_cache for g in children):
                progress_cache[goal_id] = (
                    sum(progress_cache[x][0] for x in children) + open_count,
                    sum(progress_cache[x][1] for x in children) + 1,
                )
            else:
                queue.append(goal_id)

        for goal_id, attr in result.items():
            progress = progress_cache[goal_id]
            old_name = attr["name"]
            attr["name"] = f"[{progress[0]}/{progress[1]}] {old_name}"

        repacked: Dict[GoalId, Any] = {k: v for k, v in result.items()}
        return RenderResult(repacked)
