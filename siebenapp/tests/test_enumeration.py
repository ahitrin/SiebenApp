from typing import List

import pytest

from siebenapp.domain import (
    Add,
    Select,
    child,
    blocker,
    RenderRow,
    RenderResult,
    RenderResult,
    GoalId,
)
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


def test_simple_enumeration_is_not_changed() -> None:
    e = Enumeration(
        build_goaltree(
            open_(1, "a", [2, 3]),
            open_(2, "b", blockers=[3], select=previous),
            open_(3, "c", select=selected),
        )
    )
    assert e.q() == RenderResult(
        [
            RenderRow(1, 1, "a", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "b", True, False, [blocker(3)]),
            RenderRow(3, 3, "c", True, True, []),
        ],
        select=(3, 2),
        roots={1},
    )
    assert e.settings("root") == Goals.ROOT_ID


def test_apply_mapping_for_the_10th_element(goal_chain_10) -> None:
    e = Enumeration(goal_chain_10)
    assert e.q() == RenderResult(
        [
            RenderRow(1, 1, "a", True, False, [child(2)]),
            RenderRow(2, 2, "b", True, False, [child(3)]),
            RenderRow(3, 3, "c", True, False, [child(4)]),
            RenderRow(4, 4, "d", True, False, [child(5)]),
            RenderRow(5, 5, "e", True, False, [child(6)]),
            RenderRow(6, 6, "f", True, False, [child(7)]),
            RenderRow(7, 7, "g", True, False, [child(8)]),
            RenderRow(8, 8, "h", True, False, [child(9)]),
            RenderRow(9, 9, "i", True, False, [child(0)]),
            RenderRow(0, 10, "j", True, True, []),
        ],
        select=(1, 1),
        roots={1},
    )
    assert e.settings("root") == Goals.ROOT_ID


def test_apply_mapping_for_the_11th_element(goal_chain_11) -> None:
    e = Enumeration(goal_chain_11)
    assert e.q() == RenderResult(
        [
            RenderRow(11, 1, "a", True, False, [child(12)]),
            RenderRow(12, 2, "b", True, False, [child(13)]),
            RenderRow(13, 3, "c", True, False, [child(14)]),
            RenderRow(14, 4, "d", True, False, [child(15)]),
            RenderRow(15, 5, "e", True, False, [child(16)]),
            RenderRow(16, 6, "f", True, False, [child(17)]),
            RenderRow(17, 7, "g", True, False, [child(18)]),
            RenderRow(18, 8, "h", True, False, [child(19)]),
            RenderRow(19, 9, "i", True, False, [child(10)]),
            RenderRow(10, 10, "j", True, False, [child(21)]),
            RenderRow(21, 11, "k", True, True, []),
        ],
        select=(11, 11),
        roots={11},
    )
    assert e.settings("root") == 11


def test_use_mapping_in_selection(goal_chain_10) -> None:
    e = Enumeration(goal_chain_10)
    e.accept(Select(0))
    assert e.q() == RenderResult(
        [
            RenderRow(1, 1, "a", True, False, [child(2)]),
            RenderRow(2, 2, "b", True, False, [child(3)]),
            RenderRow(3, 3, "c", True, False, [child(4)]),
            RenderRow(4, 4, "d", True, False, [child(5)]),
            RenderRow(5, 5, "e", True, False, [child(6)]),
            RenderRow(6, 6, "f", True, False, [child(7)]),
            RenderRow(7, 7, "g", True, False, [child(8)]),
            RenderRow(8, 8, "h", True, False, [child(9)]),
            RenderRow(9, 9, "i", True, False, [child(0)]),
            RenderRow(0, 10, "j", True, True, []),
        ],
        select=(0, 1),
        roots={1},
    )


