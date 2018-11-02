import math
from typing import List, Dict, Tuple, Any, Callable, Union

from siebenapp.domain import Graph
from siebenapp.goaltree import Goals
from siebenapp.zoom import Zoom


class Enumeration(Graph):
    overriden = ['_goal_filter', '_id_mapping', '_update_mapping', 'q',
                 'goaltree', 'next_view', 'select', 'selection_cache', 'view',
                 'views']

    views = {'open': 'top', 'top': 'full', 'full': 'open'}

    def __init__(self, goaltree):
        # type: (Union[Goals, Zoom]) -> None
        self.goaltree = goaltree
        self.selection_cache = []  # type: List[int]
        self.view = 'open'  # type: str
        self._update_mapping()

    def _update_mapping(self):
        # type: () -> None
        if self.view == 'top':
            goals = {k for k, v in self.goaltree.q(keys='open,switchable').items()
                     if v['open'] and v['switchable']}
            if goals and self.settings['selection'] not in goals:
                self.goaltree.select(min(goals))
            if goals and self.settings['previous_selection'] not in goals:
                self.goaltree.hold_select()
            self._goal_filter = goals
        elif self.view == 'open':
            self._goal_filter = {k for k, v in self.goaltree.q(keys='open').items() if v['open']}
        else:
            self._goal_filter = {g for g in self.goaltree.q()}

    def _id_mapping(self, keys='name'):
        # type: (str) -> Tuple[Dict[str, Any], Callable[[int], int]]
        goals = self.goaltree.q(keys)
        goals = {k: v for k, v in goals.items() if k in self._goal_filter}
        if self.view == 'top':
            for attrs in goals.values():
                if 'edge' in attrs:
                    attrs['edge'] = []
        elif self.view == 'open':
            for attrs in goals.values():
                if 'edge' in attrs:
                    attrs['edge'] = [e for e in attrs['edge'] if e[0] in self._goal_filter]

        m = {g: i + 1 for i, g in enumerate(sorted(g for g in goals if g > 0))}
        length = len(m)

        def mapping_fn(goal_id):
            # type: (int) -> int
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

    def q(self, keys: str = 'name') -> Dict[int, Any]:
        self._update_mapping()
        result = dict()  # type: Dict[int, Any]
        goals, mapping = self._id_mapping(keys)
        for old_id, val in goals.items():
            new_id = mapping(old_id)
            result[new_id] = dict((k, v) for k, v in val.items() if k != 'edge')
            if 'edge' in val:
                result[new_id]['edge'] = [(mapping(edge[0]), edge[1]) for edge in val['edge']]
        return result

    def select(self, goal_id):
        # type: (int) -> None
        self._update_mapping()
        goals, mapping = self._id_mapping()
        if goal_id >= 10:
            self.selection_cache = []
        if self.selection_cache:
            goal_id = 10 * self.selection_cache.pop() + goal_id
            if goal_id > max(mapping(k) for k in goals.keys()):
                goal_id %= int(pow(10, int(math.log(goal_id, 10))))
        possible_selections = [g for g in goals if mapping(g) == goal_id]  # type: List[int]
        if len(possible_selections) == 1:
            self.goaltree.select(possible_selections[0])
            self.selection_cache = []
        else:
            self.selection_cache.append(goal_id)

    def next_view(self):
        # type: () -> None
        self.view = self.views[self.view]
        self._update_mapping()
        self.selection_cache.clear()

    def __getattribute__(self, attr):
        overriden = object.__getattribute__(self, 'overriden')
        goaltree = object.__getattribute__(self, 'goaltree')
        if attr in overriden:
            return object.__getattribute__(self, attr)
        return getattr(goaltree, attr)
