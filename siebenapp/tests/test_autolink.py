"""
Autolink layer test cases TBD

* ✓ add autolink -> show a new pseudogoal
* add autolink1, add autolink 2 -> replace autolink1 with autolink2
* add autolink, add empty autolink -> remove a pseudogoal
* add autolink on closed goal -> do not add, show error
* add autolink, close goal -> remove autolink
* matching goal already exists, add autolink -> show new pseudogoal, do not link
* add autolink, add non-matching goal -> pass as is
* add autolink, add matching goal -> make a link
* add autolink, insert matching goal -> make a link
* add autolink, rename existing goal -> make a link
* add autolink, add matching subgoal -> do nothing
* add autolink, rename existing subgoal -> do nothing
* add 2 autolinks, add 1-matching goal -> make 1 link
* add 2 autolinks, add 2-matching goal -> make 2 links
"""
from siebenapp.autolink import AutoLink, ToggleAutoLink
from siebenapp.domain import EdgeType
from siebenapp.tests.dsl import build_goaltree, open_, selected


def test_show_new_pseudogoal_on_autolink_event():
    goals = build_goaltree(
        open_(1, "Root", [2]), open_(2, "Should be autolinked", select=selected)
    )
    al = AutoLink(goals)
    assert al.q("name,edge,select") == {
        1: {"name": "Root", "edge": [(2, EdgeType.PARENT)], "select": None},
        2: {"name": "Should be autolinked", "edge": [], "select": "select"},
    }
    al.accept(ToggleAutoLink("hello"))
    assert al.q("edge") == {
        1: {"edge": [(-12, EdgeType.PARENT)]},
        -12: {"edge": [(2, EdgeType.PARENT)]},
        2: {"edge": []},
    }
    assert al.q("name,open,select,switchable")[-12] == {
        "name": "Autolink: 'hello'",
        "open": True,
        "select": None,
        "switchable": False,
    }
