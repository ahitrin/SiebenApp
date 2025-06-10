from unittest import TestCase

from siebenapp.goaltree import Goals
from siebenapp.selectable import (
    Selectable,
    OPTION_SELECT,
    OPTION_PREV_SELECT,
    Select,
    HoldSelect,
)
from siebenapp.domain import (
    EdgeType,
    ToggleClose,
    Delete,
    ToggleLink,
    Add,
    Insert,
    Rename,
    RenderRow,
    RenderResult,
    child,
    blocker,
    relation,
)
from tests.dsl import build_goaltree, open_, clos_


class SelectableTest(TestCase):
    def setUp(self):
        self.messages = []
        self.goals = Selectable(Goals("Root", self._register_message))

    def _selection(self) -> int:
        return int(self.goals.settings("selection"))

    def _prev(self) -> int:
        return int(self.goals.settings("previous_selection"))

    def _register_message(self, msg):
        self.messages.append(msg)

    def build(self, *goal_prototypes, select: tuple[int, int]) -> Selectable:
        return Selectable(
            build_goaltree(*goal_prototypes, message_fn=self._register_message),
            [("selection", select[0]), ("previous_selection", select[1])],
        )

    def test_there_is_one_goal_at_start(self) -> None:
        assert self.goals.q() == RenderResult(
            [RenderRow(1, 1, "Root", True, True, [])],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_add_goal(self) -> None:
        self.goals.accept(Add("A", self._selection()))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "A", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_add_two_goals(self) -> None:
        self.goals.accept_all(Add("A", self._selection()), Add("B", self._selection()))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, True, []),
                RenderRow(3, 3, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_add_two_goals_in_a_chain(self) -> None:
        self.goals.accept_all(Add("A", self._selection()), Add("AA", 2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "A", True, False, [child(3)]),
                RenderRow(3, 3, "AA", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_rename_goal(self) -> None:
        self.goals.accept_all(Add("Boom", self._selection()), Select(2), Rename("A", 2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "A", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 1},
        )

    def test_insert_goal_in_the_middle(self) -> None:
        self.goals.accept_all(Add("B", self._selection()), HoldSelect(), Select(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 1},
        )
        self.goals.accept(Insert("A", self._prev(), self._selection()))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(3)]),
                RenderRow(2, 2, "B", True, True, []),
                RenderRow(3, 3, "A", True, False, [child(2)]),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 1},
        )

    def test_insert_goal_between_independent_goals(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]), open_(2, "A"), open_(3, "B"), select=(3, 2)
        )
        self.goals.accept(Insert("Wow", self._prev(), self._selection()))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, False, [blocker(4)]),
                RenderRow(3, 3, "B", True, True, []),
                RenderRow(4, 4, "Wow", True, False, [blocker(3)]),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 2},
        )

    def test_reverse_insertion(self) -> None:
        """Not sure whether such trick should be legal"""
        self.goals = self.build(
            open_(1, "Root", [2]), open_(2, "Selected"), select=(1, 2)
        )
        self.goals.accept(Insert("Intermediate?", self._prev(), self._selection()))
        # No, it's not intermediate
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "Selected", True, False, [blocker(3)]),
                RenderRow(3, 3, "Intermediate?", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 2},
        )

    def test_close_single_goal(self) -> None:
        assert self.goals.q() == RenderResult(
            [RenderRow(1, 1, "Root", True, True, [])],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )
        self.goals.accept(ToggleClose(1))
        assert self.goals.q() == RenderResult(
            [RenderRow(1, 1, "Root", False, True, [])],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_reopen_goal(self) -> None:
        self.goals = self.build(open_(1, "Root", [2]), clos_(2, "A"), select=(2, 2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, True, [child(2)]),
                RenderRow(2, 2, "A", False, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
        )
        self.goals.accept(ToggleClose(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "A", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
        )

    def test_close_goal_again(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]), open_(2, "A", [3]), clos_(3, "Ab"), select=(1, 1)
        )
        self.goals.accept_all(Select(2), ToggleClose(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, True, [child(2)]),
                RenderRow(2, 2, "A", False, True, [child(3)]),
                RenderRow(3, 3, "Ab", False, False, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )
        self.goals.accept_all(Select(2), ToggleClose(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "A", True, True, [child(3)]),
                RenderRow(3, 3, "Ab", False, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 1},
        )
        self.goals.accept_all(Select(2), ToggleClose(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, True, [child(2)]),
                RenderRow(2, 2, "A", False, True, [child(3)]),
                RenderRow(3, 3, "Ab", False, False, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_closed_leaf_goal_could_not_be_reopened(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]), clos_(2, "A", [3]), clos_(3, "B"), select=(1, 1)
        )
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, True, [child(2)]),
                RenderRow(2, 2, "A", False, True, [child(3)]),
                RenderRow(3, 3, "B", False, False, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )
        self.goals.accept_all(Select(3), ToggleClose(3))
        # nothing should change except select
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, True, [child(2)]),
                RenderRow(2, 2, "A", False, True, [child(3)]),
                RenderRow(3, 3, "B", False, False, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 1},
        )

    def test_goal_in_the_middle_could_not_be_closed(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", blockers=[4]),
            open_(3, "B", [4]),
            open_(4, "C"),
            select=(3, 3),
        )
        self.goals.accept(ToggleClose(self._selection()))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, False, [blocker(4)]),
                RenderRow(3, 3, "B", True, False, [child(4)]),
                RenderRow(4, 4, "C", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 3},
        )

    def test_blocker_could_not_be_switchable(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            clos_(2, "Blocked", blockers=[4]),
            open_(3, "Intermediate", [4]),
            clos_(4, "Blocker"),
            select=(2, 2),
        )
        # Goal 4 should not be switchable when goal 2 is closed
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "Blocked", False, True, [blocker(4)]),
                RenderRow(3, 3, "Intermediate", True, True, [child(4)]),
                RenderRow(4, 4, "Blocker", False, False, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
        )
        # Goal 4 could only become switchable when we reopen goal 2
        self.goals.accept(ToggleClose(self._selection()))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "Blocked", True, True, [blocker(4)]),
                RenderRow(3, 3, "Intermediate", True, True, [child(4)]),
                RenderRow(4, 4, "Blocker", False, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
        )

    def test_delete_single_goal(self) -> None:
        self.goals = self.build(open_(1, "Root", [2]), open_(2, "A"), select=(2, 2))
        self.goals.accept(Delete(2))
        assert self.goals.q() == RenderResult(
            [RenderRow(1, 1, "Root", True, True, [])],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_delete_leaf_goal(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]), open_(2, "A"), open_(3, "B"), select=(2, 2)
        )
        self.goals.accept(Delete(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(3)]),
                RenderRow(3, 3, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_delete_with_children(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]), open_(2, "A", [3]), open_(3, "B"), select=(2, 2)
        )
        self.goals.accept(Delete(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_delete_with_blocker(self) -> None:
        self.goals = self.build(
            open_(1, "Root", blockers=[2]),
            open_(2, "A", blockers=[3]),
            open_(3, "B"),
            select=(2, 2),
        )
        self.goals.accept(Delete(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [blocker(3)]),
                RenderRow(3, 3, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_delete_with_relation(self) -> None:
        self.goals = self.build(
            open_(1, "Root", relations=[2]),
            open_(2, "A", relations=[3]),
            open_(3, "B"),
            select=(2, 2),
        )
        self.goals.accept(Delete(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, True, [relation(3)]),
                RenderRow(3, 3, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_delete_with_relation_and_closed_root(self) -> None:
        self.goals = self.build(
            clos_(1, "Root", relations=[2]),
            open_(2, "A", relations=[3]),
            open_(3, "B"),
            select=(2, 2),
        )
        self.goals.accept(Delete(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", False, True, [relation(3)]),
                RenderRow(3, 3, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_remove_goal_chain_with_children(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]), open_(2, "A", [3]), open_(3, "B"), select=(2, 2)
        )
        self.goals.accept(Delete(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_relink_goal_chain_with_blockers(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]),
            open_(2, "A", blockers=[3]),
            open_(3, "B"),
            select=(2, 2),
        )
        self.goals.accept(Delete(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [blocker(3)]),
                RenderRow(3, 3, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_relink_goal_chain_with_relation(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]),
            open_(2, "A", relations=[3]),
            open_(3, "B"),
            select=(2, 2),
        )
        self.goals.accept(Delete(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, True, [relation(3)]),
                RenderRow(3, 3, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_cannot_convert_relation_for_closed_goal(self) -> None:
        self.goals = self.build(
            clos_(1, "Root", relations=[2]), open_(2, "Related"), select=(2, 1)
        )
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", False, True, [relation(2)]),
                RenderRow(2, 2, "Related", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 1},
        )
        self.goals.accept(ToggleLink(1, 2))
        # Nothing should change
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", False, True, [relation(2)]),
                RenderRow(2, 2, "Related", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 1},
        )
        # Error message is expected
        assert self.messages == ["Cannot add a blocking relation to the closed goal"]

    def test_select_parent_after_delete(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]),
            open_(2, "Parent", [3]),
            open_(3, "Delete me"),
            select=(3, 1),
        )
        self.goals.accept(Delete(3))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "Parent", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
        )

    def test_add_blocker_link_between_goals(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]), open_(2, "A"), open_(3, "B"), select=(3, 2)
        )
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, True, []),
                RenderRow(3, 3, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 2},
        )
        self.goals.accept(ToggleLink(2, 3))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, False, [blocker(3)]),
                RenderRow(3, 3, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 2},
        )

    def test_add_relation_link_between_goals(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]), open_(2, "A"), open_(3, "B"), select=(3, 2)
        )
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, True, []),
                RenderRow(3, 3, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 2},
        )
        self.goals.accept(ToggleLink(2, 3, EdgeType.RELATION))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, True, [relation(3)]),
                RenderRow(3, 3, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 2},
        )

    def test_no_link_to_self_is_allowed(self) -> None:
        self.goals.accept(ToggleLink(1, 1))
        assert self.goals.q() == RenderResult(
            [RenderRow(1, 1, "Root", True, True, [])],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_no_loops_allowed(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]),
            open_(2, "step", [3]),
            open_(3, "next", [4]),
            open_(4, "more"),
            select=(1, 4),
        )
        self.goals.accept(ToggleLink(4, 1))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "step", True, False, [child(3)]),
                RenderRow(3, 3, "next", True, False, [child(4)]),
                RenderRow(4, 4, "more", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 4},
        )

    def test_new_parent_link_replaces_old_one(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "Old parent", [4]),
            open_(3, "New parent"),
            open_(4, "Child"),
            select=(4, 3),
        )
        self.goals.accept(ToggleLink(3, 4, EdgeType.PARENT))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "Old parent", True, True, [relation(4)]),
                RenderRow(3, 3, "New parent", True, False, [child(4)]),
                RenderRow(4, 4, "Child", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 4, OPTION_PREV_SELECT: 3},
        )

    def test_new_parent_link_replaces_old_one_when_changed_from_blocker(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A"),
            open_(3, "B", blockers=[2]),
            select=(2, 3),
        )
        self.goals.accept(ToggleLink(3, 2, EdgeType.PARENT))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [relation(2), child(3)]),
                RenderRow(2, 2, "A", True, True, []),
                RenderRow(3, 3, "B", True, False, [child(2)]),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 3},
        )

    def test_remove_link_between_goals(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", blockers=[3]),
            open_(3, "B"),
            select=(3, 2),
        )
        self.goals.accept(ToggleLink(2, 3, EdgeType.BLOCKER))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, True, []),
                RenderRow(3, 3, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 2},
        )

    def test_change_link_type(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]), open_(2, "Top", []), select=(2, 1)
        )
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "Top", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 1},
        )
        self.goals.accept(ToggleLink(1, 2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [blocker(2)]),
                RenderRow(2, 2, "Top", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 1},
        )
        self.goals.accept(ToggleLink(1, 2, EdgeType.PARENT))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "Top", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 1},
        )
        self.goals.accept(ToggleLink(1, 2, EdgeType.RELATION))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, True, [relation(2)]),
                RenderRow(2, 2, "Top", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 1},
        )

    def test_remove_blocked_goal_without_children(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", [4]),
            open_(3, "B", blockers=[4]),
            open_(4, "C"),
            select=(4, 4),
        )
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, False, [child(4)]),
                RenderRow(3, 3, "B", True, False, [blocker(4)]),
                RenderRow(4, 4, "C", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 4, OPTION_PREV_SELECT: 4},
        )
        self.goals.accept_all(Select(3), Delete(3))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "A", True, False, [child(4)]),
                RenderRow(4, 4, "C", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_children_of_blocked_goal_are_blocked_too(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "Subgoal 1", [4]),
            open_(3, "Subgoal 2"),
            open_(4, "Nested subgoal"),
            select=(1, 1),
        )
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "Subgoal 1", True, False, [child(4)]),
                RenderRow(3, 3, "Subgoal 2", True, True, []),
                RenderRow(4, 4, "Nested subgoal", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )
        # Blocking a goal should lead to blocking of all its subgoals
        self.goals.accept(
            Add("Overall blocker", self._selection(), edge_type=EdgeType.BLOCKER)
        )
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3), blocker(5)]),
                RenderRow(2, 2, "Subgoal 1", True, False, [child(4)]),
                RenderRow(3, 3, "Subgoal 2", True, False, []),
                RenderRow(4, 4, "Nested subgoal", True, False, []),
                RenderRow(5, 5, "Overall blocker", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_nested_subgoal_cannot_block_siblings_by_parent(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "Intermediate", [4]),
            open_(3, "Intermediate 2", [5]),
            open_(4, "Pseudo-blocker"),
            open_(5, "Top"),
            select=(4, 1),
        )
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "Intermediate", True, False, [child(4)]),
                RenderRow(3, 3, "Intermediate 2", True, False, [child(5)]),
                RenderRow(4, 4, "Pseudo-blocker", True, True, []),
                RenderRow(5, 5, "Top", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 4, OPTION_PREV_SELECT: 1},
        )
        # When a subgoal blocks parent, it shouldn't make all other subgoals and itself blocked
        self.goals.accept(ToggleLink(1, 4, EdgeType.BLOCKER))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3), blocker(4)]),
                RenderRow(2, 2, "Intermediate", True, False, [child(4)]),
                RenderRow(3, 3, "Intermediate 2", True, False, [child(5)]),
                RenderRow(4, 4, "Pseudo-blocker", True, True, []),
                RenderRow(5, 5, "Top", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 4, OPTION_PREV_SELECT: 1},
        )

    def test_mutual_blocking(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2], [3]),
            open_(2, "Blocker-of-blocker"),
            open_(3, "Blocker-of-root"),
            select=(2, 3),
        )
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), blocker(3)]),
                RenderRow(2, 2, "Blocker-of-blocker", True, False, []),
                RenderRow(3, 3, "Blocker-of-root", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 3},
        )
        # When we block a blocker, which goal should be switchable? Is such a move allowed?
        self.goals.accept(ToggleLink(3, 2))
        # Seems not to be allowed
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), blocker(3)]),
                RenderRow(2, 2, "Blocker-of-blocker", True, False, []),
                RenderRow(3, 3, "Blocker-of-root", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 3},
        )

    def test_mutual_blocking_by_converting_parent_link(self) -> None:
        """In this case, we get some kind of circular blocking.
        Subgoal 3 is transformed into a blocker of 1 and (therefore) of 2.
        But it's blocked by a subgoal 2 at the same time.
        As a result, none of goals is allowed to be switchable.
        Probably, it would be fixed in the future.
        Most likely, by disallowing a 1->3 link transformation from PARENT into BLOCKER.
        """
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "Goal 2"),
            open_(3, "Goal 3", blockers=[2]),
            select=(3, 1),
        )
        self.goals.accept(ToggleLink(1, 3, EdgeType.BLOCKER))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), blocker(3)]),
                RenderRow(2, 2, "Goal 2", True, False, []),
                RenderRow(3, 3, "Goal 3", True, False, [blocker(2)]),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 1},
        )

    def test_relation_edge_does_not_block(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "Have a relation", relations=[3]),
            open_(3, "Does not block"),
            select=(1, 1),
        )
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "Have a relation", True, True, [relation(3)]),
                RenderRow(3, 3, "Does not block", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_root_goal_is_selected_by_default(self) -> None:
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )
        self.goals.accept(Add("A", self._selection()))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "A", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )
        self.goals.accept(Add("B", self._selection()))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, True, []),
                RenderRow(3, 3, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_new_goal_is_added_to_the_selected_node(self) -> None:
        self.goals.accept_all(Add("A", self._selection()), Select(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "A", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 1},
        )
        self.goals.accept(Add("B", self._selection()))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2)]),
                RenderRow(2, 2, "A", True, False, [child(3)]),
                RenderRow(3, 3, "B", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 1},
        )

    def test_keep_selection_after_closing_another_goal(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3, 4]),
            open_(2, "A"),
            open_(3, "B"),
            open_(4, "C"),
            select=(2, 2),
        )
        self.goals.accept(ToggleClose(3))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3), child(4)]),
                RenderRow(2, 2, "A", True, True, []),
                RenderRow(3, 3, "B", False, True, []),
                RenderRow(4, 4, "C", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 2},
        )

    def test_move_selection_to_another_open_goal_after_closing_selected_goal(
        self,
    ) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3, 4]),
            open_(2, "A"),
            open_(3, "B"),
            open_(4, "C"),
            select=(2, 2),
        )
        self.goals.accept(ToggleClose(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3), child(4)]),
                RenderRow(2, 2, "A", False, True, []),
                RenderRow(3, 3, "B", True, True, []),
                RenderRow(4, 4, "C", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 3, OPTION_PREV_SELECT: 3},
        )

    def test_keep_selection_to_previously_selected_goal_after_closing_another_goal(
        self,
    ) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3, 4]),
            open_(2, "A"),
            open_(3, "B"),
            open_(4, "C"),
            select=(2, 4),
        )
        self.goals.accept(ToggleClose(3))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3), child(4)]),
                RenderRow(2, 2, "A", True, True, []),
                RenderRow(3, 3, "B", False, True, []),
                RenderRow(4, 4, "C", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 4},
        )

    def test_move_selection_to_previously_selected_goal_after_closing_selected_goal(
        self,
    ) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3, 4]),
            open_(2, "A"),
            open_(3, "B"),
            open_(4, "C"),
            select=(2, 4),
        )
        self.goals.accept(ToggleClose(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3), child(4)]),
                RenderRow(2, 2, "A", False, True, []),
                RenderRow(3, 3, "B", True, True, []),
                RenderRow(4, 4, "C", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 4, OPTION_PREV_SELECT: 4},
        )

    def test_move_selection_to_another_open_goal_with_given_root_after_closing(
        self,
    ) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "Should not be selected"),
            open_(3, "Subroot", [4, 5]),
            open_(4, "Must be selected"),
            open_(5, "Closing"),
            select=(5, 5),
        )
        self.goals.accept(ToggleClose(5, root=3))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "Should not be selected", True, True, []),
                RenderRow(3, 3, "Subroot", True, False, [child(4), child(5)]),
                RenderRow(4, 4, "Must be selected", True, True, []),
                RenderRow(5, 5, "Closing", False, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 4, OPTION_PREV_SELECT: 4},
        )

    def test_do_not_select_unswitchable_goal_after_closing(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "Should not be selected"),
            open_(3, "Subroot", [4, 5]),
            open_(4, "Intermediate", [6]),
            open_(5, "Closing"),
            open_(6, "Must be selected"),
            select=(5, 5),
        )
        self.goals.accept(ToggleClose(5, root=3))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, False, [child(2), child(3)]),
                RenderRow(2, 2, "Should not be selected", True, True, []),
                RenderRow(3, 3, "Subroot", True, False, [child(4), child(5)]),
                RenderRow(4, 4, "Intermediate", True, False, [child(6)]),
                RenderRow(5, 5, "Closing", False, True, []),
                RenderRow(6, 6, "Must be selected", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 6, OPTION_PREV_SELECT: 6},
        )

    def test_ignore_wrong_selection(self) -> None:
        self.goals.accept(Select(2))
        assert self.goals.q() == RenderResult(
            [RenderRow(1, 1, "Root", True, True, [])],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_do_not_select_deleted_goals(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]), open_(2, "broken"), select=(2, 2)
        )
        self.goals.accept_all(Delete(2), Select(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(1, 1, "Root", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 1, OPTION_PREV_SELECT: 1},
        )

    def test_selection_should_be_instant(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            open_(2, "A"),
            open_(3, "B"),
            open_(4, "C"),
            open_(5, "D"),
            open_(6, "E"),
            open_(7, "F"),
            open_(8, "G"),
            open_(9, "H"),
            open_(10, "I"),
            open_(11, "J"),
            select=(1, 1),
        )
        self.goals.accept(Select(2))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(
                    1,
                    1,
                    "Root",
                    True,
                    False,
                    [
                        child(2),
                        child(3),
                        child(4),
                        child(5),
                        child(6),
                        child(7),
                        child(8),
                        child(9),
                        child(10),
                        child(11),
                    ],
                ),
                RenderRow(2, 2, "A", True, True, []),
                RenderRow(3, 3, "B", True, True, []),
                RenderRow(4, 4, "C", True, True, []),
                RenderRow(5, 5, "D", True, True, []),
                RenderRow(6, 6, "E", True, True, []),
                RenderRow(7, 7, "F", True, True, []),
                RenderRow(8, 8, "G", True, True, []),
                RenderRow(9, 9, "H", True, True, []),
                RenderRow(10, 10, "I", True, True, []),
                RenderRow(11, 11, "J", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 2, OPTION_PREV_SELECT: 1},
        )
        self.goals.accept(Select(11))
        assert self.goals.q() == RenderResult(
            [
                RenderRow(
                    1,
                    1,
                    "Root",
                    True,
                    False,
                    [
                        child(2),
                        child(3),
                        child(4),
                        child(5),
                        child(6),
                        child(7),
                        child(8),
                        child(9),
                        child(10),
                        child(11),
                    ],
                ),
                RenderRow(2, 2, "A", True, True, []),
                RenderRow(3, 3, "B", True, True, []),
                RenderRow(4, 4, "C", True, True, []),
                RenderRow(5, 5, "D", True, True, []),
                RenderRow(6, 6, "E", True, True, []),
                RenderRow(7, 7, "F", True, True, []),
                RenderRow(8, 8, "G", True, True, []),
                RenderRow(9, 9, "H", True, True, []),
                RenderRow(10, 10, "I", True, True, []),
                RenderRow(11, 11, "J", True, True, []),
            ],
            roots={1},
            global_opts={OPTION_SELECT: 11, OPTION_PREV_SELECT: 1},
        )

    def test_add_events(self) -> None:
        assert self.goals.events().pop() == ("add", 1, "Root", True)
        self.goals.accept(Add("Next", self._selection()))
        assert self.goals.events()[-2] == ("add", 2, "Next", True)
        assert self.goals.events()[-1] == ("link", 1, 2, EdgeType.PARENT)

    def test_select_events(self) -> None:
        self.goals.accept_all(Add("Next", self._selection()), Select(2))
        assert self.goals.events()[-1] == ("select", 2)
        self.goals.accept_all(HoldSelect(), Select(1))
        assert self.goals.events()[-2] == ("hold_select", 2)
        assert self.goals.events()[-1] == ("select", 1)

    def test_toggle_close_events(self) -> None:
        self.goals.accept(ToggleClose(1))
        assert self.goals.events()[-3] == ("toggle_close", False, 1)
        assert self.goals.events()[-2] == ("select", 1)
        assert self.goals.events()[-1] == ("hold_select", 1)
        self.goals.accept(ToggleClose(1))
        assert self.goals.events()[-1] == ("toggle_close", True, 1)

    def test_rename_event(self) -> None:
        self.goals.accept(Rename("New", self._selection()))
        assert self.goals.events()[-1] == ("rename", "New", 1)

    def test_delete_events(self) -> None:
        self.goals.accept_all(Add("Sheep", self._selection()), Select(2), Delete(2))
        assert self.goals.events()[-3] == ("delete", 2)
        assert self.goals.events()[-2] == ("select", 1)
        assert self.goals.events()[-1] == ("hold_select", 1)

    def test_link_events(self) -> None:
        self.goals.accept_all(
            Add("Next", self._selection()),
            Add("More", self._selection()),
            Select(2),
            HoldSelect(),
            Select(3),
            ToggleLink(2, 3),
        )
        assert self.goals.events()[-1] == ("link", 2, 3, EdgeType.BLOCKER)
        self.goals.accept(ToggleLink(2, 3))
        assert self.goals.events()[-1] == ("unlink", 2, 3, EdgeType.BLOCKER)

    def test_change_link_type_events(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "Lower", blockers=[3]),
            open_(3, "Upper", []),
            select=(3, 2),
        )
        self.goals.accept(ToggleLink(2, 3, EdgeType.PARENT))
        assert list(self.goals.events())[-4:] == [
            ("link", 2, 3, EdgeType.PARENT),
            ("unlink", 2, 3, EdgeType.BLOCKER),
            ("link", 1, 3, EdgeType.RELATION),
            ("unlink", 1, 3, EdgeType.PARENT),
        ]
        self.goals.accept(ToggleLink(2, 3, EdgeType.RELATION))
        assert list(self.goals.events())[-2:] == [
            ("link", 2, 3, EdgeType.RELATION),
            ("unlink", 2, 3, EdgeType.PARENT),
        ]

    def test_no_messages_at_start(self) -> None:
        assert self.messages == []

    def test_no_message_on_good_add(self) -> None:
        self.goals = self.build(open_(1, "Root"), select=(1, 1))
        self.goals.accept(Add("Success", self._selection()))
        assert self.messages == []

    def test_message_on_wrong_add(self) -> None:
        self.goals = self.build(clos_(1, "Root"), select=(1, 1))
        self.goals.accept(Add("Failed", self._selection()))
        assert self.messages == ["A new subgoal cannot be added to the closed one"]

    def test_no_message_on_good_insert(self) -> None:
        self.goals = self.build(open_(1, "Root", [2]), open_(2, "Top"), select=(2, 1))
        self.goals.accept(Insert("Success", self._prev(), self._selection()))
        assert self.messages == []

    def test_message_on_insert_without_two_goals(self) -> None:
        self.goals = self.build(open_(1, "Root"), select=(1, 1))
        self.goals.accept(Insert("Failed", self._prev(), self._selection()))
        assert self.messages == [
            "A new goal can be inserted only between two different goals"
        ]

    def test_message_on_circular_insert(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]), open_(2, "Top", []), select=(1, 2)
        )
        self.goals.accept(Insert("Failed", self._prev(), self._selection()))
        assert self.messages == ["Circular dependencies between goals are not allowed"]

    def test_no_message_on_valid_closing(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]), open_(2, "Top", []), select=(2, 2)
        )
        self.goals.accept(ToggleClose(2))
        assert self.messages == []

    def test_message_on_closing_blocked_goal(self) -> None:
        self.goals = self.build(open_(1, "Root", [2]), open_(2, "Top"), select=(1, 1))
        self.goals.accept(ToggleClose(1))
        assert self.messages == [
            "This goal can't be closed because it have open subgoals"
        ]

    def test_no_message_on_valid_reopening(self) -> None:
        self.goals = self.build(clos_(1, "Root", [2]), clos_(2, "Top"), select=(1, 1))
        self.goals.accept(ToggleClose(1))
        assert self.messages == []

    def test_message_on_reopening_blocked_goal(self) -> None:
        self.goals = self.build(
            clos_(1, "Root", [2]), clos_(2, "Top", []), select=(2, 2)
        )
        self.goals.accept(ToggleClose(2))
        assert self.messages == [
            "This goal can't be reopened because other subgoals block it"
        ]

    def test_no_message_on_delete_non_root_goal(self) -> None:
        self.goals = self.build(
            clos_(1, "Root", [2]), clos_(2, "Top", []), select=(2, 2)
        )
        self.goals.accept(Delete(2))
        assert self.messages == []

    def test_message_on_delete_root_goal(self) -> None:
        self.goals = self.build(clos_(1, "Root", [2]), clos_(2, "Top"), select=(1, 1))
        self.goals.accept(Delete(1))
        assert self.messages == ["Root goal can't be deleted"]

    def test_no_message_on_allowed_link(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]),
            open_(2, "Middle", [3]),
            open_(3, "Top", []),
            select=(3, 1),
        )
        self.goals.accept(ToggleLink(1, 3))
        assert self.messages == []

    def test_message_on_link_to_self(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]),
            open_(2, "Middle", [3]),
            open_(3, "Top", []),
            select=(3, 3),
        )
        self.goals.accept(ToggleLink(3, 3))
        assert self.messages == ["Goal can't be linked to itself"]

    def test_no_message_when_remove_not_last_link(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "Middle", blockers=[3]),
            open_(3, "Top", []),
            select=(3, 1),
        )
        self.goals.accept(ToggleLink(1, 3))
        assert self.messages == []

    def test_message_when_remove_last_link(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2]),
            open_(2, "Middle", [3]),
            open_(3, "Top", []),
            select=(3, 2),
        )
        self.goals.accept(ToggleLink(2, 3, EdgeType.PARENT))
        assert self.messages == ["Can't remove the last link"]

    def test_message_when_closed_goal_is_blocked_by_open_one(self) -> None:
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            clos_(2, "Middle", []),
            open_(3, "Top", []),
            select=(3, 2),
        )
        self.goals.accept(ToggleLink(2, 3))
        assert self.messages == ["Cannot add a blocking relation to the closed goal"]
