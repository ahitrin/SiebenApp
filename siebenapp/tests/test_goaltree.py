# coding: utf-8
from unittest import TestCase

from siebenapp.goaltree import Goals
from siebenapp.domain import (
    EdgeType,
    HoldSelect,
    ToggleClose,
    Delete,
    ToggleLink,
    Add,
    Select,
    Insert,
    Rename,
    RenderRow,
    RenderResult,
    child,
    blocker,
)
from siebenapp.tests.dsl import build_goaltree, open_, selected, previous, clos_


class GoalsTest(TestCase):
    def setUp(self):
        self.messages = []
        self.goals = Goals("Root", self._register_message)

    def _register_message(self, msg):
        self.messages.append(msg)

    def build(self, *goal_prototypes):
        return build_goaltree(*goal_prototypes, message_fn=self._register_message)

    def test_there_is_one_goal_at_start(self):
        assert self.goals.q() == RenderResult(
            rows=[RenderRow(1, 1, "Root", True, True, "select", [])]
        )

    def test_add_goal(self):
        self.goals.accept(Add("A"))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "select", [child(2)]),
                RenderRow(2, 2, "A", True, True, None, []),
            ]
        )

    def test_add_two_goals(self):
        self.goals.accept_all(Add("A"), Add("B"))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "select", [child(2), child(3)]),
                RenderRow(2, 2, "A", True, True, None, []),
                RenderRow(3, 3, "B", True, True, None, []),
            ]
        )

    def test_add_two_goals_in_a_chain(self):
        self.goals.accept_all(Add("A"), Add("AA", 2))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "select", [child(2)]),
                RenderRow(2, 2, "A", True, False, None, [child(3)]),
                RenderRow(3, 3, "AA", True, True, None, []),
            ]
        )

    def test_rename_goal(self):
        self.goals.accept_all(Add("Boom"), Select(2), Rename("A"))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "prev", [child(2)]),
                RenderRow(2, 2, "A", True, True, "select", []),
            ]
        )

    def test_insert_goal_in_the_middle(self):
        self.goals.accept_all(Add("B"), HoldSelect(), Select(2))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "prev", [child(2)]),
                RenderRow(2, 2, "B", True, True, "select", []),
            ]
        )
        self.goals.accept(Insert("A"))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "prev", [child(3)]),
                RenderRow(2, 2, "B", True, True, "select", []),
                RenderRow(3, 3, "A", True, False, None, [child(2)]),
            ]
        )

    def test_insert_goal_between_independent_goals(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", select=previous),
            open_(3, "B", select=selected),
        )
        self.goals.accept(Insert("Wow"))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, None, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, False, "prev", [blocker(4)]),
                RenderRow(3, 3, "B", True, True, "select", []),
                RenderRow(4, 4, "Wow", True, False, None, [blocker(3)]),
            ]
        )

    def test_reverse_insertion(self):
        """Not sure whether such trick should be legal"""
        self.goals = self.build(
            open_(1, "Root", [2], select=selected),
            open_(2, "Selected", select=previous),
        )
        self.goals.accept(Insert("Intermediate?"))
        # No, it's not intermediate
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "select", [child(2)]),
                RenderRow(2, 2, "Selected", True, False, "prev", [blocker(3)]),
                RenderRow(3, 3, "Intermediate?", True, True, None, []),
            ]
        )

    def test_close_single_goal(self):
        assert self.goals.q() == RenderResult(
            rows=[RenderRow(1, 1, "Root", True, True, "select", [])]
        )
        self.goals.accept(ToggleClose())
        assert self.goals.q() == RenderResult(
            rows=[RenderRow(1, 1, "Root", False, True, "select", [])]
        )

    def test_reopen_goal(self):
        self.goals = self.build(open_(1, "Root", [2]), clos_(2, "A", select=selected))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, True, None, [child(2)]),
                RenderRow(2, 2, "A", False, True, "select", []),
            ]
        )
        self.goals.accept(ToggleClose())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, None, [child(2)]),
                RenderRow(2, 2, "A", True, True, "select", []),
            ]
        )

    def test_close_goal_again(self):
        self.goals = self.build(
            open_(1, "Root", [2], select=selected),
            open_(2, "A", [3]),
            clos_(3, "Ab"),
        )
        self.goals.accept_all(Select(2), ToggleClose())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, True, "select", [child(2)]),
                RenderRow(2, 2, "A", False, True, None, [child(3)]),
                RenderRow(3, 3, "Ab", False, False, None, []),
            ]
        )
        self.goals.accept_all(Select(2), ToggleClose())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "prev", [child(2)]),
                RenderRow(2, 2, "A", True, True, "select", [child(3)]),
                RenderRow(3, 3, "Ab", False, True, None, []),
            ]
        )
        self.goals.accept_all(Select(2), ToggleClose())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, True, "select", [child(2)]),
                RenderRow(2, 2, "A", False, True, None, [child(3)]),
                RenderRow(3, 3, "Ab", False, False, None, []),
            ]
        )

    def test_closed_leaf_goal_could_not_be_reopened(self):
        self.goals = self.build(
            open_(1, "Root", [2], select=selected), clos_(2, "A", [3]), clos_(3, "B")
        )
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, True, "select", [child(2)]),
                RenderRow(2, 2, "A", False, True, None, [child(3)]),
                RenderRow(3, 3, "B", False, False, None, []),
            ]
        )
        self.goals.accept_all(Select(3), ToggleClose())
        # nothing should change except select
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, True, "prev", [child(2)]),
                RenderRow(2, 2, "A", False, True, None, [child(3)]),
                RenderRow(3, 3, "B", False, False, "select", []),
            ]
        )

    def test_goal_in_the_middle_could_not_be_closed(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", blockers=[4]),
            open_(3, "B", [4], select=selected),
            open_(4, "C"),
        )
        self.goals.accept(ToggleClose())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, None, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, False, None, [blocker(4)]),
                RenderRow(3, 3, "B", True, False, "select", [child(4)]),
                RenderRow(4, 4, "C", True, True, None, []),
            ]
        )

    def test_delete_single_goal(self):
        self.goals = self.build(open_(1, "Root", [2]), open_(2, "A", select=selected))
        self.goals.accept(Delete())
        assert self.goals.q() == RenderResult(
            rows=[RenderRow(1, 1, "Root", True, True, "select", [])]
        )

    def test_enumeration_should_not_be_changed_after_delete(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]), open_(2, "A", select=selected), open_(3, "B")
        )
        self.goals.accept(Delete())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "select", [child(3)]),
                RenderRow(3, 3, "B", True, True, None, []),
            ]
        )

    def test_remove_goal_chain_with_children(self):
        self.goals = self.build(
            open_(1, "Root", [2]), open_(2, "A", [3], select=selected), open_(3, "B")
        )
        self.goals.accept(Delete())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, True, "select", []),
            ]
        )

    def test_relink_goal_chain_with_blockers(self):
        self.goals = self.build(
            open_(1, "Root", [2]),
            open_(2, "A", blockers=[3], select=selected),
            open_(3, "B"),
        )
        self.goals.accept(Delete())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "select", [blocker(3)]),
                RenderRow(3, 3, "B", True, True, None, []),
            ]
        )

    def test_select_parent_after_delete(self):
        self.goals = self.build(
            open_(1, "Root", [2], select=previous),
            open_(2, "Parent", [3]),
            open_(3, "Delete me", select=selected),
        )
        self.goals.accept(Delete())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, None, [child(2)]),
                RenderRow(2, 2, "Parent", True, True, "select", []),
            ]
        )

    def test_add_link_between_goals(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", select=previous),
            open_(3, "B", select=selected),
        )
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, None, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, True, "prev", []),
                RenderRow(3, 3, "B", True, True, "select", []),
            ]
        )
        self.goals.accept(ToggleLink())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, None, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, False, "prev", [blocker(3)]),
                RenderRow(3, 3, "B", True, True, "select", []),
            ]
        )

    def test_no_link_to_self_is_allowed(self):
        self.goals.accept(ToggleLink())
        assert self.goals.q() == RenderResult(
            rows=[RenderRow(1, 1, "Root", True, True, "select", [])]
        )

    def test_no_loops_allowed(self):
        self.goals = self.build(
            open_(1, "Root", [2], select=selected),
            open_(2, "step", [3]),
            open_(3, "next", [4]),
            open_(4, "more", select=previous),
        )
        self.goals.accept(ToggleLink())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "select", [child(2)]),
                RenderRow(2, 2, "step", True, False, None, [child(3)]),
                RenderRow(3, 3, "next", True, False, None, [child(4)]),
                RenderRow(4, 4, "more", True, True, "prev", []),
            ]
        )

    def test_new_parent_link_replaces_old_one(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "Old parent", [4]),
            open_(3, "New parent", select=previous),
            open_(4, "Child", select=selected),
        )
        self.goals.accept(ToggleLink(edge_type=EdgeType.PARENT))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, None, [child(2), child(3)]),
                RenderRow(2, 2, "Old parent", True, False, None, [blocker(4)]),
                RenderRow(3, 3, "New parent", True, False, "prev", [child(4)]),
                RenderRow(4, 4, "Child", True, True, "select", []),
            ]
        )

    def test_new_parent_link_replaces_old_one_when_changed_from_blocker(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", select=selected),
            open_(3, "B", blockers=[2], select=previous),
        )
        self.goals.accept(ToggleLink(edge_type=EdgeType.PARENT))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, None, [blocker(2), child(3)]),
                RenderRow(2, 2, "A", True, True, "select", []),
                RenderRow(3, 3, "B", True, False, "prev", [child(2)]),
            ]
        )

    def test_remove_link_between_goals(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", blockers=[3], select=previous),
            open_(3, "B", select=selected),
        )
        self.goals.accept(ToggleLink(edge_type=EdgeType.BLOCKER))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, None, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, True, "prev", []),
                RenderRow(3, 3, "B", True, True, "select", []),
            ]
        )

    def test_change_link_type(self):
        self.goals = self.build(
            open_(1, "Root", [2], select=previous), open_(2, "Top", [], select=selected)
        )
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "prev", [child(2)]),
                RenderRow(2, 2, "Top", True, True, "select", []),
            ]
        )
        self.goals.accept(ToggleLink())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "prev", [blocker(2)]),
                RenderRow(2, 2, "Top", True, True, "select", []),
            ]
        )
        self.goals.accept(ToggleLink(edge_type=EdgeType.PARENT))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "prev", [child(2)]),
                RenderRow(2, 2, "Top", True, True, "select", []),
            ]
        )

    def test_remove_blocked_goal_without_children(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", [4]),
            open_(3, "B", blockers=[4]),
            open_(4, "C", select=selected),
        )
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, None, [child(2), child(3)]),
                RenderRow(2, 2, "A", True, False, None, [child(4)]),
                RenderRow(3, 3, "B", True, False, None, [blocker(4)]),
                RenderRow(4, 4, "C", True, True, "select", []),
            ]
        )
        self.goals.accept_all(Select(3), Delete())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "select", [child(2)]),
                RenderRow(2, 2, "A", True, False, None, [child(4)]),
                RenderRow(4, 4, "C", True, True, None, []),
            ]
        )

    def test_root_goal_is_selected_by_default(self):
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, True, "select", []),
            ]
        )
        self.goals.accept(Add("A"))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "select", [child(2)]),
                RenderRow(2, 2, "A", True, True, None, []),
            ]
        )
        self.goals.accept(Add("B"))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "select", [child(2), child(3)]),
                RenderRow(2, 2, "A", True, True, None, []),
                RenderRow(3, 3, "B", True, True, None, []),
            ]
        )

    def test_new_goal_is_added_to_the_selected_node(self):
        self.goals.accept_all(Add("A"), Select(2))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "prev", [child(2)]),
                RenderRow(2, 2, "A", True, True, "select", []),
            ]
        )
        self.goals.accept(Add("B"))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, "prev", [child(2)]),
                RenderRow(2, 2, "A", True, False, "select", [child(3)]),
                RenderRow(3, 3, "B", True, True, None, []),
            ]
        )

    def test_move_selection_to_another_open_goal_after_closing(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3, 4]),
            open_(2, "A", select=selected),
            open_(3, "B"),
            open_(4, "C"),
        )
        self.goals.accept(ToggleClose())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(
                    1, 1, "Root", True, False, None, [child(2), child(3), child(4)]
                ),
                RenderRow(2, 2, "A", False, True, None, []),
                RenderRow(3, 3, "B", True, True, "select", []),
                RenderRow(4, 4, "C", True, True, None, []),
            ]
        )

    def test_move_selection_to_previously_selected_goal_after_closing(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3, 4]),
            open_(2, "A", select=selected),
            open_(3, "B"),
            open_(4, "C", select=previous),
        )
        self.goals.accept(ToggleClose())
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(
                    1, 1, "Root", True, False, None, [child(2), child(3), child(4)]
                ),
                RenderRow(2, 2, "A", False, True, None, []),
                RenderRow(3, 3, "B", True, True, None, []),
                RenderRow(4, 4, "C", True, True, "select", []),
            ]
        )

    def test_move_selection_to_another_open_goal_with_given_root_after_closing(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "Should not be selected"),
            open_(3, "Subroot", [4, 5]),
            open_(4, "Must be selected"),
            open_(5, "Closing", select=selected),
        )
        self.goals.accept(ToggleClose(3))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, None, [child(2), child(3)]),
                RenderRow(2, 2, "Should not be selected", True, True, None, []),
                RenderRow(3, 3, "Subroot", True, False, None, [child(4), child(5)]),
                RenderRow(4, 4, "Must be selected", True, True, "select", []),
                RenderRow(5, 5, "Closing", False, True, None, []),
            ]
        )

    def test_do_not_select_unswitchable_goal_after_closing(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "Should not be selected"),
            open_(3, "Subroot", [4, 5]),
            open_(4, "Intermediate", [6]),
            open_(5, "Closing", select=selected),
            open_(6, "Must be selected"),
        )
        self.goals.accept(ToggleClose(3))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, False, None, [child(2), child(3)]),
                RenderRow(2, 2, "Should not be selected", True, True, None, []),
                RenderRow(3, 3, "Subroot", True, False, None, [child(4), child(5)]),
                RenderRow(4, 4, "Intermediate", True, False, None, [child(6)]),
                RenderRow(5, 5, "Closing", False, True, None, []),
                RenderRow(6, 6, "Must be selected", True, True, "select", []),
            ]
        )

    def test_ignore_wrong_selection(self):
        self.goals.accept(Select(2))
        assert self.goals.q() == RenderResult(
            rows=[RenderRow(1, 1, "Root", True, True, "select", [])]
        )

    def test_do_not_select_deleted_goals(self):
        self.goals = self.build(
            open_(1, "Root", [2]), open_(2, "broken", select=selected)
        )
        self.goals.accept_all(Delete(), Select(2))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(1, 1, "Root", True, True, "select", []),
            ]
        )

    def test_selection_should_be_instant(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3, 4, 5, 6, 7, 8, 9, 10, 11], select=selected),
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
        )
        self.goals.accept(Select(2))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(
                    1,
                    1,
                    "Root",
                    True,
                    False,
                    "prev",
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
                RenderRow(2, 2, "A", True, True, "select", []),
                RenderRow(3, 3, "B", True, True, None, []),
                RenderRow(4, 4, "C", True, True, None, []),
                RenderRow(5, 5, "D", True, True, None, []),
                RenderRow(6, 6, "E", True, True, None, []),
                RenderRow(7, 7, "F", True, True, None, []),
                RenderRow(8, 8, "G", True, True, None, []),
                RenderRow(9, 9, "H", True, True, None, []),
                RenderRow(10, 10, "I", True, True, None, []),
                RenderRow(11, 11, "J", True, True, None, []),
            ]
        )
        self.goals.accept(Select(11))
        assert self.goals.q() == RenderResult(
            rows=[
                RenderRow(
                    1,
                    1,
                    "Root",
                    True,
                    False,
                    "prev",
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
                RenderRow(2, 2, "A", True, True, None, []),
                RenderRow(3, 3, "B", True, True, None, []),
                RenderRow(4, 4, "C", True, True, None, []),
                RenderRow(5, 5, "D", True, True, None, []),
                RenderRow(6, 6, "E", True, True, None, []),
                RenderRow(7, 7, "F", True, True, None, []),
                RenderRow(8, 8, "G", True, True, None, []),
                RenderRow(9, 9, "H", True, True, None, []),
                RenderRow(10, 10, "I", True, True, None, []),
                RenderRow(11, 11, "J", True, True, "select", []),
            ]
        )

    def test_add_events(self):
        assert self.goals.events().pop() == ("add", 1, "Root", True)
        self.goals.accept(Add("Next"))
        assert self.goals.events()[-2] == ("add", 2, "Next", True)
        assert self.goals.events()[-1] == ("link", 1, 2, EdgeType.PARENT)

    def test_select_events(self):
        self.goals.accept_all(Add("Next"), Select(2))
        assert self.goals.events()[-1] == ("select", 2)
        self.goals.accept_all(HoldSelect(), Select(1))
        assert self.goals.events()[-2] == ("hold_select", 2)
        assert self.goals.events()[-1] == ("select", 1)

    def test_toggle_close_events(self):
        self.goals.accept(ToggleClose())
        assert self.goals.events()[-3] == ("toggle_close", False, 1)
        assert self.goals.events()[-2] == ("select", 1)
        assert self.goals.events()[-1] == ("hold_select", 1)
        self.goals.accept(ToggleClose())
        assert self.goals.events()[-1] == ("toggle_close", True, 1)

    def test_rename_event(self):
        self.goals.accept(Rename("New"))
        assert self.goals.events()[-1] == ("rename", "New", 1)

    def test_delete_events(self):
        self.goals.accept_all(Add("Sheep"), Select(2), Delete())
        assert self.goals.events()[-3] == ("delete", 2)
        assert self.goals.events()[-2] == ("select", 1)
        assert self.goals.events()[-1] == ("hold_select", 1)

    def test_link_events(self):
        self.goals.accept_all(
            Add("Next"), Add("More"), Select(2), HoldSelect(), Select(3), ToggleLink()
        )
        assert self.goals.events()[-1] == ("link", 2, 3, EdgeType.BLOCKER)
        self.goals.accept(ToggleLink())
        assert self.goals.events()[-1] == ("unlink", 2, 3, EdgeType.BLOCKER)

    def test_change_link_type_events(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "Lower", blockers=[3], select=previous),
            open_(3, "Upper", [], select=selected),
        )
        self.goals.accept(ToggleLink(edge_type=EdgeType.PARENT))
        assert self.goals.events()[-4] == ("link", 2, 3, EdgeType.PARENT)
        assert self.goals.events()[-3] == ("unlink", 2, 3, EdgeType.BLOCKER)
        assert self.goals.events()[-2] == ("link", 1, 3, EdgeType.BLOCKER)
        assert self.goals.events()[-1] == ("unlink", 1, 3, EdgeType.PARENT)

    def test_no_messages_at_start(self):
        assert self.messages == []

    def test_no_message_on_good_add(self):
        self.goals = self.build(open_(1, "Root", select=selected))
        self.goals.accept(Add("Success"))
        assert self.messages == []

    def test_message_on_wrong_add(self):
        self.goals = self.build(clos_(1, "Root", select=selected))
        self.goals.accept(Add("Failed"))
        assert len(self.messages) == 1

    def test_no_message_on_good_insert(self):
        self.goals = self.build(
            open_(1, "Root", [2], select=previous), open_(2, "Top", select=selected)
        )
        self.goals.accept(Insert("Success"))
        assert self.messages == []

    def test_message_on_insert_without_two_goals(self):
        self.goals = self.build(open_(1, "Root", select=selected))
        self.goals.accept(Insert("Failed"))
        assert len(self.messages) == 1

    def test_message_on_circular_insert(self):
        self.goals = self.build(
            open_(1, "Root", [2], select=selected), open_(2, "Top", [], select=previous)
        )
        self.goals.accept(Insert("Failed"))
        assert len(self.messages) == 1

    def test_no_message_on_valid_closing(self):
        self.goals = self.build(
            open_(1, "Root", [2]), open_(2, "Top", [], select=selected)
        )
        self.goals.accept(ToggleClose())
        assert self.messages == []

    def test_message_on_closing_blocked_goal(self):
        self.goals = self.build(open_(1, "Root", [2], select=selected), open_(2, "Top"))
        self.goals.accept(ToggleClose())
        assert len(self.messages) == 1

    def test_no_message_on_valid_reopening(self):
        self.goals = self.build(clos_(1, "Root", [2], select=selected), clos_(2, "Top"))
        self.goals.accept(ToggleClose())
        assert self.messages == []

    def test_message_on_reopening_blocked_goal(self):
        self.goals = self.build(
            clos_(1, "Root", [2]), clos_(2, "Top", [], select=selected)
        )
        self.goals.accept(ToggleClose())
        assert len(self.messages) == 1

    def test_no_message_on_delete_non_root_goal(self):
        self.goals = self.build(
            clos_(1, "Root", [2]), clos_(2, "Top", [], select=selected)
        )
        self.goals.accept(Delete())
        assert self.messages == []

    def test_message_on_delete_root_goal(self):
        self.goals = self.build(clos_(1, "Root", [2], select=selected), clos_(2, "Top"))
        self.goals.accept(Delete())
        assert len(self.messages) == 1

    def test_no_message_on_allowed_link(self):
        self.goals = self.build(
            open_(1, "Root", [2], select=previous),
            open_(2, "Middle", [3]),
            open_(3, "Top", [], select=selected),
        )
        self.goals.accept(ToggleLink())
        assert self.messages == []

    def test_message_on_link_to_self(self):
        self.goals = self.build(
            open_(1, "Root", [2]),
            open_(2, "Middle", [3]),
            open_(3, "Top", [], select=selected),
        )
        self.goals.accept(ToggleLink())
        assert len(self.messages) == 1

    def test_no_message_when_remove_not_last_link(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3], select=previous),
            open_(2, "Middle", blockers=[3]),
            open_(3, "Top", [], select=selected),
        )
        self.goals.accept(ToggleLink())
        assert self.messages == []

    def test_message_when_remove_last_link(self):
        self.goals = self.build(
            open_(1, "Root", [2]),
            open_(2, "Middle", [3], select=previous),
            open_(3, "Top", [], select=selected),
        )
        self.goals.accept(ToggleLink(edge_type=EdgeType.PARENT))
        assert len(self.messages) == 1

    def test_message_when_closed_goal_is_blocked_by_open_one(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            clos_(2, "Middle", [], select=previous),
            open_(3, "Top", [], select=selected),
        )
        self.goals.accept(ToggleLink())
        assert len(self.messages) == 1
