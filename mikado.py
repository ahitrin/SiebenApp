# coding: utf-8


class Goals():
    def __init__(self, name):
        self.goals = {1: name}

    def add(self, name):
        self.goals[2] = name

    def all(self):
        return self.goals

    def top(self):
        key = sorted(self.goals.keys())[-1]
        return {key: self.goals[key]}
