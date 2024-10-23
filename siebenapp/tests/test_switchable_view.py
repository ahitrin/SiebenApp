from siebenapp.domain import Add, Select, HoldSelect, RenderRow, RenderResult, child
from siebenapp.goaltree import Goals
from siebenapp.selectable import Selectable, OPTION_SELECT, OPTION_PREV_SELECT
from siebenapp.layers import persistent_layers
from siebenapp.switchable_view import ToggleSwitchableView, SwitchableView
from siebenapp.tests.dsl import build_goaltree, open_
from siebenapp.zoom import ToggleZoom


def test_toggle_hide_non_switchable_goals() -> None:
    g = build_goaltree(
        open_(1, "Root", [2, 3]), open_(2, "Switchable 1"), open_(3, "Switchable 2")
    )
    e = SwitchableView(g)
    assert e.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "Switchable 1", True, True, []),
            RenderRow(3, 3, "Switchable 2", True, True, []),
        ],
        roots={1},
    )
    e.accept(ToggleSwitchableView())
    assert e.q() == RenderResult(
        [
            RenderRow(2, 2, "Switchable 1", True, True, []),
            RenderRow(3, 3, "Switchable 2", True, True, []),
        ],
        roots={2, 3},
    )
    e.accept(ToggleSwitchableView())
    assert e.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "Switchable 1", True, True, []),
            RenderRow(3, 3, "Switchable 2", True, True, []),
        ],
        roots={1},
    )


def test_do_not_hide_unswitchable_goals_when_they_have_selection() -> None:
    v = SwitchableView(
        Selectable(
            build_goaltree(
                open_(1, "Selected", [2]),
                open_(2, "Prev-selected", [3]),
                open_(3, "Switchable"),
            ),
            [("selection", 1), ("previous_selection", 2)],
        )
    )
    v.accept_all(ToggleSwitchableView())
    assert v.q() == RenderResult(
        [
            RenderRow(1, 1, "Selected", True, False, []),
            RenderRow(2, 2, "Prev-selected", True, False, []),
            RenderRow(3, 3, "Switchable", True, True, []),
        ],
        roots={1, 2, 3},
        global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 2},
    )


def test_non_switchable_goals_disappear_on_selection_change() -> None:
    e = SwitchableView(Selectable(Goals("root")))
    e.accept_all(Add("1"), Add("2"), Select(2), ToggleSwitchableView(), Select(2))
    assert e.q() == RenderResult(
        [
            RenderRow(1, 1, "root", True, False, []),
            RenderRow(2, 2, "1", True, True, []),
            RenderRow(3, 3, "2", True, True, []),
        ],
        roots={1, 2, 3},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 1},
    )
    e.accept(HoldSelect())
    assert e.q() == RenderResult(
        [
            RenderRow(2, 2, "1", True, True, []),
            RenderRow(3, 3, "2", True, True, []),
        ],
        roots={2, 3},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
    )


def test_how_should_we_deal_with_zooming() -> None:
    g = build_goaltree(
        open_(1, "Root goal", [2]), open_(2, "Zoomed", blockers=[3]), open_(3, "Ex-top")
    )
    v = SwitchableView(
        persistent_layers(g, [("selection", 2), ("previous_selection", 2)])
    )
    v.accept_all(ToggleZoom(2), ToggleSwitchableView())
    assert v.q() == RenderResult(
        [
            RenderRow(2, 2, "Zoomed", True, False, [], {"Zoom": "Root goal"}),
            RenderRow(3, 3, "Ex-top", True, True, []),
        ],
        roots={2, 3},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
    )
    v.accept(Add("Unexpectedly hidden"))
    assert v.q() == RenderResult(
        [
            RenderRow(2, 2, "Zoomed", True, False, [], {"Zoom": "Root goal"}),
            RenderRow(3, 3, "Ex-top", True, True, []),
        ],
        roots={2, 3},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
    )


def test_filter_switchable_setting_is_not_set_by_default() -> None:
    v = SwitchableView(build_goaltree(open_(1, "only")))
    assert v.settings("filter_switchable") == 0


def test_filter_switchable_setting_is_changed_after_switch() -> None:
    v = SwitchableView(build_goaltree(open_(1, "only")))
    v.accept(ToggleSwitchableView())
    assert v.settings("filter_switchable") == 1
