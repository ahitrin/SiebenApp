import pytest

from siebenapp.autolink import AutoLink, ToggleAutoLink
from siebenapp.domain import (
    ToggleClose,
    Add,
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
from tests.dsl import build_goaltree, open_, clos_


@pytest.fixture()
def tree_2_goals():
    return AutoLink(build_goaltree(open_(1, "Root", [2]), open_(2, "Autolink on me")))


@pytest.fixture()
def tree_3v_goals():
    return AutoLink(
        build_goaltree(
            open_(1, "Root", [2, 3]),
            open_(2, "Autolink on me"),
            open_(3, "Another subgoal"),
        )
    )


@pytest.fixture()
def tree_3i_goals():
    return AutoLink(
        build_goaltree(
            open_(1, "Root", [2]),
            open_(2, "Autolink on me", [3]),
            open_(3, "Another subgoal"),
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
    )
    goals.accept(ToggleAutoLink("heLLO", 2))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(2, 2, "Autolink on me", True, True, [], {"Autolink": "hello"}),
        ],
        roots={1},
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
    )
    assert _autolink_events(goals) == []


def test_do_not_add_autolink_to_closed_goals() -> None:
    messages: list[str] = []
    goals = AutoLink(
        build_goaltree(
            open_(1, "Root", [2]),
            clos_(2, "Well, it's closed"),
            message_fn=messages.append,
        )
    )
    goals.accept(ToggleAutoLink("Failed", 2))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, True, [child(2)]),
            RenderRow(2, 2, "Well, it's closed", False, True, []),
        ],
        roots={1},
    )
    assert messages == ["Autolink cannot be set for closed goals"]
    assert _autolink_events(goals) == []


def test_do_not_add_autolink_to_root_goal() -> None:
    messages: list[str] = []
    goals = AutoLink(build_goaltree(open_(1, "Root"), message_fn=messages.append))
    goals.accept(ToggleAutoLink("misused", 1))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, True, []),
        ],
        roots={1},
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
    )
    goals.accept(ToggleClose(2))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, True, [child(2)]),
            RenderRow(2, 2, "Autolink on me", False, True, []),
        ],
        roots={1},
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
    )
    goals.accept(Delete(2))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, True, []),
        ],
        roots={1},
    )
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "test"),
        ("remove_autolink", 2),
    ]


def test_remove_autolink_on_parent_delete(tree_3i_goals) -> None:
    goals = tree_3i_goals
    goals.accept(ToggleAutoLink("test", 3))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(2, 2, "Autolink on me", True, False, [child(3)]),
            RenderRow(3, 3, "Another subgoal", True, True, [], {"Autolink": "test"}),
        ],
        roots={1},
    )
    goals.accept(Delete(2))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, True, []),
        ],
        roots={1},
    )
    assert _autolink_events(goals) == [
        ("add_autolink", 3, "test"),
        ("remove_autolink", 3),
    ]


def test_replace_same_autolink(tree_3v_goals) -> None:
    goals = tree_3v_goals
    goals.accept_all(ToggleAutoLink("same", 2), ToggleAutoLink("same", 3))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "Autolink on me", True, True, []),
            RenderRow(3, 3, "Another subgoal", True, True, [], {"Autolink": "same"}),
        ],
        roots={1},
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
    goals.accept(Add("Goodbye", 1))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "Autolink on me", True, True, [], {"Autolink": "hello"}),
            RenderRow(3, 3, "Goodbye", True, True, []),
        ],
        roots={1},
    )
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "hello"),
    ]


def test_make_a_link_on_matching_add(tree_2_goals) -> None:
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("me", 2))
    # Add a goal to the root
    goals.accept(Add("Link ME please", 1))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), relation(3)]),
            RenderRow(
                2, 2, "Autolink on me", True, False, [child(3)], {"Autolink": "me"}
            ),
            RenderRow(3, 3, "Link ME please", True, True, []),
        ],
        roots={1},
    )
    assert _autolink_events(goals) == [
        ("add_autolink", 2, "me"),
    ]


def test_do_not_make_a_link_on_not_old_matching_add(tree_2_goals) -> None:
    goals = tree_2_goals
    goals.accept_all(ToggleAutoLink("old", 2), ToggleAutoLink("new", 2))
    # Add a goal to the root
    goals.accept(Add("This is old subgoal", 1))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "Autolink on me", True, True, [], {"Autolink": "new"}),
            RenderRow(3, 3, "This is old subgoal", True, True, []),
        ],
        roots={1},
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
    goals.accept(Insert("Link ME please", 1, 3))
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
    )


def test_make_a_link_on_matching_rename(tree_3v_goals) -> None:
    goals = tree_3v_goals
    goals.accept(ToggleAutoLink("me", 2))
    goals.accept(Rename("Link ME please", 3))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), relation(3)]),
            RenderRow(
                2, 2, "Autolink on me", True, False, [child(3)], {"Autolink": "me"}
            ),
            RenderRow(3, 3, "Link ME please", True, True, []),
        ],
        roots={1},
    )


def test_do_not_make_a_link_on_matching_subgoal_add(tree_2_goals) -> None:
    goals = tree_2_goals
    goals.accept(ToggleAutoLink("me", 2))
    # Add a sub goal to the same subgoal
    goals.accept(Add("Do NOT link me please", 2))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(
                2, 2, "Autolink on me", True, False, [child(3)], {"Autolink": "me"}
            ),
            RenderRow(3, 3, "Do NOT link me please", True, True, []),
        ],
        roots={1},
    )


def test_do_not_make_a_link_on_matching_subgoal_insert(tree_3i_goals) -> None:
    goals = tree_3i_goals
    goals.accept(ToggleAutoLink("me", 2))
    # Add a sub goal to the same subgoal
    goals.accept(Insert("Do NOT link me please", 2, 3))
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
    )


def test_do_not_make_a_link_on_matching_subgoal_rename(tree_3i_goals) -> None:
    goals = tree_3i_goals
    goals.accept(ToggleAutoLink("me", 2))
    goals.accept(Rename("Do NOT link me please", 3))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2)]),
            RenderRow(
                2, 2, "Autolink on me", True, False, [child(3)], {"Autolink": "me"}
            ),
            RenderRow(3, 3, "Do NOT link me please", True, True, []),
        ],
        roots={1},
    )


def test_autolink_on_all_matching_goals(tree_3v_goals) -> None:
    goals = tree_3v_goals
    # make 2 autolinks
    goals.accept_all(ToggleAutoLink("me", 2), ToggleAutoLink("plea", 3))
    assert goals.q() == RenderResult(
        [
            RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
            RenderRow(2, 2, "Autolink on me", True, True, [], {"Autolink": "me"}),
            RenderRow(3, 3, "Another subgoal", True, True, [], {"Autolink": "plea"}),
        ],
        roots={1},
    )
    # add 2-mathing goal
    goals.accept(Add("Link me to both please", 1))
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
    )
    # re-link goal from relation into a blocker
    goals.accept(ToggleLink(3, 4, EdgeType.BLOCKER))
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
    )
