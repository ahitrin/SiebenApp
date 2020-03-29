from siebenapp.enumeration import Enumeration, BidirectionalIndex
from siebenapp.goaltree import Goals
from siebenapp.domain import (
    EdgeType,
    HoldSelect,
    ToggleClose,
    Add,
    Select,
    Insert,
    NextView,
)
from siebenapp.tests.dsl import build_goaltree, open_, previous, selected


def test_simple_enumeration_is_not_changed():
    e = Enumeration(
        build_goaltree(
            open_(1, "a", [2, 3]),
            open_(2, "b", blockers=[3], select=previous),
            open_(3, "c", select=selected),
        )
    )
    assert e.q(keys="name,edge") == {
        1: {"name": "a", "edge": [(2, EdgeType.PARENT), (3, EdgeType.PARENT)]},
        2: {"name": "b", "edge": [(3, EdgeType.BLOCKER)]},
        3: {"name": "c", "edge": []},
    }


def test_apply_mapping_for_the_10th_element():
    prototype = [
        open_(i + 1, c, [i + 2], select=(selected if i == 0 else None))
        for i, c in enumerate("abcdefghi")
    ] + [open_(10, "j")]
    goals = build_goaltree(*prototype)
    e = Enumeration(goals)
    assert e.q(keys="name,edge") == {
        1: {"name": "a", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "b", "edge": [(3, EdgeType.PARENT)]},
        3: {"name": "c", "edge": [(4, EdgeType.PARENT)]},
        4: {"name": "d", "edge": [(5, EdgeType.PARENT)]},
        5: {"name": "e", "edge": [(6, EdgeType.PARENT)]},
        6: {"name": "f", "edge": [(7, EdgeType.PARENT)]},
        7: {"name": "g", "edge": [(8, EdgeType.PARENT)]},
        8: {"name": "h", "edge": [(9, EdgeType.PARENT)]},
        9: {"name": "i", "edge": [(0, EdgeType.PARENT)]},
        0: {"name": "j", "edge": []},
    }
    # simulate goal addition
    goals.accept(Add("k"))
    assert e.q(keys="name,edge") == {
        11: {"name": "a", "edge": [(12, EdgeType.PARENT), (21, EdgeType.PARENT)]},
        12: {"name": "b", "edge": [(13, EdgeType.PARENT)]},
        13: {"name": "c", "edge": [(14, EdgeType.PARENT)]},
        14: {"name": "d", "edge": [(15, EdgeType.PARENT)]},
        15: {"name": "e", "edge": [(16, EdgeType.PARENT)]},
        16: {"name": "f", "edge": [(17, EdgeType.PARENT)]},
        17: {"name": "g", "edge": [(18, EdgeType.PARENT)]},
        18: {"name": "h", "edge": [(19, EdgeType.PARENT)]},
        19: {"name": "i", "edge": [(10, EdgeType.PARENT)]},
        10: {"name": "j", "edge": []},
        21: {"name": "k", "edge": []},
    }


def test_use_mapping_in_selection():
    prototype = [open_(i + 1, c, [i + 2]) for i, c in enumerate("abcdefghi")] + [
        open_(10, "j", select=selected)
    ]
    e = Enumeration(build_goaltree(*prototype))
    e.accept(Select(0))
    assert e.q(keys="name,select") == {
        1: {"name": "a", "select": None},
        2: {"name": "b", "select": None},
        3: {"name": "c", "select": None},
        4: {"name": "d", "select": None},
        5: {"name": "e", "select": None},
        6: {"name": "f", "select": None},
        7: {"name": "g", "select": None},
        8: {"name": "h", "select": None},
        9: {"name": "i", "select": None},
        0: {"name": "j", "select": "select"},
    }
    e.accept(Add("k"))
    e.accept(Select(1))
    e.accept(Select(6))
    assert e.q(keys="name,select") == {
        11: {"name": "a", "select": None},
        12: {"name": "b", "select": None},
        13: {"name": "c", "select": None},
        14: {"name": "d", "select": None},
        15: {"name": "e", "select": None},
        16: {"name": "f", "select": "select"},
        17: {"name": "g", "select": None},
        18: {"name": "h", "select": None},
        19: {"name": "i", "select": None},
        10: {"name": "j", "select": "prev"},
        21: {"name": "k", "select": None},
    }


