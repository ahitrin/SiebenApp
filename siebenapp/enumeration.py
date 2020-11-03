import collections
import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Any, Set, Iterable

from siebenapp.domain import Graph, Command, HoldSelect, Select


@dataclass(frozen=True)
class ToggleSwitchableView(Command):
    """Switch between "only switchable goals" and "all goals" views"""


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


class SwitchableView(Graph):
    """Non-persistent layer that allows to
    show only switchable goals"""

    def __init__(self, goaltree: Graph):
        super().__init__()
        self.goaltree = goaltree
        self._only_switchable: bool = False

    def accept(self, command: Command) -> None:
        if isinstance(command, ToggleSwitchableView):
            self._only_switchable = not self._only_switchable
            if not self._only_switchable:
                return
            ids = [
                k for k, v in self.goaltree.q("switchable").items() if v["switchable"]
            ]
            if ids and self.goaltree.settings("selection") not in ids:
                self.goaltree.accept(Select(min(ids)))
            if ids and self.goaltree.settings("previous_selection") not in ids:
                self.goaltree.accept(HoldSelect())
        else:
            self.goaltree.accept(command)

    def events(self) -> collections.deque:
        return self.goaltree.events()

    def settings(self, key: str) -> int:
        return self.goaltree.settings(key)

    def q(self, keys: str = "name") -> Dict[int, Any]:
        skip_switchable = "switchable" not in keys
        if skip_switchable:
            keys = ",".join([keys, "switchable"])
        goals = self.goaltree.q(keys)
        if self._only_switchable:
            goals = {k: v for k, v in goals.items() if v["switchable"]}
            for v in goals.values():
                if "edge" in v:
                    v.pop("edge")
        if skip_switchable:
            for v in goals.values():
                v.pop("switchable")
        return goals


class Enumeration(Graph):
    def __init__(self, goaltree: Graph) -> None:
        super().__init__()
        self.goaltree = goaltree
        self.selection_cache: List[int] = []
        self._top: bool = False
        self._goal_filter: Set[int] = set()
        self._update_mapping()

    def _update_mapping(self, clear_cache: bool = False) -> None:
        original_mapping = self.goaltree.q().keys()
        if self._top:
            goals = {
                k
                for k, v in self.goaltree.q(keys="switchable").items()
                if v["switchable"] and k in original_mapping
            }
            if goals and self.goaltree.settings("selection") not in goals:
                self.goaltree.accept(Select(min(goals)))
            if goals and self.goaltree.settings("previous_selection") not in goals:
                self.accept(HoldSelect())
            self._goal_filter = goals
        else:
            self._goal_filter = set(original_mapping)
        if clear_cache:
            self.selection_cache.clear()

    def _id_mapping(
        self, keys: str = "name"
    ) -> Tuple[Dict[int, Any], BidirectionalIndex]:
        goals = self.goaltree.q(keys)
        goals = {k: v for k, v in goals.items() if k in self._goal_filter}
        if self._top:
            for attrs in goals.values():
                if "edge" in attrs:
                    attrs["edge"] = []

        return goals, BidirectionalIndex(goals)

    def accept(self, command: Command) -> None:
        if isinstance(command, Select):
            self._select(command)
        elif isinstance(command, ToggleSwitchableView):
            self._top = not self._top
            self._update_mapping(clear_cache=True)
        else:
            self.goaltree.accept(command)

    def events(self) -> collections.deque:
        return self.goaltree.events()

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

    def _select(self, command: Select):
        self._update_mapping()
        goal_id = command.goal_id
        goals, index = self._id_mapping()
        if goal_id >= 10:
            self.selection_cache = []
        if self.selection_cache:
            goal_id = 10 * self.selection_cache.pop() + goal_id
            if goal_id > max(index.forward(k) for k in goals.keys()):
                goal_id %= int(pow(10, int(math.log(goal_id, 10))))
        original_id = index.backward(goal_id)
        if original_id != BidirectionalIndex.NOT_FOUND:
            self.goaltree.accept(Select(original_id))
            self.selection_cache = []
        else:
            self.selection_cache.append(goal_id)
