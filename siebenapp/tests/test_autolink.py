from typing import List, Tuple

import pytest

from siebenapp.autolink import AutoLink, ToggleAutoLink
from siebenapp.domain import (
    EdgeType,
    ToggleClose,
    Select,
    Add,
    HoldSelect,
    Insert,
    Rename,
    Graph,
    Delete,
    RenderRow,
)
from siebenapp.tests.dsl import build_goaltree, open_, selected, clos_


@pytest.fixture()
def tree_2_goals():
    return AutoLink(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Autolink on me", select=selected),
        )
    )


@pytest.fixture()
def tree_3v_goals():
    return AutoLink(
        build_goaltree(
            open_(1, "Root", [2, 3]),
            open_(2, "Autolink on me", select=selected),
            open_(3, "Another subgoal"),
        )
    )


@pytest.fixture()
def tree_3i_goals():
    return AutoLink(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Autolink on me", [3], select=selected),
            open_(3, "Another subgoal"),
        )
    )


def _autolink_events(goals: Graph) -> List[Tuple]:
    return [e for e in goals.events() if "autolink" in e[0]]


def test_show_new_pseudogoal_on_autolink_event(tree_2_goals):
    goals = tree_2_goals
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, False, None, [(2, EdgeType.PARENT)]),
        RenderRow(2, 2, "Autolink on me", True, True, "select", []),
    ]
    goals.accept(ToggleAutoLink("heLLO"))
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, False, None, [(-12, EdgeType.PARENT)]),
        RenderRow(2, 2, "Autolink on me", True, True, "select", []),
        RenderRow(
            -12, -1, "Autolink: 'hello'", True, False, None, [(2, EdgeType.PARENT)]
        ),
    ]
    assert _autolink_events(goals) == [("add_autolink", 2, "hello")]


def test_replace_old_autolink_with_new_one(tree_2_goals):
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink("first"), ToggleAutoLink("second"))
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, False, None, [(-12, EdgeType.PARENT)]),
        RenderRow(2, 2, "Autolink on me", True, True, "select", []),
        RenderRow(
            -12, -1, "Autolink: 'second'", True, False, None, [(2, EdgeType.PARENT)]
        ),
    ]
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "first"),
        ("remove_autolink", 2),
        ("add_autolink", 2, "second"),
    ]


def test_remove_autolink_by_sending_empty_keyword(tree_2_goals):
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink("lalala"), ToggleAutoLink(""))
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, False, None, [(2, EdgeType.PARENT)]),
        RenderRow(2, 2, "Autolink on me", True, True, "select", []),
    ]
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "lalala"),
        ("remove_autolink", 2),
    ]


def test_remove_autolink_by_sending_whitespace(tree_2_goals):
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink("lalala"), ToggleAutoLink(" "))
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, False, None, [(2, EdgeType.PARENT)]),
        RenderRow(2, 2, "Autolink on me", True, True, "select", []),
    ]
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "lalala"),
        ("remove_autolink", 2),
    ]


def test_do_not_add_autolink_on_whitespace(tree_2_goals):
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink(" "))
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, False, None, [(2, EdgeType.PARENT)]),
        RenderRow(2, 2, "Autolink on me", True, True, "select", []),
    ]
    assert _autolink_events(goals) == []


def test_do_not_add_autolink_to_closed_goals():
    messages: List[str] = []
    goals = AutoLink(
        build_goaltree(
            open_(1, "Root", [2]),
            clos_(2, "Well, it's closed", select=selected),
            message_fn=messages.append,
        )
    )
    goals.accept(ToggleAutoLink("Failed"))
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, True, None, [(2, EdgeType.PARENT)]),
        RenderRow(2, 2, "Well, it's closed", False, True, "select", []),
    ]
    assert messages == ["Autolink cannot be set for closed goals"]
    assert _autolink_events(goals) == []


def test_do_not_add_autolink_to_root_goal():
    messages: List[str] = []
    goals = AutoLink(
        build_goaltree(open_(1, "Root", select=selected), message_fn=messages.append)
    )
    goals.accept(ToggleAutoLink("misused"))
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, True, "select", []),
    ]
    assert messages == ["Autolink cannot be set for the root goal"]
    assert _autolink_events(goals) == []


def test_remove_autolink_on_close(tree_2_goals):
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("test"))
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, False, None, [(-12, EdgeType.PARENT)]),
        RenderRow(2, 2, "Autolink on me", True, True, "select", []),
        RenderRow(
            -12, -1, "Autolink: 'test'", True, False, None, [(2, EdgeType.PARENT)]
        ),
    ]
    goals.accept(ToggleClose())
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, True, "select", [(2, EdgeType.PARENT)]),
        RenderRow(2, 2, "Autolink on me", False, True, None, []),
    ]
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "test"),
        ("remove_autolink", 2),
    ]


