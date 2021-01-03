import pytest

from siebenapp.domain import Select, ToggleClose, EdgeType, HoldSelect
from siebenapp.open_view import ToggleOpenView, OpenView
from siebenapp.tests.dsl import build_goaltree, open_, selected, clos_, previous


# pylint: disable=redefined-outer-name


@pytest.fixture
def trivial():
    g = build_goaltree(open_(1, "Start", [], [], select=selected))
    return OpenView(g)


@pytest.fixture
def two_goals():
    g = build_goaltree(open_(1, "Open", [2], [], select=selected), clos_(2, "Closed"))
    return OpenView(g)


def test_open_goal_is_shown_by_default(trivial):
    assert trivial.q("name") == {1: {"name": "Start"}}


def test_open_goal_is_shown_after_switch(trivial):
    trivial.accept(ToggleOpenView())
    assert trivial.q("name") == {1: {"name": "Start"}}


def test_filter_open_setting_is_set_by_default(trivial):
    assert trivial.settings("filter_open") == 1


def test_filter_open_setting_is_changed_after_switch(trivial):
    trivial.accept(ToggleOpenView())
    assert trivial.settings("filter_open") == 0


def test_view_may_be_empty(trivial):
    trivial.accept(ToggleClose())
    assert trivial.q() == {}


def test_closed_goal_is_not_shown_by_default(two_goals):
    assert two_goals.q("name,open,edge") == {
        1: {"name": "Open", "open": True, "edge": []}
    }


def test_closed_goal_is_shown_after_switch(two_goals):
    two_goals.accept(ToggleOpenView())
    assert two_goals.q("name,open,edge") == {
        1: {"name": "Open", "open": True, "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Closed", "open": False, "edge": []},
    }
    two_goals.accept(ToggleOpenView())
    assert two_goals.q("name,open,edge") == {
        1: {"name": "Open", "open": True, "edge": []}
    }


def test_closed_selection_must_be_reset_after_hide(two_goals):
    two_goals.accept(ToggleOpenView())
    two_goals.accept(Select(2))
    assert two_goals.q("name,select") == {
        1: {"name": "Open", "select": "prev"},
        2: {"name": "Closed", "select": "select"},
    }
    assert two_goals.settings("selection") == 2
    assert two_goals.settings("previous_selection") == 1


def test_simple_open_enumeration_workflow():
    e = OpenView(
        build_goaltree(
            open_(1, "Root", [2, 3], select=previous),
            open_(2, "1", select=selected),
            open_(3, "2"),
        )
    )
    assert e.q(keys="name,select,open,edge") == {
        1: {
            "name": "Root",
            "select": "prev",
            "open": True,
            "edge": [(2, EdgeType.PARENT), (3, EdgeType.PARENT)],
        },
        2: {"name": "1", "select": "select", "open": True, "edge": []},
        3: {"name": "2", "select": None, "open": True, "edge": []},
    }
    e.accept(ToggleClose())
    assert e.q(keys="name,select,open,edge") == {
        1: {
            "name": "Root",
            "select": "select",
            "open": True,
            "edge": [(3, EdgeType.PARENT)],
        },
        3: {"name": "2", "select": None, "open": True, "edge": []},
    }


def test_goaltree_selection_may_be_changed_in_open_view():
    v = OpenView(
        build_goaltree(
            open_(1, "Root", [2, 3], select=selected),
            clos_(2, "closed"),
            clos_(3, "closed too"),
        )
    )
    v.accept_all(ToggleOpenView(), Select(2), HoldSelect(), Select(3))
    assert v.q("name,select") == {
        1: {"name": "Root", "select": None},
        2: {"name": "closed", "select": "prev"},
        3: {"name": "closed too", "select": "select"},
    }
    v.accept(ToggleOpenView())
    assert v.q("name,select") == {
        1: {"name": "Root", "select": "select"},
    }
    v.accept(ToggleOpenView())
    # Selection is still tied to the closed subgoals
    assert v.q("name,select") == {
        1: {"name": "Root", "select": "select"},
        2: {"name": "closed", "select": None},
        3: {"name": "closed too", "select": None},
    }
