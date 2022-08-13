import pytest

from siebenapp.domain import EdgeType, Add, Select
from siebenapp.enumeration import Enumeration, BidirectionalIndex
from siebenapp.goaltree import Goals
from siebenapp.layers import all_layers
from siebenapp.switchable_view import ToggleSwitchableView, SwitchableView
from siebenapp.tests.dsl import build_goaltree, open_, previous, selected
from siebenapp.zoom import ToggleZoom


@pytest.fixture
def goal_chain_10():
    """a → b → c → ... → j"""
    return build_goaltree(
        open_(1, "a", [2], select=selected),
        open_(2, "b", [3]),
        open_(3, "c", [4]),
        open_(4, "d", [5]),
        open_(5, "e", [6]),
        open_(6, "f", [7]),
        open_(7, "g", [8]),
        open_(8, "h", [9]),
        open_(9, "i", [10]),
        open_(10, "j", []),
    )


@pytest.fixture
def goal_chain_11(goal_chain_10):
    """a → b → c → ... → j → k"""
    goals = goal_chain_10
    goals.accept_all(Select(10), Add("k"), Select(1))
    return goals


def test_simple_enumeration_is_not_changed():
    e = Enumeration(
        build_goaltree(
            open_(1, "a", [2, 3]),
            open_(2, "b", blockers=[3], select=previous),
            open_(3, "c", select=selected),
        )
    )
    assert e.q(keys="name,edge").slice(keys="name,edge") == {
        1: {"name": "a", "edge": [(2, EdgeType.PARENT), (3, EdgeType.PARENT)]},
        2: {"name": "b", "edge": [(3, EdgeType.BLOCKER)]},
        3: {"name": "c", "edge": []},
    }
    assert e.settings("root") == Goals.ROOT_ID


