import pytest

from siebenapp.domain import Select
from siebenapp.enumeration import Enumeration, ToggleOpenView
from siebenapp.tests.dsl import build_goaltree, open_, selected, clos_

# pylint: disable=redefined-outer-name


@pytest.fixture
def trivial():
    g = build_goaltree(open_(1, "Start", [], [], select=selected))
    return Enumeration(g)


@pytest.fixture
def two_goals():
    g = build_goaltree(open_(1, "Open", [2], [], select=selected), clos_(2, "Closed"))
    return Enumeration(g)


def test_open_goal_is_shown_by_default(trivial):
    assert trivial.q("name") == {1: {"name": "Start"}}


def test_open_goal_is_shown_after_switch(trivial):
    trivial.accept(ToggleOpenView())
    assert trivial.q("name") == {1: {"name": "Start"}}


def test_closed_goal_is_not_shown_by_default(two_goals):
    assert two_goals.q("name") == {1: {"name": "Open"}}


def test_closed_goal_is_shown_after_switch(two_goals):
    two_goals.accept(ToggleOpenView())
    assert two_goals.q("name") == {1: {"name": "Open"}, 2: {"name": "Closed"}}
    two_goals.accept(ToggleOpenView())
    assert two_goals.q("name") == {1: {"name": "Open"}}


def test_closed_selection_must_be_reset_after_hide(two_goals):
    two_goals.accept(ToggleOpenView())
    two_goals.accept(Select(2))
    assert two_goals.q("name,select") == {
        1: {"name": "Open", "select": "prev"},
        2: {"name": "Closed", "select": "select"},
    }
