import os
import sqlite3
from collections import Counter
from contextlib import closing
from typing import Set

from hypothesis import settings, assume, note, event
from hypothesis.stateful import (
    RuleBasedStateMachine,
    rule,
    initialize,
    invariant,
    precondition,
)
from hypothesis.strategies import data, integers, booleans, text, sampled_from

from siebenapp.domain import (
    EdgeType,
    HoldSelect,
    ToggleClose,
    Delete,
    ToggleLink,
    Add,
    Select,
    Insert,
    Rename,
    Command,
)
from siebenapp.filter_view import FilterBy
from siebenapp.goaltree import Goals
from siebenapp.layers import all_layers
from siebenapp.open_view import ToggleOpenView
from siebenapp.switchable_view import ToggleSwitchableView
from siebenapp.system import save_updates, save_connection
from siebenapp.zoom import ToggleZoom

settings.register_profile("ci", settings(max_examples=1000))
settings.register_profile("dev", settings(max_examples=200))
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))


class GoaltreeRandomWalk(RuleBasedStateMachine):
    db_is_ready = False

    def __init__(self):
        super().__init__()
        self.goaltree = all_layers(Goals("Root"))
        self.database = sqlite3.connect(":memory:")

    @initialize()
    def open_db_connection(self):
        save_connection(self.goaltree, self.database)
        self.db_is_ready = True

    def teardown(self):
        self.database.close()

    def _accept_all(self, *commands: Command) -> None:
        for command in commands:
            note(str(command))
        self.goaltree.accept_all(*commands)

    def _accept(self, command: Command) -> None:
        note(str(command))
        self.goaltree.accept(command)

    #
    # Modifiers
    #

    @rule()
    def add_goal(self):
        event("add")
        self._accept(Add("a"))

    @rule()
    def delete_goal(self):
        event("delete")
        self._accept(Delete())

    @rule(d=data())
    def select_random_goal(self, d):
        event("select")
        max_key = max(self.goaltree.q().keys())
        assume(max_key >= 1)
        event("valid select 1")
        random_goal = d.draw(integers(min_value=1, max_value=max_key))
        assume(random_goal in self.goaltree.q())
        event("valid select 2")
        self._accept(Select(random_goal))
        # Any valid goal must be selectable
        assert self.goaltree.q("select")[random_goal]["select"] == "select"

    @rule()
    def hold_selection(self):
        event("hold")
        self._accept(HoldSelect())

    @rule(d=data())
    # Ignore trivial trees (without any subgoal)
    @precondition(lambda self: len(self.goaltree.q()) > 1)
    def insert(self, d):
        event("insert")
        candidates = sorted(
            list(
                goal_id
                for goal_id, attrs in self.goaltree.q("select").items()
                if attrs["select"] != "select"
            )
        )
        random_goal = d.draw(sampled_from(candidates))
        self._accept_all(HoldSelect(), Select(random_goal), Insert("i"))

    @rule(b=booleans(), d=data())
    # Ignore trivial trees (without any subgoal)
    @precondition(lambda self: len(self.goaltree.q()) > 1)
    def toggle_link(self, b, d):
        event("toggle link")
        goal_keys = sorted(list(k for k in self.goaltree.q().keys() if k > 0))
        assume(len(goal_keys) > 1)
        selection = d.draw(sampled_from(goal_keys))
        goal_keys.remove(selection)
        prev_selection = d.draw(sampled_from(goal_keys))
        event("valid toggle link")
        edge_type = EdgeType.PARENT if b else EdgeType.BLOCKER
        self._accept(
            ToggleLink(lower=prev_selection, upper=selection, edge_type=edge_type)
        )

    # @rule(c=sampled_from(" abcit"))
    # # Ignore trivial trees (without any subgoal)
    # @precondition(lambda self: len(self.goaltree.q()) > 1)
    # def add_autolink(self, c):
    #     event("autolink")
    #     event("valid autolink")
    #     self._accept(ToggleAutoLink(c))

    @rule()
    def close_or_open(self):
        event("close/open")
        self._accept(ToggleClose())

    @rule(t=text())
    def rename(self, t):
        event("rename")
        self._accept(Rename(t))

    @rule()
    def zoom(self):
        event("zoom")
        self._accept(ToggleZoom())

    @rule()
    def switchable_view(self):
        event("switchable_view")
        self._accept(ToggleSwitchableView())

    @rule()
    def open_view(self):
        event("open_view")
        self._accept(ToggleOpenView())

    @rule()
    def filter_by_text(self):
        event("filter x")
        self._accept(FilterBy("x"))

    @rule()
    def reset_filter(self):
        event("reset filter")
        self._accept(FilterBy(""))

    #
    # Verifiers
    #

    @invariant()
    def there_is_always_at_least_one_goal(self):
        assert self.goaltree.q()

    @invariant()
    def only_one_root_is_allowed_in_tree_mode(self):
        assume(not self.goaltree.settings("filter_switchable"))
        shown = self.goaltree.q("edge")
        goals: Set[int] = set(shown.keys())
        goals_with_parent: Set[int] = set(
            e[0] for attrs in shown.values() for e in attrs["edge"]
        )
        goals_without_parent = goals.difference(goals_with_parent)
        assert len(goals_without_parent) == 1

    @invariant()
    def goaltree_is_always_valid(self):
        assert self.goaltree.verify()

    @invariant()
    def there_is_always_one_selected_goal_and_at_most_one_previous(self):
        selects = self.goaltree.q("select")
        counter = Counter(s["select"] for s in selects.values())
        assert counter["select"] == 1, str(selects)
        assert counter["prev"] <= 1, str(selects)

    @invariant()
    @precondition(lambda self: self.db_is_ready)
    def full_export_and_streaming_export_must_be_the_same(self):
        note(", ".join(str(e) for e in list(self.goaltree.events())[-5:]))
        save_updates(self.goaltree, self.database)
        assert not self.goaltree.events()
        ng = build_goals(self.database)
        ng.reconfigure_from(self.goaltree)
        keys = "name,open,edge,select,switchable"
        q1 = self.goaltree.q(keys)
        q2 = ng.q(keys)
        assert q1 == q2


TestGoalTreeRandomWalk = GoaltreeRandomWalk.TestCase


def build_goals(conn):
    with closing(conn.cursor()) as cur:
        goals = list(cur.execute("select * from goals"))
        edges = list(cur.execute("select parent, child, reltype from edges"))
        db_settings = list(cur.execute("select * from settings"))
        zoom_data = list(cur.execute("select * from zoom"))
        autolink_data = list(cur.execute("select * from autolink"))
        note(
            f"Goals: {goals}, Edges: {edges}, Settings: {db_settings}, Zoom: {zoom_data}, Autolink: {autolink_data}"
        )
        goals = Goals.build(goals, edges, db_settings)
        return all_layers(goals, zoom_data, autolink_data)
