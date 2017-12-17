# coding: utf-8
from unittest import TestCase

from siebenapp.goaltree import Goals
from siebenapp.tests.dsl import build_goaltree, open_, selected


class GoalsTest(TestCase):
    def setUp(self):
        self.goals = Goals('Root')

    def test_there_is_one_goal_at_start(self):
        assert self.goals.all(keys='name,switchable') == {
            1: {'name': 'Root', 'switchable': True}
        }

    def test_new_goal_moves_to_top(self):
        self.goals.add('A')
        assert self.goals.all(keys='name,switchable') == {
            1: {'name': 'Root', 'switchable': False},
            2: {'name': 'A', 'switchable': True}}

    def test_two_new_goals_move_to_top(self):
        self.goals.add('A')
        self.goals.add('B')
        assert self.goals.all(keys='name,switchable') == {
            1: {'name': 'Root', 'switchable': False},
            2: {'name': 'A', 'switchable': True},
            3: {'name': 'B', 'switchable': True}}

    def test_two_goals_in_a_chain(self):
        self.goals.add('A')
        self.goals.add('AA', 2)
        assert self.goals.all(keys='name,switchable') == {
            1: {'name': 'Root', 'switchable': False},
            2: {'name': 'A', 'switchable': False},
            3: {'name': 'AA', 'switchable': True}}

    def test_rename_goal(self):
        self.goals.add('Boom')
        self.goals.select(2)
        self.goals.rename('A')
        assert self.goals.all() == {1: {'name': 'Root'}, 2: {'name': 'A'}}

    def test_swap_goals(self):
        self.goals.add('Wroom')
        self.goals.hold_select()
        self.goals.select(2)
        self.goals.swap_goals()
        assert self.goals.all() == {1: {'name': 'Wroom'}, 2: {'name': 'Root'}}

    def test_insert_goal_in_the_middle(self):
        self.goals.add('B')
        self.goals.hold_select()
        self.goals.select(2)
        self.goals.insert('A')
        assert self.goals.all(keys='name,edge,switchable') == {
                1: {'name': 'Root', 'edge': [3], 'switchable': False},
                2: {'name': 'B', 'edge': [], 'switchable': True},
                3: {'name': 'A', 'edge': [2], 'switchable': False},
        }

    def test_insert_goal_between_independent_goals(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.select(2)
        self.goals.hold_select()
        self.goals.select(3)
        self.goals.insert('Wow')
        assert self.goals.all(keys='name,edge,switchable') == {
                1: {'name': 'Root', 'edge': [2, 3], 'switchable': False},
                2: {'name': 'A', 'edge': [4], 'switchable': False},
                3: {'name': 'B', 'edge': [], 'switchable': True},
                4: {'name': 'Wow', 'edge': [3], 'switchable': False},
        }

    def test_close_single_goal(self):
        assert self.goals.all(keys='name,open') == {
                1: {'name': 'Root', 'open': True}}
        self.goals.toggle_close()
        assert self.goals.all(keys='name,open,switchable') == {
                1: {'name': 'Root', 'open': False, 'switchable': True}}

    def test_reopen_goal(self):
        self.goals.add('A')
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open') == {1: {'open': True}, 2: {'open': False}}
        assert self.goals.all(keys='select') == {1: {'select': 'select'}, 2: {'select': None}}
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open,switchable') == {
            1: {'open': True, 'switchable': False},
            2: {'open': True, 'switchable': True}}

    def test_close_goal_again(self):
        self.goals.add('A')
        self.goals.select(2)
        self.goals.add('Ab')
        self.goals.select(3)
        self.goals.toggle_close()
        assert self.goals.all(keys='open,switchable') == {
            1: {'open': True, 'switchable': False},
            2: {'open': True, 'switchable': True},
            3: {'open': False, 'switchable': True}}
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open,switchable') == {
            1: {'open': True, 'switchable': True},
            2: {'open': False, 'switchable': True},
            3: {'open': False, 'switchable': False}}
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open,switchable') == {
            1: {'open': True, 'switchable': False},
            2: {'open': True, 'switchable': True},
            3: {'open': False, 'switchable': True}}
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open,switchable') == {
            1: {'open': True, 'switchable': True},
            2: {'open': False, 'switchable': True},
            3: {'open': False, 'switchable': False}}

    def test_closed_leaf_goal_could_not_be_reopened(self):
        self.goals.add('A')
        self.goals.select(2)
        self.goals.add('B')
        self.goals.select(3)
        self.goals.toggle_close()
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open,switchable') == {
            1: {'open': True, 'switchable': True},
            2: {'open': False, 'switchable': True},
            3: {'open': False, 'switchable': False}}
        self.goals.select(3)
        self.goals.toggle_close()
        # nothing should change
        assert self.goals.all(keys='open,switchable') == {
            1: {'open': True, 'switchable': True},
            2: {'open': False, 'switchable': True},
            3: {'open': False, 'switchable': False}}

    def test_goal_in_the_middle_could_not_be_closed(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.select(2)
        self.goals.add('C')
        self.goals.select(3)
        self.goals.hold_select()
        self.goals.select(4)
        self.goals.toggle_link()
        # now goals 2 and 3 are blocked by the goal 4
        self.goals.select(3)
        self.goals.toggle_close()
        assert self.goals.all(keys='open') == {1: {'open': True}, 2: {'open': True}, 3: {'open': True},
                                               4: {'open': True}}

    def test_delete_single_goal(self):
        self.goals.add('A')
        self.goals.select(2)
        self.goals.delete()
        assert self.goals.all(keys='name,select,switchable') == {
                1: {'name': 'Root', 'select': 'select', 'switchable': True},
        }

    def test_enumeration_should_not_be_changed_after_delete(self):
        self.goals.add('A')
        self.goals.add('B')
        assert self.goals.all() == {1: {'name': 'Root'}, 2: {'name': 'A'}, 3: {'name': 'B'}}
        self.goals.select(2)
        self.goals.delete()
        assert self.goals.all(keys='name,switchable') == {
            1: {'name': 'Root', 'switchable': False},
            3: {'name': 'B', 'switchable': True}}

    def test_remove_goal_chain(self):
        self.goals.add('A')
        self.goals.add('B', 2)
        self.goals.select(2)
        self.goals.delete()
        assert self.goals.all() == {1: {'name': 'Root'}}

    def test_add_link_between_goals(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.select(2)
        self.goals.hold_select()
        self.goals.select(3)
        self.goals.toggle_link()
        assert self.goals.all(keys='switchable') == {
            1: {'switchable': False}, 2: {'switchable': False}, 3: {'switchable': True}
        }

    def test_view_edges(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.add('C', 2)
        self.goals.select(3)
        self.goals.hold_select()
        self.goals.select(4)
        self.goals.toggle_link()
        assert self.goals.all(keys='edge,switchable') == {
            1: {'edge': [2, 3], 'switchable': False},
            2: {'edge': [4], 'switchable': False},
            3: {'edge': [4], 'switchable': False},
            4: {'edge': [], 'switchable': True}}

    def test_no_link_to_self_is_allowed(self):
        self.goals.toggle_link()
        assert self.goals.all(keys='edge') == {1: {'edge': []}}

    def test_no_loops_allowed(self):
        self.goals.add('step')
        self.goals.select(2)
        self.goals.add('next')
        self.goals.select(3)
        self.goals.add('more')
        self.goals.select(4)
        self.goals.hold_select()
        self.goals.select(1)
        self.goals.toggle_link()
        assert self.goals.all(keys='edge') == {
            1: {'edge': [2]}, 2: {'edge': [3]}, 3: {'edge': [4]}, 4: {'edge': []}}

    def test_remove_link_between_goals(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.select(2)
        self.goals.hold_select()
        self.goals.select(3)
        self.goals.toggle_link()
        self.goals.toggle_link()
        assert self.goals.all(keys='switchable') == {
            1: {'switchable': False}, 2: {'switchable': True}, 3: {'switchable': True}
        }

    def test_remove_goal_in_the_middle(self):
        self.goals = build_goaltree(
            open_(1, 'Root', [2, 3]),
            open_(2, 'A', [4]),
            open_(3, 'B', [4]),
            open_(4, 'C', select=selected)
        )
        assert self.goals.all(keys='name,edge') == {
                1: {'name': 'Root', 'edge': [2, 3]},
                2: {'name': 'A', 'edge': [4]},
                3: {'name': 'B', 'edge': [4]},
                4: {'name': 'C', 'edge': []}}
        self.goals.select(3)
        self.goals.delete()
        assert self.goals.all(keys='name,edge,switchable') == {
                1: {'name': 'Root', 'edge': [2], 'switchable': False},
                2: {'name': 'A', 'edge': [4], 'switchable': False},
                4: {'name': 'C', 'edge': [], 'switchable': True}}

    def test_root_goal_is_selected_by_default(self):
        assert self.goals.all(keys='select') == {1: {'select': 'select'}}
        self.goals.add('A')
        assert self.goals.all(keys='select') == {1: {'select': 'select'}, 2: {'select': None}}
        self.goals.add('B')
        assert self.goals.all(keys='select') == {1: {'select': 'select'}, 2: {'select': None}, 3: {'select': None}}

    def test_new_goal_is_added_to_the_selected_node(self):
        self.goals.add('A')
        self.goals.select(2)
        assert self.goals.all(keys='name,select') == {
            1: {'name': 'Root', 'select': 'prev'},
            2: {'name': 'A', 'select': 'select'},
        }
        self.goals.add('B')
        assert self.goals.all(keys='name,select,edge') == {
            1: {'name': 'Root', 'select': 'prev', 'edge': [2]},
            2: {'name': 'A', 'select': 'select', 'edge': [3]},
            3: {'name': 'B', 'select': None, 'edge': []},
        }

    def test_move_selection_to_the_root_after_closing(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open,select') == {
                1: {'open': True, 'select': 'select'},
                2: {'open': False, 'select': None},
                3: {'open': True, 'select': None}}

    def test_ignore_wrong_selection(self):
        self.goals.select(2)
        assert self.goals.all(keys='select') == {
            1: {'select': 'select'}}

    def test_do_not_select_deleted_goals(self):
        self.goals.add('broken')
        self.goals.select(2)
        assert self.goals.all(keys='select') == {
            1: {'select': 'prev'}, 2: {'select': 'select'}}
        self.goals.delete()
        self.goals.select(2)
        assert self.goals.all(keys='select') == {
            1: {'select': 'select'}}

    def test_selection_should_be_instant(self):
        for char in '234567890A':
            self.goals.add(char)
        assert self.goals.all(keys='select') == {
            1: {'select': 'select'}, 2: {'select': None}, 3: {'select': None},
            4: {'select': None}, 5: {'select': None}, 6: {'select': None}, 7: {'select': None},
            8: {'select': None}, 9: {'select': None}, 10: {'select': None}, 11: {'select': None}}
        self.goals.select(2)
        assert self.goals.all(keys='select') == {
            1: {'select': 'prev'}, 2: {'select': 'select'}, 3: {'select': None}, 4: {'select': None},
            5: {'select': None}, 6: {'select': None}, 7: {'select': None}, 8: {'select': None},
            9: {'select': None}, 10: {'select': None}, 11: {'select': None}}
        self.goals.select(11)
        assert self.goals.all(keys='select') == {
            1: {'select': 'prev'}, 2: {'select': None}, 3: {'select': None}, 4: {'select': None},
            5: {'select': None}, 6: {'select': None}, 7: {'select': None}, 8: {'select': None},
            9: {'select': None}, 10: {'select': None}, 11: {'select': 'select'}}

    def test_add_events(self):
        assert self.goals.events.pop() == ('add', 1, 'Root', True)
        self.goals.add('Next')
        assert self.goals.events[-2] == ('add', 2, 'Next', True)
        assert self.goals.events[-1] == ('link', 1, 2)

    def test_select_events(self):
        self.goals.add('Next')
        self.goals.select(2)
        assert self.goals.events[-1] == ('select', 2)
        self.goals.hold_select()
        self.goals.select(1)
        assert self.goals.events[-2] == ('hold_select', 2)
        assert self.goals.events[-1] == ('select', 1)

    def test_toggle_close_events(self):
        self.goals.toggle_close()
        assert self.goals.events[-3] == ('toggle_close', False, 1)
        assert self.goals.events[-2] == ('select', 1)
        assert self.goals.events[-1] == ('hold_select', 1)
        self.goals.toggle_close()
        assert self.goals.events[-1] == ('toggle_close', True, 1)

    def test_rename_event(self):
        self.goals.rename('New')
        assert self.goals.events[-1] == ('rename', 'New', 1)

    def test_swap_event(self):
        self.goals.add('Next')
        self.goals.hold_select()
        self.goals.select(2)
        self.goals.swap_goals()
        assert self.goals.events[-2] == ('rename', 'Next', 1)
        assert self.goals.events[-1] == ('rename', 'Root', 2)

    def test_delete_events(self):
        self.goals.add('Sheep')
        self.goals.select(2)
        self.goals.delete()
        assert self.goals.events[-3] == ('delete', 2)
        assert self.goals.events[-2] == ('select', 1)
        assert self.goals.events[-1] == ('hold_select', 1)

    def test_link_events(self):
        self.goals.add('Next')
        self.goals.add('More')
        self.goals.select(2)
        self.goals.hold_select()
        self.goals.select(3)
        self.goals.toggle_link()
        assert self.goals.events[-1] == ('link', 2, 3)
        self.goals.toggle_link()
        assert self.goals.events[-1] == ('unlink', 2, 3)
