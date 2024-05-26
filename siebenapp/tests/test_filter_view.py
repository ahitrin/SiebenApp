from _pytest.fixtures import fixture

from siebenapp.domain import Select, HoldSelect, child, blocker, RenderRow, RenderResult
from siebenapp.filter_view import FilterBy, FilterView
from siebenapp.tests.dsl import build_goaltree, open_, selected
from siebenapp.zoom import Zoom, ToggleZoom


@fixture
def goaltree():
    return FilterView(
        build_goaltree(
            open_(1, "Alpha", [2], [], [], selected),
            open_(2, "Beta", [3]),
            open_(3, "Gamma", []),
        )
    )


@fixture
def zoomed_goaltree():
    return FilterView(
        Zoom(
            build_goaltree(
                open_(1, "Alpha", [2], [], [], selected),
                open_(2, "Beta", [3]),
                open_(3, "Gamma", []),
            )
        )
    )


def test_empty_string_means_no_filter(goaltree) -> None:
    goaltree.accept(FilterBy(""))
    assert goaltree.q() == RenderResult(
        [
            RenderRow(1, 1, "Alpha", True, False, [child(2)]),
            RenderRow(2, 2, "Beta", True, False, [child(3)]),
            RenderRow(3, 3, "Gamma", True, True, []),
        ],
        select=(1, 1),
        roots={1},
    )


def test_filter_by_substring(goaltree) -> None:
    goaltree.accept(FilterBy("ph"))
    assert goaltree.q() == RenderResult(
        [
            RenderRow(1, 1, "Alpha", True, False, [], {"Filter": "ph"}),
        ],
        select=(1, 1),
        roots={1},
    )


def test_selected_goal_must_not_be_filtered_out(goaltree) -> None:
    goaltree.accept_all(Select(3), HoldSelect(), FilterBy("Be"))
    assert goaltree.q() == RenderResult(
        [
            RenderRow(2, 2, "Beta", True, False, [child(3)], {"Filter": "be"}),
            RenderRow(3, 3, "Gamma", True, True, []),
        ],
        select=(3, 3),
        roots={2},
    )


def test_show_fake_goal_when_filter_matches_nothing(goaltree) -> None:
    goaltree.accept_all(Select(3), FilterBy("matching no one"))
    assert goaltree.q() == RenderResult(
        [
            RenderRow(1, 1, "Alpha", True, False, []),
            RenderRow(3, 3, "Gamma", True, True, []),
            RenderRow(-2, -2, "Filter by 'matching no one'", True, False, []),
        ],
        select=(3, 1),
        roots={1, 3, -2},
    )


def test_zoomed_parent_goal_must_not_be_filtered_out(zoomed_goaltree) -> None:
    zoomed_goaltree.accept_all(HoldSelect(), Select(2), ToggleZoom(), FilterBy("mm"))
    assert zoomed_goaltree.q() == RenderResult(
        [
            RenderRow(2, 2, "Beta", True, False, [child(3)], {"Zoom": "Alpha"}),
            RenderRow(3, 3, "Gamma", True, True, [], {"Filter": "mm"}),
            RenderRow(-1, -1, "Alpha", True, False, [blocker(2)]),
        ],
        select=(2, -1),
        roots={-1},
    )


def test_empty_filter_string_means_resetting(goaltree) -> None:
    goaltree.accept_all(FilterBy("B"), FilterBy(""))
    assert goaltree.q() == RenderResult(
        [
            RenderRow(1, 1, "Alpha", True, False, [child(2)]),
            RenderRow(2, 2, "Beta", True, False, [child(3)]),
            RenderRow(3, 3, "Gamma", True, True, []),
        ],
        select=(1, 1),
        roots={1},
    )


def test_filter_is_case_insensitive(goaltree) -> None:
    goaltree.accept(FilterBy("ETA"))
    assert goaltree.q() == RenderResult(
        [
            RenderRow(1, 1, "Alpha", True, False, [child(2)]),
            RenderRow(2, 2, "Beta", True, False, [], {"Filter": "eta"}),
        ],
        select=(1, 1),
        roots={1},
    )
