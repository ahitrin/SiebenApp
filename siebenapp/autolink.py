from dataclasses import dataclass
from typing import Dict, Any, List, Union, Tuple, Optional

from siebenapp.domain import (
    Graph,
    Command,
    with_key,
    EdgeType,
    ToggleClose,
    Add,
    ToggleLink,
    Insert,
    Rename,
    Delete,
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
        selected_id = self.settings("selection")
        if selected_id in self.goaltree.closed:
            self.error("Autolink cannot be set for closed goals")
            return
        if selected_id == Goals.ROOT_ID:
            self.error("Autolink cannot be set for the root goal")
            return
        keyword = command.keyword.lower().strip()
        if selected_id in self.back_kw:
            self.keywords.pop(self.back_kw[selected_id])
            self.back_kw.pop(selected_id)
            self.events().append(("remove_autolink", selected_id))
        if keyword in self.keywords:
            old_id = self.keywords.pop(keyword)
            self.back_kw.pop(old_id)
            self.events().append(("remove_autolink", old_id))
        if not keyword:
            # empty keyword? exit right now
            return
        self.keywords[keyword] = selected_id
        self.back_kw[selected_id] = keyword
        self.events().append(("add_autolink", selected_id, keyword))

    def accept_ToggleClose(self, command: ToggleClose) -> None:
        selected_id = self.settings("selection")
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
        matching = self._find_matching_goals(command.name)
        ids_before = set(self.goaltree.goals.keys())
        self.goaltree.accept(command)
        ids_after = set(self.goaltree.goals.keys())
        ids_diff = ids_after.difference(ids_before)
        if ids_diff:
            added_id = ids_diff.pop()
            self._make_links(matching, added_id)

    def accept_Rename(self, command: Rename) -> None:
        matching = self._find_matching_goals(command.new_name)
        self.goaltree.accept(command)
        selected_id = command.goal_id or self.settings("selection")
        self._make_links(matching, selected_id)

    def accept_Delete(self, command: Delete) -> None:
        selected_id = command.goal_id or self.settings("selection")
        self.goaltree.accept(command)
        if selected_id in self.back_kw:
            added_kw = self.back_kw.pop(selected_id)
            self.keywords.pop(added_kw)
            self.events().append(("remove_autolink", selected_id))

    def _find_matching_goals(self, text: str) -> List[int]:
        return [goal_id for kw, goal_id in self.keywords.items() if kw in text.lower()]

    def _make_links(self, matching_goals: List[int], target_goal: int) -> None:
        if not matching_goals:
            return
        self_children: Dict[int, List[int]] = {
            goal_id: [e[0] for e in attrs["edge"]]
            for goal_id, attrs in self.goaltree.q("edge").items()
        }
        for add_to in matching_goals:
            if target_goal not in self_children[add_to]:
                self.goaltree.accept(ToggleLink(add_to, target_goal, EdgeType.BLOCKER))

    @with_key("edge")
    def q(self, keys: str = "name") -> Dict[int, Any]:
        goals = self.goaltree.q(keys)
        new_goals: Dict[int, Any] = dict(goals)
        for keyword, goal_id in self.keywords.items():
            pseudo_id = -(goal_id + 10)
            for real_goal, attrs in goals.items():
                real_edges = attrs.pop("edge")
                new_edges = [
                    e if e[0] != goal_id else (pseudo_id, e[1]) for e in real_edges
                ]
                attrs["edge"] = new_edges
                new_goals[real_goal] = attrs
            pseudo_goal: Dict[str, Any] = {"edge": [(goal_id, EdgeType.PARENT)]}
            if "name" in keys:
                pseudo_goal["name"] = f"Autolink: '{keyword}'"
            if "open" in keys:
                pseudo_goal["open"] = True
            if "select" in keys:
                pseudo_goal["select"] = None
            if "switchable" in keys:
                pseudo_goal["switchable"] = False
            new_goals[pseudo_id] = pseudo_goal
        return new_goals

    @staticmethod
    def export(goals: "AutoLink") -> AutoLinkData:
        return [(goal_id, kw) for goal_id, kw in goals.back_kw.items()]
