# coding: utf-8


class Goals():
    def __init__(self, name):
        self.goals = {1: name}
        self.transitions = dict()

    def add(self, name, add_to=1):
        next_id = len(self.goals) + 1
        self.goals[next_id] = name
        self._link(add_to, next_id)
        return next_id

    def all(self):
        return self.goals

    def top(self):
        return {key: self.goals[key]
                for key in self.goals.keys()
                if key not in self.transitions.keys()}

    def insert(self, lower, upper, name):
        key = self.add(name, lower)
        self._link(key, upper)

    def rename(self, goal_id, new_name):
        self.goals[goal_id] = new_name

    def _link(self, lower, upper):
        self.transitions.setdefault(lower, list())
        self.transitions[lower].append(upper)
