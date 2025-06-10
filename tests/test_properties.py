import os
import sqlite3
from contextlib import closing
from dataclasses import asdict

from hypothesis import settings, assume, note, event
from hypothesis.stateful import (
    RuleBasedStateMachine,
    rule,
    initialize,
    invariant,
    precondition,
)
from hypothesis.strategies import data, integers, text, sampled_from

from siebenapp.autolink import ToggleAutoLink
from siebenapp.domain import (
    EdgeType,
    ToggleClose,
    Delete,
    ToggleLink,
    Add,
    Insert,
    Rename,
    Command,
    GoalId,
    Graph,
)
from siebenapp.filter_view import FilterBy
from siebenapp.goaltree import Goals
from siebenapp.selectable import OPTION_SELECT, OPTION_PREV_SELECT, Select, HoldSelect
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
    def open_db_connection(self) -> None:
        save_connection(self.goaltree, self.database)
        self.db_is_ready = True

    def teardown(self) -> None:
        self.database.close()

    def _accept(self, command: Command) -> None:
        note(str(command))
        self.goaltree.accept(command)

    #
    # Modifiers
    #

    @rule()
    def add_goal(self) -> None:
        event("add")
        self._accept(Add("a", self.goaltree.settings("selection")))

    @rule(d=data())
    def delete_goal(self, d) -> None:
        event("delete")
        goal_keys = sorted(
            list(row.goal_id for row in self.goaltree.q().rows if row.goal_id > 0)
        )
        assume(len(goal_keys) > 1)
        selection = d.draw(sampled_from(goal_keys))
        self._accept(Delete(selection))

    @rule(d=data())
    def select_random_goal(self, d) -> None:
        event("select")
        max_key = max(
            [r.goal_id for r in self.goaltree.q().rows if isinstance(r.goal_id, int)]
        )
        assume(max_key >= 1)
        event("valid select 1")
        random_goal = d.draw(integers(min_value=1, max_value=max_key))
        assume(random_goal in {r.goal_id for r in self.goaltree.q().rows})
        event("valid select 2")
        self._accept(Select(random_goal))
        # Any valid goal must be selectable
        render_result = self.goaltree.q()
        assert (
            render_result.by_id(random_goal).goal_id
            == render_result.global_opts[OPTION_SELECT]
        )

    @rule()
    def hold_selection(self) -> None:
        event("hold")
        self._accept(HoldSelect())

    @rule()
    # Run insert only when two different goals are selected
    @precondition(
        lambda self: len(
            {
                self.goaltree.q().global_opts[OPTION_SELECT],
                self.goaltree.q().global_opts[OPTION_PREV_SELECT],
            }.difference({-1})
        )
        > 1
    )
    def insert(self) -> None:
        event("insert")
        self._accept(
            Insert(
                "i",
                self.goaltree.settings("previous_selection"),
                self.goaltree.settings("selection"),
            )
        )

    @rule(
        edge_type=integers(min_value=EdgeType.RELATION, max_value=EdgeType.PARENT),
        d=data(),
    )
    # Ignore trivial trees (without any subgoal)
    @precondition(lambda self: len(self.goaltree.q().rows) > 1)
    def toggle_link(self, edge_type, d) -> None:
        event("toggle link")
        goal_keys = sorted(
            list(row.goal_id for row in self.goaltree.q().rows if row.goal_id > 0)
        )
        assume(len(goal_keys) > 1)
        selection = d.draw(sampled_from(goal_keys))
        goal_keys.remove(selection)
        prev_selection = d.draw(sampled_from(goal_keys))
        event("valid toggle link")
        self._accept(ToggleLink(prev_selection, selection, edge_type))

    @rule(c=sampled_from(" abcit"), d=data())
    # Ignore trivial trees (without any subgoal)
    @precondition(
        lambda self: len([1 for row in self.goaltree.q().rows if row.goal_id > 0]) > 1
    )
    def add_autolink(self, c, d) -> None:
        event("autolink")
        event("valid autolink")
        goal_keys = sorted(
            list(row.goal_id for row in self.goaltree.q().rows if row.goal_id > 0)
        )
        selection = d.draw(sampled_from(goal_keys))
        self._accept(ToggleAutoLink(c, selection))

    @rule()
    def close_or_open(self) -> None:
        event("close/open")
        self._accept(ToggleClose(self.goaltree.settings("selection")))

    @rule(t=text(), d=data())
    def rename(self, t, d) -> None:
        event("rename")
        goal_keys = sorted(
            list(row.goal_id for row in self.goaltree.q().rows if row.goal_id > 0)
        )
        selection = d.draw(sampled_from(goal_keys))
        self._accept(Rename(t, selection))

    @rule()
    def zoom(self) -> None:
        event("zoom")
        selection = self.goaltree.settings("selection")
        self._accept(ToggleZoom(selection))

    @rule()
    def switchable_view(self) -> None:
        event("switchable_view")
        self._accept(ToggleSwitchableView())

    @rule()
    def open_view(self) -> None:
        event("open_view")
        self._accept(ToggleOpenView())

    @rule()
    def filter_by_text(self) -> None:
        event("filter x")
        self._accept(FilterBy("x"))

    @rule()
    def reset_filter(self) -> None:
        event("reset filter")
        self._accept(FilterBy(""))

    #
    # Verifiers
    #

    @invariant()
    def there_is_always_at_least_one_goal(self) -> None:
        assert self.goaltree.q().rows

    @invariant()
    def fake_goals_should_never_be_switchable(self) -> None:
        fake_goals = [
            (row.goal_id, row.is_switchable)
            for row in self.goaltree.q().rows
            if isinstance(row.goal_id, int) and row.goal_id < 0
        ]
        switchable_fakes = [g for g, sw in fake_goals if sw]
        assert not switchable_fakes, f"Switchable fake goals: {switchable_fakes}"

    @invariant()
    def goaltree_is_always_valid(self) -> None:
        self.goaltree.verify()

    @invariant()
    def there_is_always_one_selected_goal_and_at_most_one_previous(self) -> None:
        render_result = self.goaltree.q()
        assert render_result.global_opts[OPTION_SELECT] != 0, str(
            render_result.global_opts
        )
        assert render_result.global_opts[OPTION_PREV_SELECT] != 0, str(
            render_result.global_opts
        )

    @invariant()
    def root_goals_should_not_have_incoming_edges(self) -> None:
        render_result = self.goaltree.q()
        result_roots: set[GoalId] = render_result.roots
        has_incoming_edges: set[GoalId] = {
            e[0] for row in render_result.rows for e in row.edges
        }
        actual_roots: set[GoalId] = {
            row.goal_id
            for row in render_result.rows
            if row.goal_id not in has_incoming_edges
        }
        assert result_roots == actual_roots

    @invariant()
    @precondition(lambda self: self.db_is_ready)
    def full_export_and_streaming_export_must_be_the_same(self) -> None:
        note(", ".join(str(e) for e in list(self.goaltree.events())[-5:]))
        save_updates(self.goaltree, self.database)
        assert not self.goaltree.events()
        ng = build_goals(self.database)
        ng.reconfigure_from(self.goaltree)
        q1 = self.goaltree.q()
        q2 = ng.q()
        assert q1 == q2


TestGoalTreeRandomWalk = GoaltreeRandomWalk.TestCase


def build_goals(conn) -> Graph:
    with closing(conn.cursor()) as cur:
        goal_list = list(cur.execute("select * from goals"))
        edges = list(cur.execute("select parent, child, reltype from edges"))
        db_settings = list(cur.execute("select * from settings"))
        zoom_data = list(cur.execute("select * from zoom"))
        autolink_data = list(cur.execute("select * from autolink"))
        note(
            f"Goals: {goal_list}, Edges: {edges}, Settings: {db_settings}, "
            "Zoom: {zoom_data}, Autolink: {autolink_data}"
        )
        goals: Goals = Goals.build(goal_list, edges)
        wrapped = all_layers(goals, db_settings, zoom_data, autolink_data)
        note(str(asdict(wrapped.q())))
        return wrapped
