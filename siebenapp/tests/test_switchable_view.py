from siebenapp.domain import Add, Select, HoldSelect
from siebenapp.goaltree import Goals
from siebenapp.layers import persistent_layers
from siebenapp.switchable_view import ToggleSwitchableView, SwitchableView
from siebenapp.tests.dsl import build_goaltree, open_, selected, previous
from siebenapp.zoom import ToggleZoom


def test_toggle_hide_non_switchable_goals():
    g = build_goaltree(
        open_(1, "Root", [2, 3]),
        open_(2, "Switchable 1", select=selected),
        open_(3, "Switchable 2"),
    )
    e = SwitchableView(g)
    assert e.q(keys="name,switchable,select") == {
        1: {"name": "Root", "switchable": False, "select": None},
        2: {"name": "Switchable 1", "switchable": True, "select": "select"},
        3: {"name": "Switchable 2", "switchable": True, "select": None},
    }
    e.accept(ToggleSwitchableView())
    assert e.q(keys="name,switchable,select") == {
        2: {"name": "Switchable 1", "switchable": True, "select": "select"},
        3: {"name": "Switchable 2", "switchable": True, "select": None},
    }
    e.accept(ToggleSwitchableView())
    assert e.q(keys="name,switchable,select") == {
        1: {"name": "Root", "switchable": False, "select": None},
        2: {"name": "Switchable 1", "switchable": True, "select": "select"},
        3: {"name": "Switchable 2", "switchable": True, "select": None},
    }


def test_do_not_hide_unswitchable_goals_when_they_have_selection():
    v = SwitchableView(
        build_goaltree(
            open_(1, "Selected", [2], select=selected),
            open_(2, "Prev-selected", [3], select=previous),
            open_(3, "Switchable"),
        )
    )
    v.accept_all(ToggleSwitchableView())
    assert v.q("name,switchable,select") == {
        1: {"name": "Selected", "switchable": False, "select": "select"},
        2: {"name": "Prev-selected", "switchable": False, "select": "prev"},
        3: {"name": "Switchable", "switchable": True, "select": None},
    }


def test_non_switchable_goals_disappear_on_selection_change():
    e = SwitchableView(Goals("root"))
    e.accept_all(Add("1"), Add("2"), Select(2), ToggleSwitchableView(), Select(2))
    assert e.q("name,switchable,select") == {
        1: {"name": "root", "switchable": False, "select": "prev"},
        2: {"name": "1", "switchable": True, "select": "select"},
        3: {"name": "2", "switchable": True, "select": None},
    }
    e.accept(HoldSelect())
    assert e.q("name,switchable,select") == {
        2: {"name": "1", "switchable": True, "select": "select"},
        3: {"name": "2", "switchable": True, "select": None},
    }


def test_how_should_we_deal_with_zooming():
    g = build_goaltree(
        open_(1, "Root", [2]),
        open_(2, "Zoomed", blockers=[3], select=selected),
        open_(3, "Ex-top"),
    )
    v = SwitchableView(persistent_layers(g))
    v.accept_all(ToggleZoom(), ToggleSwitchableView())
    assert v.q("name,select") == {
        2: {"name": "Zoomed", "select": "select"},
        3: {"name": "Ex-top", "select": None},
    }
    v.accept(Add("Unexpectedly hidden"))
    assert v.q("name,select") == {
        2: {"name": "Zoomed", "select": "select"},
        3: {"name": "Ex-top", "select": None},
        4: {"name": "Unexpectedly hidden", "select": None},
    }


def test_filter_switchable_setting_is_not_set_by_default():
    v = SwitchableView(build_goaltree(open_(1, "only", select=selected)))
    assert v.settings("filter_switchable") == 0


def test_filter_switchable_setting_is_changed_after_switch():
    v = SwitchableView(build_goaltree(open_(1, "only", select=selected)))
    v.accept(ToggleSwitchableView())
    assert v.settings("filter_switchable") == 1
