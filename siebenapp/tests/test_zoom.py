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
    RenderRow,
    RenderResult,
)
from siebenapp.goaltree import Goals
from siebenapp.tests.dsl import build_goaltree, open_, selected, previous, clos_
from siebenapp.zoom import Zoom, ToggleZoom


def _zoom_events(goals: Graph) -> List[Tuple]:
    return [e for e in goals.events() if "zoom" in e[0]]


def test_single_goal_could_not_be_zoomed():
    goals = Zoom(Goals("Root"))
    assert goals.q() == RenderResult(
        rows=[RenderRow(1, 1, "Root", True, True, "select", [])]
    )
    goals.accept(ToggleZoom())
    assert goals.q() == RenderResult(
        rows=[RenderRow(1, 1, "Root", True, True, "select", [])]
    )
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
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(3, 3, "Zoomed", True, True, "select", []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(3)]),
        ]
    )
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
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Zoomed", True, True, "select", []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2)]),
        ]
    )


def test_do_not_hide_subgoals():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Zoomed", [3], select=selected),
            open_(3, "Visible"),
        )
    )
    goals.accept(ToggleZoom())
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Zoomed", True, False, "select", [child(3)]),
            RenderRow(3, 3, "Visible", True, True, None, []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2)]),
        ]
    )
    goals.accept(Add("More children", 3))
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Zoomed", True, False, "select", [child(3)]),
            RenderRow(3, 3, "Visible", True, False, None, [child(4)]),
            RenderRow(4, 4, "More children", True, True, None, []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2)]),
        ]
    )


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
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Zoomed", True, False, "select", [blocker(3)]),
            RenderRow(3, 3, "Blocker", True, False, None, []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2)]),
        ]
    )


def test_double_zoom_means_unzoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2, 3]),
            open_(2, "Zoomed", select=selected),
            open_(3, "Hidden"),
        )
    )
    goals.accept(ToggleZoom())
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Zoomed", True, True, "select", []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2)]),
        ]
    )
    goals.accept(ToggleZoom())
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "Root", True, False, None, [child(2), child(3)]),
            RenderRow(2, 2, "Zoomed", True, True, "select", []),
            RenderRow(3, 3, "Hidden", True, True, None, []),
        ]
    )


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
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(3, 3, "Intermediate zoom", True, False, "prev", [child(4)]),
            RenderRow(4, 4, "Next zoom", True, False, "select", [child(5)]),
            RenderRow(5, 5, "Top", True, True, None, []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(3), blocker(4)]),
        ]
    )
    goals.accept(ToggleZoom())
    # Zoom on goal 3 still exists
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(3, 3, "Intermediate zoom", True, False, "prev", [child(4)]),
            RenderRow(4, 4, "Next zoom", True, False, "select", [child(5)]),
            RenderRow(5, 5, "Top", True, True, None, []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(3)]),
        ]
    )


def test_selection_should_not_be_changed_if_selected_goal_is_visible():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Select root", [3], select=selected),
            open_(3, "Previous selected", select=previous),
        )
    )
    goals.accept(ToggleZoom())
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Select root", True, False, "select", [child(3)]),
            RenderRow(3, 3, "Previous selected", True, True, "prev", []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2)]),
        ]
    )


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
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Previous selected", True, True, "prev", []),
            RenderRow(3, 3, "Zoomed", True, True, "select", []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2), blocker(3)]),
        ]
    )


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
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Blocker", True, False, None, [child(3)]),
            RenderRow(3, 3, "Previous selected", True, True, "prev", []),
            RenderRow(4, 4, "Zoomed", True, False, "select", [blocker(2)]),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(3), blocker(4)]),
        ]
    )


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
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "A", True, False, None, [blocker(3)]),
            RenderRow(3, 3, "D", True, False, "select", [blocker(4)]),
            RenderRow(4, 4, "E", True, True, "prev", []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2), blocker(4)]),
        ]
    )
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
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Out of zoom", True, True, "select", []),
            RenderRow(3, 3, "Zoom root", True, True, "prev", []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2), blocker(3)]),
        ]
    )


