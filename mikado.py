# coding: utf-8


class Goals():
    def __init__(self, name):
        self.goals = {1: name}
        self.edges = dict()
        self.closed = set()

    def add(self, name, add_to=1):
        next_id = len(self.goals) + 1
        self.goals[next_id] = name
        self.link(add_to, next_id)
        return next_id

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
                value['edge'] = self.edges[key] if key in self.edges else []
            result[key] = value if len(keys) > 1 else value[keys[0]]
        return result

    def top(self):
        return {key: value
                for key, value in self.goals.items()
                if key not in self.edges.keys() and
                   key not in self.closed}

    def insert(self, lower, upper, name):
        key = self.add(name, lower)
        self.link(key, upper)

    def rename(self, goal_id, new_name):
        self.goals[goal_id] = new_name

    def close(self, goal_id):
        self.closed.add(goal_id)

    def reopen(self, goal_id):
        self.closed.remove(goal_id)

    def delete(self, goal_id):
        self.goals.pop(goal_id)
        if goal_id in self.edges:
            for next_goal in self.edges[goal_id]:
                other_edges = list()
                for k in (k for k in self.edges if k != goal_id):
                    other_edges.extend(self.edges[k])
                if next_goal not in set(other_edges):
                    self.delete(next_goal)
            self.edges.pop(goal_id)
        for key in sorted(k for k in self.goals.keys() if k > goal_id):
            self.goals[key - 1] = self.goals.pop(key)
        for key, values in self.edges.items():
            self.edges[key] = [v for v in values if v < goal_id] + \
                              [v - 1 for v in values if v > goal_id]

    def link(self, lower, upper):
        self.edges.setdefault(lower, list())
        self.edges[lower].append(upper)

    def unlink(self, lower, upper):
        self.edges[lower].remove(upper)
        if not self.edges[lower]:
            self.edges.pop(lower)
