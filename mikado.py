# coding: utf-8


class Goals():
    def __init__(self, name):
        self.goals = {1: name}

    def all(self):
        return self.goals

    def top(self):
        return self.goals
