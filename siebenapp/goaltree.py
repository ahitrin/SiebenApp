# coding: utf-8
import collections
from typing import Callable, Dict, Optional, List, Set, Any, Tuple


class Goals:
    def __init__(self, name, message_fn=None):
        # type: (str, Callable[[str], None]) -> None
        self.goals = {}  # type: Dict[int, Optional[str]]
        self.edges = {}  # type: Dict[int, List[int]]
        self.back_edges = {}  # type: Dict[int, List[int]]
        self.closed = set()  # type: Set[int]
        self.settings = {
            'selection': 1,
            'previous_selection': 1,
        }                   # type: Dict[str, int]
        self.events = collections.deque()  # type: collections.deque
        self.message_fn = message_fn
        self._add_no_link(name)

    def _msg(self, message):
        # type: (str) -> None
        if self.message_fn:
            self.message_fn(message)

    def add(self, name, add_to=0):
        # type: (str, int) -> bool
        if add_to == 0:
            add_to = self.settings['selection']
        if add_to in self.closed:
            self._msg("A new subgoal cannot be added to the closed one")
            return False
        next_id = self._add_no_link(name)
        self.toggle_link(add_to, next_id)
        return True

    def _add_no_link(self, name):
        # type: (str) -> int
        next_id = max(list(self.goals.keys()) + [0]) + 1
        self.goals[next_id] = name
        self.edges[next_id] = list()
        self.back_edges[next_id] = list()
        self.events.append(('add', next_id, name, True))
        return next_id

    def select(self, goal_id):
        # type: (int) -> None
        if goal_id in self.goals and self.goals[goal_id] is not None:
            self.settings['selection'] = goal_id
            self.events.append(('select', goal_id))

    def hold_select(self):
        # type: () -> None
        self.settings['previous_selection'] = self.settings['selection']
        self.events.append(('hold_select', self.settings['selection']))

    def q(self, keys='name'):
        # type: (str) -> Dict[str, Any]
        """Run search query against goaltree state"""

        def sel(x):
            # type: (int) -> Optional[str]
            if x == self.settings['selection']:
                return 'select'
            elif x == self.settings['previous_selection']:
                return 'prev'
            return None

        keys = keys.split(',')
        result = dict()  # type: Dict[str, Any]
        for key, name in ((k, n) for k, n in self.goals.items() if n is not None):
            switchable = (
                    (key not in self.closed and
                     all(x in self.closed for x in self.edges[key])) or
                    (key in self.closed and (not self.back_edges[key] or
                                             any(x for x in self.back_edges[key] if x not in self.closed))))
            value = {
                'edge': sorted(self.edges[key]),
                'name': name,
                'open': key not in self.closed,
                'select': sel(key),
                'switchable': switchable,
            }
            result[key] = {k: v for k, v in value.items() if k in keys}
        return result

    def insert(self, name):
        # type: (str) -> None
        if self.settings['selection'] == self.settings['previous_selection']:
            self._msg("A new goal can be inserted only between two different goals")
            return
        if self.add(name, self.settings['previous_selection']):
            key = len(self.goals)
            self.toggle_link(key, self.settings['selection'])
            if self.settings['selection'] in self.edges[self.settings['previous_selection']]:
                self.toggle_link(self.settings['previous_selection'], self.settings['selection'])

    def rename(self, new_name, goal_id=0):
        # type: (str, int) -> None
        if goal_id == 0:
            goal_id = self.settings['selection']
        self.goals[goal_id] = new_name
        self.events.append(('rename', new_name, goal_id))

    def swap_goals(self):
        # type: () -> None
        first, second = self.settings['selection'], self.settings['previous_selection']
        first_name, second_name = self.goals[first], self.goals[second]
        self.rename(first_name, second)
        self.rename(second_name, first)

    def toggle_close(self):
        # type: () -> None
        if self.settings['selection'] in self.closed:
            if self._may_be_reopened():
                self.closed.remove(self.settings['selection'])
                self.events.append(('toggle_close', True, self.settings['selection']))
            else:
                self._msg("This goal can't be reopened because other subgoals block it")
        else:
            if self._may_be_closed():
                self.closed.add(self.settings['selection'])
                self.events.append(('toggle_close', False, self.settings['selection']))
                self.select(1)
                self.hold_select()
            else:
                self._msg("This goal can't be closed because it have open subgoals")

    def _may_be_closed(self):
        # type: () -> bool
        return all(g in self.closed for g in self.edges[self.settings['selection']])

    def _may_be_reopened(self):
        # type: () -> bool
        parent_goals = self.back_edges[self.settings['selection']]
        return all(g not in self.closed for g in parent_goals)

    def delete(self, goal_id=0):
        # type: (int) -> None
        if goal_id == 0:
            goal_id = self.settings['selection']
        if goal_id == 1:
            self._msg("Root goal can't be deleted")
            return
        self._delete(goal_id)
        self.select(1)
        self.hold_select()

    def _delete(self, goal_id):
        # type: (int) -> None
        self.goals[goal_id] = None
        self.closed.add(goal_id)
        next_to_remove = self.edges.pop(goal_id, {})
        self.back_edges.pop(goal_id, {})
        for key in self.edges:
            if goal_id in self.edges[key]:
                self.edges[key].remove(goal_id)
        for key in self.back_edges:
            if goal_id in self.back_edges[key]:
                self.back_edges[key].remove(goal_id)
        for next_goal in next_to_remove:
            if not self.back_edges.get(next_goal, []):
                self._delete(next_goal)
        self.events.append(('delete', goal_id))

    def toggle_link(self, lower=0, upper=0):
        # type: (int, int) -> None
        lower = self.settings['previous_selection'] if lower == 0 else lower
        upper = self.settings['selection'] if upper == 0 else upper
        if lower == upper:
            self._msg("Goal can't be linked to itself")
            return
        if upper in self.edges[lower]:
            self._remove_existing_link(lower, upper)
        else:
            self._create_new_link(lower, upper)

    def _remove_existing_link(self, lower, upper):
        # type: (int, int) -> None
        edges_to_upper = len(self.back_edges[upper])
        if edges_to_upper > 1:
            self.edges[lower].remove(upper)
            self.back_edges[upper].remove(lower)
            self.events.append(('unlink', lower, upper))
        else:
            self._msg("Can't remove the last link")

    def _create_new_link(self, lower, upper):
        # type: (int, int) -> None
        if lower in self.closed and upper not in self.closed:
            self._msg("An open goal can't block already closed one")
            return
        front, visited, total = {upper}, set(), set()
        while front:
            g = front.pop()
            visited.add(g)
            for e in self.edges[g]:
                total.add(e)
                if e not in visited:
                    front.add(e)
        if lower not in total:
            self.edges[lower].append(upper)
            self.back_edges[upper].append(lower)
            self.events.append(('link', lower, upper))
        else:
            self._msg("Circular dependencies between goals are not allowed")

    def verify(self):
        # type: () -> bool
        assert all(g in self.closed for p in self.closed for g in self.edges.get(p, [])), \
            'Open goals could not be blocked by closed ones'

        queue, visited = [1], set()
        while queue:
            goal = queue.pop()
            queue.extend(g for g in self.edges[goal]
                         if g not in visited and self.goals[g] is not None)
            visited.add(goal)
        assert visited == set(x for x in self.goals if self.goals[x] is not None), \
            'All subgoals must be accessible from the root goal'

        deleted_nodes = [g for g, v in self.goals.items() if v is None]
        assert all(not self.edges.get(n) for n in deleted_nodes), \
            'Deleted goals must have no dependencies'

        assert all(k in self.settings for k in {'selection', 'previous_selection'})

        return True

    @staticmethod
    def build(goals, edges, settings, message_fn=None):
        # type: (List[Tuple[int, str]], List[Tuple[int, int]], List[Tuple[str, int]], Callable[[str], None]) -> Goals
        result = Goals('', message_fn)
        result.events.clear()  # remove initial goal
        goals_dict = dict((g[0], g[1]) for g in goals)
        result.goals = dict((i, goals_dict.get(i))
                            for i in range(1, max(goals_dict.keys()) + 1))
        result.closed = set(g[0] for g in goals if not g[2]).union(
            set(k for k, v in result.goals.items() if v is None))
        d = collections.defaultdict(list)
        bd = collections.defaultdict(list)
        for parent, child in edges:
            d[parent].append(child)
            bd[child].append(parent)
        result.edges = dict(d)
        result.back_edges = dict(bd)
        result.edges.update(dict((g, []) for g in result.goals if g not in d))
        result.back_edges.update(dict((g, []) for g in result.goals if g not in bd))
        result.settings.update(settings)
        result.verify()
        return result

    @staticmethod
    def export(goals):
        # type: (Goals) -> Tuple[List[Tuple[int, str, bool]], List[Tuple[int, int]], List[Tuple[str, int]]]
        nodes = [(g_id, g_name, g_id not in goals.closed)
                 for g_id, g_name in goals.goals.items()]
        edges = [(parent, child) for parent in goals.edges
                 for child in goals.edges[parent]]
        settings = list(goals.settings.items())
        return nodes, edges, settings
