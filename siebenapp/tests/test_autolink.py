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
    assert goals.q().slice("name,edge,select") == {
        1: {"name": "Root", "edge": [(2, EdgeType.PARENT)], "select": None},
        2: {"name": "Autolink on me", "edge": [], "select": "select"},
    }
    goals.accept(ToggleAutoLink("heLLO"))
    assert goals.q().slice("edge") == {
        1: {"edge": [(-12, EdgeType.PARENT)]},
        -12: {"edge": [(2, EdgeType.PARENT)]},
        2: {"edge": []},
    }
    assert goals.q().slice("name,open,select,switchable")[-12] == {
        "name": "Autolink: 'hello'",
        "open": True,
        "select": None,
        "switchable": False,
    }
    assert _autolink_events(goals) == [("add_autolink", 2, "hello")]


def test_replace_old_autolink_with_new_one(tree_2_goals):
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink("first"), ToggleAutoLink("second"))
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'second'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": []},
    }
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "first"),
        ("remove_autolink", 2),
        ("add_autolink", 2, "second"),
    ]


def test_remove_autolink_by_sending_empty_keyword(tree_2_goals):
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink("lalala"), ToggleAutoLink(""))
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": []},
    }
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "lalala"),
        ("remove_autolink", 2),
    ]


def test_remove_autolink_by_sending_whitespace(tree_2_goals):
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink("lalala"), ToggleAutoLink(" "))
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": []},
    }
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "lalala"),
        ("remove_autolink", 2),
    ]


def test_do_not_add_autolink_on_whitespace(tree_2_goals):
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink(" "))
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": []},
    }
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
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Well, it's closed", "edge": []},
    }
    assert messages == ["Autolink cannot be set for closed goals"]
    assert _autolink_events(goals) == []


def test_do_not_add_autolink_to_root_goal():
    messages: List[str] = []
    goals = AutoLink(
        build_goaltree(open_(1, "Root", select=selected), message_fn=messages.append)
    )
    goals.accept(ToggleAutoLink("misused"))
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": []},
    }
    assert messages == ["Autolink cannot be set for the root goal"]
    assert _autolink_events(goals) == []


def test_remove_autolink_on_close(tree_2_goals):
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("test"))
    assert goals.q().slice("edge,open") == {
        1: {"edge": [(-12, EdgeType.PARENT)], "open": True},
        -12: {"edge": [(2, EdgeType.PARENT)], "open": True},
        2: {"edge": [], "open": True},
    }
    goals.accept(ToggleClose())
    assert goals.q().slice("edge,open") == {
        1: {"edge": [(2, EdgeType.PARENT)], "open": True},
        2: {"edge": [], "open": False},
    }
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "test"),
        ("remove_autolink", 2),
    ]


def test_remove_autolink_on_delete(tree_2_goals):
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("test"))
    assert goals.q().slice("edge,open") == {
        1: {"edge": [(-12, EdgeType.PARENT)], "open": True},
        -12: {"edge": [(2, EdgeType.PARENT)], "open": True},
        2: {"edge": [], "open": True},
    }
    goals.accept(Delete())
    assert goals.q().slice("edge,open") == {
        1: {"edge": [], "open": True},
    }
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "test"),
        ("remove_autolink", 2),
    ]


def test_remove_autolink_on_parent_delete(tree_3i_goals):
    goals = tree_3i_goals
    goals.accept_all(Select(3), ToggleAutoLink("test"))
    assert goals.q().slice("edge") == {
        1: {"edge": [(2, EdgeType.PARENT)]},
        2: {"edge": [(-13, EdgeType.PARENT)]},
        -13: {"edge": [(3, EdgeType.PARENT)]},
        3: {"edge": []},
    }
    goals.accept_all(Select(2), Delete())
    assert goals.q().slice("edge") == {1: {"edge": []}}
    assert _autolink_events(goals) == [
        ("add_autolink", 3, "test"),
        ("remove_autolink", 3),
    ]


