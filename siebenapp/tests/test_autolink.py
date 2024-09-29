import pytest

from siebenapp.autolink import AutoLink, ToggleAutoLink
from siebenapp.domain import (
    ToggleClose,
    Select,
    Add,
    HoldSelect,
    Insert,
    Rename,
    Graph,
    Delete,
    RenderRow,
    RenderResult,
    child,
    blocker,
    relation,
    ToggleLink,
    EdgeType,
)
from siebenapp.goaltree import OPTION_SELECT, OPTION_PREV_SELECT, Selectable
from siebenapp.tests.dsl import build_goaltree, open_, clos_


@pytest.fixture()
def tree_2_goals():
    return AutoLink(
        Selectable(
            build_goaltree(open_(1, "Root", [2]), open_(2, "Autolink on me")),
            [("selection", 2), ("previous_selection", 2)],
        )
    )


@pytest.fixture()
def tree_3v_goals():
    return AutoLink(
        Selectable(
            build_goaltree(
                open_(1, "Root", [2, 3]),
                open_(2, "Autolink on me"),
                open_(3, "Another subgoal"),
            ),
            [("selection", 2), ("previous_selection", 2)],
        )
    )


@pytest.fixture()
def tree_3i_goals():
    return AutoLink(
        Selectable(
            build_goaltree(
                open_(1, "Root", [2]),
                open_(2, "Autolink on me", [3]),
                open_(3, "Another subgoal"),
            ),
            [("selection", 2), ("previous_selection", 2)],
        )
    )


def _autolink_events(goals: Graph) -> list[tuple]:
    return [e for e in goals.events() if "autolink" in e[0]]


def test_show_new_pseudogoal_on_autolink_event(tree_2_goals) -> None:
    goals = tree_2_goals
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(2, 2, "Autolink on me", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
    )
    goals.accept(ToggleAutoLink("heLLO", 2))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(2, 2, "Autolink on me", True, True, [], {"Autolink": "hello"}),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
    )
    assert _autolink_events(goals) == [("add_autolink", 2, "hello")]


def test_replace_old_autolink_with_new_one(tree_2_goals) -> None:
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink("first", 2), ToggleAutoLink("second", 2))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(2, 2, "Autolink on me", True, True, [], {"Autolink": "second"}),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
    )
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "first"),
        ("remove_autolink", 2),
        ("add_autolink", 2, "second"),
    ]


def test_remove_autolink_by_sending_empty_keyword(tree_2_goals) -> None:
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink("lalala", 2), ToggleAutoLink("", 2))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(2, 2, "Autolink on me", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
    )
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "lalala"),
        ("remove_autolink", 2),
    ]


def test_remove_autolink_by_sending_whitespace(tree_2_goals) -> None:
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink("lalala", 2), ToggleAutoLink(" ", 2))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(2, 2, "Autolink on me", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
    )
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "lalala"),
        ("remove_autolink", 2),
    ]


def test_do_not_add_autolink_on_whitespace(tree_2_goals) -> None:
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink(" ", 2))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(2, 2, "Autolink on me", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
    )
    assert _autolink_events(goals) == []


def test_do_not_add_autolink_to_closed_goals() -> None:
    messages: list[str] = []
    goals = AutoLink(
        Selectable(
            build_goaltree(
                open_(1, "Root", [2]),
                clos_(2, "Well, it's closed"),
                message_fn=messages.append,
            ),
            [("selection", 2), ("previous_selection", 2)],
        )
    )
    goals.accept(ToggleAutoLink("Failed", 2))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, True, [child(2)]),
            RenderRow(2, 2, "Well, it's closed", False, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
    )
    assert messages == ["Autolink cannot be set for closed goals"]
    assert _autolink_events(goals) == []