def test_closing_zoom_root_should_cause_unzoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Intermediate", [3]),
            open_(3, "Zoom here", select=selected),
        )
    )
    goals.accept_all(ToggleZoom(), ToggleClose())
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "Root", True, False, None, [child(2)]),
            RenderRow(2, 2, "Intermediate", True, True, "select", [child(3)]),
            RenderRow(3, 3, "Zoom here", False, True, None, []),
        ]
    )


def test_goal_closing_must_not_cause_root_selection():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Zoom root", [3], select=selected),
            open_(3, "Close me"),
        )
    )
    goals.accept(ToggleZoom())
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Zoom root", True, False, "select", [child(3)]),
            RenderRow(3, 3, "Close me", True, True, None, []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2)]),
        ]
    )
    goals.accept_all(Select(3), ToggleClose())
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Zoom root", True, True, "select", [child(3)]),
            RenderRow(3, 3, "Close me", False, True, None, []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2)]),
        ]
    )


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
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Zoom root", True, True, "select", [child(3)]),
            RenderRow(3, 3, "Reopen me", False, True, None, []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2)]),
        ]
    )
    goals.accept_all(Select(3), ToggleClose())
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Zoom root", True, False, "prev", [child(3)]),
            RenderRow(3, 3, "Reopen me", True, True, "select", []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2)]),
        ]
    )


def test_deleting_zoom_root_should_cause_unzoom():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Intermediate", [3]),
            open_(3, "Zoom here", select=selected),
        )
    )
    goals.accept_all(ToggleZoom(), Delete())
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "Root", True, False, None, [child(2)]),
            RenderRow(2, 2, "Intermediate", True, True, "select", []),
        ]
    )


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
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Intermediate", True, False, "prev", []),
            RenderRow(5, 5, "Final zoom", True, True, "select", []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2), blocker(5)]),
        ]
    )
    assert _zoom_events(goals) == [
        ("zoom", 2, 3),
        ("zoom", 3, 4),
        ("zoom", 4, 5),
    ]
    goals.accept_all(Select(2), Delete())
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "Root", True, True, "select", []),
        ]
    )
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
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(3, 3, "Zoom root", True, False, "select", [child(4)]),
            RenderRow(4, 4, "Deleted", True, True, None, []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(3)]),
        ]
    )
    goals.accept_all(Select(4), Delete())
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(3, 3, "Zoom root", True, True, "select", []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(3)]),
        ]
    )


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
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Zoom root", True, True, "select", []),
            RenderRow(-1, -1, "Root", True, False, "prev", [blocker(2)]),
        ]
    )
    assert goals.selections() == {-1, 2}


def test_zoom_root_must_not_be_switchable():
    goals = Zoom(
        build_goaltree(
            open_(1, "Root", [2], select=previous),
            clos_(2, "Closed", [], select=selected),
        )
    )
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "Root", True, True, "prev", [child(2)]),
            RenderRow(2, 2, "Closed", False, True, "select", []),
        ]
    )
    goals.accept(ToggleZoom())
    assert goals.q() == RenderResult(
        rows=[
            RenderRow(2, 2, "Closed", False, True, "select", []),
            RenderRow(-1, -1, "Root", True, False, "prev", [blocker(2)]),
        ]
    )


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
    expected = RenderResult(
        rows=[
            RenderRow(2, 2, "Selected and out of tree", True, True, "select", []),
            RenderRow(3, 3, "Zoom root", True, False, None, [child(4)]),
            RenderRow(4, 4, "Top", True, True, None, []),
            RenderRow(-1, -1, "Root", True, False, None, [blocker(2), blocker(3)]),
        ]
    )
    assert goals.q() == expected
    # Try to zoom out of current stack should not be allowed!
    goals.accept(ToggleZoom())
    assert goals.q() == expected
    assert len(messages) == 1
