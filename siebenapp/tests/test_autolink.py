"""
Autolink layer test cases TBD

* ✓ add autolink -> show a new pseudogoal
* ✓ add autolink1, add autolink 2 -> replace autolink1 with autolink2
* ✓ add autolink, add empty autolink -> remove a pseudogoal
* ✓ add autolink on closed goal -> do not add, show error
* ✓ add autolink on root goal -> do not add, show error
* ✓ add autolink, close goal -> remove autolink
* ✓ add autolink, add non-matching goal -> pass as is
* ✓ add autolink, add matching goal -> make a link
* ✓ add autolink1, add autolink2, add matching1 goal -> do not make a link
* ✓ add autolink, insert matching goal -> make a link
* ✓ add autolink, rename existing goal -> make a link
* ✓ add autolink, add matching subgoal -> do nothing
* ✓ add autolink, rename existing subgoal -> do nothing
* add 2 autolinks, add 1-matching goal -> make 1 link
* add 2 autolinks, add 2-matching goal -> make 2 links
"""
from typing import List

from siebenapp.autolink import AutoLink, ToggleAutoLink
from siebenapp.domain import (
    EdgeType,
    ToggleClose,
    Select,
    Add,
    HoldSelect,
    Insert,
    Rename,
)
from siebenapp.tests.dsl import build_goaltree, open_, selected, clos_


def test_show_new_pseudogoal_on_autolink_event():
    goals = AutoLink(
        build_goaltree(
            open_(1, "Root", [2]), open_(2, "Should be autolinked", select=selected)
        )
    )
    assert goals.q("name,edge,select") == {
        1: {"name": "Root", "edge": [(2, EdgeType.PARENT)], "select": None},
        2: {"name": "Should be autolinked", "edge": [], "select": "select"},
    }
    goals.accept(ToggleAutoLink("heLLO"))
    assert goals.q("edge") == {
        1: {"edge": [(-12, EdgeType.PARENT)]},
        -12: {"edge": [(2, EdgeType.PARENT)]},
        2: {"edge": []},
    }
    assert goals.q("name,open,select,switchable")[-12] == {
        "name": "Autolink: 'hello'",
        "open": True,
        "select": None,
        "switchable": False,
    }


def test_replace_old_autolink_with_new_one():
    goals = AutoLink(
        build_goaltree(
            open_(1, "Root", [2]), open_(2, "Should be autolinked", select=selected)
        )
    )
    goals.accept_all(ToggleAutoLink("first"), ToggleAutoLink("second"))
    assert goals.q("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'second'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Should be autolinked", "edge": []},
    }


def test_remove_autolink_by_sending_empty_keyword():
    goals = AutoLink(
        build_goaltree(
            open_(1, "Root", [2]), open_(2, "Should be autolinked", select=selected)
        )
    )
    goals.accept_all(ToggleAutoLink("lalala"), ToggleAutoLink(""))
    assert goals.q("name,edge") == {
        1: {"name": "Root", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Should be autolinked", "edge": []},
    }


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
    assert goals.q("name,edge") == {
        1: {"name": "Root", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Well, it's closed", "edge": []},
    }
    assert messages == ["Autolink cannot be set for closed goals"]


def test_do_not_add_autolink_to_root_goal():
    messages: List[str] = []
    goals = AutoLink(
        build_goaltree(open_(1, "Root", select=selected), message_fn=messages.append)
    )
    goals.accept(ToggleAutoLink("misused"))
    assert goals.q("name,edge") == {
        1: {"name": "Root", "edge": []},
    }
    assert messages == ["Autolink cannot be set for the root goal"]


def test_remove_autolink_on_close():
    goals = AutoLink(
        build_goaltree(
            open_(1, "Root", [2]), open_(2, "Should be autolinked", select=selected)
        )
    )
    goals.accept(ToggleAutoLink("test"))
    assert goals.q("edge") == {
        1: {"edge": [(-12, EdgeType.PARENT)]},
        -12: {"edge": [(2, EdgeType.PARENT)]},
        2: {"edge": []},
    }
    goals.accept(ToggleClose())
    assert goals.q("edge") == {
        1: {"edge": [(2, EdgeType.PARENT)]},
        2: {"edge": []},
    }


def test_do_not_make_a_link_on_not_matching_add():
    goals = AutoLink(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Autolink on me", select=selected),
        )
    )
    goals.accept(ToggleAutoLink("hello"))
    # Add a goal to the root
    goals.accept_all(Select(1), Add("Goodbye"))
    assert goals.q("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT), (3, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'hello'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": []},
        3: {"name": "Goodbye", "edge": []},
    }


