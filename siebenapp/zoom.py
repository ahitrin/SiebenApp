import collections
from dataclasses import dataclass
from typing import Dict, Any, Set, List, Tuple, Optional

from siebenapp.domain import (
    Graph,
    EdgeType,
    Command,
    HoldSelect,
    ToggleClose,
    Delete,
    ToggleLink,
    Select,
    Insert,
    with_key,
)
from siebenapp.goaltree import Goals


@dataclass(frozen=True)
class ToggleZoom(Command):
    """Hide or show all goals blocked by the current one"""


ZoomData = List[Tuple[int, int]]


class Zoom(Graph):
    def __init__(self, goaltree: Goals, zoom_data: Optional[ZoomData] = None) -> None:
        super().__init__(goaltree)
        self.zoom_root = [x[1] for x in zoom_data] if zoom_data else [1]

    def accept_ToggleZoom(self, command: ToggleZoom):
        selection = self.settings("selection")
        if selection == self.zoom_root[-1] and len(self.zoom_root) > 1:
            # unzoom
            last_zoom = self.zoom_root.pop(-1)
            self.events().append(("unzoom", last_zoom))
        elif selection not in self.zoom_root:
            self.zoom_root.append(selection)
            self.events().append(("zoom", len(self.zoom_root), selection))
        else:
            return
        visible_goals = self._build_visible_goals()
        if self.settings("previous_selection") not in visible_goals:
            self.accept(HoldSelect())

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
        zoomed_goals[-1]["edge"] = [(self.zoom_root[-1], EdgeType.BLOCKER)]
        return zoomed_goals

    def accept_ToggleClose(self, command: ToggleClose):
        if self.settings("selection") == self.zoom_root[-1]:
            self.accept_ToggleZoom(ToggleZoom())
        # Note: zoom_root may be changed inside accept_ToggleZoom
        self.goaltree.accept(ToggleClose(self.zoom_root[-1]))

    def accept_Insert(self, command: Insert):
        self.goaltree.accept(command)
        if self.settings("selection") not in self._build_visible_goals():
            self.goaltree.accept_all(Select(self.zoom_root[-1]), HoldSelect())

    def accept_ToggleLink(self, command: ToggleLink):
        self.goaltree.accept(command)
        visible_goals = self._build_visible_goals()
        if (
            self.settings("selection") not in visible_goals
            or self.settings("previous_selection") not in visible_goals
        ):
            self.goaltree.accept_all(Select(self.zoom_root[-1]), HoldSelect())

    def accept_Delete(self, command: Delete) -> None:
        if self.settings("selection") == self.zoom_root[-1]:
            self.accept_ToggleZoom(ToggleZoom())
        self.goaltree.accept(command)
        if self.settings("selection") != self.zoom_root[-1]:
            self.goaltree.accept_all(Select(self.zoom_root[-1]), HoldSelect())

    def verify(self) -> bool:
        ok = self.goaltree.verify()
        if len(self.zoom_root) == 1:
            return ok
        visible_goals = self._build_visible_goals()
        assert (
            self.settings("selection") in visible_goals
        ), "Selected goal must be within visible area"
        assert (
            self.settings("previous_selection") in visible_goals
        ), "Prev-selected goal must be within visible area"
        return ok

    def _build_visible_goals(self, edges: Dict[int, Any] = None) -> Set[int]:
        if edges is None:
            edges = self.goaltree.q("edge")
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

    @staticmethod
    def export(goals):
        # type: (Zoom) -> ZoomData
        return [(idx + 1, goal) for idx, goal in enumerate(goals.zoom_root)]
