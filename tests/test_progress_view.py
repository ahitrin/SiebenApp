from _pytest.fixtures import fixture

from siebenapp.domain import (
    ToggleClose,
    RenderRow,
    RenderResult,
    child,
    blocker,
)
from siebenapp.progress_view import ProgressView, ToggleProgress
from tests.dsl import build_goaltree, open_


@fixture
def goaltree():
    return ProgressView(
        build_goaltree(
            open_(1, "Root", [2, 3]),
            open_(2, "With blocker", [], [4]),
            open_(3, "With subgoal", [4]),
            open_(4, "Top goal"),
        )
    )


def test_no_progress_by_default(goaltree) -> None:
    assert goaltree.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "With blocker", True, False, [blocker(4)]),
            RenderRow(3, 3, "With subgoal", True, False, [child(4)]),
            RenderRow(4, 4, "Top goal", True, True, []),
        ],
        roots={1},
    )


def test_show_progress(goaltree) -> None:
    goaltree.accept(ToggleProgress())
    assert goaltree.q() == RenderResult(
        [
            RenderRow(
                1,
                1,
                "Root",
                True,
                False,
                [child(2), child(3)],
                {"Progress": "0% (0/4)", "Id": "1"},
            ),
            RenderRow(
                2,
                2,
                "With blocker",
                True,
                False,
                [blocker(4)],
                {"Progress": "0% (0/1)", "Id": "2"},
            ),
            RenderRow(
                3,
                3,
                "With subgoal",
                True,
                False,
                [child(4)],
                {"Progress": "0% (0/2)", "Id": "3"},
            ),
            RenderRow(
                4, 4, "Top goal", True, True, [], {"Progress": "0% (0/1)", "Id": "4"}
            ),
        ],
        roots={1},
    )


def test_toggle_hide_progress(goaltree) -> None:
    goaltree.accept_all(ToggleProgress(), ToggleProgress())
    assert goaltree.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "With blocker", True, False, [blocker(4)]),
            RenderRow(3, 3, "With subgoal", True, False, [child(4)]),
            RenderRow(4, 4, "Top goal", True, True, []),
        ],
        roots={1},
    )


def test_change_progress_on_close(goaltree) -> None:
    goaltree.accept_all(ToggleProgress(), ToggleClose(4))
    assert goaltree.q() == RenderResult(
        [
            RenderRow(
                1,
                1,
                "Root",
                True,
                False,
                [child(2), child(3)],
                {"Progress": "25% (1/4)", "Id": "1"},
            ),
            RenderRow(
                2,
                2,
                "With blocker",
                True,
                True,
                [blocker(4)],
                {"Progress": "0% (0/1)", "Id": "2"},
            ),
            RenderRow(
                3,
                3,
                "With subgoal",
                True,
                True,
                [child(4)],
                {"Progress": "50% (1/2)", "Id": "3"},
            ),
            RenderRow(
                4, 4, "Top goal", False, True, [], {"Progress": "100% (1/1)", "Id": "4"}
            ),
        ],
        roots={1},
    )
    goaltree.accept(ToggleClose(2))
    assert goaltree.q() == RenderResult(
        [
            RenderRow(
                1,
                1,
                "Root",
                True,
                False,
                [child(2), child(3)],
                {"Progress": "50% (2/4)", "Id": "1"},
            ),
            RenderRow(
                2,
                2,
                "With blocker",
                False,
                True,
                [blocker(4)],
                {"Progress": "100% (1/1)", "Id": "2"},
            ),
            RenderRow(
                3,
                3,
                "With subgoal",
                True,
                True,
                [child(4)],
                {"Progress": "50% (1/2)", "Id": "3"},
            ),
            RenderRow(
                4,
                4,
                "Top goal",
                False,
                False,
                [],
                {"Progress": "100% (1/1)", "Id": "4"},
            ),
        ],
        roots={1},
    )
