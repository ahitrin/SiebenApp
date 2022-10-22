from _pytest.fixtures import fixture

from siebenapp.domain import (
    Select,
    ToggleClose,
    RenderRow,
    RenderResult,
    RenderResult,
    child,
    blocker,
)
from siebenapp.progress_view import ProgressView, ToggleProgress
from siebenapp.tests.dsl import build_goaltree, selected, open_


@fixture
def goaltree():
    return ProgressView(
        build_goaltree(
            open_(1, "Root", [2, 3], select=selected),
            open_(2, "With blocker", [], [4]),
            open_(3, "With subgoal", [4]),
            open_(4, "Top goal"),
        )
    )


def test_no_progress_by_default(goaltree):
    assert goaltree.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "Root", True, False, "select", [child(2), child(3)]),
            RenderRow(2, 2, "With blocker", True, False, None, [blocker(4)]),
            RenderRow(3, 3, "With subgoal", True, False, None, [child(4)]),
            RenderRow(4, 4, "Top goal", True, True, None, []),
        ],
        select=(1, 1),
    )


def test_show_progress(goaltree):
    goaltree.accept(ToggleProgress())
    assert goaltree.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "[0/4] Root", True, False, "select", [child(2), child(3)]),
            RenderRow(2, 2, "[0/1] With blocker", True, False, None, [blocker(4)]),
            RenderRow(3, 3, "[0/2] With subgoal", True, False, None, [child(4)]),
            RenderRow(4, 4, "[0/1] Top goal", True, True, None, []),
        ],
        select=(1, 1),
    )


def test_toggle_hide_progress(goaltree):
    goaltree.accept_all(ToggleProgress(), ToggleProgress())
    assert goaltree.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "Root", True, False, "select", [child(2), child(3)]),
            RenderRow(2, 2, "With blocker", True, False, None, [blocker(4)]),
            RenderRow(3, 3, "With subgoal", True, False, None, [child(4)]),
            RenderRow(4, 4, "Top goal", True, True, None, []),
        ],
        select=(1, 1),
    )


def test_change_progress_on_close(goaltree):
    goaltree.accept_all(ToggleProgress(), Select(4), ToggleClose())
    assert goaltree.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "[1/4] Root", True, False, "select", [child(2), child(3)]),
            RenderRow(2, 2, "[0/1] With blocker", True, True, None, [blocker(4)]),
            RenderRow(3, 3, "[1/2] With subgoal", True, True, None, [child(4)]),
            RenderRow(4, 4, "[1/1] Top goal", False, True, None, []),
        ],
        select=(1, 1),
    )
    goaltree.accept_all(Select(2), ToggleClose())
    assert goaltree.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "[2/4] Root", True, False, "select", [child(2), child(3)]),
            RenderRow(2, 2, "[1/1] With blocker", False, True, None, [blocker(4)]),
            RenderRow(3, 3, "[1/2] With subgoal", True, True, None, [child(4)]),
            RenderRow(4, 4, "[1/1] Top goal", False, True, None, []),
        ],
        select=(1, 1),
    )
