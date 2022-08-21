from typing import List, Tuple

from siebenapp.domain import (
    EdgeType,
    HoldSelect,
    ToggleClose,
    Delete,
    ToggleLink,
    Add,
    Select,
    Graph,
    child,
    blocker,
)
from siebenapp.goaltree import Goals
from siebenapp.tests.dsl import build_goaltree, open_, selected, previous, clos_
from siebenapp.zoom import Zoom, ToggleZoom


def _zoom_events(goals: Graph) -> List[Tuple]:
    return [e for e in goals.events() if "zoom" in e[0]]


def test_single_goal_could_not_be_zoomed():
    goals = Zoom(Goals("Root"))
    assert goals.q().slice("name") == {1: {"name": "Root"}}
    goals.accept(ToggleZoom())
    assert goals.q().slice("name") == {1: {"name": "Root"}}
    assert goals.settings("root") == 1


def test_skip_intermediate_goal_during_zoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Hidden", [3]),
            open_(3, "Zoomed", select=selected),
        )
    )
    goals.accept(ToggleZoom())
    assert goals.q().slice(keys="name,edge") == {
        -1: {"name": "Root", "edge": [blocker(3)]},
        3: {"name": "Zoomed", "edge": []},
    }
    assert goals.settings("root") == -1


def test_hide_neighbour_goals_during_zoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2, 3, 4]),
            open_(2, "Zoomed", select=selected),
            open_(3, "Hidden 1"),
            open_(4, "Hidden 2"),
        )
    )
    goals.accept(ToggleZoom())
    assert goals.q().slice(keys="name,edge") == {
        -1: {"name": "Root", "edge": [blocker(2)]},
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
    goals.accept(ToggleZoom())
    assert goals.q().slice(keys="name,edge") == {
        -1: {"name": "Root", "edge": [blocker(2)]},
        2: {"name": "Zoomed", "edge": [child(3)]},
        3: {"name": "Visible", "edge": []},
    }
    goals.accept(Add("More children", 3))
    assert goals.q().slice(keys="name,edge") == {
        -1: {"name": "Root", "edge": [blocker(2)]},
        2: {"name": "Zoomed", "edge": [child(3)]},
        3: {"name": "Visible", "edge": [child(4)]},
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
    goals.accept(ToggleZoom())
    assert goals.q().slice(keys="name,edge,switchable") == {
        -1: {"name": "Root", "edge": [blocker(2)], "switchable": False},
        2: {"name": "Zoomed", "edge": [blocker(3)], "switchable": False},
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
    goals.accept(ToggleZoom())
    assert goals.q().slice("name") == {
        -1: {"name": "Root"},
        2: {"name": "Zoomed"},
    }
    goals.accept(ToggleZoom())
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [child(2), child(3)]},
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
    goals.accept_all(ToggleZoom(), Select(4), ToggleZoom())
    assert goals.q().slice("edge") == {
        -1: {"edge": [blocker(3), blocker(4)]},
        3: {"edge": [child(4)]},
        4: {"edge": [child(5)]},
        5: {"edge": []},
    }
    goals.accept(ToggleZoom())
    # Zoom on goal 3 still exists
    assert goals.q().slice("edge") == {
        -1: {"edge": [blocker(3)]},
        3: {"edge": [child(4)]},
        4: {"edge": [child(5)]},
        5: {"edge": []},
    }


def test_selection_should_not_be_changed_if_selected_goal_is_visible():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Select root", [3], select=selected),
            open_(3, "Previous selected", select=previous),
        )
    )
    goals.accept(ToggleZoom())
    assert goals.q().slice(keys="name,edge,select") == {
        -1: {"name": "Root", "edge": [blocker(2)], "select": None},
        2: {"name": "Select root", "edge": [child(3)], "select": "select"},
        3: {"name": "Previous selected", "edge": [], "select": "prev"},
    }


def test_selection_should_not_be_changed_if_selected_goal_is_sibling_to_zoom_root():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2, 3]),
            open_(2, "Previous selected", select=previous),
            open_(3, "Zoomed", select=selected),
        )
    )
    goals.accept(ToggleZoom())
    assert goals.events()[-1] == ("zoom", 2, 3)
    assert goals.q().slice("name,edge,select") == {
        -1: {
            "name": "Root",
            "edge": [blocker(2), blocker(3)],
            "select": None,
        },
        2: {"name": "Previous selected", "edge": [], "select": "prev"},
        3: {"name": "Zoomed", "edge": [], "select": "select"},
    }


def test_selection_should_not_be_changed_if_selected_goal_is_not_a_child_of_zoom_root():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2, 4]),
            open_(2, "Blocker", [3]),
            open_(3, "Previous selected", select=previous),
            open_(4, "Zoomed", blockers=[2], select=selected),
        )
    )
    goals.accept(ToggleZoom())
    assert goals.events()[-1] == ("zoom", 2, 4)
    assert goals.q().slice("name,edge,select") == {
        -1: {
            "name": "Root",
            "edge": [blocker(3), blocker(4)],
            "select": None,
        },
        2: {"name": "Blocker", "edge": [child(3)], "select": None},
        3: {"name": "Previous selected", "edge": [], "select": "prev"},
        4: {"name": "Zoomed", "edge": [blocker(2)], "select": "select"},
    }