def test_replace_same_autolink(tree_3v_goals):
    goals = tree_3v_goals
    goals.accept_all(ToggleAutoLink("same"), Select(3), ToggleAutoLink("same"))
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(2, EdgeType.PARENT), (-13, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": []},
        -13: {"name": "Autolink: 'same'", "edge": [(3, EdgeType.PARENT)]},
        3: {"name": "Another subgoal", "edge": []},
    }
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
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT), (3, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'hello'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": []},
        3: {"name": "Goodbye", "edge": []},
    }
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "hello"),
    ]


def test_make_a_link_on_matching_add(tree_2_goals):
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("me"))
    # Add a goal to the root
    goals.accept_all(Select(1), Add("Link ME please"))
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT), (3, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'me'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": [(3, EdgeType.BLOCKER)]},
        3: {"name": "Link ME please", "edge": []},
    }
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "me"),
    ]


def test_do_not_make_a_link_on_not_old_matching_add(tree_2_goals):
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink("old"), ToggleAutoLink("new"))
    # Add a goal to the root
    goals.accept_all(Select(1), Add("This is old subgoal"))
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT), (3, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'new'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": []},
        3: {"name": "This is old subgoal", "edge": []},
    }
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
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT), (4, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'me'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": [(4, EdgeType.BLOCKER)]},
        4: {"name": "Link ME please", "edge": [(3, EdgeType.PARENT)]},
        3: {"name": "Another subgoal", "edge": []},
    }


def test_make_a_link_on_matching_rename(tree_3v_goals):
    goals = tree_3v_goals
    goals.accept(ToggleAutoLink("me"))
    goals.accept_all(Select(3), Rename("Link ME please"))
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT), (3, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'me'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": [(3, EdgeType.BLOCKER)]},
        3: {"name": "Link ME please", "edge": []},
    }


def test_do_not_make_a_link_on_matching_subgoal_add(tree_2_goals):
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("me"))
    # Add a sub goal to the same subgoal
    goals.accept_all(Add("Do NOT link me please"))
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'me'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": [(3, EdgeType.PARENT)]},
        3: {"name": "Do NOT link me please", "edge": []},
    }


def test_do_not_make_a_link_on_matching_subgoal_insert(tree_3i_goals):
    goals = tree_3i_goals
    goals.accept(ToggleAutoLink("me"))
    # Add a sub goal to the same subgoal
    goals.accept_all(HoldSelect(), Select(3), Insert("Do NOT link me please"))
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'me'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": [(4, EdgeType.PARENT)]},
        4: {"name": "Do NOT link me please", "edge": [(3, EdgeType.PARENT)]},
        3: {"name": "Another subgoal", "edge": []},
    }


def test_do_not_make_a_link_on_matching_subgoal_rename(tree_3i_goals):
    goals = tree_3i_goals
    goals.accept(ToggleAutoLink("me"))
    goals.accept_all(Select(3), Rename("Do NOT link me please"))
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'me'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": [(3, EdgeType.PARENT)]},
        3: {"name": "Do NOT link me please", "edge": []},
    }


def test_autolink_on_all_matching_goals(tree_3v_goals):
    goals = tree_3v_goals
    # make 2 autolinks
    goals.accept_all(ToggleAutoLink("me"), Select(3), ToggleAutoLink("plea"))
    assert goals.q().slice("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT), (-13, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'me'", "edge": [(2, EdgeType.PARENT)]},
        -13: {"name": "Autolink: 'plea'", "edge": [(3, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": []},
        3: {"name": "Another subgoal", "edge": []},
    }
    # add 2-mathing goal
    goals.accept_all(Select(1), Add("Link me to both please"))
    assert goals.q().slice("name,edge") == {
        1: {
            "name": "Root",
            "edge": [
                (-12, EdgeType.PARENT),
                (-13, EdgeType.PARENT),
                (4, EdgeType.PARENT),
            ],
        },
        -12: {"name": "Autolink: 'me'", "edge": [(2, EdgeType.PARENT)]},
        -13: {"name": "Autolink: 'plea'", "edge": [(3, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": [(4, EdgeType.BLOCKER)]},
        3: {"name": "Another subgoal", "edge": [(4, EdgeType.BLOCKER)]},
        4: {"name": "Link me to both please", "edge": []},
    }
