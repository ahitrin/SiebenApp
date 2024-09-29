import pytest

from siebenapp.autolink import ToggleAutoLink
from siebenapp.domain import (
    Add,
    Rename,
    ToggleClose,
    Delete,
    Insert,
    Select,
    HoldSelect,
)
from siebenapp.filter_view import FilterBy
from siebenapp.layers import all_layers
from siebenapp.open_view import ToggleOpenView
from siebenapp.progress_view import ToggleProgress
from siebenapp.render import GoalsHolder
from siebenapp.switchable_view import ToggleSwitchableView
from siebenapp.tests.dsl import build_goaltree, open_, clos_
from siebenapp.zoom import ToggleZoom

WIDTH = 3


@pytest.fixture
def sample_tree():
    return all_layers(
        build_goaltree(
            open_(1, "Root", [2, 3, 4]),
            open_(2, "Selected"),
            open_(3, "Previous", [5], blockers=[4]),
            open_(4, "Blocked", blockers=[6]),
            clos_(5, "Closed intermediate", [6]),
            clos_(6, "Closed top"),
        ),
        [("selection", 2), ("previous_selection", 3)],
    )


@pytest.fixture
def sample_holder(sample_tree):
    return GoalsHolder(sample_tree, ":memory:")


def test_no_diff_on_start(sample_holder):
    holder = sample_holder
    result = holder.render(WIDTH)
    assert result[1] == []


@pytest.mark.parametrize(
    "event",
    [
        Add("New"),
        Insert("Middle"),
        Rename("New name"),
        ToggleClose(),
        Delete(),
        FilterBy("anything"),
        ToggleAutoLink("keyword", 2),
        ToggleProgress(),
        ToggleZoom(),
        ToggleSwitchableView(),
        ToggleOpenView(),
    ],
)
def test_no_diff_when_goaltree_changes(sample_holder, event):
    holder = sample_holder
    holder.render(WIDTH)  # Prepare cached result
    holder.accept(event)
    result = holder.render(WIDTH)
    assert result[1] == []


def test_make_diff_on_select(sample_holder):
    holder = sample_holder
    holder.render(WIDTH)  # Prepare cached result
    holder.accept(Select(4))
    result = holder.render(WIDTH)
    assert result[1] == [2, 4]


def test_make_diff_on_hold(sample_holder):
    holder = sample_holder
    holder.render(WIDTH)  # Prepare cached result
    holder.accept(HoldSelect())
    result = holder.render(WIDTH)
    assert result[1] == [3, 2]