def test_select_goal_by_full_id():
    prototype = [open_(1, "a", [2, 3, 4, 5, 6, 7, 8, 9, 10, 11], select=selected)] + [
        open_(i + 2, c) for i, c in enumerate("bcdefghijk")
    ]
    e = Enumeration(build_goaltree(*prototype))
    assert e.q(keys="name,select") == {
        11: {"name": "a", "select": "select"},
        12: {"name": "b", "select": None},
        13: {"name": "c", "select": None},
        14: {"name": "d", "select": None},
        15: {"name": "e", "select": None},
        16: {"name": "f", "select": None},
        17: {"name": "g", "select": None},
        18: {"name": "h", "select": None},
        19: {"name": "i", "select": None},
        10: {"name": "j", "select": None},
        21: {"name": "k", "select": None},
    }
    e.accept(Select(13))
    assert e.q(keys="name,select") == {
        11: {"name": "a", "select": "prev"},
        12: {"name": "b", "select": None},
        13: {"name": "c", "select": "select"},
        14: {"name": "d", "select": None},
        15: {"name": "e", "select": None},
        16: {"name": "f", "select": None},
        17: {"name": "g", "select": None},
        18: {"name": "h", "select": None},
        19: {"name": "i", "select": None},
        10: {"name": "j", "select": None},
        21: {"name": "k", "select": None},
    }


def test_select_goal_by_full_id_with_non_empty_cache():
    prototype = [open_(1, "a", [2, 3, 4, 5, 6, 7, 8, 9, 10, 11], select=selected)] + [
        open_(i + 2, c) for i, c in enumerate("bcdefghijk")
    ]
    e = Enumeration(build_goaltree(*prototype))
    assert e.q(keys="name,select") == {
        11: {"name": "a", "select": "select"},
        12: {"name": "b", "select": None},
        13: {"name": "c", "select": None},
        14: {"name": "d", "select": None},
        15: {"name": "e", "select": None},
        16: {"name": "f", "select": None},
        17: {"name": "g", "select": None},
        18: {"name": "h", "select": None},
        19: {"name": "i", "select": None},
        10: {"name": "j", "select": None},
        21: {"name": "k", "select": None},
    }
    e.accept(Select(2))
    e.accept(Select(13))
    assert e.q(keys="name,select") == {
        11: {"name": "a", "select": "prev"},
        12: {"name": "b", "select": None},
        13: {"name": "c", "select": "select"},
        14: {"name": "d", "select": None},
        15: {"name": "e", "select": None},
        16: {"name": "f", "select": None},
        17: {"name": "g", "select": None},
        18: {"name": "h", "select": None},
        19: {"name": "i", "select": None},
        10: {"name": "j", "select": None},
        21: {"name": "k", "select": None},
    }


def test_mapping_for_top():
    e = Enumeration(
        build_goaltree(
            open_(1, "a", [2, 20], select=selected), open_(2, "b"), open_(20, "x")
        )
    )
    assert e.q(keys="name,switchable,select") == {
        1: {"name": "a", "switchable": False, "select": "select"},
        2: {"name": "b", "switchable": True, "select": None},
        3: {"name": "x", "switchable": True, "select": None},
    }


def test_toggle_switch_view():
    e = Enumeration(Goals("Root"))
    assert e.view_title() == "open"
    e.accept(NextView())
    assert e.view_title() == "top"
    e.accept(NextView())
    assert e.view_title() == "full"
    e.accept(NextView())
    assert e.view_title() == "open"


def test_goaltree_selection_may_be_changed_in_top_view():
    g = build_goaltree(
        open_(1, "Root", [2, 3], select=selected), open_(2, "Top 1"), open_(3, "Top 2"),
    )
    e = Enumeration(g)
    assert e.q(keys="name,switchable,select") == {
        1: {"name": "Root", "switchable": False, "select": "select"},
        2: {"name": "Top 1", "switchable": True, "select": None},
        3: {"name": "Top 2", "switchable": True, "select": None},
    }
    e.accept(NextView())
    assert g.events()[-2] == ("select", 2)
    assert g.events()[-1] == ("hold_select", 2)
    assert e.q(keys="name,switchable,select") == {
        1: {"name": "Top 1", "switchable": True, "select": "select"},
        2: {"name": "Top 2", "switchable": True, "select": None},
    }


def test_goaltree_previous_selection_may_be_changed_in_top_view():
    g = build_goaltree(
        open_(1, "Root", [2, 3], select=previous),
        open_(2, "Top 1", select=selected),
        open_(3, "Top 2"),
    )
    e = Enumeration(g)
    assert e.q(keys="name,switchable,select") == {
        1: {"name": "Root", "switchable": False, "select": "prev"},
        2: {"name": "Top 1", "switchable": True, "select": "select"},
        3: {"name": "Top 2", "switchable": True, "select": None},
    }
    e.accept(NextView())
    assert g.events()[-1] == ("hold_select", 2)
    assert e.q(keys="name,switchable,select") == {
        1: {"name": "Top 1", "switchable": True, "select": "select"},
        2: {"name": "Top 2", "switchable": True, "select": None},
    }
    e.accept(Insert("Illegal goal"))
    # New goal must not be inserted because previous selection is reset after the view switching
    e.accept(NextView())
    assert e.q(keys="name,switchable,select") == {
        1: {"name": "Root", "switchable": False, "select": None},
        2: {"name": "Top 1", "switchable": True, "select": "select"},
        3: {"name": "Top 2", "switchable": True, "select": None},
    }


