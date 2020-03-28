from typing import Dict, Any, Set, List, Tuple

from siebenapp.domain import (
    Graph,
    EdgeType,
    Command,
    HoldSelect,
    ToggleClose,
    Delete,
    ToggleLink,
)
from siebenapp.goaltree import Goals

ZoomData = List[Tuple[int, int]]


class Zoom(Graph):
    override = [
        "accept",
        "add",
        "_build_visible_goals",
        "_delete",
        "export",
        "goaltree",
        "insert",
        "q",
        "rename",
        "select",
        "_toggle_close",
        "_toggle_link",
        "toggle_zoom",
        "verify",
        "zoom_root",
    ]

    def __init__(self, goaltree: Goals) -> None:
        self.goaltree = goaltree
        self.zoom_root = [1]

    def accept(self, command: Command) -> None:
        if isinstance(command, ToggleClose):
            self._toggle_close()
        elif isinstance(command, ToggleLink):
            self._toggle_link(command)
        elif isinstance(command, Delete):
            self._delete(command)
        else:
            self.goaltree.accept(command)

    def add(
        self, name: str, add_to: int = 0, edge_type: EdgeType = EdgeType.PARENT
    ) -> None:
        self.goaltree.add(name, add_to, edge_type)

    def toggle_zoom(self) -> None:
        selection = self.settings["selection"]
        if selection == self.zoom_root[-1] and len(self.zoom_root) > 1:
            # unzoom
            last_zoom = self.zoom_root.pop(-1)
            self.events.append(("unzoom", last_zoom))
        elif selection not in self.zoom_root:
            self.zoom_root.append(selection)
            self.events.append(("zoom", len(self.zoom_root), selection))
        else:
            return
        visible_goals = self._build_visible_goals()
        if self.settings["previous_selection"] not in visible_goals:
            self.accept(HoldSelect())

    def select(self, goal_id: int) -> None:
        self.goaltree.select(goal_id)

    def rename(self, new_name: str, goal_id: int = 0) -> None:
        self.goaltree.rename(new_name, goal_id)

    def q(self, keys: str = "name") -> Dict[int, Any]:
        origin_goals = self.goaltree.q(keys)
        if self.zoom_root == [1]:
            return origin_goals
        visible_goals = self._build_visible_goals()
        zoomed_goals = {k: v for k, v in origin_goals.items() if k in visible_goals}
        zoomed_goals[-1] = origin_goals[1]
        if "edge" in keys:
            for goal in zoomed_goals:
                zoomed_goals[goal]["edge"] = [
                    g for g in zoomed_goals[goal]["edge"] if g[0] in visible_goals
                ]
            zoomed_goals[-1]["edge"] = [(self.zoom_root[-1], EdgeType.BLOCKER)]
        return zoomed_goals

    def _toggle_close(self) -> None:
        if self.settings["selection"] == self.zoom_root[-1]:
            self.toggle_zoom()
        self.goaltree.accept(ToggleClose())
        if self.settings["selection"] not in self._build_visible_goals():
            self.goaltree.select(self.zoom_root[-1])
            self.accept(HoldSelect())

    def insert(self, name: str) -> None:
        self.goaltree.insert(name)
        if self.settings["selection"] not in self._build_visible_goals():
            self.goaltree.select(self.zoom_root[-1])
            self.accept(HoldSelect())

    def _toggle_link(self, command: ToggleLink):
        self.goaltree.accept(command)
        if self.settings["selection"] not in self._build_visible_goals():
            self.goaltree.select(self.zoom_root[-1])
            self.accept(HoldSelect())

    def _delete(self, command: Delete) -> None:
        if self.settings["selection"] == self.zoom_root[-1]:
            self.toggle_zoom()
        self.goaltree.accept(command)
        if self.settings["selection"] != self.zoom_root[-1]:
            self.goaltree.select(self.zoom_root[-1])
            self.accept(HoldSelect())

    def verify(self) -> bool:
        ok = self.goaltree.verify()
        if len(self.zoom_root) == 1:
            return ok
        visible_goals = self._build_visible_goals()
        assert (
            self.settings["selection"] in visible_goals
        ), "Selected goal must be within visible area"
        assert (
            self.settings["previous_selection"] in visible_goals
        ), "Prev-selected goal must be within visible area"
        return ok

    def _build_visible_goals(self) -> Set[int]:
        edges = self.goaltree.q("edge")
        current_zoom_root = self.zoom_root[-1]
        visible_goals = {current_zoom_root}
        edges_to_visit = set(edges[current_zoom_root]["edge"])
        while edges_to_visit:
            next_edge = edges_to_visit.pop()
            visible_goals.add(next_edge[0])
            if next_edge[1] == EdgeType.PARENT:
                edges_to_visit.update(edges[next_edge[0]]["edge"])
        return visible_goals

    def __getattribute__(self, item):
        override = object.__getattribute__(self, "override")
        if item in override:
            return object.__getattribute__(self, item)
        goals = object.__getattribute__(self, "goaltree")
        return getattr(goals, item)

    @staticmethod
    def build(goals, data):
        # type: (Goals, ZoomData) -> Zoom
        result = Zoom(goals)
        result.zoom_root = [x[1] for x in data] if data else [1]
        return result

    @staticmethod
    def export(goals):
        # type: (Zoom) -> ZoomData
        return [(idx + 1, goal) for idx, goal in enumerate(goals.zoom_root)]
