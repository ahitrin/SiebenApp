import collections
import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Any, Set, Iterable

from siebenapp.domain import Graph, Command, HoldSelect, Select


@dataclass(frozen=True)
class ToggleOpenView(Command):
    """Switch between "only open goals" and "all goals" views"""


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


class OpenView(Graph):
    """Non-persistent view layer that allows to switch
    between only-open and all goals"""

    def __init__(self, goaltree: Graph):
        super().__init__()
        self.goaltree = goaltree
        self._open: bool = True

    def accept(self, command: Command) -> None:
        if isinstance(command, ToggleOpenView):
            self._open = not self._open
        else:
            self.goaltree.accept(command)

    def events(self) -> collections.deque:
        return self.goaltree.events()

    def q(self, keys: str = "name") -> Dict[int, Any]:
        skip_open = "open" not in keys
        if skip_open:
            keys = ",".join([keys, "open"])
        goals = self.goaltree.q(keys)
        result: Dict[int, Any] = {
            k: {} for k, v in goals.items() if not self._open or v["open"]
        }
        for goal_id in result:
            val = goals[goal_id]
            result[goal_id] = dict(
                (k, v) for k, v in val.items() if k not in ["edge", "open"]
            )
            if not skip_open:
                result[goal_id]["open"] = val["open"]
            if "edge" in val:
                result[goal_id]["edge"] = [
                    (edge[0], edge[1]) for edge in val["edge"] if edge[0] in result
                ]
        return result


class Enumeration(Graph):
    def __init__(self, goaltree: Graph) -> None:
        super().__init__()
        self.goaltree = goaltree
        self.selection_cache: List[int] = []
        self._top: bool = False
        self._goal_filter: Set[int] = set()
        self._update_mapping()

    def _update_mapping(self, clear_cache: bool = False) -> None:
        self._goal_filter = self._update_top_mapping(self._update_open_mapping())
        if clear_cache:
            self.selection_cache.clear()

    def _update_open_mapping(self) -> Set[int]:
        return set(self.goaltree.q().keys())

    def _update_top_mapping(self, original_mapping: Set[int]) -> Set[int]:
        if not self._top:
            return set(original_mapping)
        goals = {
            k
            for k, v in self.goaltree.q(keys="open,switchable").items()
            if v["open"] and v["switchable"] and k in original_mapping
        }
        if goals and self.goaltree.settings("selection") not in goals:
            self.goaltree.accept(Select(min(goals)))
        if goals and self.goaltree.settings("previous_selection") not in goals:
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
