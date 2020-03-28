from siebenapp.goaltree import Goals
from siebenapp.domain import EdgeType, HoldSelect, ToggleClose, Delete, ToggleLink
from siebenapp.tests.dsl import build_goaltree, open_, selected, previous
from siebenapp.zoom import Zoom


def test_single_goal_could_not_be_zoomed():
    goals = Zoom(Goals("Root"))
    assert goals.q() == {1: {"name": "Root"}}
    goals.toggle_zoom()
    assert goals.q() == {1: {"name": "Root"}}


def test_skip_intermediate_goal_during_zoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Hidden", [3]),
            open_(3, "Zoomed", select=selected),
        )
    )
    goals.toggle_zoom()
    assert goals.q(keys="name,edge") == {
        -1: {"name": "Root", "edge": [(3, EdgeType.BLOCKER)]},
        3: {"name": "Zoomed", "edge": []},
    }


def test_hide_neighbour_goals_during_zoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2, 3, 4]),
            open_(2, "Zoomed", select=selected),
            open_(3, "Hidden 1"),
            open_(4, "Hidden 2"),
        )
    )
    goals.toggle_zoom()
    assert goals.q(keys="name,edge") == {
        -1: {"name": "Root", "edge": [(2, EdgeType.BLOCKER)]},
        2: {"name": "Zoomed", "edge": []},
    }


def test_do_not_hide_subgoals():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Zoomed", [3], select=selected),
            open_(3, "Visible"),
        )
    )
    goals.toggle_zoom()
    assert goals.q(keys="name,edge") == {
        -1: {"name": "Root", "edge": [(2, EdgeType.BLOCKER)]},
        2: {"name": "Zoomed", "edge": [(3, EdgeType.PARENT)]},
        3: {"name": "Visible", "edge": []},
    }
    goals.add("More children", 3)
    assert goals.q(keys="name,edge") == {
        -1: {"name": "Root", "edge": [(2, EdgeType.BLOCKER)]},
        2: {"name": "Zoomed", "edge": [(3, EdgeType.PARENT)]},
        3: {"name": "Visible", "edge": [(4, EdgeType.PARENT)]},
        4: {"name": "More children", "edge": []},
    }


def test_hide_subgoals_of_blockers():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2, 3]),
            open_(2, "Zoomed", blockers=[3], select=selected),
            open_(3, "Blocker", [4]),
            open_(4, "Should be hidden"),
        )
    )
    goals.toggle_zoom()
    assert goals.q(keys="name,edge,switchable") == {
        -1: {"name": "Root", "edge": [(2, EdgeType.BLOCKER)], "switchable": False},
        2: {"name": "Zoomed", "edge": [(3, EdgeType.BLOCKER)], "switchable": False},
        3: {"name": "Blocker", "edge": [], "switchable": False},
    }


def test_double_zoom_means_unzoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2, 3]),
            open_(2, "Zoomed", select=selected),
            open_(3, "Hidden"),
        )
    )
    goals.toggle_zoom()
    assert goals.q() == {
        -1: {"name": "Root"},
        2: {"name": "Zoomed"},
    }
    goals.toggle_zoom()
    assert goals.q("name,edge") == {
        1: {"name": "Root", "edge": [(2, EdgeType.PARENT), (3, EdgeType.PARENT)]},
        2: {"name": "Zoomed", "edge": []},
        3: {"name": "Hidden", "edge": []},
    }


def test_stacked_zoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Skip me", [3]),
            open_(3, "Intermediate zoom", [4], select=selected),
            open_(4, "Next zoom", [5]),
            open_(5, "Top"),
        )
    )
    goals.toggle_zoom()
    goals.select(4)
    goals.toggle_zoom()
    assert set(goals.q().keys()) == {-1, 4, 5}
    goals.toggle_zoom()
    # Zoom on goal 3 still exists
    assert set(goals.q().keys()) == {-1, 3, 4, 5}


def test_selection_should_not_be_changed_if_selected_goal_is_visible():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Select root", [3], select=selected),
            open_(3, "Previous selected", select=previous),
        )
    )
    goals.toggle_zoom()
    assert goals.q(keys="name,select") == {
        -1: {"name": "Root", "select": None},
        2: {"name": "Select root", "select": "select"},
        3: {"name": "Previous selected", "select": "prev"},
    }


def test_selection_should_be_changed_if_selected_goal_is_sibling_to_zoom_root():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2, 3]),
            open_(2, "Previous selected", select=previous),
            open_(3, "Zoomed", select=selected),
        )
    )
    goals.toggle_zoom()
    assert goals.events[-1] == ("hold_select", 3)
    assert goals.q("name,select") == {
        -1: {"name": "Root", "select": None},
        3: {"name": "Zoomed", "select": "select"},
    }


def test_selection_should_be_changed_if_selected_goal_is_not_a_child_of_zoom_root():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2, 4]),
            open_(2, "Blocker", [3]),
            open_(3, "Previous selected", select=previous),
            open_(4, "Zoomed", blockers=[2], select=selected),
        )
    )
    goals.toggle_zoom()
    assert goals.events[-1] == ("hold_select", 4)
    assert goals.q("name,select") == {
        -1: {"name": "Root", "select": None},
        2: {"name": "Blocker", "select": None},
        4: {"name": "Zoomed", "select": "select"},
    }


