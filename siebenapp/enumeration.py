import math
from typing import List, Dict, Tuple, Any, Callable, Union

from siebenapp.domain import Graph, EdgeType
from siebenapp.goaltree import Goals
from siebenapp.zoom import Zoom


class Enumeration(Graph):
    overriden = [
        "add",
        "_goal_filter",
        "_id_mapping",
        "_update_mapping",
        "goaltree",
        "hold_select",
        "insert",
        "next_view",
        "q",
        "rename",
        "select",
        "selection_cache",
        "view",
        "views",
    ]

    views = {"open": "top", "top": "full", "full": "open"}

    def __init__(self, goaltree: Union[Goals, Zoom]) -> None:
        self.goaltree = goaltree
        self.selection_cache: List[int] = []
        self.view: str = "open"
        self._update_mapping()

    def _update_mapping(self) -> None:
        if self.view == "top":
            goals = {
                k
                for k, v in self.goaltree.q(keys="open,switchable").items()
                if v["open"] and v["switchable"]
            }
            if goals and self.settings["selection"] not in goals:
                self.goaltree.select(min(goals))
            if goals and self.settings["previous_selection"] not in goals:
                self.goaltree.hold_select()
            self._goal_filter = goals
        elif self.view == "open":
            self._goal_filter = {
                k for k, v in self.goaltree.q(keys="open").items() if v["open"]
            }
        else:
            self._goal_filter = dict(self.goaltree.q())

    def _id_mapping(
        self, keys: str = "name"
    ) -> Tuple[Dict[int, Any], Callable[[int], int]]:
        goals = self.goaltree.q(keys)
        goals = {k: v for k, v in goals.items() if k in self._goal_filter}
        if self.view == "top":
            for attrs in goals.values():
                if "edge" in attrs:
                    attrs["edge"] = []
        elif self.view == "open":
            for attrs in goals.values():
                if "edge" in attrs:
                    attrs["edge"] = [
                        e for e in attrs["edge"] if e[0] in self._goal_filter
                    ]

        m = {g: i + 1 for i, g in enumerate(sorted(g for g in goals if g > 0))}
        length = len(m)

        def mapping_fn(goal_id: int) -> int:
            if goal_id < 0:
                return goal_id
            goal_id = m[goal_id]
            new_id = goal_id % 10
            if length > 10:
                new_id += 10 * ((goal_id - 1) // 10 + 1)
            if length > 90:
                new_id += 100 * ((goal_id - 1) // 100 + 1)
            if length > 900:
                new_id += 1000 * ((goal_id - 1) // 1000 + 1)
            return new_id

        return goals, mapping_fn

    def add(self, name: str, add_to: int = 0, edge_type: EdgeType = EdgeType.PARENT) -> bool:
        return self.goaltree.add(name, add_to, edge_type)

    def insert(self, name: str) -> None:
        self.goaltree.insert(name)

    def rename(self, new_name: str, goal_id: int = 0) -> None:
        self.goaltree.rename(new_name, goal_id)

    def q(self, keys: str = "name") -> Dict[int, Any]:
        self._update_mapping()
        result: Dict[int, Any] = dict()
        goals, mapping = self._id_mapping(keys)
        for old_id, val in goals.items():
            new_id = mapping(old_id)
            result[new_id] = dict((k, v) for k, v in val.items() if k != "edge")
            if "edge" in val:
                result[new_id]["edge"] = [
                    (mapping(edge[0]), edge[1]) for edge in val["edge"]
                ]
        return result

    def select(self, goal_id: int) -> None:
        self._update_mapping()
        goals, mapping = self._id_mapping()
        if goal_id >= 10:
            self.selection_cache = []
        if self.selection_cache:
            goal_id = 10 * self.selection_cache.pop() + goal_id
            if goal_id > max(mapping(k) for k in goals.keys()):
                goal_id %= int(pow(10, int(math.log(goal_id, 10))))
        possible_selections: List[int] = [g for g in goals if mapping(g) == goal_id]
        if len(possible_selections) == 1:
            self.goaltree.select(possible_selections[0])
            self.selection_cache = []
        else:
            self.selection_cache.append(goal_id)

    def hold_select(self) -> None:
        self.goaltree.hold_select()

    def next_view(self) -> None:
        self.view = self.views[self.view]
        self._update_mapping()
        self.selection_cache.clear()

    def __getattribute__(self, attr):
        overriden = object.__getattribute__(self, "overriden")
        if attr in overriden:
            return object.__getattribute__(self, attr)
        goaltree = object.__getattribute__(self, "goaltree")
        return getattr(goaltree, attr)
