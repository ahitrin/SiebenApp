from dataclasses import dataclass
from typing import Dict, Any, Set, List, Tuple, Optional

from siebenapp.domain import (
    Graph,
    EdgeType,
    Command,
    ToggleClose,
    Delete,
    GoalId,
    RenderResult,
    RenderRow,
    blocker,
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
            rows = self.goaltree.q().rows
            visible_goals = self._build_visible_goals(rows)
            if selection in visible_goals:
                self.zoom_root.append(selection)
                self.events().append(("zoom", len(self.zoom_root), selection))
            else:
                self.error("Zooming outside of current zoom root is not allowed!")

    def q(self) -> RenderResult:
        rows = self.goaltree.q().rows
        origin_root = rows[0]
        assert origin_root.goal_id == Goals.ROOT_ID
        if self.zoom_root == [1]:
            return RenderResult(rows=rows)
        visible_goals = self._build_visible_goals(rows)
        selected_goals: Set[int] = {
            self.settings("selection"),
            self.settings("previous_selection"),
        }.difference({Goals.ROOT_ID})
        global_root_edges: List[Tuple[GoalId, EdgeType]] = [
            blocker(self.zoom_root[-1])
        ] + [
            blocker(goal_id)
            for goal_id in selected_goals
            if goal_id not in visible_goals
        ]
        zoomed_rows: List[RenderRow] = [
            RenderRow(
                r.goal_id,
                r.raw_id,
                r.name,
                r.is_open,
                r.is_switchable,
                r.select,
                [e for e in r.edges if e[0] in visible_goals.union(selected_goals)],
            )
            for r in rows
            if r.goal_id in visible_goals.union(selected_goals)
        ]
        fake_root = RenderRow(
            -1,
            -1,
            origin_root.name,
            origin_root.is_open,
            False,
            origin_root.select,
            sorted(list(set(global_root_edges))),
        )
        return RenderResult(rows=zoomed_rows + [fake_root])

    def accept_ToggleClose(self, command: ToggleClose):
        if self.settings("selection") == self.zoom_root[-1]:
            self.accept_ToggleZoom(ToggleZoom())
        # Note: zoom_root may be changed inside accept_ToggleZoom
        self.goaltree.accept(ToggleClose(self.zoom_root[-1]))

    def accept_Delete(self, command: Delete) -> None:
        ids_before: Set[int] = set(self.goaltree.q().slice("name").keys())
        self.goaltree.accept(command)
        ids_after: Set[int] = set(self.goaltree.q().slice("name").keys())
        removed = ids_before.difference(ids_after)
        while self.zoom_root and self.zoom_root[-1] in removed:
            last_zoom = self.zoom_root.pop(-1)
            self.events().append(("unzoom", last_zoom))

    def settings(self, key: str) -> Any:
        if key == "root" and self.zoom_root[-1] != Goals.ROOT_ID:
            return -1
        return self.goaltree.settings(key)

    def selections(self) -> Set[int]:
        ids = self.goaltree.selections()
        if len(self.zoom_root) > 1 and Goals.ROOT_ID in ids:
            ids.remove(Goals.ROOT_ID)
            ids.add(-1)
        return ids

    def _build_visible_goals(self, rows: List[RenderRow]) -> Set[GoalId]:
        current_zoom_root = self.zoom_root[-1]
        if current_zoom_root == Goals.ROOT_ID:
            return set(row.goal_id for row in rows)
        index: Dict[GoalId, RenderRow] = {row.goal_id: row for row in rows}
        visible_goals: Set[GoalId] = {current_zoom_root}
        edges_to_visit = set(index[current_zoom_root].edges)
        while edges_to_visit:
            edge_id, edge_type = edges_to_visit.pop()
            visible_goals.add(edge_id)
            if edge_type == EdgeType.PARENT:
                edges_to_visit.update(index[edge_id].edges)
        return visible_goals

    def verify(self) -> None:
        self.goaltree.verify()
        assert (
            self.zoom_root[0] == Goals.ROOT_ID
        ), "Zoom stack must always start from the root"

    @staticmethod
    def export(goals):
        # type: (Zoom) -> ZoomData
        return [(idx + 1, goal) for idx, goal in enumerate(goals.zoom_root)]