def test_remove_autolink_on_delete(tree_2_goals):
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("test"))
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, False, None, [(-12, EdgeType.PARENT)]),
        RenderRow(2, 2, "Autolink on me", True, True, "select", []),
        RenderRow(
            -12, -1, "Autolink: 'test'", True, False, None, [(2, EdgeType.PARENT)]
        ),
    ]
    goals.accept(Delete())
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, True, "select", []),
    ]
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "test"),
        ("remove_autolink", 2),
    ]


def test_remove_autolink_on_parent_delete(tree_3i_goals):
    goals = tree_3i_goals
    goals.accept_all(Select(3), ToggleAutoLink("test"))
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, False, None, [(2, EdgeType.PARENT)]),
        RenderRow(
            2, 2, "Autolink on me", True, False, "prev", [(-13, EdgeType.PARENT)]
        ),
        RenderRow(3, 3, "Another subgoal", True, True, "select", []),
        RenderRow(
            -13, -1, "Autolink: 'test'", True, False, None, [(3, EdgeType.PARENT)]
        ),
    ]
    goals.accept_all(Select(2), Delete())
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, True, "select", []),
    ]
    assert _autolink_events(goals) == [
        ("add_autolink", 3, "test"),
        ("remove_autolink", 3),
    ]


def test_replace_same_autolink(tree_3v_goals):
    goals = tree_3v_goals
    goals.accept_all(ToggleAutoLink("same"), Select(3), ToggleAutoLink("same"))
    assert goals.q().rows == [
        RenderRow(
            1,
            1,
            "Root",
            True,
            False,
            None,
            [(2, EdgeType.PARENT), (-13, EdgeType.PARENT)],
        ),
        RenderRow(2, 2, "Autolink on me", True, True, "prev", []),
        RenderRow(3, 3, "Another subgoal", True, True, "select", []),
        RenderRow(
            -13, -1, "Autolink: 'same'", True, False, None, [(3, EdgeType.PARENT)]
        ),
    ]
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "same"),
        ("remove_autolink", 2),
        ("add_autolink", 3, "same"),
    ]


def test_do_not_make_a_link_on_not_matching_add(tree_2_goals):
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("hello"))
    # Add a goal to the root
    goals.accept_all(Select(1), Add("Goodbye"))
    assert goals.q().rows == [
        RenderRow(
            1,
            1,
            "Root",
            True,
            False,
            "select",
            [(-12, EdgeType.PARENT), (3, EdgeType.PARENT)],
        ),
        RenderRow(2, 2, "Autolink on me", True, True, "prev", []),
        RenderRow(3, 3, "Goodbye", True, True, None, []),
        RenderRow(
            -12, -1, "Autolink: 'hello'", True, False, None, [(2, EdgeType.PARENT)]
        ),
    ]
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "hello"),
    ]


def test_make_a_link_on_matching_add(tree_2_goals):
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("me"))
    # Add a goal to the root
    goals.accept_all(Select(1), Add("Link ME please"))
    assert goals.q().rows == [
        RenderRow(
            1,
            1,
            "Root",
            True,
            False,
            "select",
            [(-12, EdgeType.PARENT), (3, EdgeType.PARENT)],
        ),
        RenderRow(2, 2, "Autolink on me", True, False, "prev", [(3, EdgeType.BLOCKER)]),
        RenderRow(3, 3, "Link ME please", True, True, None, []),
        RenderRow(-12, -1, "Autolink: 'me'", True, False, None, [(2, EdgeType.PARENT)]),
    ]
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "me"),
    ]


def test_do_not_make_a_link_on_not_old_matching_add(tree_2_goals):
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink("old"), ToggleAutoLink("new"))
    # Add a goal to the root
    goals.accept_all(Select(1), Add("This is old subgoal"))
    assert goals.q().rows == [
        RenderRow(
            1,
            1,
            "Root",
            True,
            False,
            "select",
            [(-12, EdgeType.PARENT), (3, EdgeType.PARENT)],
        ),
        RenderRow(2, 2, "Autolink on me", True, True, "prev", []),
        RenderRow(3, 3, "This is old subgoal", True, True, None, []),
        RenderRow(
            -12, -1, "Autolink: 'new'", True, False, None, [(2, EdgeType.PARENT)]
        ),
    ]
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "old"),
        ("remove_autolink", 2),
        ("add_autolink", 2, "new"),
    ]


def test_make_a_link_on_matching_insert(tree_3v_goals):
    goals = tree_3v_goals
    goals.accept(ToggleAutoLink("me"))
    # Add a goal to the root
    goals.accept_all(Select(1), HoldSelect(), Select(3), Insert("Link ME please"))
    assert goals.q().rows == [
        RenderRow(
            1,
            1,
            "Root",
            True,
            False,
            "prev",
            [(-12, EdgeType.PARENT), (4, EdgeType.PARENT)],
        ),
        RenderRow(2, 2, "Autolink on me", True, False, None, [(4, EdgeType.BLOCKER)]),
        RenderRow(3, 3, "Another subgoal", True, True, "select", []),
        RenderRow(4, 4, "Link ME please", True, False, None, [(3, EdgeType.PARENT)]),
        RenderRow(-12, -1, "Autolink: 'me'", True, False, None, [(2, EdgeType.PARENT)]),
    ]


