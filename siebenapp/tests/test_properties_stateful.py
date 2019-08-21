import os

from hypothesis import settings, assume
from hypothesis._strategies import data, integers, booleans
from hypothesis.stateful import RuleBasedStateMachine, rule

from siebenapp.goaltree import Goals, Edge

settings.register_profile('ci', settings(max_examples=2000))
settings.register_profile('dev', settings(max_examples=200))
settings.load_profile(os.getenv('HYPOTHESIS_PROFILE', 'dev'))


class GoaltreeRandomWalk(RuleBasedStateMachine):
    def __init__(self):
        super(GoaltreeRandomWalk, self).__init__()
        self.goaltree = Goals('Root')

    #
    # Modifiers
    #

    @rule(b=booleans())
    def add_goal(self, b):
        edge_type = Edge.PARENT if b else Edge.BLOCKER
        self.goaltree.add('a', edge_type=edge_type)

    @rule()
    def delete_goal(self):
        self.goaltree.delete()

    @rule(d=data())
    def select_random_goal(self, d):
        random_goal = d.draw(integers(min_value=1, max_value=max(self.goaltree.q().keys())))
        self.goaltree.select(random_goal)

    @rule()
    def hold_selection(self):
        self.goaltree.hold_select()

    @rule()
    def insert(self):
        selection = self.goaltree.settings['selection']
        prev_selection = self.goaltree.settings['previous_selection']
        assume(selection != prev_selection)
        self.goaltree.insert('i')

    @rule(b=booleans(), d=data())
    def toggle_link(self, b, d):
        selection = d.draw(integers(min_value=1, max_value=max(self.goaltree.q().keys())))
        prev_selection = d.draw(integers(min_value=1, max_value=max(self.goaltree.q().keys())))
        assume(selection != prev_selection)
        edge_type = Edge.PARENT if b else Edge.BLOCKER
        self.goaltree.toggle_link(edge_type=edge_type)

    #
    # Verifiers
    #

    @rule()
    def goaltree_is_always_valid(self):
        assert self.goaltree.verify()


TestGoalTreeRandomWalk = GoaltreeRandomWalk.TestCase
