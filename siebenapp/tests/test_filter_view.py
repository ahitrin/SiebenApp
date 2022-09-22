from _pytest.fixtures import fixture

from siebenapp.domain import Select, HoldSelect, child, blocker, RenderRow, RenderResult
from siebenapp.filter_view import FilterBy, FilterView
from siebenapp.goaltree import Goals
from siebenapp.tests.dsl import build_goaltree, open_, selected
from siebenapp.zoom import Zoom, ToggleZoom


@fixture
def goaltree():
    return FilterView(
        build_goaltree(
            open_(1, "Alpha", [2], [], selected),
            open_(2, "Beta", [3]),
            open_(3, "Gamma", []),
        )
    )


@fixture
def zoomed_goaltree():
    return FilterView(
        Zoom(
            build_goaltree(
                open_(1, "Alpha", [2], [], selected),
                open_(2, "Beta", [3]),
                open_(3, "Gamma", []),
            )
        )
    )


def test_empty_string_means_no_filter(goaltree):
    goaltree.accept(FilterBy(""))
    assert goaltree.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "Alpha", True, False, "select", [child(2)]),
            RenderRow(2, 2, "Beta", True, False, None, [child(3)]),
            RenderRow(3, 3, "Gamma", True, True, None, []),
        ]
    )
    assert goaltree.settings("root") == Goals.ROOT_ID


def test_filter_by_substring(goaltree):
    goaltree.accept(FilterBy("ph"))
    assert goaltree.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "Alpha", True, False, "select", [blocker(-2)]),
            RenderRow(-2, -2, "Filter by 'ph'", True, False, None, []),
        ]
    )
    assert goaltree.settings("root") == 1


def test_selected_goal_must_not_be_filtered_out(goaltree):
    goaltree.accept_all(Select(3), HoldSelect(), FilterBy("Be"))
    assert goaltree.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Beta", True, False, None, [child(3)]),
            RenderRow(3, 3, "Gamma", True, True, "select", []),
            RenderRow(
                -2, -2, "Filter by 'be'", True, False, None, [blocker(2), blocker(3)]
            ),
        ]
    )
    assert goaltree.settings("root") == -2


def test_previously_selected_goal_must_not_be_filtered_out(goaltree):
    goaltree.accept_all(Select(3), FilterBy("matching no one"))
    assert goaltree.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "Alpha", True, False, "prev", [blocker(-2)]),
            RenderRow(3, 3, "Gamma", True, True, "select", []),
            RenderRow(
                -2, -2, "Filter by 'matching no one'", True, False, None, [blocker(3)]
            ),
        ]
    )
    assert goaltree.settings("root") == 1


def test_zoomed_parent_goal_must_not_be_filtered_out(zoomed_goaltree):
    zoomed_goaltree.accept_all(HoldSelect(), Select(2), ToggleZoom(), FilterBy("mm"))
    assert zoomed_goaltree.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Beta", True, False, "select", [child(3)]),
            RenderRow(3, 3, "Gamma", True, True, None, []),
            RenderRow(-1, -1, "Alpha", True, False, "prev", [blocker(2), blocker(-2)]),
            RenderRow(
                -2, -2, "Filter by 'mm'", True, False, None, [blocker(2), blocker(3)]
            ),
        ]
    )
    assert zoomed_goaltree.settings("root") == -1


def test_empty_filter_string_means_resetting(goaltree):
    goaltree.accept_all(FilterBy("B"), FilterBy(""))
    assert goaltree.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "Alpha", True, False, "select", [child(2)]),
            RenderRow(2, 2, "Beta", True, False, None, [child(3)]),
            RenderRow(3, 3, "Gamma", True, True, None, []),
        ]
    )


def test_filter_is_case_insensitive(goaltree):
    goaltree.accept(FilterBy("ETA"))
    assert goaltree.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "Alpha", True, False, "select", [child(2), blocker(-2)]),
            RenderRow(2, 2, "Beta", True, False, None, []),
            RenderRow(-2, -2, "Filter by 'eta'", True, False, None, [blocker(2)]),
        ]
    )
