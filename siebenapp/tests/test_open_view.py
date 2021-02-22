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


def test_closed_goals_are_shown_when_selected():
    v = OpenView(
        build_goaltree(
            open_(1, "Root", [2, 3], select=selected),
            clos_(2, "closed"),
            clos_(3, "closed too", [4]),
            clos_(4, "closed and not selected"),
        )
    )
    v.accept_all(ToggleOpenView(), Select(2), HoldSelect(), Select(3))
    assert v.q("name,select,open") == {
        1: {"name": "Root", "open": True, "select": None},
        2: {"name": "closed", "open": False, "select": "prev"},
        3: {"name": "closed too", "open": False, "select": "select"},
        4: {"name": "closed and not selected", "open": False, "select": None},
    }
    v.accept(ToggleOpenView())
    # Still show: open goals, selected goals
    assert v.q("name,select,open") == {
        1: {"name": "Root", "open": True, "select": None},
        2: {"name": "closed", "open": False, "select": "prev"},
        3: {"name": "closed too", "open": False, "select": "select"},
    }
