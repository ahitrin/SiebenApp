from dataclasses import dataclass, replace

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

    goal_id: int


ZoomData = list[tuple[int, int]]


def _replace_with_fake(goal_id: GoalId):
    return goal_id if goal_id != Goals.ROOT_ID else -1


class Zoom(Graph):
    def __init__(self, goaltree: Graph, zoom_data: ZoomData | None = None) -> None:
        super().__init__(goaltree)
        self.zoom_root: list[int] = [x[1] for x in zoom_data] if zoom_data else [1]

    def accept_ToggleZoom(self, command: ToggleZoom):
        target = command.goal_id
        if target == self.zoom_root[-1] and len(self.zoom_root) > 1:
            # unzoom
            last_zoom = self.zoom_root.pop(-1)
            self.events().append(("unzoom", last_zoom))
        elif target not in self.zoom_root:
            # try to zoom
            render_result = self.goaltree.q()
            visible_goals = self._build_visible_goals(render_result)
            if target in visible_goals:
                self.zoom_root.append(target)
                self.events().append(("zoom", len(self.zoom_root), target))
            else:
                self.error("Zooming outside of current zoom root is not allowed!")

    def q(self) -> RenderResult:
        render_result = self.goaltree.q()
        if self.zoom_root == [Goals.ROOT_ID]:
            return render_result
        origin_root: RenderRow = render_result.by_id(list(render_result.roots)[0])
        assert origin_root.goal_id == Goals.ROOT_ID
        visible_goals = (
            self._build_visible_goals(render_result)
            .union(render_result.global_opts.values())
            .difference({Goals.ROOT_ID})
        )
        rows: list[RenderRow] = [
            replace(
                r,
                edges=[e for e in r.edges if e[0] in visible_goals],
                attrs=r.attrs
                | (
                    {"Zoom": origin_root.name}
                    if r.goal_id == self.zoom_root[-1]
                    else {}
                ),
            )
            for r in render_result.rows
            if r.goal_id in visible_goals
        ]
        if Goals.ROOT_ID in render_result.global_opts.values():
            rows.append(
                RenderRow(
                    -1,
                    -1,
                    origin_root.name,
                    origin_root.is_open,
                    False,
                    True,
                    [
                        blocker(goal_id)
                        for goal_id, _ in origin_root.edges
                        if goal_id in visible_goals
                    ],
                )
            )
        new_global_opts = {
            k: _replace_with_fake(v) for k, v in render_result.global_opts.items()
        }
        all_ids: set[GoalId] = {r.goal_id for r in rows}
        linked_ids: set[GoalId] = {goal_id for r in rows for goal_id, _ in r.edges}
        new_roots: set[GoalId] = all_ids.difference(linked_ids)
        return replace(
            render_result,
            rows=rows,
            roots=new_roots,
            global_opts=new_global_opts,
        )

    def accept_ToggleClose(self, command: ToggleClose):
        if command.goal_id == self.zoom_root[-1]:
            self.accept_ToggleZoom(ToggleZoom(self.zoom_root[-1]))
        # Note: zoom_root may be changed inside accept_ToggleZoom
        self.goaltree.accept(ToggleClose(command.goal_id, self.zoom_root[-1]))

    def accept_Delete(self, command: Delete) -> None:
        ids_before: set[int] = {r.raw_id for r in self.goaltree.q().rows}
        self.goaltree.accept(command)
        ids_after: set[int] = {r.raw_id for r in self.goaltree.q().rows}
        removed = ids_before.difference(ids_after)
        while self.zoom_root and self.zoom_root[-1] in removed:
            last_zoom = self.zoom_root.pop(-1)
            self.events().append(("unzoom", last_zoom))

    def _build_visible_goals(self, render_result: RenderResult) -> set[GoalId]:
        current_zoom_root = self.zoom_root[-1]
        if current_zoom_root == Goals.ROOT_ID:
            return {row.goal_id for row in render_result.rows}
        visible_goals: set[GoalId] = {current_zoom_root}
        edges_to_visit = set(render_result.by_id(current_zoom_root).edges)
        while edges_to_visit:
            edge_id, edge_type = edges_to_visit.pop()
            visible_goals.add(edge_id)
            if edge_type == EdgeType.PARENT:
                edges_to_visit.update(render_result.by_id(edge_id).edges)
        return visible_goals

    def verify(self) -> None:
        self.goaltree.verify()
        assert (
            self.zoom_root[0] == Goals.ROOT_ID
        ), "Zoom stack must always start from the root"

    @staticmethod
    def export(goals: "Zoom") -> ZoomData:
        return [(idx + 1, goal) for idx, goal in enumerate(goals.zoom_root)]