def test_do_not_add_autolink_to_root_goal() -> None:
    messages: list[str] = []
    goals = AutoLink(
        Selectable(build_goaltree(open_(1, "Root"), message_fn=messages.append))
    )
    goals.accept(ToggleAutoLink("misused", 1))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
    )
    assert messages == ["Autolink cannot be set for the root goal"]
    assert _autolink_events(goals) == []


def test_remove_autolink_on_close(tree_2_goals) -> None:
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("test", 2))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(2, 2, "Autolink on me", True, True, [], {"Autolink": "test"}),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
    )
    goals.accept(ToggleClose())
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, True, [child(2)]),
            RenderRow(2, 2, "Autolink on me", False, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
    )
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "test"),
        ("remove_autolink", 2),
    ]


def test_remove_autolink_on_delete(tree_2_goals) -> None:
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("test", 2))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(2, 2, "Autolink on me", True, True, [], {"Autolink": "test"}),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
    )
    goals.accept(Delete())
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
    )
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "test"),
        ("remove_autolink", 2),
    ]


def test_remove_autolink_on_parent_delete(tree_3i_goals) -> None:
    goals = tree_3i_goals
    goals.accept_all(Select(3), ToggleAutoLink("test", 3))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(2, 2, "Autolink on me", True, False, [child(3)]),
            RenderRow(3, 3, "Another subgoal", True, True, [], {"Autolink": "test"}),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 2},
    )
    goals.accept_all(Select(2), Delete())
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
    )
    assert _autolink_events(goals) == [
        ("add_autolink", 3, "test"),
        ("remove_autolink", 3),
    ]


def test_replace_same_autolink(tree_3v_goals) -> None:
    goals = tree_3v_goals
    goals.accept_all(ToggleAutoLink("same", 2), Select(3), ToggleAutoLink("same", 3))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "Autolink on me", True, True, []),
            RenderRow(3, 3, "Another subgoal", True, True, [], {"Autolink": "same"}),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 2},
    )
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "same"),
        ("remove_autolink", 2),
        ("add_autolink", 3, "same"),
    ]


def test_do_not_make_a_link_on_not_matching_add(tree_2_goals) -> None:
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("hello", 2))
    # Add a goal to the root
    goals.accept_all(Select(1), Add("Goodbye"))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "Autolink on me", True, True, [], {"Autolink": "hello"}),
            RenderRow(3, 3, "Goodbye", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 2},
    )
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "hello"),
    ]


def test_make_a_link_on_matching_add(tree_2_goals) -> None:
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("me", 2))
    # Add a goal to the root
    goals.accept_all(Select(1), Add("Link ME please"))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), relation(3)]),
            RenderRow(
                2, 2, "Autolink on me", True, False, [child(3)], {"Autolink": "me"}
            ),
            RenderRow(3, 3, "Link ME please", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 2},
    )
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "me"),
    ]


def test_do_not_make_a_link_on_not_old_matching_add(tree_2_goals) -> None:
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink("old", 2), ToggleAutoLink("new", 2))
    # Add a goal to the root
    goals.accept_all(Select(1), Add("This is old subgoal"))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "Autolink on me", True, True, [], {"Autolink": "new"}),
            RenderRow(3, 3, "This is old subgoal", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 2},
    )
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "old"),
        ("remove_autolink", 2),
        ("add_autolink", 2, "new"),
    ]


def test_make_a_link_on_matching_insert(tree_3v_goals) -> None:
    goals = tree_3v_goals
    goals.accept(ToggleAutoLink("me", 2))
    # Add a goal to the root
    goals.accept_all(Select(1), HoldSelect(), Select(3), Insert("Link ME please"))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), relation(4)]),
            RenderRow(
                2, 2, "Autolink on me", True, False, [child(4)], {"Autolink": "me"}
            ),
            RenderRow(3, 3, "Another subgoal", True, True, []),
            RenderRow(4, 4, "Link ME please", True, False, [child(3)]),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 1},
    )


