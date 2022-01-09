from _pytest.fixtures import fixture

from siebenapp.domain import EdgeType, Select, HoldSelect
from siebenapp.filter_view import FilterBy, FilterView
from siebenapp.tests.dsl import build_goaltree, open_, selected


@fixture
def goaltree():
    return FilterView(
        build_goaltree(
            open_(1, "Alpha", [2], [], selected),
            open_(2, "Beta", [3]),
            open_(3, "Gamma", []),
        )
    )


def test_empty_string_means_no_filter(goaltree):
    goaltree.accept(FilterBy(""))
    assert goaltree.q("name,edge,select") == {
        1: {"name": "Alpha", "edge": [(2, EdgeType.PARENT)], "select": "select"},
        2: {"name": "Beta", "edge": [(3, EdgeType.PARENT)], "select": None},
        3: {"name": "Gamma", "edge": [], "select": None},
    }


def test_filter_by_substring(goaltree):
    goaltree.accept(FilterBy("ph"))
    assert goaltree.q("name,edge,select,open,switchable") == {
        1: {
            "name": "Alpha",
            "edge": [(-2, EdgeType.BLOCKER)],
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


def test_selected_goal_must_not_be_filtered_out(goaltree):
    goaltree.accept_all(Select(3), HoldSelect(), FilterBy("Be"))
    assert goaltree.q("name,edge,select") == {
        -2: {
            "name": "Filter by 'be'",
            "edge": [(2, EdgeType.BLOCKER), (3, EdgeType.BLOCKER)],
            "select": None,
        },
        2: {"name": "Beta", "edge": [(3, EdgeType.PARENT)], "select": None},
        3: {"name": "Gamma", "edge": [], "select": "select"},
    }


def test_previously_selected_goal_must_not_be_filtered_out(goaltree):
    goaltree.accept_all(Select(3), FilterBy("matching no one"))
    assert goaltree.q("name,edge,select") == {
        1: {"name": "Alpha", "edge": [(-2, EdgeType.BLOCKER)], "select": "prev"},
        -2: {
            "name": "Filter by 'matching no one'",
            "edge": [(3, EdgeType.BLOCKER)],
            "select": None,
        },
        3: {"name": "Gamma", "edge": [], "select": "select"},
    }


def test_empty_filter_string_means_resetting(goaltree):
    goaltree.accept_all(FilterBy("B"), FilterBy(""))
    assert goaltree.q("name,edge,select") == {
        1: {"name": "Alpha", "edge": [(2, EdgeType.PARENT)], "select": "select"},
        2: {"name": "Beta", "edge": [(3, EdgeType.PARENT)], "select": None},
        3: {"name": "Gamma", "edge": [], "select": None},
    }


def test_filter_is_case_insensitive(goaltree):
    goaltree.accept(FilterBy("ETA"))
    assert goaltree.q("name,edge,select") == {
        1: {
            "name": "Alpha",
            "edge": [(-2, EdgeType.BLOCKER), (2, EdgeType.PARENT)],
            "select": "select",
        },
        -2: {
            "name": "Filter by 'eta'",
            "edge": [(2, EdgeType.BLOCKER)],
            "select": None,
        },
        2: {"name": "Beta", "edge": [], "select": None},
    }