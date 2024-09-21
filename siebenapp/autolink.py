from dataclasses import dataclass, replace

from siebenapp.domain import (
    Graph,
    Command,
    EdgeType,
    ToggleClose,
    Add,
    ToggleLink,
    Insert,
    Rename,
    Delete,
    GoalId,
    RenderResult,
    RenderRow,
)
from siebenapp.goaltree import Goals, OPTION_SELECT


@dataclass(frozen=True)
class ToggleAutoLink(Command):
    keyword: str


AutoLinkData = list[tuple[int, str]]


class AutoLink(Graph):
    def __init__(self, goals: Graph, data: AutoLinkData | None = None):
        super().__init__(goals)
        self.keywords: dict[str, int] = {}
        self.back_kw: dict[int, str] = {}
        if data:
            for goal_id, keyword in data:
                self.keywords[keyword] = goal_id
                self.back_kw[goal_id] = keyword

    def accept_ToggleAutoLink(self, command: ToggleAutoLink) -> None:
        render_result: RenderResult = self.goaltree.q()
        selected_id: int = int(render_result.global_opts[OPTION_SELECT])
        selected_goal = render_result.by_id(selected_id)
        if not selected_goal.is_open:
            self.error("Autolink cannot be set for closed goals")
            return
        if selected_id == Goals.ROOT_ID:
            self.error("Autolink cannot be set for the root goal")
            return
        keyword: str = command.keyword.lower().strip()
        if selected_id in self.back_kw:
            self.keywords.pop(self.back_kw[selected_id])
            self.back_kw.pop(selected_id)
            self.events().append(("remove_autolink", selected_id))
        if keyword in self.keywords:
            old_id: int = self.keywords.pop(keyword)
            self.back_kw.pop(old_id)
            self.events().append(("remove_autolink", old_id))
        if not keyword:
            # empty keyword? exit right now
            return
        self.keywords[keyword] = selected_id
        self.back_kw[selected_id] = keyword
        self.events().append(("add_autolink", selected_id, keyword))

    def accept_ToggleClose(self, command: ToggleClose) -> None:
        selected_id: int = self.settings("selection")
        if selected_id in self.back_kw:
            self.keywords.pop(self.back_kw[selected_id])
            self.back_kw.pop(selected_id)
            self.events().append(("remove_autolink", selected_id))
        self.goaltree.accept(command)

    def accept_Add(self, command: Add) -> None:
        self._autolink_new_goal(command)

    def accept_Insert(self, command: Insert) -> None:
        self._autolink_new_goal(command)

    def _autolink_new_goal(self, command: Add | Insert) -> None:
        matching: list[int] = self._find_matching_goals(command.name)
        ids_before: set[int] = set(self.goaltree.goals.keys())
        self.goaltree.accept(command)
        ids_after: set[int] = set(self.goaltree.goals.keys())
        ids_diff: set[int] = ids_after.difference(ids_before)
        if ids_diff:
            added_id: int = ids_diff.pop()
            self._make_links(matching, added_id)

    def accept_Rename(self, command: Rename) -> None:
        matching: list[int] = self._find_matching_goals(command.new_name)
        self.goaltree.accept(command)
        selected_id: int = command.goal_id or self.settings("selection")
        self._make_links(matching, selected_id)

    def accept_Delete(self, command: Delete) -> None:
        selected_id: int = command.goal_id or self.settings("selection")
        edges: dict[int, list[tuple[GoalId, EdgeType]]] = {
            row.raw_id: row.edges for row in self.goaltree.q().rows
        }
        goals_to_check: list[int] = [selected_id]
        while goals_to_check:
            goal_id: int = goals_to_check.pop()
            goals_to_check.extend(
                e[0]
                for e in edges[goal_id]
                if e[1] == EdgeType.PARENT and isinstance(e[0], int)
            )
            if goal_id in self.back_kw:
                added_kw: str = self.back_kw.pop(goal_id)
                self.keywords.pop(added_kw)
                self.events().append(("remove_autolink", goal_id))
        self.goaltree.accept(command)

    def _find_matching_goals(self, text: str) -> list[int]:
        return [goal_id for kw, goal_id in self.keywords.items() if kw in text.lower()]

    def _make_links(self, matching_goals: list[int], target_goal: int) -> None:
        if not matching_goals:
            return
        self_children: dict[int, list[GoalId]] = {
            row.raw_id: [e[0] for e in row.edges] for row in self.goaltree.q().rows
        }
        for add_to in matching_goals:
            if target_goal not in self_children[add_to]:
                self.goaltree.accept(ToggleLink(add_to, target_goal, EdgeType.PARENT))

    def q(self) -> RenderResult:
        render_result = self.goaltree.q()
        if not self.back_kw:
            # Fast exit without creating new objects
            return render_result
        rows: list[RenderRow] = [
            replace(
                row,
                attrs=row.attrs
                | (
                    {"Autolink": self.back_kw[int(row.goal_id)]}
                    if row.goal_id in self.back_kw
                    else {}
                ),
            )
            for row in render_result.rows
        ]
        return RenderResult(
            rows,
            select=render_result.select,
            roots=render_result.roots,
            global_opts=render_result.global_opts,
        )

    @staticmethod
    def fake_id(goal_id: GoalId) -> GoalId:
        return -(goal_id + 10) if isinstance(goal_id, int) else goal_id

    @staticmethod
    def export(goals: "AutoLink") -> AutoLinkData:
        return [(goal_id, kw) for goal_id, kw in goals.back_kw.items()]
