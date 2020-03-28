import math
from typing import List, Dict, Tuple, Any, Union, Set, Iterable

from siebenapp.domain import (
    Graph,
    EdgeType,
    Command,
    HoldSelect,
    ToggleClose,
)
from siebenapp.goaltree import Goals
from siebenapp.zoom import Zoom


class BidirectionalIndex:
    NOT_FOUND = -2

    def __init__(self, goals: Iterable[int]):
        self.m = {g: i + 1 for i, g in enumerate(sorted(g for g in goals if g > 0))}
        self.length = len(self.m)

    def forward(self, goal_id: int) -> int:
        if goal_id < 0:
            return goal_id
        goal_id = self.m[goal_id]
        new_id = goal_id % 10
        if self.length > 10:
            new_id += 10 * ((goal_id - 1) // 10 + 1)
        if self.length > 90:
            new_id += 100 * ((goal_id - 1) // 100 + 1)
        if self.length > 900:
            new_id += 1000 * ((goal_id - 1) // 1000 + 1)
        return new_id

    def backward(self, goal_id: int) -> int:
        possible_selections: List[int] = [
            g for g in self.m if self.forward(g) == goal_id
        ]
        if len(possible_selections) == 1:
            return possible_selections[0]
        return BidirectionalIndex.NOT_FOUND


class Enumeration(Graph):
    overriden = [
        "accept",
        "_goal_filter",
        "_id_mapping",
        "_update_mapping",
        "_update_top_mapping",
        "_update_open_mapping",
        "goaltree",
        "insert",
        "next_view",
        "q",
        "rename",
        "select",
        "selection_cache",
        "view_title",
        "_views",
        "_open",
        "_top",
        "_labels",
    ]

    _views = {
        (True, True): (True, True),
        (True, False): (False, True),
        (False, True): (False, False),
        (False, False): (True, False),
    }  # (_open, _top) -> (_open, _top)
    _labels = {
        (True, True): "open + top",
        (True, False): "open",
        (False, True): "top",
        (False, False): "full",
    }

    def __init__(self, goaltree: Union[Goals, Zoom]) -> None:
        self.goaltree = goaltree
        self.selection_cache: List[int] = []
        self._open: bool = True
        self._top: bool = False
        self._goal_filter: Set[int] = set()
        self._update_mapping()

    def view_title(self):
        return self._labels[self._open, self._top]

    def _update_mapping(self) -> None:
        self._goal_filter = self._update_top_mapping(self._update_open_mapping())

    def _update_open_mapping(self) -> Set[int]:
        if not self._open:
            return set(self.goaltree.q().keys())
        return {k for k, v in self.goaltree.q(keys="open").items() if v["open"]}

    def _update_top_mapping(self, original_mapping: Set[int]) -> Set[int]:
        if not self._top:
            return set(original_mapping)
        goals = {
            k
            for k, v in self.goaltree.q(keys="open,switchable").items()
            if v["open"] and v["switchable"] and k in original_mapping
        }
        if goals and self.settings["selection"] not in goals:
            self.goaltree.select(min(goals))
        if goals and self.settings["previous_selection"] not in goals:
            self.accept(HoldSelect())
        return goals

    def _id_mapping(
        self, keys: str = "name"
    ) -> Tuple[Dict[int, Any], BidirectionalIndex]:
        goals = self.goaltree.q(keys)
        goals = {k: v for k, v in goals.items() if k in self._goal_filter}
        if self._top:
            for attrs in goals.values():
                if "edge" in attrs:
                    attrs["edge"] = []
        elif self._open:
            for attrs in goals.values():
                if "edge" in attrs:
                    attrs["edge"] = [
                        e for e in attrs["edge"] if e[0] in self._goal_filter
                    ]

        return goals, BidirectionalIndex(goals)

    def accept(self, command: Command) -> None:
        self.goaltree.accept(command)

    def insert(self, name: str) -> None:
        self.goaltree.insert(name)

    def rename(self, new_name: str, goal_id: int = 0) -> None:
        self.goaltree.rename(new_name, goal_id)

    def q(self, keys: str = "name") -> Dict[int, Any]:
        self._update_mapping()
        result: Dict[int, Any] = dict()
        goals, index = self._id_mapping(keys)
        for old_id, val in goals.items():
            new_id = index.forward(old_id)
            result[new_id] = dict((k, v) for k, v in val.items() if k != "edge")
            if "edge" in val:
                result[new_id]["edge"] = [
                    (index.forward(edge[0]), edge[1]) for edge in val["edge"]
                ]
        return result

    def select(self, goal_id: int) -> None:
        self._update_mapping()
        goals, index = self._id_mapping()
        if goal_id >= 10:
            self.selection_cache = []
        if self.selection_cache:
            goal_id = 10 * self.selection_cache.pop() + goal_id
            if goal_id > max(index.forward(k) for k in goals.keys()):
                goal_id %= int(pow(10, int(math.log(goal_id, 10))))
        original_id = index.backward(goal_id)
        if original_id != BidirectionalIndex.NOT_FOUND:
            self.goaltree.select(original_id)
            self.selection_cache = []
        else:
            self.selection_cache.append(goal_id)

    def next_view(self) -> None:
        self._open, self._top = self._views[self._open, self._top]
        self._update_mapping()
        self.selection_cache.clear()

    def __getattribute__(self, attr):
        overriden = object.__getattribute__(self, "overriden")
        if attr in overriden:
            return object.__getattribute__(self, attr)
        goaltree = object.__getattribute__(self, "goaltree")
        return getattr(goaltree, attr)