def test_make_a_link_on_matching_rename(tree_3v_goals):
    goals = tree_3v_goals
    goals.accept(ToggleAutoLink("me"))
    goals.accept_all(Select(3), Rename("Link ME please"))
    assert goals.q().rows == [
        RenderRow(
            1,
            1,
            "Root",
            True,
            False,
            None,
            [(-12, EdgeType.PARENT), (3, EdgeType.PARENT)],
        ),
        RenderRow(2, 2, "Autolink on me", True, False, "prev", [(3, EdgeType.BLOCKER)]),
        RenderRow(3, 3, "Link ME please", True, True, "select", []),
        RenderRow(-12, -1, "Autolink: 'me'", True, False, None, [(2, EdgeType.PARENT)]),
    ]


def test_do_not_make_a_link_on_matching_subgoal_add(tree_2_goals):
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("me"))
    # Add a sub goal to the same subgoal
    goals.accept_all(Add("Do NOT link me please"))
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, False, None, [(-12, EdgeType.PARENT)]),
        RenderRow(
            2, 2, "Autolink on me", True, False, "select", [(3, EdgeType.PARENT)]
        ),
        RenderRow(3, 3, "Do NOT link me please", True, True, None, []),
        RenderRow(-12, -1, "Autolink: 'me'", True, False, None, [(2, EdgeType.PARENT)]),
    ]


def test_do_not_make_a_link_on_matching_subgoal_insert(tree_3i_goals):
    goals = tree_3i_goals
    goals.accept(ToggleAutoLink("me"))
    # Add a sub goal to the same subgoal
    goals.accept_all(HoldSelect(), Select(3), Insert("Do NOT link me please"))
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, False, None, [(-12, EdgeType.PARENT)]),
        RenderRow(2, 2, "Autolink on me", True, False, "prev", [(4, EdgeType.PARENT)]),
        RenderRow(3, 3, "Another subgoal", True, True, "select", []),
        RenderRow(
            4, 4, "Do NOT link me please", True, False, None, [(3, EdgeType.PARENT)]
        ),
        RenderRow(-12, -1, "Autolink: 'me'", True, False, None, [(2, EdgeType.PARENT)]),
    ]


def test_do_not_make_a_link_on_matching_subgoal_rename(tree_3i_goals):
    goals = tree_3i_goals
    goals.accept(ToggleAutoLink("me"))
    goals.accept_all(Select(3), Rename("Do NOT link me please"))
    assert goals.q().rows == [
        RenderRow(1, 1, "Root", True, False, None, [(-12, EdgeType.PARENT)]),
        RenderRow(2, 2, "Autolink on me", True, False, "prev", [(3, EdgeType.PARENT)]),
        RenderRow(3, 3, "Do NOT link me please", True, True, "select", []),
        RenderRow(-12, -1, "Autolink: 'me'", True, False, None, [(2, EdgeType.PARENT)]),
    ]


def test_autolink_on_all_matching_goals(tree_3v_goals):
    goals = tree_3v_goals
    # make 2 autolinks
    goals.accept_all(ToggleAutoLink("me"), Select(3), ToggleAutoLink("plea"))
    assert goals.q().rows == [
        RenderRow(
            1,
            1,
            "Root",
            True,
            False,
            None,
            [(-12, EdgeType.PARENT), (-13, EdgeType.PARENT)],
        ),
        RenderRow(2, 2, "Autolink on me", True, True, "prev", []),
        RenderRow(3, 3, "Another subgoal", True, True, "select", []),
        RenderRow(-12, -1, "Autolink: 'me'", True, False, None, [(2, EdgeType.PARENT)]),
        RenderRow(
            -13, -1, "Autolink: 'plea'", True, False, None, [(3, EdgeType.PARENT)]
        ),
    ]
    # add 2-mathing goal
    goals.accept_all(Select(1), Add("Link me to both please"))
    assert goals.q().rows == [
        RenderRow(
            1,
            1,
            "Root",
            True,
            False,
            "select",
            [(-12, EdgeType.PARENT), (-13, EdgeType.PARENT), (4, EdgeType.PARENT)],
        ),
        RenderRow(2, 2, "Autolink on me", True, False, "prev", [(4, EdgeType.BLOCKER)]),
        RenderRow(3, 3, "Another subgoal", True, False, None, [(4, EdgeType.BLOCKER)]),
        RenderRow(4, 4, "Link me to both please", True, True, None, []),
        RenderRow(-12, -1, "Autolink: 'me'", True, False, None, [(2, EdgeType.PARENT)]),
        RenderRow(
            -13, -1, "Autolink: 'plea'", True, False, None, [(3, EdgeType.PARENT)]
        ),
    ]