def test_make_a_link_on_matching_rename(tree_3v_goals) -> None:
    goals = tree_3v_goals
    goals.accept(ToggleAutoLink("me", 2))
    goals.accept_all(Select(3), Rename("Link ME please"))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), relation(3)]),
            RenderRow(
                2, 2, "Autolink on me", True, False, [child(3)], {"Autolink": "me"}
            ),
            RenderRow(3, 3, "Link ME please", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 2},
    )


def test_do_not_make_a_link_on_matching_subgoal_add(tree_2_goals) -> None:
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("me", 2))
    # Add a sub goal to the same subgoal
    goals.accept_all(Add("Do NOT link me please"))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(
                2, 2, "Autolink on me", True, False, [child(3)], {"Autolink": "me"}
            ),
            RenderRow(3, 3, "Do NOT link me please", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
    )


def test_do_not_make_a_link_on_matching_subgoal_insert(tree_3i_goals) -> None:
    goals = tree_3i_goals
    goals.accept(ToggleAutoLink("me", 2))
    # Add a sub goal to the same subgoal
    goals.accept_all(HoldSelect(), Select(3), Insert("Do NOT link me please"))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(
                2, 2, "Autolink on me", True, False, [child(4)], {"Autolink": "me"}
            ),
            RenderRow(3, 3, "Another subgoal", True, True, []),
            RenderRow(4, 4, "Do NOT link me please", True, False, [child(3)]),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 2},
    )


def test_do_not_make_a_link_on_matching_subgoal_rename(tree_3i_goals) -> None:
    goals = tree_3i_goals
    goals.accept(ToggleAutoLink("me", 2))
    goals.accept_all(Select(3), Rename("Do NOT link me please"))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(
                2, 2, "Autolink on me", True, False, [child(3)], {"Autolink": "me"}
            ),
            RenderRow(3, 3, "Do NOT link me please", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 2},
    )


def test_autolink_on_all_matching_goals(tree_3v_goals) -> None:
    goals = tree_3v_goals
    # make 2 autolinks
    goals.accept_all(ToggleAutoLink("me", 2), Select(3), ToggleAutoLink("plea", 3))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "Autolink on me", True, True, [], {"Autolink": "me"}),
            RenderRow(3, 3, "Another subgoal", True, True, [], {"Autolink": "plea"}),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 2},
    )
    # add 2-mathing goal
    goals.accept_all(Select(1), Add("Link me to both please"))
    assert goals.q() == RenderResult(
        [
            RenderRow(
                1,
                1,
                "Root",
                True,
                False,
                [child(2), child(3), relation(4)],
            ),
            RenderRow(
                2, 2, "Autolink on me", True, True, [relation(4)], {"Autolink": "me"}
            ),
            RenderRow(
                3, 3, "Another subgoal", True, False, [child(4)], {"Autolink": "plea"}
            ),
            RenderRow(4, 4, "Link me to both please", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 2},
    )


def test_relink_as_blocker(tree_3v_goals) -> None:
    goals = tree_3v_goals
    # add a subgoal that matches autolink pattern
    goals.accept_all(ToggleAutoLink("target", 2), Add("relink target", 3))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(
                2, 2, "Autolink on me", True, False, [child(4)], {"Autolink": "target"}
            ),
            RenderRow(3, 3, "Another subgoal", True, True, [relation(4)]),
            RenderRow(4, 4, "relink target", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
    )
    # re-link goal from relation into a blocker
    goals.accept_all(Select(3), HoldSelect(), Select(4))
    goals.accept(ToggleLink(edge_type=EdgeType.BLOCKER))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(
                2, 2, "Autolink on me", True, False, [child(4)], {"Autolink": "target"}
            ),
            RenderRow(3, 3, "Another subgoal", True, False, [blocker(4)]),
            RenderRow(4, 4, "relink target", True, True, []),
        ],
        roots={1},
        global_opts={OPTION_SELECT: 4, OPTION_PREV_SELECT: 3},
    )
