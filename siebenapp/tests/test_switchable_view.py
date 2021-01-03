from siebenapp.domain import Insert, Add, Select, ToggleClose
from siebenapp.switchable_view import ToggleSwitchableView, SwitchableView
from siebenapp.goaltree import Goals
from siebenapp.open_view import OpenView
from siebenapp.tests.dsl import build_goaltree, open_, selected, previous
from siebenapp.zoom import ToggleZoom, Zoom


def test_goaltree_selection_may_be_changed_in_switchable_view():
    g = build_goaltree(
        open_(1, "Root", [2, 3], select=selected),
        open_(2, "Switchable 1"),
        open_(3, "Switchable 2"),
    )
    e = SwitchableView(g)
    assert e.q(keys="name,switchable,select") == {
        1: {"name": "Root", "switchable": False, "select": "select"},
        2: {"name": "Switchable 1", "switchable": True, "select": None},
        3: {"name": "Switchable 2", "switchable": True, "select": None},
    }
    e.accept(ToggleSwitchableView())
    assert g.events()[-2] == ("select", 2)
    assert g.events()[-1] == ("hold_select", 2)
    assert e.q(keys="name,switchable,select") == {
        2: {"name": "Switchable 1", "switchable": True, "select": "select"},
        3: {"name": "Switchable 2", "switchable": True, "select": None},
    }


def test_goaltree_previous_selection_may_be_changed_in_switchable_view():
    g = build_goaltree(
        open_(1, "Root", [2, 3], select=previous),
        open_(2, "Switchable 1", select=selected),
        open_(3, "Switchable 2"),
    )
    e = SwitchableView(g)
    assert e.q(keys="name,switchable,select") == {
        1: {"name": "Root", "switchable": False, "select": "prev"},
        2: {"name": "Switchable 1", "switchable": True, "select": "select"},
        3: {"name": "Switchable 2", "switchable": True, "select": None},
    }
    e.accept(ToggleSwitchableView())
    assert g.events()[-1] == ("hold_select", 2)
    assert e.q(keys="name,switchable,select") == {
        2: {"name": "Switchable 1", "switchable": True, "select": "select"},
        3: {"name": "Switchable 2", "switchable": True, "select": None},
    }
    e.accept(Insert("Illegal goal"))
    # New goal must not be inserted because previous selection is reset after the view switching
    e.accept(ToggleSwitchableView())
    assert e.q(keys="name,switchable,select") == {
        1: {"name": "Root", "switchable": False, "select": None},
        2: {"name": "Switchable 1", "switchable": True, "select": "select"},
        3: {"name": "Switchable 2", "switchable": True, "select": None},
    }


def test_switchable_view_may_be_empty_when_underlying_layer_is_empty():
    e = SwitchableView(OpenView(Goals("closed")))
    e.accept_all(ToggleClose(), ToggleSwitchableView())
    assert e.q() == {}


def test_simple_switchable_enumeration_workflow():
    e = SwitchableView(Goals("root"))
    e.accept_all(Add("1"), Add("2"), Select(2), ToggleSwitchableView(), Select(2))
    assert e.q() == {2: {"name": "1"}, 3: {"name": "2"}}


def test_change_selection_on_goal_add():
    v = SwitchableView(Goals("Root"))
    v.accept_all(ToggleSwitchableView(), Add("Must be selected"))
    assert v.q("name,select") == {2: {"name": "Must be selected", "select": "select"}}


def test_change_selection_on_goal_closing():
    g = build_goaltree(
        open_(1, "Root", [2]),
        open_(2, "Subroot", [3]),
        open_(3, "Closing", select=selected),
    )
    v = SwitchableView(OpenView(g))
    v.accept(ToggleSwitchableView())
    assert v.q("name,select") == {3: {"name": "Closing", "select": "select"}}
    v.accept(ToggleClose())
    assert v.q("name,select") == {2: {"name": "Subroot", "select": "select"}}


def test_how_should_we_deal_with_zooming():
    g = build_goaltree(
        open_(1, "Root", [2]),
        open_(2, "Zoomed", blockers=[3], select=selected),
        open_(3, "Ex-top"),
    )
    v = SwitchableView(Zoom(g))
    v.accept_all(ToggleZoom(), ToggleSwitchableView())
    assert v.q("name,select") == {3: {"name": "Ex-top", "select": "select"}}
    v.accept(Add("Unexpectedly hidden"))
    # I definitely don't like this behavior. Seems that we should show something here
    assert v.q("name,select") == {}


def test_filter_switchable_setting_is_not_set_by_default():
    v = SwitchableView(build_goaltree(open_(1, "only", select=selected)))
    assert v.settings("filter_switchable") == 0


def test_filter_switchable_setting_is_changed_after_switch():
    v = SwitchableView(build_goaltree(open_(1, "only", select=selected)))
    v.accept(ToggleSwitchableView())
    assert v.settings("filter_switchable") == 1
