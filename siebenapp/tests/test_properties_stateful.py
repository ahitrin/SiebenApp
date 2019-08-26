import os
import sqlite3
from collections import Counter

from hypothesis import settings, assume
from hypothesis._strategies import data, integers, booleans
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant, precondition

from siebenapp.goaltree import Goals, Edge
from siebenapp.system import run_migrations, save_updates
from siebenapp.tests.test_properties import build_goals

settings.register_profile('ci', settings(max_examples=2000))
settings.register_profile('dev', settings(max_examples=200))
settings.load_profile(os.getenv('HYPOTHESIS_PROFILE', 'dev'))


class GoaltreeRandomWalk(RuleBasedStateMachine):
    db_is_ready = False

    def __init__(self):
        super(GoaltreeRandomWalk, self).__init__()
        self.goaltree = Goals('Root')
        self.database = sqlite3.connect(':memory:')

    @initialize()
    def open_db_connection(self):
        run_migrations(self.database)
        self.db_is_ready = True

    def teardown(self):
        self.database.close()

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
        assume(random_goal in self.goaltree.q())
        self.goaltree.select(random_goal)
        # Any valid goal must be selectable
        assert self.goaltree.q('select')[random_goal]['select'] == 'select'

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

    @invariant()
    def goaltree_is_always_valid(self):
        assert self.goaltree.verify()

    @invariant()
    def there_is_always_one_selected_goal_and_at_most_one_previous(self):
        selects = self.goaltree.q('select').values()
        counter = Counter(s['select'] for s in selects)
        assert counter['select'] == 1
        assert counter['prev'] <= 1

    @invariant()
    @precondition(lambda self: self.db_is_ready)
    def test_full_export_and_streaming_export_must_be_the_same(self):
        save_updates(self.goaltree, self.database)
        assert not self.goaltree.events
        ng = build_goals(self.database)
        assert self.goaltree.q('name,open,edge,select,switchable') == ng.q('name,open,edge,select,switchable')


TestGoalTreeRandomWalk = GoaltreeRandomWalk.TestCase
