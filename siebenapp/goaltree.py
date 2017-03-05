# coding: utf-8
import collections


class Goals():
    def __init__(self, name):
        self.goals = {}
        self.edges = {}
        self.closed = set()
        self.selection = 1
        self.previous_selection = 1
        self.events = collections.deque()
        self.add(name)

    def add(self, name, add_to=0):
        if add_to == 0:
            add_to = self.selection
        if add_to in self.closed:
            return False
        next_id = max(list(self.goals.keys()) + [0]) + 1
        self.goals[next_id] = name
        self.edges[next_id] = list()
        self.events.append(('add', next_id, name, True))
        self.toggle_link(add_to, next_id)
        self.selection_cache = []
        return True

    def id_mapping(self, goal_id):
        new_id = goal_id % 10
        if len(self.goals) > 10:
            new_id += 10 * ((goal_id - 1) // 10 + 1)
        if len(self.goals) > 90:
            new_id += 100 * ((goal_id - 1) // 100 + 1)
        return new_id

    def _select(self, goal_id):
        self.selection_cache = []
        self.selection = goal_id
        self.events.append(('select', self.selection))

    def select(self, goal_id):
        if goal_id > len(self.goals):
            return
        if self.selection_cache:
            goal_id = 10 * self.selection_cache.pop() + goal_id
        possible_selections = [g for g in self.goals.keys()
                               if self.id_mapping(g) == goal_id]
        if len(possible_selections) == 1:
            if self.goals[possible_selections[0]]:
                self._select(possible_selections[0])
        else:
            self.selection_cache.append(goal_id)

    def hold_select(self):
        self.previous_selection = self.selection
        self.selection_cache = []
        self.events.append(('hold_select', self.selection))

    def all(self, keys='name'):
        keys = keys.split(',')
        result = dict()
        for key, name in ((k, n) for k, n in self.goals.items() if n is not None):
            value = {}
            if 'open' in keys:
                value['open'] = key not in self.closed
            if 'name' in keys:
                value['name'] = name
            if 'edge' in keys:
                value['edge'] = sorted(self.id_mapping(e) for e in self.edges[key])
            if 'select' in keys:
                if key == self.selection:
                    value['select'] = 'select'
                elif key == self.previous_selection:
                    value['select'] = 'prev'
                else:
                    value['select'] = None
            result[self.id_mapping(key)] = value
        return result

    def top(self):
        return set([self.id_mapping(goal) for goal in self.goals
                    if goal not in self.closed and
                        all(g in self.closed for g in self.edges[goal])])

    def insert(self, name):
        self.selection_cache = []
        if self.selection == self.previous_selection:
            return
        if self.add(name, self.previous_selection):
            key = len(self.goals)
            self.toggle_link(key, self.selection)
            if self.selection in self.edges[self.previous_selection]:
                self.toggle_link(self.previous_selection, self.selection)

    def rename(self, new_name, goal_id=0):
        if goal_id == 0:
            goal_id = self.selection
        self.goals[goal_id] = new_name
        self.selection_cache = []
        self.events.append(('rename', new_name, goal_id))

    def swap_goals(self):
        first, second = self.selection, self.previous_selection
        first_name, second_name = self.goals[first], self.goals[second]
        self.rename(first_name, second)
        self.rename(second_name, first)

    def toggle_close(self):
        if self.selection in self.closed:
            parent_goals = [g for g, v in self.edges.items() if self.selection in v]
            if not parent_goals or any(g for g in parent_goals if g not in self.closed):
                self.closed.remove(self.selection)
                self.events.append(('toggle_close', True, self.selection))
        else:
            if all(g in self.closed for g in self.edges[self.selection]):
                self.closed.add(self.selection)
                self.events.append(('toggle_close', False, self.selection))
                self._select(1)
                self.hold_select()
        self.selection_cache = []

    def delete(self, goal_id=0):
        self.selection_cache = []
        if goal_id == 0:
            goal_id = self.selection
        if goal_id == 1:
            return
        self._delete(goal_id)
        self._select(1)
        self.hold_select()

    def _delete(self, goal_id):
        self.goals[goal_id] = None
        self.closed.add(goal_id)
        next_to_remove = self.edges.pop(goal_id)
        for key, values in self.edges.items():
            self.edges[key] = [v for v in values if v != goal_id]
        for next_goal in next_to_remove:
            other_edges = set(e for es in self.edges.values() for e in es)
            if next_goal not in other_edges:
                self._delete(next_goal)
        self.events.append(('delete', goal_id))

    def toggle_link(self, lower=0, upper=0):
        if lower == 0:
            lower = self.previous_selection
        if upper == 0:
            upper = self.selection
        self.selection_cache = []
        if lower == upper:
            return
        if upper in self.edges[lower]:
            # remove existing link unless it's the last one
            edges_to_upper = sum(1 for g in self.goals
                                 if g in self.edges and upper in self.edges[g])
            if edges_to_upper > 1:
                self.edges[lower].remove(upper)
                self.events.append(('unlink', lower, upper))
        else:
            # create a new link unless it breaks validity
            if lower in self.closed and upper not in self.closed:
                return
            front, visited, total = set([upper]), set(), set()
            while front:
                g = front.pop()
                visited.add(g)
                for e in self.edges[g]:
                    total.add(e)
                    if e not in visited:
                        front.add(e)
            if lower not in total:
                self.edges[lower].append(upper)
                self.events.append(('link', lower, upper))

    def verify(self):
        assert all(g in self.closed for p in self.closed for g in self.edges.get(p, [])), \
                'Open goals could not be blocked by closed ones'

        queue, visited = [1], set()
        while queue:
            goal = queue.pop()
            queue.extend(g for g in self.edges[goal]
                           if g not in visited and self.goals[g] is not None)
            visited.add(goal)
        assert visited == set(x for x in self.goals.keys()
                                if self.goals[x] is not None), \
                'All subgoals must be accessible from the root goal'

        deleted_nodes = [g for g, v in self.goals.items() if v is None]
        assert all(not self.edges.get(n) for n in deleted_nodes), \
                'Deleted goals must have no dependencies'

        return True

    @staticmethod
    def build(goals, edges, selection):
        result = Goals('')
        result.events.pop()             # remove initial goal
        goals_dict = dict((g[0], g[1]) for g in goals)
        result.goals = dict((i, goals_dict.get(i))
                            for i in range(1, max(goals_dict.keys()) + 1))
        result.closed = set(g[0] for g in goals if not g[2])
        d = collections.defaultdict(lambda: list())
        for parent, child in edges:
            d[parent].append(child)
        result.edges = dict(d)
        result.edges.update(dict((g, []) for g in result.goals if g not in d))
        selects = dict(selection)
        result.selection = selects.get('selection', 1)
        result.previous_selection = selects.get('previous_selection', 1)
        result.verify()
        return result

    @staticmethod
    def export(goals):
        gs = [(g_id, g_name, g_id not in goals.closed)
            for g_id, g_name in goals.goals.items()]
        es = [(parent, child) for parent in goals.edges
                            for child in goals.edges[parent]]
        sel = [('selection', goals.selection),
            ('previous_selection', goals.previous_selection)]
        return gs, es, sel


class Enumeration():
    proxied = ['add', 'closed', 'delete', 'edges', 'events', 'goals',
               'hold_select', 'insert', 'previous_selection', 'rename',
               'select', 'selection', 'swap_goals', 'toggle_close',
               'toggle_link', 'top', 'verify',
              ]

    @classmethod
    def _id_mapping(self, goals):
        length = len(goals)
        def mapping_fn(goal_id):
            new_id = goal_id % 10
            if length > 10:
                new_id += 10 * ((goal_id - 1) // 10 + 1)
            if length > 90:
                new_id += 100 * ((goal_id - 1) // 100 + 1)
            return new_id
        return mapping_fn

    def __init__(self, goaltree):
        self.goaltree = goaltree

    def all(self, *args, **kwargs):
        result = dict()
        goals = self.goaltree.all(*args, **kwargs)
        mapping = self._id_mapping(goals)
        for old_id, val in goals.items():
            new_id = mapping(old_id)
            result[new_id] = val
        return result

    def __getattribute__(self, attr):
        proxied = object.__getattribute__(self, 'proxied')
        if attr in proxied:
            return getattr(object.__getattribute__(self, "goaltree"), attr)
        else:
            return object.__getattribute__(self, attr)