def test_apply_mapping_for_the_10th_element(goal_chain_10):
    e = Enumeration(goal_chain_10)
    assert e.q(keys="name,edge").slice(keys="name,edge") == {
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
    assert e.settings("root") == Goals.ROOT_ID


def test_apply_mapping_for_the_11th_element(goal_chain_11):
    e = Enumeration(goal_chain_11)
    assert e.q(keys="name,edge").slice(keys="name,edge") == {
        11: {"name": "a", "edge": [(12, EdgeType.PARENT)]},
        12: {"name": "b", "edge": [(13, EdgeType.PARENT)]},
        13: {"name": "c", "edge": [(14, EdgeType.PARENT)]},
        14: {"name": "d", "edge": [(15, EdgeType.PARENT)]},
        15: {"name": "e", "edge": [(16, EdgeType.PARENT)]},
        16: {"name": "f", "edge": [(17, EdgeType.PARENT)]},
        17: {"name": "g", "edge": [(18, EdgeType.PARENT)]},
        18: {"name": "h", "edge": [(19, EdgeType.PARENT)]},
        19: {"name": "i", "edge": [(10, EdgeType.PARENT)]},
        10: {"name": "j", "edge": [(21, EdgeType.PARENT)]},
        21: {"name": "k", "edge": []},
    }
    assert e.settings("root") == 11


def test_use_mapping_in_selection(goal_chain_10):
    e = Enumeration(goal_chain_10)
    e.accept(Select(0))
    assert e.q(keys="name,select").slice(keys="name,select") == {
        1: {"name": "a", "select": "prev"},
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


def test_do_not_select_goal_by_partial_id(goal_chain_11):
    e = Enumeration(goal_chain_11)
    # Select(1) is kept in cache, and selection is not changed yet
    e.accept_all(Select(1))
    assert e.q(keys="name,select").slice(keys="name,select") == {
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


def test_select_goal_by_id_parts(goal_chain_11):
    e = Enumeration(goal_chain_11)
    e.accept_all(Select(1), Select(6))
    assert e.q(keys="name,select").slice(keys="name,select") == {
        11: {"name": "a", "select": "prev"},
        12: {"name": "b", "select": None},
        13: {"name": "c", "select": None},
        14: {"name": "d", "select": None},
        15: {"name": "e", "select": None},
        16: {"name": "f", "select": "select"},
        17: {"name": "g", "select": None},
        18: {"name": "h", "select": None},
        19: {"name": "i", "select": None},
        10: {"name": "j", "select": None},
        21: {"name": "k", "select": None},
    }


def test_select_goal_by_full_id(goal_chain_11):
    e = Enumeration(goal_chain_11)
    assert e.q(keys="name,select").slice(keys="name,select") == {
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
    assert e.q(keys="name,select").slice(keys="name,select") == {
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


def test_select_goal_by_full_id_with_non_empty_cache(goal_chain_11):
    e = Enumeration(goal_chain_11)
    assert e.q(keys="name,select").slice(keys="name,select") == {
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
    e.accept_all(Select(2), Select(13))
    assert e.q(keys="name,select").slice(keys="name,select") == {
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


def test_enumerated_goals_must_have_the_same_dimension():
    e = Enumeration(
        build_goaltree(
            open_(1, "a", [2, 20], select=selected), open_(2, "b"), open_(20, "x")
        )
    )
    assert e.q(keys="name,switchable,select").slice(keys="name,switchable,select") == {
        1: {"name": "a", "switchable": False, "select": "select"},
        2: {"name": "b", "switchable": True, "select": None},
        3: {"name": "x", "switchable": True, "select": None},
    }


def test_selection_cache_should_be_reset_after_view_switch(goal_chain_11):
    e = Enumeration(SwitchableView(goal_chain_11))
    e.accept_all(Add("Also top"))
    e.accept(Select(1))
    # Select(1) is kept in a cache and not applied yet
    e.accept(ToggleSwitchableView())
    assert e.q("name,select").slice("name,select") == {
        1: {"name": "a", "select": "select"},
        2: {"name": "k", "select": None},
        3: {"name": "Also top", "select": None},
    }
    # Select(2) is being applied without any effect from the previous selection
    # This happens because selection cache was reset
    e.accept(Select(2))
    assert e.q("name,select").slice("name,select") == {
        1: {"name": "a", "select": "prev"},
        2: {"name": "k", "select": "select"},
        3: {"name": "Also top", "select": None},
    }


def test_selection_cache_should_avoid_overflow(goal_chain_11):
    e = Enumeration(goal_chain_11)
    assert e.q(keys="select").slice(keys="select")[11] == {"select": "select"}
    e.accept(Select(5))
    assert e.q(keys="select").slice(keys="select")[11] == {"select": "select"}
    e.accept(Select(1))
    assert e.q(keys="select").slice(keys="select")[11] == {"select": "select"}
    assert e.q(keys="select").slice(keys="select")[14] == {"select": None}
    e.accept(Select(4))
    assert e.q(keys="select").slice(keys="select")[11] == {"select": "prev"}
    assert e.q(keys="select").slice(keys="select")[14] == {"select": "select"}


def test_do_not_enumerate_goals_with_negative_id():
    g = all_layers(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Zoomed", [3], select=selected),
            open_(3, "Top"),
        )
    )
    g.accept(ToggleZoom())
    assert g.q("name,select,edge").slice("name,select,edge") == {
        -1: {"name": "Root", "select": None, "edge": [(2, EdgeType.BLOCKER)]},
        2: {"name": "Zoomed", "select": "select", "edge": [(3, EdgeType.PARENT)]},
        3: {"name": "Top", "select": None, "edge": []},
    }
    e = Enumeration(g)
    assert e.q("name,select,edge").slice("name,select,edge") == {
        -1: {"name": "Root", "select": None, "edge": [(1, EdgeType.BLOCKER)]},
        1: {"name": "Zoomed", "select": "select", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Top", "select": None, "edge": []},
    }


def test_all_keys_in_enumeration_must_be_of_the_same_length():
    items = [i + 1 for i in range(2999)]
    e = BidirectionalIndex(items)
    mapped = [e.forward(x) for x in items]
    assert len(mapped) == len(items)
    assert {len(str(k)) for k in mapped} == {4}
