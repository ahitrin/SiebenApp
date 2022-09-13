import pytest

from siebenapp.domain import Select, ToggleClose, HoldSelect, child, blocker, RenderRow
from siebenapp.open_view import ToggleOpenView, OpenView
from siebenapp.tests.dsl import build_goaltree, open_, selected, clos_, previous


@pytest.fixture
def trivial():
    g = build_goaltree(open_(1, "Start", [], [], select=selected))
    return OpenView(g)


@pytest.fixture
def two_goals():
    g = build_goaltree(open_(1, "Open", [2], [], select=selected), clos_(2, "Closed"))
    return OpenView(g)


def test_open_goal_is_shown_by_default(trivial):
    assert trivial.q().rows == [
        RenderRow(1, 1, "Start", True, True, "select", []),
    ]


def test_open_goal_is_shown_after_switch(trivial):
    trivial.accept(ToggleOpenView())
    assert trivial.q().rows == [
        RenderRow(1, 1, "Start", True, True, "select", []),
    ]


def test_filter_open_setting_is_set_by_default(trivial):
    assert trivial.settings("filter_open") == 1


def test_filter_open_setting_is_changed_after_switch(trivial):
    trivial.accept(ToggleOpenView())
    assert trivial.settings("filter_open") == 0


def test_closed_goal_is_not_shown_by_default(two_goals):
    assert two_goals.q().rows == [
        RenderRow(1, 1, "Open", True, True, "select", []),
    ]


def test_closed_goal_is_shown_after_switch(two_goals):
    two_goals.accept(ToggleOpenView())
    assert two_goals.q().rows == [
        RenderRow(1, 1, "Open", True, True, "select", [child(2)]),
        RenderRow(2, 2, "Closed", False, True, None, []),
    ]
    two_goals.accept(ToggleOpenView())
    assert two_goals.q().rows == [
        RenderRow(1, 1, "Open", True, True, "select", []),
    ]


def test_simple_open_enumeration_workflow():
    e = OpenView(
        build_goaltree(
            open_(1, "Root", [2, 3], select=previous),
            open_(2, "1", select=selected),
            open_(3, "2"),
        )
    )
    assert e.q().rows == [
        RenderRow(1, 1, "Root", True, False, "prev", [child(2), child(3)]),
        RenderRow(2, 2, "1", True, True, "select", []),
        RenderRow(3, 3, "2", True, True, None, []),
    ]
    e.accept(ToggleClose())
    assert e.q().rows == [
        RenderRow(1, 1, "Root", True, False, "select", [child(3)]),
        RenderRow(3, 3, "2", True, True, None, []),
    ]


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
    assert v.q().rows == [
        RenderRow(1, 1, "Root", True, True, None, [child(2), child(3)]),
        RenderRow(2, 2, "closed", False, True, "prev", []),
        RenderRow(3, 3, "closed too", False, True, "select", [child(4)]),
        RenderRow(4, 4, "closed and not selected", False, False, None, []),
    ]
    v.accept(ToggleOpenView())
    # Still show: open goals, selected goals
    assert v.q().rows == [
        RenderRow(1, 1, "Root", True, True, None, [child(2), child(3)]),
        RenderRow(2, 2, "closed", False, True, "prev", []),
        RenderRow(3, 3, "closed too", False, True, "select", []),
    ]


def test_build_fake_links_to_far_closed_goals():
    v = OpenView(
        build_goaltree(
            open_(1, "Root", blockers=[2], select=previous),
            clos_(2, "Middle", blockers=[3]),
            clos_(3, "Top", select=selected),
        )
    )
    assert v.q().rows == [
        RenderRow(1, 1, "Root", True, True, "prev", [blocker(3)]),
        RenderRow(3, 3, "Top", False, False, "select", []),
    ]


def test_still_show_root_when_it_is_closed_and_unselected():
    v = OpenView(
        build_goaltree(
            clos_(1, "Hidden root", [2]),
            clos_(2, "Visible", select=selected),
        )
    )
    assert v.q().rows == [
        RenderRow(1, 1, "Hidden root", False, True, None, [child(2)]),
        RenderRow(2, 2, "Visible", False, False, "select", []),
    ]
