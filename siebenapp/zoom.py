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


def _replace_with_fake(goal_id: GoalId):
    return goal_id if goal_id != Goals.ROOT_ID else -1


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
            render_result = self.goaltree.q()
            visible_goals = self._build_visible_goals(render_result)
            if selection in visible_goals:
                self.zoom_root.append(selection)
                self.events().append(("zoom", len(self.zoom_root), selection))
            else:
                self.error("Zooming outside of current zoom root is not allowed!")

    def q(self) -> RenderResult:
        render_result = self.goaltree.q()
        if self.zoom_root == [1]:
            return render_result
        rows = render_result.rows
        origin_root = rows[0]
        assert origin_root.goal_id == Goals.ROOT_ID
        visible_goals = self._build_visible_goals(render_result)
        selected_goals: Set[int] = {
            self.settings("selection"),
            self.settings("previous_selection"),
        }.difference({Goals.ROOT_ID})
        zoomed_rows: List[RenderRow] = [
            RenderRow(
                r.goal_id,
                r.raw_id,
                r.name,
                r.is_open,
                r.is_switchable,
                [e for e in r.edges if e[0] in visible_goals.union(selected_goals)],
                {
                    # We could use `r.attrs | (...)` in Python 3.9+
                    **r.attrs,
                    **({"Zoom": "root"} if r.goal_id == self.zoom_root[-1] else {}),
                },
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
            sorted(
                list(
                    blocker(goal_id)
                    for goal_id in selected_goals.difference(visible_goals).union(
                        {self.zoom_root[-1]}
                    )
                )
            ),
        )
        new_select = (
            _replace_with_fake(render_result.select[0]),
            _replace_with_fake(render_result.select[1]),
        )
        return RenderResult(zoomed_rows + [fake_root], select=new_select, roots={-1})

    def accept_ToggleClose(self, command: ToggleClose):
        if self.settings("selection") == self.zoom_root[-1]:
            self.accept_ToggleZoom(ToggleZoom())
        # Note: zoom_root may be changed inside accept_ToggleZoom
        self.goaltree.accept(ToggleClose(self.zoom_root[-1]))

    def accept_Delete(self, command: Delete) -> None:
        ids_before: Set[int] = set(r.raw_id for r in self.goaltree.q().rows)
        self.goaltree.accept(command)
        ids_after: Set[int] = set(r.raw_id for r in self.goaltree.q().rows)
        removed = ids_before.difference(ids_after)
        while self.zoom_root and self.zoom_root[-1] in removed:
            last_zoom = self.zoom_root.pop(-1)
            self.events().append(("unzoom", last_zoom))

    def settings(self, key: str) -> Any:
        if key == "root" and self.zoom_root[-1] != Goals.ROOT_ID:
            return -1
        return self.goaltree.settings(key)

    def _build_visible_goals(self, render_result: RenderResult) -> Set[GoalId]:
        rows = render_result.rows
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
