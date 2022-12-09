import pytest

from siebenapp.domain import (
    Select,
    ToggleClose,
    HoldSelect,
    child,
    blocker,
    RenderRow,
    RenderResult,
)
from siebenapp.open_view import ToggleOpenView, OpenView
from siebenapp.tests.dsl import build_goaltree, open_, selected, clos_, previous
from siebenapp.zoom import Zoom, ToggleZoom


@pytest.fixture
def trivial():
    g = build_goaltree(open_(1, "Start", [], [], select=selected))
    return OpenView(g)


@pytest.fixture
def two_goals():
    g = build_goaltree(open_(1, "Open", [2], [], select=selected), clos_(2, "Closed"))
    return OpenView(g)


def test_open_goal_is_shown_by_default(trivial) -> None:
    assert trivial.q() == RenderResult(
        [
            RenderRow(1, 1, "Start", True, True, []),
        ],
        select=(1, 1),
        roots={1},
    )


def test_open_goal_is_shown_after_switch(trivial) -> None:
    trivial.accept(ToggleOpenView())
    assert trivial.q() == RenderResult(
        [
            RenderRow(1, 1, "Start", True, True, []),
        ],
        select=(1, 1),
        roots={1},
    )


def test_filter_open_setting_is_set_by_default(trivial) -> None:
    assert trivial.settings("filter_open") == 1


def test_filter_open_setting_is_changed_after_switch(trivial) -> None:
    trivial.accept(ToggleOpenView())
    assert trivial.settings("filter_open") == 0


def test_closed_goal_is_not_shown_by_default(two_goals) -> None:
    assert two_goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Open", True, True, []),
        ],
        select=(1, 1),
        roots={1},
    )


def test_closed_goal_is_shown_after_switch(two_goals) -> None:
    two_goals.accept(ToggleOpenView())
    assert two_goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Open", True, True, [child(2)]),
            RenderRow(2, 2, "Closed", False, True, []),
        ],
        select=(1, 1),
        roots={1},
    )
    two_goals.accept(ToggleOpenView())
    assert two_goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Open", True, True, []),
        ],
        select=(1, 1),
        roots={1},
    )


def test_simple_open_enumeration_workflow() -> None:
    e = OpenView(
        build_goaltree(
            open_(1, "Root", [2, 3], select=previous),
            open_(2, "1", select=selected),
            open_(3, "2"),
        )
    )
    assert e.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "1", True, True, []),
            RenderRow(3, 3, "2", True, True, []),
        ],
        select=(2, 1),
        roots={1},
    )
    e.accept(ToggleClose())
    assert e.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(3)]),
            RenderRow(3, 3, "2", True, True, []),
        ],
        select=(1, 1),
        roots={1},
    )


def test_closed_goals_are_shown_when_selected() -> None:
    v = OpenView(
        build_goaltree(
            open_(1, "Root", [2, 3], select=selected),
            clos_(2, "closed"),
            clos_(3, "closed too", [4]),
            clos_(4, "closed and not selected"),
        )
    )
    v.accept_all(ToggleOpenView(), Select(2), HoldSelect(), Select(3))
    assert v.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, True, [child(2), child(3)]),
            RenderRow(2, 2, "closed", False, True, []),
            RenderRow(3, 3, "closed too", False, True, [child(4)]),
            RenderRow(4, 4, "closed and not selected", False, False, []),
        ],
        select=(3, 2),
        roots={1},
    )
    v.accept(ToggleOpenView())
    # Still show: open goals, selected goals
    assert v.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, True, [child(2), child(3)]),
            RenderRow(2, 2, "closed", False, True, []),
            RenderRow(3, 3, "closed too", False, True, []),
        ],
        select=(3, 2),
        roots={1},
    )


def test_do_not_build_fake_links_to_far_closed_goals() -> None:
    v = OpenView(
        build_goaltree(
            open_(1, "Root", blockers=[2], select=previous),
            clos_(2, "Middle", blockers=[3]),
            clos_(3, "Top", select=selected),
        )
    )
    assert v.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, True, []),
            RenderRow(3, 3, "Top", False, False, []),
        ],
        select=(3, 1),
        roots={1, 3},
    )


def test_still_show_root_when_it_is_closed_and_unselected() -> None:
    v = OpenView(
        build_goaltree(
            clos_(1, "Hidden root", [2]),
            clos_(2, "Visible", select=selected),
        )
    )
    assert v.q() == RenderResult(
        [
            RenderRow(1, 1, "Hidden root", False, True, [child(2)]),
            RenderRow(2, 2, "Visible", False, False, []),
        ],
        select=(2, 2),
        roots={1},
    )


def test_add_dangling_goals_to_old_root_on_zoom() -> None:
    v = OpenView(
        Zoom(
            build_goaltree(
                open_(1, "Root", [2]),
                open_(2, "Zoom root", [3, 5], select=selected),
                clos_(3, "Transitive", [4]),
                clos_(4, "Previous top", select=previous),
                open_(5, "Current top"),
            )
        )
    )
    v.accept(ToggleZoom())
    assert v.q() == RenderResult(
        [
            RenderRow(2, 2, "Zoom root", True, False, [child(5)], {"Zoom": "root"}),
            RenderRow(4, 4, "Previous top", False, False, []),
            RenderRow(5, 5, "Current top", True, True, []),
            RenderRow(-1, -1, "Root", True, False, [blocker(2)]),
        ],
        select=(2, 4),
        roots={-1, 4},
    )
