from dataclasses import dataclass
from typing import Dict, Any

from siebenapp.domain import (
    Graph,
    Command,
    with_key,
    EdgeType,
    ToggleClose,
    Add,
    ToggleLink,
)
from siebenapp.goaltree import Goals


@dataclass(frozen=True)
class ToggleAutoLink(Command):
    keyword: str


class AutoLink(Graph):
    def __init__(self, goals: Graph):
        super(AutoLink, self).__init__(goals)
        self.keywords: Dict[str, int] = {}
        self.back_kw: Dict[int, str] = {}

    def accept_ToggleAutoLink(self, command: ToggleAutoLink):
        selected_id = self.settings("selection")
        if selected_id in self.goaltree.closed:
            self.goaltree._msg("Autolink cannot be set for closed goals")
            return
        if selected_id == Goals.ROOT_ID:
            self.goaltree._msg("Autolink cannot be set for the root goal")
            return
        keyword = command.keyword.lower()
        if selected_id in self.back_kw:
            if not keyword:
                # remove
                self.keywords.pop(self.back_kw[selected_id])
                self.back_kw.pop(selected_id)
                return
        self.keywords[keyword] = selected_id
        self.back_kw[selected_id] = keyword

    def accept_ToggleClose(self, command: ToggleClose):
        selected_id = self.settings("selection")
        if selected_id in self.back_kw:
            self.keywords.pop(self.back_kw[selected_id])
            self.back_kw.pop(selected_id)

    def accept_Add(self, command: Add):
        matching = [
            goal_id for kw, goal_id in self.keywords.items() if kw in command.name
        ]
        ids_before = set(self.goaltree.goals.keys())
        self.goaltree.accept(command)
        ids_after = set(self.goaltree.goals.keys())
        ids_diff = ids_after.difference(ids_before)
        if not matching or not ids_diff:
            return
        added_id = ids_diff.pop()
        add_to = matching.pop(0)
        self.goaltree.accept(ToggleLink(add_to, added_id, EdgeType.BLOCKER))

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
