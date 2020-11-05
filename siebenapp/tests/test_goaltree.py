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
        assert self.goals.q(keys="name,switchable") == {
            1: {"name": "Root", "switchable": True}
        }

    def test_new_goal_moves_to_top(self):
        self.goals.accept(Add("A"))
        assert self.goals.q(keys="name,switchable") == {
            1: {"name": "Root", "switchable": False},
            2: {"name": "A", "switchable": True},
        }

    def test_added_goal_has_strong_link_with_parent(self):
        self.goals.accept(Add("New"))
        assert self.goals.q(keys="name,edge") == {
            1: {"name": "Root", "edge": [(2, EdgeType.PARENT)]},
            2: {"name": "New", "edge": []},
        }

    def test_two_new_goals_move_to_top(self):
        self.goals.accept_all(Add("A"), Add("B"))
        assert self.goals.q(keys="name,switchable") == {
            1: {"name": "Root", "switchable": False},
            2: {"name": "A", "switchable": True},
            3: {"name": "B", "switchable": True},
        }

    def test_two_goals_in_a_chain(self):
        self.goals.accept_all(Add("A"), Add("AA", 2))
        assert self.goals.q(keys="name,switchable") == {
            1: {"name": "Root", "switchable": False},
            2: {"name": "A", "switchable": False},
            3: {"name": "AA", "switchable": True},
        }

    def test_rename_goal(self):
        self.goals.accept_all(Add("Boom"), Select(2), Rename("A"))
        assert self.goals.q() == {1: {"name": "Root"}, 2: {"name": "A"}}

    def test_insert_goal_in_the_middle(self):
        self.goals.accept_all(Add("B"), HoldSelect(), Select(2))
        assert self.goals.q(keys="name,edge,switchable") == {
            1: {"name": "Root", "edge": [(2, EdgeType.PARENT)], "switchable": False},
            2: {"name": "B", "edge": [], "switchable": True},
        }
        self.goals.accept(Insert("A"))
        assert self.goals.q(keys="name,edge,switchable") == {
            1: {"name": "Root", "edge": [(3, EdgeType.PARENT)], "switchable": False},
            2: {"name": "B", "edge": [], "switchable": True},
            3: {"name": "A", "edge": [(2, EdgeType.PARENT)], "switchable": False},
        }

    def test_insert_goal_between_independent_goals(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", select=previous),
            open_(3, "B", select=selected),
        )
        self.goals.accept(Insert("Wow"))
        assert self.goals.q(keys="name,edge,switchable") == {
            1: {
                "name": "Root",
                "edge": [(2, EdgeType.PARENT), (3, EdgeType.PARENT)],
                "switchable": False,
            },
            2: {"name": "A", "edge": [(4, EdgeType.BLOCKER)], "switchable": False},
            3: {"name": "B", "edge": [], "switchable": True},
            4: {"name": "Wow", "edge": [(3, EdgeType.BLOCKER)], "switchable": False},
        }

    def test_reverse_insertion(self):
        """Not sure whether such trick should be legal"""
        self.goals = self.build(
            open_(1, "Root", [2], select=selected),
            open_(2, "Selected", select=previous)
        )
        self.goals.accept(Insert("Intermediate?"))
        # No, it's not intermediate
        assert self.goals.q("name,edge") == {
            1: {"name": "Root", "edge": [(2, EdgeType.PARENT)]},
            2: {"name": "Selected", "edge": [(3, EdgeType.BLOCKER)]},
            3: {"name": "Intermediate?", "edge": []},
        }

    def test_close_single_goal(self):
        assert self.goals.q(keys="name,open") == {1: {"name": "Root", "open": True}}
        self.goals.accept(ToggleClose())
        assert self.goals.q(keys="name,open,switchable") == {
            1: {"name": "Root", "open": False, "switchable": True}
        }

    def test_reopen_goal(self):
        self.goals = self.build(open_(1, "Root", [2]), clos_(2, "A", select=selected))
        assert self.goals.q(keys="open") == {1: {"open": True}, 2: {"open": False}}
        self.goals.accept(ToggleClose())
        assert self.goals.q(keys="open,switchable") == {
            1: {"open": True, "switchable": False},
            2: {"open": True, "switchable": True},
        }

    def test_close_goal_again(self):
        self.goals = self.build(
            open_(1, "Root", [2], select=selected), open_(2, "A", [3]), clos_(3, "Ab"),
        )
        self.goals.accept_all(Select(2), ToggleClose())
        assert self.goals.q(keys="open,switchable") == {
            1: {"open": True, "switchable": True},
            2: {"open": False, "switchable": True},
            3: {"open": False, "switchable": False},
        }
        self.goals.accept_all(Select(2), ToggleClose())
        assert self.goals.q(keys="open,switchable") == {
            1: {"open": True, "switchable": False},
            2: {"open": True, "switchable": True},
            3: {"open": False, "switchable": True},
        }
        self.goals.accept_all(Select(2), ToggleClose())
        assert self.goals.q(keys="open,switchable") == {
            1: {"open": True, "switchable": True},
            2: {"open": False, "switchable": True},
            3: {"open": False, "switchable": False},
        }

    def test_closed_leaf_goal_could_not_be_reopened(self):
        self.goals = self.build(
            open_(1, "Root", [2], select=selected), clos_(2, "A", [3]), clos_(3, "B")
        )
        assert self.goals.q(keys="open,switchable") == {
            1: {"open": True, "switchable": True},
            2: {"open": False, "switchable": True},
            3: {"open": False, "switchable": False},
        }
        self.goals.accept_all(Select(3), ToggleClose())
        # nothing should change
        assert self.goals.q(keys="open,switchable") == {
            1: {"open": True, "switchable": True},
            2: {"open": False, "switchable": True},
            3: {"open": False, "switchable": False},
        }

    def test_goal_in_the_middle_could_not_be_closed(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", blockers=[4]),
            open_(3, "B", [4], select=selected),
            open_(4, "C"),
        )
        self.goals.accept(ToggleClose())
        assert self.goals.q(keys="open") == {
            1: {"open": True},
            2: {"open": True},
            3: {"open": True},
            4: {"open": True},
        }

    def test_delete_single_goal(self):
        self.goals = self.build(open_(1, "Root", [2]), open_(2, "A", select=selected))
        self.goals.accept(Delete())
        assert self.goals.q(keys="name,select,switchable") == {
            1: {"name": "Root", "select": "select", "switchable": True},
        }

    def test_enumeration_should_not_be_changed_after_delete(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]), open_(2, "A", select=selected), open_(3, "B")
        )
        self.goals.accept(Delete())
        assert self.goals.q(keys="name,switchable") == {
            1: {"name": "Root", "switchable": False},
            3: {"name": "B", "switchable": True},
        }

    def test_remove_goal_chain_with_children(self):
        self.goals = self.build(
            open_(1, "Root", [2]), open_(2, "A", [3], select=selected), open_(3, "B")
        )
        self.goals.accept(Delete())
        assert self.goals.q() == {1: {"name": "Root"}}

    def test_relink_goal_chain_with_blockers(self):
        self.goals = self.build(
            open_(1, "Root", [2]),
            open_(2, "A", blockers=[3], select=selected),
            open_(3, "B"),
        )
        self.goals.accept(Delete())
        assert self.goals.q("name,edge") == {
            1: {"name": "Root", "edge": [(3, EdgeType.BLOCKER)]},
            3: {"name": "B", "edge": []},
        }

    def test_select_parent_after_delete(self):
        self.goals = self.build(
            open_(1, "Root", [2], select=previous),
            open_(2, "Parent", [3]),
            open_(3, "Delete me", select=selected),
        )
        self.goals.accept(Delete())
        assert self.goals.q("name,edge,select") == {
            1: {"name": "Root", "edge": [(2, EdgeType.PARENT)], "select": None},
            2: {"name": "Parent", "edge": [], "select": "select"},
        }

    def test_add_link_between_goals(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", select=previous),
            open_(3, "B", select=selected),
        )
        assert self.goals.q(keys="switchable,edge") == {
            1: {
                "switchable": False,
                "edge": [(2, EdgeType.PARENT), (3, EdgeType.PARENT)],
            },
            2: {"switchable": True, "edge": []},
            3: {"switchable": True, "edge": []},
        }
        self.goals.accept(ToggleLink())
        assert self.goals.q(keys="switchable,edge") == {
            1: {
                "switchable": False,
                "edge": [(2, EdgeType.PARENT), (3, EdgeType.PARENT)],
            },
            2: {"switchable": False, "edge": [(3, EdgeType.BLOCKER)]},
            3: {"switchable": True, "edge": []},
        }

    def test_view_edges(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", [4]),
            open_(3, "B", blockers=[4], select=previous),
            open_(4, "C", select=selected),
        )
        assert self.goals.q(keys="edge,switchable") == {
            1: {
                "edge": [(2, EdgeType.PARENT), (3, EdgeType.PARENT)],
                "switchable": False,
            },
            2: {"edge": [(4, EdgeType.PARENT)], "switchable": False},
            3: {"edge": [(4, EdgeType.BLOCKER)], "switchable": False},
            4: {"edge": [], "switchable": True},
        }

    def test_no_link_to_self_is_allowed(self):
        self.goals.accept(ToggleLink())
        assert self.goals.q(keys="edge") == {1: {"edge": []}}

    def test_no_loops_allowed(self):
        self.goals = self.build(
            open_(1, "Root", [2], select=selected),
            open_(2, "step", [3]),
            open_(3, "next", [4]),
            open_(4, "more", select=previous),
        )
        self.goals.accept(ToggleLink())
        assert self.goals.q(keys="edge") == {
            1: {"edge": [(2, EdgeType.PARENT)]},
            2: {"edge": [(3, EdgeType.PARENT)]},
            3: {"edge": [(4, EdgeType.PARENT)]},
            4: {"edge": []},
        }

    def test_new_parent_link_replaces_old_one(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "Old parent", [4]),
            open_(3, "New parent", select=previous),
            open_(4, "Child", select=selected),
        )
        self.goals.accept(ToggleLink(edge_type=EdgeType.PARENT))
        assert self.goals.q(keys="edge") == {
            1: {"edge": [(2, EdgeType.PARENT), (3, EdgeType.PARENT)]},
            2: {"edge": [(4, EdgeType.BLOCKER)]},
            3: {"edge": [(4, EdgeType.PARENT)]},
            4: {"edge": []},
        }

    def test_new_parent_link_replaces_old_one_when_changed_from_blocker(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", select=selected),
            open_(3, "B", blockers=[2], select=previous),
        )
        self.goals.accept(ToggleLink(edge_type=EdgeType.PARENT))
        assert self.goals.q("name,edge") == {
            1: {"name": "Root", "edge": [(2, EdgeType.BLOCKER), (3, EdgeType.PARENT)]},
            2: {"name": "A", "edge": []},
            3: {"name": "B", "edge": [(2, EdgeType.PARENT)]},
        }

    def test_remove_link_between_goals(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", blockers=[3], select=previous),
            open_(3, "B", select=selected),
        )
        self.goals.accept(ToggleLink(edge_type=EdgeType.BLOCKER))
        assert self.goals.q(keys="edge,switchable") == {
            1: {
                "edge": [(2, EdgeType.PARENT), (3, EdgeType.PARENT)],
                "switchable": False,
            },
            2: {"edge": [], "switchable": True},
            3: {"edge": [], "switchable": True},
        }

    def test_change_link_type(self):
        self.goals = self.build(
            open_(1, "Root", [2], select=previous), open_(2, "Top", [], select=selected)
        )
        assert self.goals.q(keys="name,edge") == {
            1: {"name": "Root", "edge": [(2, EdgeType.PARENT)]},
            2: {"name": "Top", "edge": []},
        }
        self.goals.accept(ToggleLink())
        assert self.goals.q(keys="name,edge") == {
            1: {"name": "Root", "edge": [(2, EdgeType.BLOCKER)]},
            2: {"name": "Top", "edge": []},
        }
        self.goals.accept(ToggleLink(edge_type=EdgeType.PARENT))
        assert self.goals.q(keys="name,edge") == {
            1: {"name": "Root", "edge": [(2, EdgeType.PARENT)]},
            2: {"name": "Top", "edge": []},
        }

    def test_remove_blocked_goal_without_children(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]),
            open_(2, "A", [4]),
            open_(3, "B", blockers=[4]),
            open_(4, "C", select=selected),
        )
        assert self.goals.q(keys="name,edge") == {
            1: {"name": "Root", "edge": [(2, EdgeType.PARENT), (3, EdgeType.PARENT)]},
            2: {"name": "A", "edge": [(4, EdgeType.PARENT)]},
            3: {"name": "B", "edge": [(4, EdgeType.BLOCKER)]},
            4: {"name": "C", "edge": []},
        }
        self.goals.accept_all(Select(3), Delete())
        assert self.goals.q(keys="name,edge,switchable") == {
            1: {"name": "Root", "edge": [(2, EdgeType.PARENT)], "switchable": False},
            2: {"name": "A", "edge": [(4, EdgeType.PARENT)], "switchable": False},
            4: {"name": "C", "edge": [], "switchable": True},
        }

    def test_root_goal_is_selected_by_default(self):
        assert self.goals.q(keys="select") == {1: {"select": "select"}}
        self.goals.accept(Add("A"))
        assert self.goals.q(keys="select") == {
            1: {"select": "select"},
            2: {"select": None},
        }
        self.goals.accept(Add("B"))
        assert self.goals.q(keys="select") == {
            1: {"select": "select"},
            2: {"select": None},
            3: {"select": None},
        }

    def test_new_goal_is_added_to_the_selected_node(self):
        self.goals.accept_all(Add("A"), Select(2))
        assert self.goals.q(keys="name,select") == {
            1: {"name": "Root", "select": "prev"},
            2: {"name": "A", "select": "select"},
        }
        self.goals.accept(Add("B"))
        assert self.goals.q(keys="name,select,edge") == {
            1: {"name": "Root", "select": "prev", "edge": [(2, EdgeType.PARENT)]},
            2: {"name": "A", "select": "select", "edge": [(3, EdgeType.PARENT)]},
            3: {"name": "B", "select": None, "edge": []},
        }

    def test_move_selection_to_the_root_after_closing(self):
        self.goals = self.build(
            open_(1, "Root", [2, 3]), open_(2, "A", select=selected), open_(3, "B")
        )
        self.goals.accept(ToggleClose())
        assert self.goals.q(keys="open,select") == {
            1: {"open": True, "select": "select"},
            2: {"open": False, "select": None},
            3: {"open": True, "select": None},
        }

    def test_ignore_wrong_selection(self):
        self.goals.accept(Select(2))
        assert self.goals.q(keys="select") == {1: {"select": "select"}}

    def test_do_not_select_deleted_goals(self):
        self.goals = self.build(
            open_(1, "Root", [2]), open_(2, "broken", select=selected)
        )
        self.goals.accept_all(Delete(), Select(2))
        assert self.goals.q(keys="select") == {1: {"select": "select"}}

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
        assert self.goals.q(keys="select") == {
            1: {"select": "prev"},
            2: {"select": "select"},
            3: {"select": None},
            4: {"select": None},
            5: {"select": None},
            6: {"select": None},
            7: {"select": None},
            8: {"select": None},
            9: {"select": None},
            10: {"select": None},
            11: {"select": None},
        }
        self.goals.accept(Select(11))
        assert self.goals.q(keys="select") == {
            1: {"select": "prev"},
            2: {"select": None},
            3: {"select": None},
            4: {"select": None},
            5: {"select": None},
            6: {"select": None},
            7: {"select": None},
            8: {"select": None},
            9: {"select": None},
            10: {"select": None},
            11: {"select": "select"},
        }

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
