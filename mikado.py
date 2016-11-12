# coding: utf-8


class Goals():
    def __init__(self, name):
        self.goals = {1: name}
        self.transitions = dict()
        self.closed = set()

    def add(self, name, add_to=1):
        next_id = len(self.goals) + 1
        self.goals[next_id] = name
        self._link(add_to, next_id)
        return next_id

    def all(self):
        return {k: v for k, v in self.goals.items()
                     if k not in self.closed}

    def all_with_status(self):
        return {k: {'name': v, 'open': k not in self.closed}
                for k, v in self.goals.items()}

    def top(self):
        return {key: value
                for key, value in self.goals.items()
                if key not in self.transitions.keys() and
                   key not in self.closed}

    def insert(self, lower, upper, name):
        key = self.add(name, lower)
        self._link(key, upper)

    def rename(self, goal_id, new_name):
        self.goals[goal_id] = new_name

    def close(self, goal_id):
        self.closed.add(goal_id)

    def _link(self, lower, upper):
        self.transitions.setdefault(lower, list())
        self.transitions[lower].append(upper)