def test_do_not_select_goal_by_partial_id(goal_chain_11) -> None:
    e = Enumeration(goal_chain_11)
    # Select(1) is kept in cache, and selection is not changed yet
    e.accept_all(Select(1))
    assert e.q() == RenderResult(
        [
            RenderRow(11, 1, "a", True, False, [child(12)]),
            RenderRow(12, 2, "b", True, False, [child(13)]),
            RenderRow(13, 3, "c", True, False, [child(14)]),
            RenderRow(14, 4, "d", True, False, [child(15)]),
            RenderRow(15, 5, "e", True, False, [child(16)]),
            RenderRow(16, 6, "f", True, False, [child(17)]),
            RenderRow(17, 7, "g", True, False, [child(18)]),
            RenderRow(18, 8, "h", True, False, [child(19)]),
            RenderRow(19, 9, "i", True, False, [child(10)]),
            RenderRow(10, 10, "j", True, False, [child(21)]),
            RenderRow(21, 11, "k", True, True, []),
        ],
        select=(11, 11),
        roots={11},
    )


def test_select_goal_by_id_parts(goal_chain_11) -> None:
    e = Enumeration(goal_chain_11)
    e.accept_all(Select(1), Select(6))
    assert e.q() == RenderResult(
        [
            RenderRow(11, 1, "a", True, False, [child(12)]),
            RenderRow(12, 2, "b", True, False, [child(13)]),
            RenderRow(13, 3, "c", True, False, [child(14)]),
            RenderRow(14, 4, "d", True, False, [child(15)]),
            RenderRow(15, 5, "e", True, False, [child(16)]),
            RenderRow(16, 6, "f", True, False, [child(17)]),
            RenderRow(17, 7, "g", True, False, [child(18)]),
            RenderRow(18, 8, "h", True, False, [child(19)]),
            RenderRow(19, 9, "i", True, False, [child(10)]),
            RenderRow(10, 10, "j", True, False, [child(21)]),
            RenderRow(21, 11, "k", True, True, []),
        ],
        select=(16, 11),
        roots={11},
    )


def test_select_goal_by_full_id(goal_chain_11) -> None:
    e = Enumeration(goal_chain_11)
    assert e.q() == RenderResult(
        [
            RenderRow(11, 1, "a", True, False, [child(12)]),
            RenderRow(12, 2, "b", True, False, [child(13)]),
            RenderRow(13, 3, "c", True, False, [child(14)]),
            RenderRow(14, 4, "d", True, False, [child(15)]),
            RenderRow(15, 5, "e", True, False, [child(16)]),
            RenderRow(16, 6, "f", True, False, [child(17)]),
            RenderRow(17, 7, "g", True, False, [child(18)]),
            RenderRow(18, 8, "h", True, False, [child(19)]),
            RenderRow(19, 9, "i", True, False, [child(10)]),
            RenderRow(10, 10, "j", True, False, [child(21)]),
            RenderRow(21, 11, "k", True, True, []),
        ],
        select=(11, 11),
        roots={11},
    )
    e.accept(Select(13))
    assert e.q() == RenderResult(
        [
            RenderRow(11, 1, "a", True, False, [child(12)]),
            RenderRow(12, 2, "b", True, False, [child(13)]),
            RenderRow(13, 3, "c", True, False, [child(14)]),
            RenderRow(14, 4, "d", True, False, [child(15)]),
            RenderRow(15, 5, "e", True, False, [child(16)]),
            RenderRow(16, 6, "f", True, False, [child(17)]),
            RenderRow(17, 7, "g", True, False, [child(18)]),
            RenderRow(18, 8, "h", True, False, [child(19)]),
            RenderRow(19, 9, "i", True, False, [child(10)]),
            RenderRow(10, 10, "j", True, False, [child(21)]),
            RenderRow(21, 11, "k", True, True, []),
        ],
        select=(13, 11),
        roots={11},
    )