def test_selection_cache_should_be_reset_after_view_switch():
    # 1 -> 2 -> 3 -> .. -> 10 -> 11
    prototype = [
        open_(i, str(i), [i + 1], select=(selected if i == 1 else None))
        for i in range(1, 11)
    ] + [open_(11, "11")]
    g = build_goaltree(*prototype)
    g.accept(Add("Also top", 1))
    e = Enumeration(g)
    e.accept(Select(1))
    e.accept(NextView())
    assert e.q("name,select") == {
        1: {"name": "11", "select": "select"},
        2: {"name": "Also top", "select": None},
    }
    e.accept(Select(2))
    assert e.q("name,select") == {
        1: {"name": "11", "select": "prev"},
        2: {"name": "Also top", "select": "select"},
    }


def test_selection_cache_should_avoid_overflow():
    prototype = [
        open_(1, "Root", [2, 3, 4, 5, 6, 7, 8, 9, 10, 11], select=selected)
    ] + [open_(i, str(i)) for i in range(2, 12)]
    e = Enumeration(build_goaltree(*prototype))
    assert e.q(keys="select")[11] == {"select": "select"}
    e.accept(Select(5))
    assert e.q(keys="select")[11] == {"select": "select"}
    e.accept(Select(1))
    assert e.q(keys="select")[11] == {"select": "select"}
    assert e.q(keys="select")[14] == {"select": None}
    e.accept(Select(4))
    assert e.q(keys="select")[11] == {"select": "prev"}
    assert e.q(keys="select")[14] == {"select": "select"}


def test_top_view_may_be_empty():
    e = Enumeration(Goals("closed"))
    e.accept(ToggleClose())
    e.accept(NextView())
    assert e.q() == {}


def test_simple_top_enumeration_workflow():
    e = Enumeration(Goals("root"))
    e.accept(Add("1"))
    e.accept(Add("2"))
    e.accept(Select(2))
    e.accept(NextView())
    e.accept(Select(2))
    assert e.q() == {1: {"name": "1"}, 2: {"name": "2"}}


def test_open_view_may_be_empty():
    e = Enumeration(Goals("closed"))
    e.accept(ToggleClose())
    assert e.q() == {}


def test_simple_open_enumeration_workflow():
    e = Enumeration(Goals("Root"))
    e.accept(Add("1"))
    e.accept(Add("2"))
    e.accept(Select(2))
    assert e.q(keys="name,select,open,edge") == {
        1: {
            "name": "Root",
            "select": "prev",
            "open": True,
            "edge": [(2, EdgeType.PARENT), (3, EdgeType.PARENT)],
        },
        2: {"name": "1", "select": "select", "open": True, "edge": []},
        3: {"name": "2", "select": None, "open": True, "edge": []},
    }
    e.accept(ToggleClose())
    assert e.q(keys="name,select,open,edge") == {
        1: {
            "name": "Root",
            "select": "select",
            "open": True,
            "edge": [(2, EdgeType.PARENT)],
        },
        2: {"name": "2", "select": None, "open": True, "edge": []},
    }


class PseudoZoomedGoals(Goals):
    def q(self, keys="name"):
        goals = super(PseudoZoomedGoals, self).q(keys)
        goals[-1] = goals.pop(1)
        return goals


def test_do_not_enumerate_goals_with_negative_id():
    g = PseudoZoomedGoals("Root")
    g.accept(Add("Zoomed"))
    g.accept(Select(2))
    g.accept(HoldSelect())
    g.accept(Add("Top"))
    assert g.q("name,select,edge") == {
        -1: {"name": "Root", "select": None, "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Zoomed", "select": "select", "edge": [(3, EdgeType.PARENT)]},
        3: {"name": "Top", "select": None, "edge": []},
    }
    e = Enumeration(g)
    assert e.q("name,select,edge") == {
        -1: {"name": "Root", "select": None, "edge": [(1, EdgeType.PARENT)]},
        1: {"name": "Zoomed", "select": "select", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Top", "select": None, "edge": []},
    }


def test_all_keys_in_enumeration_must_be_of_the_same_length():
    items = [i + 1 for i in range(2999)]
    e = BidirectionalIndex(items)
    mapped = [e.forward(x) for x in items]
    assert len(mapped) == len(items)
    assert set(len(str(k)) for k in mapped) == {4}
