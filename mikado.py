# coding: utf-8


class Goals():
    def __init__(self, name):
        self.goals = {1: name}
        self.edges = {1: []}
        self.closed = set()
        self.selection = 1
        self.previous_selection = 1

    def add(self, name, add_to=0):
        if add_to == 0:
            add_to = self.selection
        next_id = len(self.goals) + 1
        self.goals[next_id] = name
        self.edges[next_id] = list()
        self.toggle_link(add_to, next_id)
        return next_id

    def select(self, goal_id):
        self.selection = goal_id

    def hold_select(self):
        self.previous_selection = self.selection

    def all(self, keys='name'):
        keys = keys.split(',')
        result = dict()
        for key, name in self.goals.items():
            value = {}
            if 'open' in keys:
                value['open'] = key not in self.closed
            if 'name' in keys:
                value['name'] = name
            if 'edge' in keys:
                value['edge'] = self.edges[key]
            if 'select' in keys:
                value['select'] = (key == self.selection)
            result[key] = value if len(keys) > 1 else value[keys[0]]
        return result

    def top(self):
        return {key: value
                for key, value in self.goals.items()
                if not self.edges[key] and
                   key not in self.closed}

    def insert(self, lower, upper, name):
        key = self.add(name, lower)
        self.toggle_link(key, upper)

    def rename(self, new_name):
        self.goals[self.selection] = new_name

    def toggle_close(self):
        if self.selection in self.closed:
            self.closed.remove(self.selection)
        else:
            self.closed.add(self.selection)
            self.selection = 1

    def delete(self, goal_id=0):
        if goal_id == 0:
            goal_id = self.selection
        self.goals.pop(goal_id)
        for next_goal in self.edges[goal_id]:
            other_edges = list()
            for k in (k for k in self.edges if k != goal_id):
                other_edges.extend(self.edges[k])
            if next_goal not in set(other_edges):
                self.delete(next_goal)
        self.edges.pop(goal_id)
        for key in sorted(k for k in self.goals if k > goal_id):
            self.goals[key - 1] = self.goals.pop(key)
            self.edges[key - 1] = self.edges.pop(key)
        for key, values in self.edges.items():
            self.edges[key] = [v for v in values if v < goal_id] + \
                              [v - 1 for v in values if v > goal_id]
        self.selection = 1

    def toggle_link(self, lower=0, upper=0):
        if lower == 0:
            lower = self.previous_selection
        if upper == 0:
            upper = self.selection
        if upper in self.edges[lower]:
            # remove existing link
            self.edges[lower].remove(upper)
        else:
            # create new link
            self.edges[lower].append(upper)