def test_previous_selection_should_not_be_changed_or_reset_after_zoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "", blockers=[2, 3]),
            open_(2, "", [4]),
            open_(3, "", [2], select=selected),
            open_(4, "", blockers=[5], select=previous),
            open_(5, ""),
        )
    )
    goals.verify()
    goals.accept(ToggleZoom())
    goals.verify()
    # Currently, we cannot make such move via user interface because goal 3 is hidden
    goals.accept(ToggleLink(3, 2, EdgeType.BLOCKER))
    goals.verify()


def test_selection_should_not_be_changed_on_stacked_unzoom_a_long_chain_of_blockers():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", blockers=[2]),
            open_(2, "A", blockers=[3], select=selected),
            open_(3, "D", blockers=[4]),
            open_(4, "E"),
        )
    )
    goals.accept_all(
        ToggleZoom(),  # zoom on 2/A
        Select(3),
        ToggleZoom(),  # zoom on 3/D
        Select(4),
        HoldSelect(),  # set previous selection onto 4/E
        Select(3),
        ToggleZoom(),  # unzoom on 3/D (zoom root is on 2/A again))
    )
    assert goals.q().slice("name,edge,select") == {
        -1: {
            "name": "Root",
            "edge": [blocker(2), blocker(4)],
            "select": None,
        },
        2: {"name": "A", "edge": [blocker(3)], "select": None},
        3: {"name": "D", "edge": [blocker(4)], "select": "select"},
        4: {"name": "E", "edge": [], "select": "prev"},
    }
    goals.verify()


def test_unlink_for_goal_outside_of_zoomed_tree_should_not_cause_selection_change():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2, 3]),
            open_(2, "Out of zoom"),
            open_(3, "Zoom root", blockers=[2], select=selected),
        )
    )
    goals.accept_all(
        ToggleZoom(),
        HoldSelect(),
        Select(2),
        ToggleLink(),  # unlink 3 -> 2
    )
    assert goals.q().slice("name,edge,select") == {
        -1: {
            "name": "Root",
            "edge": [blocker(2), blocker(3)],
            "select": None,
        },
        2: {"name": "Out of zoom", "edge": [], "select": "select"},
        3: {"name": "Zoom root", "edge": [], "select": "prev"},
    }


def test_closing_zoom_root_should_cause_unzoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Intermediate", [3]),
            open_(3, "Zoom here", select=selected),
        )
    )
    goals.accept_all(ToggleZoom(), ToggleClose())
    assert goals.q().slice(keys="name,edge,select,open") == {
        1: {
            "name": "Root",
            "edge": [child(2)],
            "select": None,
            "open": True,
        },
        2: {
            "name": "Intermediate",
            "edge": [child(3)],
            "select": "select",
            "open": True,
        },
        3: {"name": "Zoom here", "edge": [], "select": None, "open": False},
    }


def test_goal_closing_must_not_cause_root_selection():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Zoom root", [3], select=selected),
            open_(3, "Close me"),
        )
    )
    goals.accept(ToggleZoom())
    assert goals.q().slice(keys="name,edge,select,open") == {
        -1: {
            "name": "Root",
            "edge": [blocker(2)],
            "select": None,
            "open": True,
        },
        2: {
            "name": "Zoom root",
            "edge": [child(3)],
            "select": "select",
            "open": True,
        },
        3: {"name": "Close me", "edge": [], "select": None, "open": True},
    }
    goals.accept_all(Select(3), ToggleClose())
    assert goals.q().slice(keys="name,edge,select,open") == {
        -1: {
            "name": "Root",
            "edge": [blocker(2)],
            "select": None,
            "open": True,
        },
        2: {
            "name": "Zoom root",
            "edge": [child(3)],
            "select": "select",
            "open": True,
        },
        3: {"name": "Close me", "edge": [], "select": None, "open": False},
    }


def test_goal_reopening_must_not_change_selection():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Zoom root", [3], select=selected),
            open_(3, "Reopen me"),
        )
    )
    goals.accept_all(
        ToggleZoom(),
        Select(3),
        ToggleClose(),
    )
    assert goals.q().slice(keys="name,edge,select,open") == {
        -1: {
            "name": "Root",
            "edge": [blocker(2)],
            "select": None,
            "open": True,
        },
        2: {
            "name": "Zoom root",
            "edge": [child(3)],
            "select": "select",
            "open": True,
        },
        3: {"name": "Reopen me", "edge": [], "select": None, "open": False},
    }
    goals.accept_all(Select(3), ToggleClose())
    assert goals.q().slice(keys="name,edge,select,open") == {
        -1: {
            "name": "Root",
            "edge": [blocker(2)],
            "select": None,
            "open": True,
        },
        2: {
            "name": "Zoom root",
            "edge": [child(3)],
            "select": "prev",
            "open": True,
        },
        3: {"name": "Reopen me", "edge": [], "select": "select", "open": True},
    }


