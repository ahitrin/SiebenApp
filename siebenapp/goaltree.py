# coding: utf-8
import collections
from typing import Callable, Dict, Optional, List, Set, Any, Tuple

from siebenapp.domain import Graph


class Edge(collections.namedtuple('Edge', 'source target type')):
    TYPE_SOFT = 1
    TYPE_STRONG = 2
    __slots__ = ()


GoalsData = List[Tuple[int, Optional[str], bool]]
EdgesData = List[Tuple[int, int, int]]
OptionsData = List[Tuple[str, int]]


class Goals(Graph):
    def __init__(self, name: str, message_fn: Callable[[str], None] = None) -> None:
        self.goals = {}  # type: Dict[int, Optional[str]]
        self.edges = {}  # type: Dict[int, List[Edge]]
        self.back_edges = {}  # type: Dict[int, List[Edge]]
        self.closed = set()  # type: Set[int]
        self.settings = {
            'selection': 1,
            'previous_selection': 1,
        }  # type: Dict[str, int]
        self.events = collections.deque()  # type: collections.deque
        self.message_fn = message_fn
        self._add_no_link(name)

    def _msg(self, message: str) -> None:
        if self.message_fn:
            self.message_fn(message)

    def _has_link(self, lower: int, upper: int) -> bool:
        return upper in set(x.target for x in self.edges[lower])

    def add(self, name: str, add_to: int = 0, edge_type: int = Edge.TYPE_STRONG) -> bool:
        if add_to == 0:
            add_to = self.settings['selection']
        if add_to in self.closed:
            self._msg("A new subgoal cannot be added to the closed one")
            return False
        next_id = self._add_no_link(name)
        self.toggle_link(add_to, next_id, edge_type)
        return True

    def _add_no_link(self, name: str) -> int:
        next_id = max(list(self.goals.keys()) + [0]) + 1
        self.goals[next_id] = name
        self.edges[next_id] = list()
        self.back_edges[next_id] = list()
        self.events.append(('add', next_id, name, True))
        return next_id

    def select(self, goal_id: int) -> None:
        if goal_id in self.goals and self.goals[goal_id] is not None:
            self.settings['selection'] = goal_id
            self.events.append(('select', goal_id))

    def hold_select(self) -> None:
        self.settings['previous_selection'] = self.settings['selection']
        self.events.append(('hold_select', self.settings['selection']))

    def q(self, keys: str = 'name') -> Dict[int, Any]:
        def sel(x):
            # type: (int) -> Optional[str]
            if x == self.settings['selection']:
                return 'select'
            elif x == self.settings['previous_selection']:
                return 'prev'
            return None

        keys_list = keys.split(',')
        result = dict()  # type: Dict[int, Any]
        for key, name in ((k, n) for k, n in self.goals.items() if n is not None):
            value = {
                'edge': sorted([(x.target, x.type) for x in self.edges[key]]),
                'name': name,
                'open': key not in self.closed,
                'select': sel(key),
                'switchable': self._switchable(key),
            }
            result[key] = {k: v for k, v in value.items() if k in keys_list}
        return result

    def _switchable(self, key: int) -> bool:
        if key in self.closed:
            has_open_parents = any(y for y in self.back_edges[key]
                                   if y.source not in self.closed)
            has_no_parents = not self.back_edges[key]
            return has_open_parents or has_no_parents
        return all(x.target in self.closed for x in self.edges[key])

    def insert(self, name: str) -> None:
        lower = self.settings['previous_selection']
        upper = self.settings['selection']
        if lower == upper:
            self._msg("A new goal can be inserted only between two different goals")
            return
        edge_type = Edge.TYPE_SOFT
        for edge in self.edges[lower]:
            if edge.target == upper:
                edge_type = edge.type
                break
        if self.add(name, lower, edge_type):
            key = len(self.goals)
            self.toggle_link(key, upper, edge_type)
            if self._has_link(lower, upper):
                self.toggle_link(lower, upper, edge_type)

    def rename(self, new_name: str, goal_id: int = 0) -> None:
        if goal_id == 0:
            goal_id = self.settings['selection']
        self.goals[goal_id] = new_name
        self.events.append(('rename', new_name, goal_id))

    def toggle_close(self) -> None:
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

    def _may_be_closed(self) -> bool:
        return all(g.target in self.closed for g in self.edges[self.settings['selection']])

    def _may_be_reopened(self) -> bool:
        parent_edges = self.back_edges[self.settings['selection']]
        return all(g.source not in self.closed for g in parent_edges)

    def delete(self, goal_id: int = 0) -> None:
        if goal_id == 0:
            goal_id = self.settings['selection']
        if goal_id == 1:
            self._msg("Root goal can't be deleted")
            return
        self._delete(goal_id)
        self.select(1)
        self.hold_select()

    def _delete(self, goal_id: int) -> None:
        self.goals[goal_id] = None
        self.closed.add(goal_id)
        next_to_remove = self.edges.pop(goal_id, [])  # type: List[Edge]
        self.back_edges.pop(goal_id, {})
        for key, values in self.edges.items():
            self.edges[key] = [x for x in values if x.target != goal_id]
        for key, values in self.back_edges.items():
            self.back_edges[key] = [x for x in values if x.source != goal_id]
        for next_goal in next_to_remove:
            if not self.back_edges.get(next_goal.target, []):
                self._delete(next_goal.target)
        self.events.append(('delete', goal_id))

    def toggle_link(self, lower: int = 0, upper: int = 0, edge_type: int = Edge.TYPE_SOFT) -> None:
        lower = self.settings['previous_selection'] if lower == 0 else lower
        upper = self.settings['selection'] if upper == 0 else upper
        if lower == upper:
            self._msg("Goal can't be linked to itself")
            return
        if self._has_link(lower, upper):
            current_edge_type = None
            for edge in self.edges[lower]:
                if edge.target == upper:
                    current_edge_type = edge.type
                    break
            if current_edge_type != edge_type:
                self._create_new_link(lower, upper, edge_type)
            self._remove_existing_link(lower, upper, current_edge_type)
        else:
            self._create_new_link(lower, upper, edge_type)

    def _remove_existing_link(self, lower: int, upper: int, edge_type=None) -> None:
        edges_to_upper = len(self.back_edges[upper])
        if edges_to_upper > 1:
            edge = Edge(lower, upper, edge_type)
            self.edges[lower].remove(edge)
            self.back_edges[upper].remove(edge)
            self.events.append(('unlink', lower, upper, edge_type))
        else:
            self._msg("Can't remove the last link")

    def _create_new_link(self, lower: int, upper: int, edge_type: int) -> None:
        if lower in self.closed and upper not in self.closed:
            self._msg("An open goal can't block already closed one")
            return
        front = {upper}  # type: Set[int]
        visited = set()  # type: Set[int]
        total = set()  # type: Set[int]
        while front:
            g = front.pop()
            visited.add(g)
            for e in self.edges[g]:
                total.add(e.target)
                if e not in visited:
                    front.add(e.target)
        if lower not in total:
            edge = Edge(lower, upper, edge_type)
            self.edges[lower].append(edge)
            self.back_edges[upper].append(edge)
            self.events.append(('link', lower, upper, edge.type))
        else:
            self._msg("Circular dependencies between goals are not allowed")

    def verify(self) -> bool:
        assert all(g.target in self.closed for p in self.closed for g in self.edges.get(p, [])), \
            'Open goals could not be blocked by closed ones'

        queue = [1]  # type: List[int]
        visited = set()  # type: Set[int]
        while queue:
            goal = queue.pop()
            queue.extend(g.target for g in self.edges[goal]
                         if g.target not in visited and self.goals[g.target] is not None)
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
        # type: (GoalsData, EdgesData, OptionsData, Callable[[str], None]) -> Goals
        result = Goals('', message_fn)
        result.events.clear()  # remove initial goal
        goals_dict = dict((g[0], g[1]) for g in goals)
        result.goals = dict((i, goals_dict.get(i))
                            for i in range(1, max(goals_dict.keys()) + 1))
        result.closed = set(g[0] for g in goals if not g[2]).union(
            set(k for k, v in result.goals.items() if v is None))
        d = collections.defaultdict(list)  # type: Dict[int, List[Edge]]
        bd = collections.defaultdict(list)  # type: Dict[int, List[Edge]]
        for parent, child, link_type in edges:
            edge = Edge(parent, child, link_type)
            d[parent].append(edge)
            bd[child].append(edge)
        result.edges = dict(d)
        result.back_edges = dict(bd)
        result.edges.update(dict((g, []) for g in result.goals if g not in d))
        result.back_edges.update(dict((g, []) for g in result.goals if g not in bd))
        result.settings.update(settings)
        result.verify()
        return result

    @staticmethod
    def export(goals):
        # type: (Goals) -> Tuple[GoalsData, EdgesData, OptionsData]
        nodes = [(g_id, g_name, g_id not in goals.closed)
                 for g_id, g_name in goals.goals.items()]
        edges = [(parent, child.target, child.type) for parent in goals.edges
                 for child in goals.edges[parent]]
        settings = list(goals.settings.items())
        return nodes, edges, settings
