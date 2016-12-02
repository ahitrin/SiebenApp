# coding: utf-8


class Goals():
    def __init__(self, name):
        self.goals = {1: name}
        self.edges = {1: []}
        self.closed = set()
        self.selection = 1
        self.selection_cache = []
        self.previous_selection = 1

    def add(self, name, add_to=0):
        if add_to == 0:
            add_to = self.selection
        if add_to in self.closed:
            return False
        next_id = len(self.goals) + 1
        self.goals[next_id] = name
        self.edges[next_id] = list()
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

    def select(self, goal_id):
        if goal_id > len(self.goals):
            return
        if self.selection_cache:
            goal_id = 10 * self.selection_cache.pop() + goal_id
        possible_selections = [g for g in self.goals.keys()
                               if self.id_mapping(g) == goal_id]
        if len(possible_selections) == 1:
            if self.goals[possible_selections[0]]:
                self.selection_cache = []
                self.selection = possible_selections[0]
        else:
            self.selection_cache.append(goal_id)

    def hold_select(self):
        self.previous_selection = self.selection
        self.selection_cache = []

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
            result[self.id_mapping(key)] = value if len(keys) > 1 else value[keys[0]]
        return result

    def top(self):
        return {self.id_mapping(key): value
                for key, value in self.goals.items()
                if key not in self.closed and
                   all(g in self.closed for g in self.edges[key])}

    def insert(self, name):
        self.selection_cache = []
        if self.selection == self.previous_selection:
            return
        if self.add(name, self.previous_selection):
            key = len(self.goals)
            self.toggle_link(key, self.selection)
            if self.selection in self.edges[self.previous_selection]:
                self.toggle_link(self.previous_selection, self.selection)

    def rename(self, new_name):
        self.goals[self.selection] = new_name
        self.selection_cache = []

    def toggle_close(self):
        if self.selection in self.closed:
            parent_goals = [g for g, v in self.edges.items() if self.selection in v]
            if any(g for g in parent_goals if g not in self.closed):
                self.closed.remove(self.selection)
        else:
            linked_goals = [g for g in self.edges[self.selection] if g not in self.closed]
            other_open_goals = [g for g in self.goals if g not in self.closed and g != self.selection]
            accessible_goals = set(g for o in other_open_goals for g in self.edges[o])
            if all(g in accessible_goals for g in linked_goals):
                self.closed.add(self.selection)
                self.selection = 1
                self.previous_selection = 1
        self.selection_cache = []

    def delete(self, goal_id=0):
        self.selection_cache = []
        if goal_id == 0:
            goal_id = self.selection
        if goal_id == 1:
            return
        self.goals[goal_id] = None
        self.closed.add(goal_id)
        for next_goal in self.edges[goal_id]:
            other_edges = list()
            for k in (k for k in self.edges if k != goal_id):
                other_edges.extend(self.edges[k])
            if next_goal not in set(other_edges):
                self.delete(next_goal)
        self.edges.pop(goal_id)
        for key, values in self.edges.items():
            self.edges[key] = [v for v in values if v != goal_id]
        self.selection = 1
        self.previous_selection = 1

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
        else:
            # create new link
            self.edges[lower].append(upper)