def test_make_a_link_on_matching_add():
    goals = AutoLink(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Autolink on me", select=selected),
        )
    )
    goals.accept(ToggleAutoLink("me"))
    # Add a goal to the root
    goals.accept_all(Select(1), Add("Link ME please"))
    assert goals.q("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT), (3, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'me'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": [(3, EdgeType.BLOCKER)]},
        3: {"name": "Link ME please", "edge": []},
    }


def test_do_not_make_a_link_on_not_old_matching_add():
    goals = AutoLink(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Autolink on me", select=selected),
        )
    )
    goals.accept_all(ToggleAutoLink("old"), ToggleAutoLink("new"))
    # Add a goal to the root
    goals.accept_all(Select(1), Add("This is old subgoal"))
    assert goals.q("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT), (3, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'new'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": []},
        3: {"name": "This is old subgoal", "edge": []},
    }


def test_make_a_link_on_matching_insert():
    goals = AutoLink(
        build_goaltree(
            open_(1, "Root", [2, 3]),
            open_(2, "Autolink on me", select=selected),
            open_(3, "Another subgoal"),
        )
    )
    goals.accept(ToggleAutoLink("me"))
    # Add a goal to the root
    goals.accept_all(Select(1), HoldSelect(), Select(3), Insert("Link ME please"))
    assert goals.q("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT), (4, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'me'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": [(4, EdgeType.BLOCKER)]},
        4: {"name": "Link ME please", "edge": [(3, EdgeType.PARENT)]},
        3: {"name": "Another subgoal", "edge": []},
    }


def test_make_a_link_on_matching_rename():
    goals = AutoLink(
        build_goaltree(
            open_(1, "Root", [2, 3]),
            open_(2, "Autolink on me", select=selected),
            open_(3, "Another subgoal"),
        )
    )
    goals.accept(ToggleAutoLink("me"))
    # Add a goal to the root
    goals.accept_all(Select(3), Rename("Link ME please"))
    assert goals.q("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT), (3, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'me'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": [(3, EdgeType.BLOCKER)]},
        3: {"name": "Link ME please", "edge": []},
    }


def test_do_not_make_a_link_on_matching_subgoal_add():
    goals = AutoLink(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Autolink on me", select=selected),
        )
    )
    goals.accept(ToggleAutoLink("me"))
    # Add a sub goal to the same subgoal
    goals.accept_all(Add("Do NOT link me please"))
    assert goals.q("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'me'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": [(3, EdgeType.PARENT)]},
        3: {"name": "Do NOT link me please", "edge": []},
    }


def test_do_not_make_a_link_on_matching_subbbgoal_rename():
    goals = AutoLink(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Autolink on me", [3], select=selected),
            open_(3, "Another subgoal"),
        )
    )
    goals.accept(ToggleAutoLink("me"))
    # Add a goal to the root
    goals.accept_all(Select(3), Rename("Do NOT link me please"))
    assert goals.q("name,edge") == {
        1: {"name": "Root", "edge": [(-12, EdgeType.PARENT)]},
        -12: {"name": "Autolink: 'me'", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Autolink on me", "edge": [(3, EdgeType.PARENT)]},
        3: {"name": "Do NOT link me please", "edge": []},
    }
