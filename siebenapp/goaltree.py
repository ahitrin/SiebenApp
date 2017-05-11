# coding: utf-8
import collections


class Goals:
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
        self._update_top()
        return True

    def select(self, goal_id):
        if goal_id in self.goals and self.goals[goal_id] is not None:
            self.selection = goal_id
            self.events.append(('select', self.selection))

    def hold_select(self):
        self.previous_selection = self.selection
        self.events.append(('hold_select', self.selection))

    def all(self, keys='name'):
        def sel(x):
            if x == self.selection:
                return 'select'
            elif x == self.previous_selection:
                return 'prev'
            return None
        keys = keys.split(',')
        result = dict()
        for key, name in ((k, n) for k, n in self.goals.items() if n is not None):
            value = {
                'edge': sorted(self.edges[key]),
                'name': name,
                'open': key not in self.closed,
                'select': sel(key),
                'top': key in self._top,
            }
            result[key] = {k: v for k, v in value.items() if k in keys}
        return result

    def _update_top(self):
        self._top = set([goal for goal in self.goals
                         if goal not in self.closed and
                         all(g in self.closed for g in self.edges[goal])])

    def insert(self, name):
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
        self.events.append(('rename', new_name, goal_id))

    def swap_goals(self):
        first, second = self.selection, self.previous_selection
        first_name, second_name = self.goals[first], self.goals[second]
        self.rename(first_name, second)
        self.rename(second_name, first)
        self._update_top()

    def toggle_close(self):
        if self.selection in self.closed:
            if self._may_be_reopened():
                self.closed.remove(self.selection)
                self.events.append(('toggle_close', True, self.selection))
        else:
            if self._may_be_closed():
                self.closed.add(self.selection)
                self.events.append(('toggle_close', False, self.selection))
                self.select(1)
                self.hold_select()
        self._update_top()

    def _may_be_closed(self):
        return all(g in self.closed for g in self.edges[self.selection])

    def _may_be_reopened(self):
        parent_goals = [g for g, v in self.edges.items() if self.selection in v]
        return all(g not in self.closed for g in parent_goals)

    def delete(self, goal_id=0):
        if goal_id == 0:
            goal_id = self.selection
        if goal_id == 1:
            return
        self._delete(goal_id)
        self.select(1)
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
        self._update_top()

    def toggle_link(self, lower=0, upper=0):
        if lower == 0:
            lower = self.previous_selection
        if upper == 0:
            upper = self.selection
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
                self.events.append(('link', lower, upper))
        self._update_top()

    def verify(self):
        assert all(g in self.closed for p in self.closed for g in self.edges.get(p, [])), \
            'Open goals could not be blocked by closed ones'

        assert all(k not in self._top for k, v in self.goals.items() if v is None), \
            'Deleted goals must not be considered as top'

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
        result.events.clear()  # remove initial goal
        goals_dict = dict((g[0], g[1]) for g in goals)
        result.goals = dict((i, goals_dict.get(i))
                            for i in range(1, max(goals_dict.keys()) + 1))
        result.closed = set(g[0] for g in goals if not g[2]).union(
            set(k for k, v in result.goals.items() if v is None))
        d = collections.defaultdict(lambda: list())
        for parent, child in edges:
            d[parent].append(child)
        result.edges = dict(d)
        result.edges.update(dict((g, []) for g in result.goals if g not in d))
        selects = dict(selection)
        result.selection = selects.get('selection', 1)
        result.previous_selection = selects.get('previous_selection', 1)
        result._update_top()
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


class Enumeration:
    proxied = ['add', 'closed', 'delete', 'edges', 'events', 'goals',
               'hold_select', 'insert', 'previous_selection', 'rename',
               'selection', 'swap_goals', 'toggle_close', 'toggle_link',
               'verify',
               ]

    views = {'open': 'top', 'top': 'full', 'full': 'open'}

    def __init__(self, goaltree):
        self.goaltree = goaltree
        self.selection_cache = []
        self.view = 'open'
        self._update_mapping()

    def _update_mapping(self):
        if self.view == 'top':
            goals = {k for k, v in self.goaltree.all(keys='top').items() if v['top']}
            if self.goaltree.selection not in goals:
                self.goaltree.select(min(goals))
            if self.goaltree.previous_selection not in goals:
                self.goaltree.hold_select()
            self._goal_filter = goals
        else:
            self._goal_filter = {g for g in self.goaltree.all()}

    def _id_mapping(self, *args, **kwargs):
        goals = self.goaltree.all(*args, **kwargs)
        if self.view == 'top':
            goals = {k:v for k, v in goals.items() if k in self._goal_filter}
            for attrs in goals.values():
                if 'edge' in attrs:
                    attrs['edge'] = []

        m = {g: i + 1 for i, g in enumerate(sorted(goals))}
        length = len(m)

        def mapping_fn(goal_id):
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

    def all(self, *args, **kwargs):
        result = dict()
        goals, mapping = self._id_mapping(*args, **kwargs)
        for old_id, val in goals.items():
            new_id = mapping(old_id)
            result[new_id] = dict((k, v) for k, v in val.items() if k != 'edge')
            if 'edge' in val:
                result[new_id]['edge'] = [mapping(goal_id) for goal_id in val['edge']]
        return result

    def select(self, goal_id):
        goals, mapping = self._id_mapping()
        if self.selection_cache:
            goal_id = 10 * self.selection_cache.pop() + goal_id
        possible_selections = [g for g in goals if mapping(g) == goal_id]
        if len(possible_selections) == 1:
            self.goaltree.select(possible_selections[0])
            self.selection_cache = []
        else:
            self.selection_cache.append(goal_id)

    def next_view(self):
        self.view = self.views[self.view]
        self._update_mapping()

    def __getattribute__(self, attr):
        proxied = object.__getattribute__(self, 'proxied')
        goaltree = object.__getattribute__(self, 'goaltree')
        if attr in proxied:
            return getattr(goaltree, attr)
        else:
            return object.__getattribute__(self, attr)