def test_deleting_zoom_root_should_cause_unzoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Intermediate", [3]),
            open_(3, "Zoom here", select=selected),
        )
    )
    goals.accept_all(ToggleZoom(), Delete())
    assert goals.q().slice(keys="name,edge,select,open") == {
        1: {
            "name": "Root",
            "edge": [child(2)],
            "select": None,
            "open": True,
        },
        2: {"name": "Intermediate", "edge": [], "select": "select", "open": True},
    }


def test_deleting_parent_goal_should_cause_unzoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Intermediate", [3], select=previous),
            open_(3, "Zoom here", [4], select=selected),
            open_(4, "Next zoom", [5]),
            open_(5, "Final zoom"),
        )
    )
    goals.accept_all(ToggleZoom(), Select(4), ToggleZoom(), Select(5), ToggleZoom())
    assert goals.q().slice(keys="name,edge,select") == {
        -1: {
            "name": "Root",
            "edge": [blocker(2), blocker(5)],
            "select": None,
        },
        2: {"name": "Intermediate", "edge": [], "select": "prev"},
        5: {"name": "Final zoom", "edge": [], "select": "select"},
    }
    assert _zoom_events(goals) == [
        ("zoom", 2, 3),
        ("zoom", 3, 4),
        ("zoom", 4, 5),
    ]
    goals.accept_all(Select(2), Delete())
    assert goals.q().slice(keys="name,edge,select") == {
        1: {
            "name": "Root",
            "edge": [],
            "select": "select",
        },
    }
    assert _zoom_events(goals) == [
        ("zoom", 2, 3),
        ("zoom", 3, 4),
        ("zoom", 4, 5),
        ("unzoom", 5),
        ("unzoom", 4),
        ("unzoom", 3),
    ]


def test_goal_deletion_must_not_cause_root_selection():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Hidden", [3]),
            open_(3, "Zoom root", [4], select=selected),
            open_(4, "Deleted"),
        )
    )
    goals.accept(ToggleZoom())
    assert goals.q().slice(keys="name,edge,select") == {
        -1: {"name": "Root", "edge": [blocker(3)], "select": None},
        3: {"name": "Zoom root", "edge": [child(4)], "select": "select"},
        4: {"name": "Deleted", "edge": [], "select": None},
    }
    goals.accept_all(Select(4), Delete())
    assert goals.q().slice(keys="name,edge,select") == {
        -1: {"name": "Root", "edge": [blocker(3)], "select": None},
        3: {"name": "Zoom root", "edge": [], "select": "select"},
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
    goals.accept(ToggleZoom())
    assert goals.events()[-1] == ("zoom", 2, 2)
    goals.accept_all(Select(4), HoldSelect(), ToggleZoom())
    assert goals.events()[-1] == ("zoom", 3, 4)
    goals.accept(ToggleZoom())
    assert goals.events()[-1] == ("unzoom", 4)
    goals.accept_all(Select(5), ToggleClose())
    assert goals.events()[-2] == ("toggle_close", False, 5)
    assert goals.events()[-1] == ("select", 4)


def test_do_not_duplicate_parent_prev_selection():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2], select=previous),
            open_(2, "Zoom root", select=selected),
        )
    )
    assert goals.selections() == {1, 2}
    goals.accept(ToggleZoom())
    assert goals.q().slice("name,edge,select") == {
        -1: {"name": "Root", "edge": [blocker(2)], "select": "prev"},
        2: {"name": "Zoom root", "edge": [], "select": "select"},
    }
    assert goals.selections() == {-1, 2}


def test_zoom_root_must_not_be_switchable():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2], select=previous),
            clos_(2, "Closed", [], select=selected),
        )
    )
    assert goals.q().slice("switchable") == {
        1: {"switchable": True},
        2: {"switchable": True},
    }
    goals.accept(ToggleZoom())
    assert goals.q().slice("switchable") == {
        -1: {"switchable": False},
        2: {"switchable": True},
    }


def test_zoom_attempt_out_of_stack():
    messages = []
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2, 3]),
            open_(2, "Selected and out of tree", select=previous),
            open_(3, "Zoom root", [4], select=selected),
            open_(4, "Top"),
            message_fn=messages.append,
        )
    )
    goals.accept_all(ToggleZoom(), Select(2), HoldSelect())
    expected = {
        -1: {
            "name": "Root",
            "edge": [blocker(2), blocker(3)],
            "select": None,
        },
        2: {"name": "Selected and out of tree", "edge": [], "select": "select"},
        3: {"name": "Zoom root", "edge": [child(4)], "select": None},
        4: {"name": "Top", "edge": [], "select": None},
    }
    assert goals.q().slice("name,select,edge") == expected
    # Try to zoom out of current stack should not be allowed!
    goals.accept(ToggleZoom())
    assert goals.q().slice("name,select,edge") == expected
    assert len(messages) == 1
