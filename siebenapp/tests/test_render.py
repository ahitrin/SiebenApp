import pytest

from siebenapp.enumeration import Enumeration
from siebenapp.switchable_view import ToggleSwitchableView, SwitchableView
from siebenapp.domain import EdgeType
from siebenapp.render import Renderer
from siebenapp.tests.dsl import build_goaltree, open_, selected


def get_in(data, column):
    return {k: v[column] for k, v in data.items()}


def test_render_simplest_goal_tree():
    goals = build_goaltree(open_(1, "Alone", [], select=selected))
    result = Renderer(goals).build().graph
    assert result == {
        1: {
            "row": 0,
            "col": 0,
            "col1": 0,
            "edge": [],
            "name": "Alone",
            "open": True,
            "select": "select",
            "switchable": True,
        }
    }


def test_render_4_subgoals_in_a_row():
    goals = build_goaltree(
        open_(1, "Root", [2, 3, 4, 5], select=selected),
        open_(2, "A"),
        open_(3, "B"),
        open_(4, "C"),
        open_(5, "D"),
    )
    result = Renderer(goals).build().graph
    assert get_in(result, "row") == {
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        1: 1,
    }


def test_render_add_fake_vertex():
    goals = build_goaltree(
        open_(1, "Root", [2, 3], select=selected),
        open_(2, "A", blockers=[3]),
        open_(3, "B"),
    )
    result = Renderer(goals).build().graph
    assert get_in(result, "row") == {
        3: 0,
        2: 1,
        "1_1": 1,
        1: 2,
    }


def test_render_add_several_fake_vertex():
    goals = build_goaltree(
        open_(1, "Root", [2, 5], select=selected),
        open_(2, "A", [3]),
        open_(3, "B", [4]),
        open_(4, "C", blockers=[5]),
        open_(5, "top"),
    )
    result = Renderer(goals).build().graph
    assert get_in(result, "row") == {
        5: 0,
        4: 1,
        "1_1": 1,
        3: 2,
        "1_2": 2,
        2: 3,
        "1_3": 3,
        1: 4,
    }


def test_render_5_subgoals_in_several_rows():
    goals = build_goaltree(
        open_(1, "One", [2, 3, 4, 5, 6], select=selected),
        open_(2, "Two"),
        open_(3, "Three"),
        open_(4, "Four"),
        open_(5, "Five"),
        open_(6, "Six"),
    )
    result = Renderer(goals).build().graph
    assert get_in(result, "row") == {
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 1,
        "1_1": 1,
        1: 2,
    }


def test_split_long_edges_using_fake_goals():
    goals = build_goaltree(
        open_(1, "Root", [2], blockers=[5], select=selected),
        open_(2, "A", [3]),
        open_(3, "B", [4]),
        open_(4, "C", [5]),
        open_(5, "top"),
    )
    result = Renderer(goals).build().graph
    assert get_in(result, "edge") == {
        5: [],
        4: [(5, EdgeType.PARENT)],
        "1_1": [(5, EdgeType.BLOCKER)],
        3: [(4, EdgeType.PARENT)],
        "1_2": [("1_1", EdgeType.BLOCKER)],
        2: [(3, EdgeType.PARENT)],
        "1_3": [("1_2", EdgeType.BLOCKER)],
        1: [(2, EdgeType.PARENT), ("1_3", EdgeType.BLOCKER)],
    }


def test_use_different_long_edge_types():
    goals = build_goaltree(
        open_(1, "Root", [2], [3], select=selected),
        open_(2, "A", [3]),
        open_(3, "B", []),
    )
    result = Renderer(goals).build().graph
    assert get_in(result, "edge") == {
        3: [],
        2: [(3, EdgeType.PARENT)],
        "1_1": [(3, EdgeType.BLOCKER)],
        1: [(2, EdgeType.PARENT), ("1_1", EdgeType.BLOCKER)],
    }


def test_balance_upper_level():
    goals = build_goaltree(
        open_(1, "Root", [2, 3, 4], select=selected),
        open_(2, "A", blockers=[5]),
        open_(3, "B", blockers=[5]),
        open_(4, "C", [5]),
        open_(5, "Top"),
    )
    result = Renderer(goals).build().graph
    # Top goal should be placed in the middle of the layer
    assert result[5]["col"] == 1


def test_render_in_switchable_view():
    goals = build_goaltree(
        open_(1, "Uno", [2, 3, 4, 5, 6]),
        open_(2, "Dos"),
        open_(3, "Tres"),
        open_(4, "Quatro"),
        open_(5, "Cinco"),
        open_(6, "Sext", select=selected),
    )
    view = Enumeration(SwitchableView(goals))
    view.accept(ToggleSwitchableView())
    result = Renderer(view).build().graph
    # Just verify that it renders fine
    assert len(result) == 5


@pytest.mark.parametrize(
    "before,after",
    [
        ({1: 0}, [1]),
        ({5: 1, 6: 0, 3: 2}, [6, 5, 3]),
        ({3: 0, 4: 0, 2: 0}, [2, 3, 4]),
        ({5: 1}, [None, 5]),
        ({6: 0, 3: 3}, [6, None, None, 3]),
        ({6: 1, 3: 4}, [6, None, None, 3]),
        ({6: 1, 3: 12}, [6, None, None, 3]),
        ({17: 0, 16: 1, 18: 2, 22: 2, 24: 0}, [17, 24, 16, 18, 22]),
    ],
)
def test_place(before, after):
    r = Renderer(build_goaltree(open_(1, "Root", select=selected)), 4)
    # NB: do we still need to test internal implementation of Renderer?
    # Not sure
    assert after == r.place(before)
