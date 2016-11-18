# coding: utf-8
from mikado import Goals
from unittest import TestCase


class GoalsTest(TestCase):
    def setUp(self):
        self.goals = Goals('Root')

    def test_there_is_one_goal_at_start(self):
        assert self.goals.all() == {1: 'Root'}
        assert self.goals.top() == {1: 'Root'}

    def test_new_goal_moves_to_top(self):
        self.goals.add('A')
        assert self.goals.all() == {1: 'Root', 2: 'A'}
        assert self.goals.top() == {2: 'A'}

    def test_two_new_goals_move_to_top(self):
        self.goals.add('A')
        self.goals.add('B')
        assert self.goals.all() == {1: 'Root', 2: 'A', 3: 'B'}
        assert self.goals.top() == {2: 'A', 3: 'B'}

    def test_two_goals_in_a_chain(self):
        self.goals.add('A')
        self.goals.add('AA', 2)
        assert self.goals.all() == {1: 'Root', 2: 'A', 3: 'AA'}
        assert self.goals.top() == {3: 'AA'}

    def test_rename_goal(self):
        self.goals.add('Boom')
        self.goals.select(2)
        self.goals.rename('A')
        assert self.goals.all() == {1: 'Root', 2: 'A'}

    def test_insert_goal_in_the_middle(self):
        self.goals.add('B')
        self.goals.select(1)
        self.goals.hold_select()
        self.goals.select(2)
        self.goals.insert('A')
        assert self.goals.all() == {1: 'Root', 2: 'B', 3: 'A'}
        assert self.goals.top() == {2: 'B'}

    def test_close_single_goal(self):
        assert self.goals.all(keys='name,open') == {
                1: {'name': 'Root', 'open': True}}
        self.goals.toggle_close()
        assert self.goals.all() == {1: 'Root'}
        assert self.goals.top() == {}
        assert self.goals.all(keys='name,open') == {
                1: {'name': 'Root', 'open': False}}

    def test_reopen_goal(self):
        self.goals.add('A')
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open') == {1: True, 2: False}
        assert self.goals.all(keys='select') == {1: True, 2: False}
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open') == {1: True, 2: True}

    def test_delete_single_goal(self):
        self.goals.add('A')
        self.goals.select(2)
        self.goals.delete()
        assert self.goals.all(keys='name,select') == {
                1: {'name': 'Root', 'select': True},
        }

    def test_enumeration_should_not_be_changed_after_delete(self):
        self.goals.add('A')
        self.goals.add('B')
        assert self.goals.all() == {1: 'Root', 2: 'A', 3: 'B'}
        self.goals.select(2)
        self.goals.delete()
        assert self.goals.all() == {1: 'Root', 3: 'B'}

    def test_remove_goal_chain(self):
        self.goals.add('A')
        self.goals.add('B', 2)
        self.goals.select(2)
        self.goals.delete()
        assert self.goals.all() == {1: 'Root'}

    def test_add_link_between_goals(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.select(2)
        self.goals.hold_select()
        self.goals.select(3)
        self.goals.toggle_link()
        assert self.goals.top() == {3: 'B'}

    def test_view_edges(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.add('C', 2)
        self.goals.select(3)
        self.goals.hold_select()
        self.goals.select(4)
        self.goals.toggle_link()
        assert self.goals.top() == {4: 'C'}
        assert self.goals.all(keys='edge') == {
                1: [2, 3], 2: [4], 3: [4], 4: []}

    def test_remove_link_between_goals(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.select(2)
        self.goals.hold_select()
        self.goals.select(3)
        self.goals.toggle_link()
        self.goals.toggle_link()
        assert self.goals.top() == {2: 'A', 3: 'B'}

    def test_remove_goal_in_the_middle(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.add('C', 2)
        self.goals.select(3)
        self.goals.hold_select()
        self.goals.select(4)
        self.goals.toggle_link()
        assert self.goals.all(keys='name,edge') == {
                1: {'name': 'Root', 'edge': [2, 3]},
                2: {'name': 'A', 'edge': [4]},
                3: {'name': 'B', 'edge': [4]},
                4: {'name': 'C', 'edge': []}}
        self.goals.select(3)
        self.goals.delete()
        assert self.goals.all(keys='name,edge') == {
                1: {'name': 'Root', 'edge': [2]},
                2: {'name': 'A', 'edge': [4]},
                4: {'name': 'C', 'edge': []}}

    def test_root_goal_is_selected_by_default(self):
        assert self.goals.all(keys='select') == {1: True}
        self.goals.add('A')
        assert self.goals.all(keys='select') == {1: True, 2: False}
        self.goals.add('B')
        assert self.goals.all(keys='select') == {1: True, 2: False, 3: False}

    def test_new_goal_is_added_to_the_selected_node(self):
        self.goals.add('A')
        self.goals.select(2)
        assert self.goals.all(keys='name,select') == {
            1: {'name': 'Root', 'select': False},
            2: {'name': 'A', 'select': True},
        }
        self.goals.add('B')
        assert self.goals.all(keys='name,select,edge') == {
            1: {'name': 'Root', 'select': False, 'edge': [2]},
            2: {'name': 'A', 'select': True, 'edge': [3]},
            3: {'name': 'B', 'select': False, 'edge': []},
        }

    def test_move_selection_to_the_root_after_closing(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open,select') == {
                1: {'open': True, 'select': True},
                2: {'open': False, 'select': False},
                3: {'open': True, 'select': False}}

    def test_node_enumeration_must_be_keyboard_friendly(self):
        for char in '23456789':
            self.goals.add(char)
        assert self.goals.all(keys='name,edge') == {
            1: {'name': 'Root', 'edge': [2, 3, 4, 5, 6, 7, 8, 9]},
            2: {'name': '2', 'edge': []},
            3: {'name': '3', 'edge': []},
            4: {'name': '4', 'edge': []},
            5: {'name': '5', 'edge': []},
            6: {'name': '6', 'edge': []},
            7: {'name': '7', 'edge': []},
            8: {'name': '8', 'edge': []},
            9: {'name': '9', 'edge': []},
        }
        self.goals.add('0 is next to 9')
        assert self.goals.all(keys='name,edge') == {
            1: {'name': 'Root', 'edge': [0, 2, 3, 4, 5, 6, 7, 8, 9]},
            2: {'name': '2', 'edge': []},
            3: {'name': '3', 'edge': []},
            4: {'name': '4', 'edge': []},
            5: {'name': '5', 'edge': []},
            6: {'name': '6', 'edge': []},
            7: {'name': '7', 'edge': []},
            8: {'name': '8', 'edge': []},
            9: {'name': '9', 'edge': []},
            0: {'name': '0 is next to 9', 'edge': []},
        }
        self.goals.select(0)
        assert self.goals.all(keys='select') == {1: False, 2: False, 3: False,
                4: False, 5: False, 6: False, 7: False, 8: False, 9: False,
                0: True}
