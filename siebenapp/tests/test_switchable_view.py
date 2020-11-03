from siebenapp.domain import Insert, Add, Select, ToggleClose
from siebenapp.enumeration import Enumeration, SwitchableView, ToggleSwitchableView
from siebenapp.goaltree import Goals
from siebenapp.open_view import OpenView
from siebenapp.tests.dsl import build_goaltree, open_, selected, previous


def test_goaltree_selection_may_be_changed_in_top_view():
    g = build_goaltree(
        open_(1, "Root", [2, 3], select=selected), open_(2, "Top 1"), open_(3, "Top 2"),
    )
    e = Enumeration(SwitchableView(g))
    assert e.q(keys="name,switchable,select") == {
        1: {"name": "Root", "switchable": False, "select": "select"},
        2: {"name": "Top 1", "switchable": True, "select": None},
        3: {"name": "Top 2", "switchable": True, "select": None},
    }
    e.accept(ToggleSwitchableView())
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
    e = Enumeration(SwitchableView(g))
    assert e.q(keys="name,switchable,select") == {
        1: {"name": "Root", "switchable": False, "select": "prev"},
        2: {"name": "Top 1", "switchable": True, "select": "select"},
        3: {"name": "Top 2", "switchable": True, "select": None},
    }
    e.accept(ToggleSwitchableView())
    assert g.events()[-1] == ("hold_select", 2)
    assert e.q(keys="name,switchable,select") == {
        1: {"name": "Top 1", "switchable": True, "select": "select"},
        2: {"name": "Top 2", "switchable": True, "select": None},
    }
    e.accept(Insert("Illegal goal"))
    # New goal must not be inserted because previous selection is reset after the view switching
    e.accept(ToggleSwitchableView())
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
    e = Enumeration(SwitchableView(g))
    e.accept_all(Select(1), ToggleSwitchableView())
    assert e.q("name,select") == {
        1: {"name": "11", "select": "select"},
        2: {"name": "Also top", "select": None},
    }
    e.accept(Select(2))
    assert e.q("name,select") == {
        1: {"name": "11", "select": "prev"},
        2: {"name": "Also top", "select": "select"},
    }


def test_top_view_may_be_empty_when_underlying_layer_is_empty():
    e = Enumeration(SwitchableView(OpenView(Goals("closed"))))
    e.accept_all(ToggleClose(), ToggleSwitchableView())
    assert e.q() == {}


def test_simple_top_enumeration_workflow():
    e = Enumeration(SwitchableView(Goals("root")))
    e.accept_all(Add("1"), Add("2"), Select(2), ToggleSwitchableView(), Select(2))
    assert e.q() == {1: {"name": "1"}, 2: {"name": "2"}}
