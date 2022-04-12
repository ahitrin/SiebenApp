from dataclasses import dataclass
from typing import Dict, Any, Set, List, Tuple, Optional

from siebenapp.domain import (
    Graph,
    EdgeType,
    Command,
    ToggleClose,
    Delete,
    with_key,
)
from siebenapp.goaltree import Goals


@dataclass(frozen=True)
class ToggleZoom(Command):
    """Hide or show all goals blocked by the current one"""


ZoomData = List[Tuple[int, int]]


class Zoom(Graph):
    def __init__(self, goaltree: Graph, zoom_data: Optional[ZoomData] = None) -> None:
        super().__init__(goaltree)
        self.zoom_root: List[int] = [x[1] for x in zoom_data] if zoom_data else [1]

    def accept_ToggleZoom(self, command: ToggleZoom):
        selection = self.settings("selection")
        if selection == self.zoom_root[-1] and len(self.zoom_root) > 1:
            # unzoom
            last_zoom = self.zoom_root.pop(-1)
            self.events().append(("unzoom", last_zoom))
        elif selection not in self.zoom_root:
            # try to zoom
            origin_goals = self.goaltree.q("edge")
            visible_goals = self._build_visible_goals(origin_goals)
            if selection in visible_goals:
                self.zoom_root.append(selection)
                self.events().append(("zoom", len(self.zoom_root), selection))
            else:
                self.error("Zooming outside of current zoom root is not allowed!")

    @with_key("edge")
    def q(self, keys: str = "name") -> Dict[int, Any]:
        origin_goals = self.goaltree.q(keys)
        if self.zoom_root == [1]:
            return origin_goals
        visible_goals = self._build_visible_goals(origin_goals)
        zoomed_goals = {k: v for k, v in origin_goals.items() if k in visible_goals}
        zoomed_goals[-1] = origin_goals[1]
        for goal in zoomed_goals:
            zoomed_goals[goal]["edge"] = [
                g for g in zoomed_goals[goal]["edge"] if g[0] in visible_goals
            ]
        global_root_edges: Set[Tuple[int, EdgeType]] = {
            (self.zoom_root[-1], EdgeType.BLOCKER)
        }
        for goal_id in [
            self.settings("selection"),
            self.settings("previous_selection"),
        ]:
            if goal_id not in visible_goals and goal_id != Goals.ROOT_ID:
                attrs = origin_goals[goal_id]
                attrs["edge"] = [e for e in attrs["edge"] if e[0] in visible_goals]
                zoomed_goals[goal_id] = attrs
                global_root_edges.add((goal_id, EdgeType.BLOCKER))
        if "switchable" in keys:
            zoomed_goals[-1]["switchable"] = False
        zoomed_goals[-1]["edge"] = sorted(list(global_root_edges))
        return zoomed_goals

    def accept_ToggleClose(self, command: ToggleClose):
        if self.settings("selection") == self.zoom_root[-1]:
            self.accept_ToggleZoom(ToggleZoom())
        # Note: zoom_root may be changed inside accept_ToggleZoom
        self.goaltree.accept(ToggleClose(self.zoom_root[-1]))

    def accept_Delete(self, command: Delete) -> None:
        ids_before: Set[int] = set(self.goaltree.q().keys())
        self.goaltree.accept(command)
        ids_after: Set[int] = set(self.goaltree.q().keys())
        removed = ids_before.difference(ids_after)
        while self.zoom_root and self.zoom_root[-1] in removed:
            last_zoom = self.zoom_root.pop(-1)
            self.events().append(("unzoom", last_zoom))

    def selections(self) -> Set[int]:
        ids = self.goaltree.selections()
        if len(self.zoom_root) > 1 and Goals.ROOT_ID in ids:
            ids.remove(Goals.ROOT_ID)
            ids.add(-1)
        return ids

    def _build_visible_goals(self, edges: Dict[int, Any]) -> Set[int]:
        current_zoom_root = self.zoom_root[-1]
        if current_zoom_root == Goals.ROOT_ID:
            return set(edges.keys())
        visible_goals = {current_zoom_root}
        edges_to_visit = set(edges[current_zoom_root]["edge"])
        while edges_to_visit:
            edge_id, edge_type = edges_to_visit.pop()
            visible_goals.add(edge_id)
            if edge_type == EdgeType.PARENT:
                edges_to_visit.update(edges[edge_id]["edge"])
        return visible_goals

    def verify(self) -> bool:
        ok = self.goaltree.verify()
        assert (
            self.zoom_root[0] == Goals.ROOT_ID
        ), "Zoom stack must always start from the root"
        return ok

    @staticmethod
    def export(goals):
        # type: (Zoom) -> ZoomData
        return [(idx + 1, goal) for idx, goal in enumerate(goals.zoom_root)]
