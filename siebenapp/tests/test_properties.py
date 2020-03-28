import os
import sqlite3
from collections import Counter
from contextlib import closing

from hypothesis import settings, assume, note
from hypothesis.strategies import data, integers, booleans, text
from hypothesis.stateful import (
    RuleBasedStateMachine,
    rule,
    initialize,
    invariant,
    precondition,
)

from siebenapp.goaltree import Goals
from siebenapp.domain import (
    EdgeType,
    HoldSelect,
    ToggleClose,
    Delete,
    ToggleLink,
    Add,
    Select,
)
from siebenapp.system import run_migrations, save_updates
from siebenapp.zoom import Zoom

settings.register_profile("ci", settings(max_examples=1000))
settings.register_profile("dev", settings(max_examples=200))
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))


class GoaltreeRandomWalk(RuleBasedStateMachine):
    db_is_ready = False

    def __init__(self):
        super(GoaltreeRandomWalk, self).__init__()
        self.goaltree = Zoom(Goals("Root"))
        self.database = sqlite3.connect(":memory:")

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
        edge_type = EdgeType.PARENT if b else EdgeType.BLOCKER
        self.goaltree.accept(Add("a", edge_type=edge_type))

    @rule()
    def delete_goal(self):
        self.goaltree.accept(Delete())

    @rule(d=data())
    def select_random_goal(self, d):
        random_goal = d.draw(
            integers(min_value=1, max_value=max(self.goaltree.q().keys()))
        )
        assume(random_goal in self.goaltree.q())
        self.goaltree.accept(Select(random_goal))
        # Any valid goal must be selectable
        assert self.goaltree.q("select")[random_goal]["select"] == "select"

    @rule()
    def hold_selection(self):
        self.goaltree.accept(HoldSelect())

    @rule()
    def insert(self):
        selection = self.goaltree.settings["selection"]
        prev_selection = self.goaltree.settings["previous_selection"]
        assume(selection != prev_selection)
        self.goaltree.insert("i")

    @rule(b=booleans(), d=data())
    def toggle_link(self, b, d):
        selection = d.draw(
            integers(min_value=1, max_value=max(self.goaltree.q().keys()))
        )
        prev_selection = d.draw(
            integers(min_value=1, max_value=max(self.goaltree.q().keys()))
        )
        assume(selection != prev_selection)
        edge_type = EdgeType.PARENT if b else EdgeType.BLOCKER
        self.goaltree.accept(ToggleLink(edge_type=edge_type))

    @rule()
    def close_or_open(self):
        self.goaltree.accept(ToggleClose())

    @rule(t=text())
    def rename(self, t):
        self.goaltree.rename(t)

    @rule()
    def zoom(self):
        self.goaltree.toggle_zoom()

    #
    # Verifiers
    #

    @invariant()
    def there_is_always_at_least_one_goal(self):
        assert self.goaltree.q()

    @invariant()
    def goaltree_is_always_valid(self):
        assert self.goaltree.verify()

    @invariant()
    def there_is_always_one_selected_goal_and_at_most_one_previous(self):
        selects = self.goaltree.q("select").values()
        counter = Counter(s["select"] for s in selects)
        assert counter["select"] == 1
        assert counter["prev"] <= 1

    @invariant()
    @precondition(lambda self: self.db_is_ready)
    def test_full_export_and_streaming_export_must_be_the_same(self):
        save_updates(self.goaltree, self.database)
        assert not self.goaltree.events
        ng = build_goals(self.database)
        q1 = self.goaltree.goaltree.q("name,open,edge,select,switchable")
        q2 = ng.q("name,open,edge,select,switchable")
        assert q1 == q2


TestGoalTreeRandomWalk = GoaltreeRandomWalk.TestCase


def build_goals(conn):
    with closing(conn.cursor()) as cur:
        goals = list(cur.execute("select * from goals"))
        edges = list(cur.execute("select parent, child, reltype from edges"))
        selection = list(cur.execute("select * from settings"))
        note(f"Goals: {goals}, Edges: {edges}, Selection: {selection}")
        return Goals.build(goals, edges, selection)
