# coding: utf-8


class Goals():
    def __init__(self, name):
        self.goals = {1: name}
        self.transitions = dict()

    def add(self, name, add_to=1):
        next_id = len(self.goals) + 1
        self.goals[next_id] = name
        self.transitions.setdefault(add_to, list())
        self.transitions[add_to].append(next_id)

    def all(self):
        return self.goals

    def top(self):
        return {key: self.goals[key]
                for key in self.goals.keys()
                if key not in self.transitions.keys()}