def test_selection_should_be_changed_on_stacked_unzoom_a_long_chain_of_blockers():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", blockers=[2]),
            open_(2, "A", blockers=[3], select=selected),
            open_(3, "D", blockers=[4]),
            open_(4, "E"),
        )
    )
    goals.toggle_zoom()  # zoom on 2
    goals.select(3)
    goals.toggle_zoom()  # zoom on 3
    goals.select(4)
    goals.accept(HoldSelect())  # set previous selection onto 4
    goals.select(3)
    goals.toggle_zoom()  # unzoom on 3 (zoom root is on 2 again)
    assert goals.q("name,select") == {
        -1: {"name": "Root", "select": None},
        2: {"name": "A", "select": None},
        3: {"name": "D", "select": "select"},
    }
    assert goals.verify()


def test_unlink_for_goal_outside_of_zoomed_tree_should_cause_selection_change():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2, 3]),
            open_(2, "Out of zoom"),
            open_(3, "Zoom root", blockers=[2], select=selected),
        )
    )
    goals.toggle_zoom()
    goals.accept(HoldSelect())
    goals.select(2)
    goals.accept(ToggleLink())  # unlink 3 -> 2
    assert goals.q("name,select") == {
        -1: {"name": "Root", "select": None},
        3: {"name": "Zoom root", "select": "select"},
    }


def test_closing_zoom_root_should_cause_unzoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Intermediate", [3]),
            open_(3, "Zoom here", select=selected),
        )
    )
    goals.toggle_zoom()
    goals.accept(ToggleClose())
    assert goals.q(keys="name,select,open") == {
        1: {"name": "Root", "select": "select", "open": True},
        2: {"name": "Intermediate", "select": None, "open": True},
        3: {"name": "Zoom here", "select": None, "open": False},
    }


def test_goal_closing_must_not_cause_root_selection():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Zoom root", [3], select=selected),
            open_(3, "Close me"),
        )
    )
    goals.toggle_zoom()
    assert goals.q(keys="name,select,open") == {
        -1: {"name": "Root", "select": None, "open": True},
        2: {"name": "Zoom root", "select": "select", "open": True},
        3: {"name": "Close me", "select": None, "open": True},
    }
    goals.select(3)
    goals.accept(ToggleClose())
    assert goals.q(keys="name,select,open") == {
        -1: {"name": "Root", "select": None, "open": True},
        2: {"name": "Zoom root", "select": "select", "open": True},
        3: {"name": "Close me", "select": None, "open": False},
    }


def test_goal_reopening_must_not_change_selection():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Zoom root", [3], select=selected),
            open_(3, "Reopen me"),
        )
    )
    goals.toggle_zoom()
    goals.select(3)
    goals.accept(ToggleClose())
    assert goals.q(keys="name,select,open") == {
        -1: {"name": "Root", "select": None, "open": True},
        2: {"name": "Zoom root", "select": "select", "open": True},
        3: {"name": "Reopen me", "select": None, "open": False},
    }
    goals.select(3)
    goals.accept(ToggleClose())
    assert goals.q(keys="name,select,open") == {
        -1: {"name": "Root", "select": None, "open": True},
        2: {"name": "Zoom root", "select": "prev", "open": True},
        3: {"name": "Reopen me", "select": "select", "open": True},
    }


def test_deleting_zoom_root_should_cause_unzoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Intermediate", [3]),
            open_(3, "Zoom here", select=selected),
        )
    )
    goals.toggle_zoom()
    goals.accept(Delete())
    assert goals.q(keys="name,select,open") == {
        1: {"name": "Root", "select": "select", "open": True},
        2: {"name": "Intermediate", "select": None, "open": True},
    }


def test_goal_deletion_must_not_cause_root_selection():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Hidden", [3]),
            open_(3, "Zoom root", [4], select=selected),
            open_(4, "Deleted"),
        )
    )
    goals.toggle_zoom()
    assert goals.q(keys="name,select") == {
        -1: {"name": "Root", "select": None},
        3: {"name": "Zoom root", "select": "select"},
        4: {"name": "Deleted", "select": None},
    }
    goals.select(4)
    goals.accept(Delete())
    assert goals.q(keys="name,select") == {
        -1: {"name": "Root", "select": None},
        3: {"name": "Zoom root", "select": "select"},
    }


def test_zoom_events():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "First zoom", [3], select=selected),
            open_(3, "Intermediate", [4]),
            open_(4, "Second zoom", [5]),
            open_(5, "Top"),
        )
    )
    goals.toggle_zoom()
    assert goals.events[-1] == ("zoom", 2, 2)
    goals.select(4)
    goals.accept(HoldSelect())
    goals.toggle_zoom()
    assert goals.events[-1] == ("zoom", 3, 4)
    goals.toggle_zoom()
    assert goals.events[-1] == ("unzoom", 4)
