from _pytest.fixtures import fixture

from siebenapp.domain import Select, ToggleClose
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
    assert goaltree.q("name") == {
        1: {"name": "Root"},
        2: {"name": "With blocker"},
        3: {"name": "With subgoal"},
        4: {"name": "Top goal"},
    }


def test_show_progress(goaltree):
    goaltree.accept(ToggleProgress())
    assert goaltree.q("name") == {
        1: {"name": "[0/4] Root"},
        2: {"name": "[0/1] With blocker"},
        3: {"name": "[0/2] With subgoal"},
        4: {"name": "[0/1] Top goal"},
    }


def test_toggle_hide_progress(goaltree):
    goaltree.accept_all(ToggleProgress(), ToggleProgress())
    assert goaltree.q("name") == {
        1: {"name": "Root"},
        2: {"name": "With blocker"},
        3: {"name": "With subgoal"},
        4: {"name": "Top goal"},
    }


def test_change_progress_on_close(goaltree):
    goaltree.accept_all(ToggleProgress(), Select(4), ToggleClose())
    assert goaltree.q("name") == {
        1: {"name": "[1/4] Root"},
        2: {"name": "[0/1] With blocker"},
        3: {"name": "[1/2] With subgoal"},
        4: {"name": "[1/1] Top goal"},
    }
    goaltree.accept_all(Select(2), ToggleClose())
    assert goaltree.q("name") == {
        1: {"name": "[2/4] Root"},
        2: {"name": "[1/1] With blocker"},
        3: {"name": "[1/2] With subgoal"},
        4: {"name": "[1/1] Top goal"},
    }
