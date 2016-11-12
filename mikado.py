# coding: utf-8


class Goals():
    def __init__(self, name):
        self.goals = {1: name}
        self.top_keys = set([1])

    def add(self, name):
        next_id = len(self.goals) + 1
        self.goals[next_id] = name
        self.top_keys.add(next_id)
        if 1 in self.top_keys:
            self.top_keys.remove(1)

    def all(self):
        return self.goals

    def top(self):
        return {key: self.goals[key]
                for key in self.top_keys}