def test_select_goal_by_full_id_with_non_empty_cache(goal_chain_11) -> None:
    e = Enumeration(goal_chain_11)
    assert e.q() == RenderResult(
        [
            RenderRow(11, 1, "a", True, False, [child(12)]),
            RenderRow(12, 2, "b", True, False, [child(13)]),
            RenderRow(13, 3, "c", True, False, [child(14)]),
            RenderRow(14, 4, "d", True, False, [child(15)]),
            RenderRow(15, 5, "e", True, False, [child(16)]),
            RenderRow(16, 6, "f", True, False, [child(17)]),
            RenderRow(17, 7, "g", True, False, [child(18)]),
            RenderRow(18, 8, "h", True, False, [child(19)]),
            RenderRow(19, 9, "i", True, False, [child(10)]),
            RenderRow(10, 10, "j", True, False, [child(21)]),
            RenderRow(21, 11, "k", True, True, []),
        ],
        select=(11, 11),
        roots={11},
    )
    e.accept_all(Select(2), Select(13))
    assert e.q() == RenderResult(
        [
            RenderRow(11, 1, "a", True, False, [child(12)]),
            RenderRow(12, 2, "b", True, False, [child(13)]),
            RenderRow(13, 3, "c", True, False, [child(14)]),
            RenderRow(14, 4, "d", True, False, [child(15)]),
            RenderRow(15, 5, "e", True, False, [child(16)]),
            RenderRow(16, 6, "f", True, False, [child(17)]),
            RenderRow(17, 7, "g", True, False, [child(18)]),
            RenderRow(18, 8, "h", True, False, [child(19)]),
            RenderRow(19, 9, "i", True, False, [child(10)]),
            RenderRow(10, 10, "j", True, False, [child(21)]),
            RenderRow(21, 11, "k", True, True, []),
        ],
        select=(13, 11),
        roots={11},
    )


def test_enumerated_goals_must_have_the_same_dimension() -> None:
    e = Enumeration(
        build_goaltree(
            open_(1, "a", [2, 20], select=selected), open_(2, "b"), open_(20, "x")
        )
    )
    assert e.q() == RenderResult(
        [
            RenderRow(1, 1, "a", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "b", True, True, []),
            RenderRow(3, 20, "x", True, True, []),
        ],
        select=(1, 1),
        roots={1},
    )


def test_selection_cache_should_be_reset_after_view_switch(goal_chain_11) -> None:
    e = Enumeration(SwitchableView(goal_chain_11))
    e.accept_all(Add("Also top"))
    e.accept(Select(1))
    # Select(1) is kept in a cache and not applied yet
    e.accept(ToggleSwitchableView())
    assert e.q() == RenderResult(
        [
            RenderRow(1, 1, "a", True, False, []),
            RenderRow(2, 11, "k", True, True, []),
            RenderRow(3, 12, "Also top", True, True, []),
        ],
        select=(1, 1),
        roots={1, 2, 3},
    )
    # Select(2) is being applied without any effect from the previous selection
    # This happens because selection cache was reset
    e.accept(Select(2))
    assert e.q() == RenderResult(
        [
            RenderRow(1, 1, "a", True, False, []),
            RenderRow(2, 11, "k", True, True, []),
            RenderRow(3, 12, "Also top", True, True, []),
        ],
        select=(2, 1),
        roots={1, 2, 3},
    )


def test_selection_cache_should_avoid_overflow(goal_chain_11) -> None:
    e = Enumeration(goal_chain_11)
    assert e.q().select == (11, 11)
    e.accept(Select(5))
    assert e.q().select == (11, 11)
    e.accept(Select(1))
    assert e.q().select == (11, 11)
    e.accept(Select(4))
    assert e.q().select == (14, 11)


def test_do_not_enumerate_goals_with_negative_id() -> None:
    g = all_layers(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Zoomed", [3], select=selected),
            open_(3, "Top"),
        )
    )
    g.accept(ToggleZoom())
    assert g.q() == RenderResult(
        [
            RenderRow(2, 2, "Zoomed", True, False, [child(3)], {"Zoom": "root"}),
            RenderRow(3, 3, "Top", True, True, []),
            RenderRow(-1, -1, "Root", True, False, [blocker(2)]),
        ],
        select=(2, 2),
        roots={2},
    )
    e = Enumeration(g)
    assert e.q() == RenderResult(
        [
            RenderRow(1, 2, "Zoomed", True, False, [child(2)], {"Zoom": "root"}),
            RenderRow(2, 3, "Top", True, True, []),
            RenderRow(-1, -1, "Root", True, False, [blocker(1)]),
        ],
        select=(1, 1),
        roots={1},
    )


def test_all_keys_in_enumeration_must_be_of_the_same_length() -> None:
    items = [i + 1 for i in range(2999)]
    e = BidirectionalIndex(items)
    mapped = [e.forward(x) for x in items]
    assert len(mapped) == len(items)
    assert {len(str(k)) for k in mapped} == {4}
