from _pytest.fixtures import fixture

from siebenapp.domain import EdgeType, Select, HoldSelect, child, blocker
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
    assert goaltree.q().slice("name,edge,select") == {
        1: {"name": "Alpha", "edge": [child(2)], "select": "select"},
        2: {"name": "Beta", "edge": [child(3)], "select": None},
        3: {"name": "Gamma", "edge": [], "select": None},
    }
    assert goaltree.settings("root") == Goals.ROOT_ID


def test_filter_by_substring(goaltree):
    goaltree.accept(FilterBy("ph"))
    assert goaltree.q().slice("name,edge,select,open,switchable") == {
        1: {
            "name": "Alpha",
            "edge": [blocker(-2)],
            "select": "select",
            "open": True,
            "switchable": False,
        },
        -2: {
            "name": "Filter by 'ph'",
            "edge": [],
            "select": None,
            "open": True,
            "switchable": False,
        },
    }
    assert goaltree.settings("root") == 1


def test_selected_goal_must_not_be_filtered_out(goaltree):
    goaltree.accept_all(Select(3), HoldSelect(), FilterBy("Be"))
    assert goaltree.q().slice("name,edge,select") == {
        -2: {
            "name": "Filter by 'be'",
            "edge": [blocker(2), blocker(3)],
            "select": None,
        },
        2: {"name": "Beta", "edge": [child(3)], "select": None},
        3: {"name": "Gamma", "edge": [], "select": "select"},
    }
    assert goaltree.settings("root") == -2


def test_previously_selected_goal_must_not_be_filtered_out(goaltree):
    goaltree.accept_all(Select(3), FilterBy("matching no one"))
    assert goaltree.q().slice("name,edge,select") == {
        1: {"name": "Alpha", "edge": [blocker(-2)], "select": "prev"},
        -2: {
            "name": "Filter by 'matching no one'",
            "edge": [blocker(3)],
            "select": None,
        },
        3: {"name": "Gamma", "edge": [], "select": "select"},
    }
    assert goaltree.settings("root") == 1


def test_zoomed_parent_goal_must_not_be_filtered_out(zoomed_goaltree):
    zoomed_goaltree.accept_all(HoldSelect(), Select(2), ToggleZoom(), FilterBy("mm"))
    assert zoomed_goaltree.q().slice("name,edge,select") == {
        -1: {
            "name": "Alpha",
            "edge": [blocker(-2), blocker(2)],
            "select": "prev",
        },
        -2: {
            "name": "Filter by 'mm'",
            "edge": [blocker(2), blocker(3)],
            "select": None,
        },
        2: {"name": "Beta", "edge": [child(3)], "select": "select"},
        3: {"name": "Gamma", "edge": [], "select": None},
    }
    assert zoomed_goaltree.settings("root") == -1


def test_empty_filter_string_means_resetting(goaltree):
    goaltree.accept_all(FilterBy("B"), FilterBy(""))
    assert goaltree.q().slice("name,edge,select") == {
        1: {"name": "Alpha", "edge": [child(2)], "select": "select"},
        2: {"name": "Beta", "edge": [child(3)], "select": None},
        3: {"name": "Gamma", "edge": [], "select": None},
    }


def test_filter_is_case_insensitive(goaltree):
    goaltree.accept(FilterBy("ETA"))
    assert goaltree.q().slice("name,edge,select") == {
        1: {
            "name": "Alpha",
            "edge": [blocker(-2), child(2)],
            "select": "select",
        },
        -2: {
            "name": "Filter by 'eta'",
            "edge": [blocker(2)],
            "select": None,
        },
        2: {"name": "Beta", "edge": [], "select": None},
    }
