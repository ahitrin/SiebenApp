from dataclasses import dataclass
from typing import Dict, Any, List, Union, Tuple, Optional, Set

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
)
from siebenapp.goaltree import Goals


@dataclass(frozen=True)
class ToggleAutoLink(Command):
    keyword: str


AutoLinkData = List[Tuple[int, str]]


class AutoLink(Graph):
    def __init__(self, goals: Graph, data: Optional[AutoLinkData] = None):
        super(AutoLink, self).__init__(goals)
        self.keywords: Dict[str, int] = {}
        self.back_kw: Dict[int, str] = {}
        if data:
            for goal_id, keyword in data:
                self.keywords[keyword] = goal_id
                self.back_kw[goal_id] = keyword

    def accept_ToggleAutoLink(self, command: ToggleAutoLink) -> None:
        selected_id: int = self.settings("selection")
        if selected_id in self.goaltree.closed:
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

    def _autolink_new_goal(self, command: Union[Add, Insert]) -> None:
        matching: List[int] = self._find_matching_goals(command.name)
        ids_before: Set[int] = set(self.goaltree.goals.keys())
        self.goaltree.accept(command)
        ids_after: Set[int] = set(self.goaltree.goals.keys())
        ids_diff: Set[int] = ids_after.difference(ids_before)
        if ids_diff:
            added_id: int = ids_diff.pop()
            self._make_links(matching, added_id)

    def accept_Rename(self, command: Rename) -> None:
        matching: List[int] = self._find_matching_goals(command.new_name)
        self.goaltree.accept(command)
        selected_id: int = command.goal_id or self.settings("selection")
        self._make_links(matching, selected_id)

    def accept_Delete(self, command: Delete) -> None:
        selected_id: int = command.goal_id or self.settings("selection")
        edges: Dict[int, Any] = self.goaltree.q().slice("edge")
        goals_to_check: List[int] = [selected_id]
        while goals_to_check:
            goal_id: int = goals_to_check.pop()
            goals_to_check.extend(
                e[0] for e in edges[goal_id]["edge"] if e[1] == EdgeType.PARENT
            )
            if goal_id in self.back_kw:
                added_kw: str = self.back_kw.pop(goal_id)
                self.keywords.pop(added_kw)
                self.events().append(("remove_autolink", goal_id))
        self.goaltree.accept(command)

    def _find_matching_goals(self, text: str) -> List[int]:
        return [goal_id for kw, goal_id in self.keywords.items() if kw in text.lower()]

    def _make_links(self, matching_goals: List[int], target_goal: int) -> None:
        if not matching_goals:
            return
        self_children: Dict[int, List[int]] = {
            goal_id: [e[0] for e in attrs["edge"]]
            for goal_id, attrs in self.goaltree.q().slice("edge").items()
        }
        for add_to in matching_goals:
            if target_goal not in self_children[add_to]:
                self.goaltree.accept(ToggleLink(add_to, target_goal, EdgeType.BLOCKER))

    def q(self) -> RenderResult:
        goals: Dict[GoalId, Any] = self.goaltree.q().slice(
            "name,open,switchable,edge,select"
        )
        new_goals: Dict[GoalId, Any] = {k: v for k, v in goals.items()}
        for keyword, goal_id in self.keywords.items():
            pseudo_id: int = -(goal_id + 10)
            for real_goal, attrs in goals.items():
                real_edges: List[Tuple[int, EdgeType]] = attrs.pop("edge")
                new_edges: List[Tuple[int, EdgeType]] = [
                    e if e[0] != goal_id else (pseudo_id, e[1]) for e in real_edges
                ]
                attrs["edge"] = new_edges
                new_goals[real_goal] = attrs
            pseudo_goal: Dict[str, Any] = {
                "edge": [(goal_id, EdgeType.PARENT)],
                "name": f"Autolink: '{keyword}'",
                "open": True,
                "select": None,
                "switchable": False,
            }
            new_goals[pseudo_id] = pseudo_goal
        return RenderResult(new_goals)

    @staticmethod
    def export(goals: "AutoLink") -> AutoLinkData:
        return [(goal_id, kw) for goal_id, kw in goals.back_kw.items()]
