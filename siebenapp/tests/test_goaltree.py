# coding: utf-8
from siebenapp.goaltree import Goals, Enumeration
from unittest import TestCase


class GoalsTest(TestCase):
    def setUp(self):
        self.goals = Goals('Root')

    def test_there_is_one_goal_at_start(self):
        assert self.goals.all() == {1: {'name': 'Root'}}
        assert self.goals.top() == set([1])

    def test_new_goal_moves_to_top(self):
        self.goals.add('A')
        assert self.goals.all() == {1: {'name': 'Root'}, 2: {'name': 'A'}}
        assert self.goals.top() == set([2])

    def test_two_new_goals_move_to_top(self):
        self.goals.add('A')
        self.goals.add('B')
        assert self.goals.all() == {1: {'name': 'Root'}, 2: {'name': 'A'}, 3: {'name': 'B'}}
        assert self.goals.top() == set([2, 3])

    def test_two_goals_in_a_chain(self):
        self.goals.add('A')
        self.goals.add('AA', 2)
        assert self.goals.all() == {1: {'name': 'Root'}, 2: {'name': 'A'}, 3: {'name': 'AA'}}
        assert self.goals.top() == set([3])

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
        assert self.goals.all(keys='name,edge') == {
                1: {'name': 'Root', 'edge': [3]},
                2: {'name': 'B', 'edge': []},
                3: {'name': 'A', 'edge': [2]},
        }
        assert self.goals.top() == set([2])

    def test_insert_goal_between_independent_goals(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.select(2)
        self.goals.hold_select()
        self.goals.select(3)
        self.goals.insert('Wow')
        assert self.goals.all(keys='name,edge') == {
                1: {'name': 'Root', 'edge': [2, 3]},
                2: {'name': 'A', 'edge': [4]},
                3: {'name': 'B', 'edge': []},
                4: {'name': 'Wow', 'edge': [3]},
        }
        assert self.goals.top() == set([3])

    def test_close_single_goal(self):
        assert self.goals.all(keys='name,open') == {
                1: {'name': 'Root', 'open': True}}
        self.goals.toggle_close()
        assert self.goals.all() == {1: {'name': 'Root'}}
        assert self.goals.top() == set()
        assert self.goals.all(keys='name,open') == {
                1: {'name': 'Root', 'open': False}}

    def test_reopen_goal(self):
        self.goals.add('A')
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open') == {1: {'open': True}, 2: {'open': False}}
        assert self.goals.all(keys='select') == {1: {'select': 'select'}, 2: {'select': None}}
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open') == {1: {'open': True}, 2: {'open': True}}
        assert self.goals.top() == set([2])

    def test_close_goal_again(self):
        self.goals.add('A')
        self.goals.select(2)
        self.goals.add('Ab')
        self.goals.select(3)
        self.goals.toggle_close()
        assert self.goals.all(keys='open') == {1: {'open': True}, 2: {'open': True}, 3: {'open': False}}
        assert self.goals.top() == set([2])
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open') == {1: {'open': True}, 2: {'open': False}, 3: {'open': False}}
        assert self.goals.top() == set([1])
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open') == {1: {'open': True}, 2: {'open': True}, 3: {'open': False}}
        assert self.goals.top() == set([2])
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open') == {1: {'open': True}, 2: {'open': False}, 3: {'open': False}}
        assert self.goals.top() == set([1])

    def test_closed_leaf_goal_could_not_be_reopened(self):
        self.goals.add('A')
        self.goals.select(2)
        self.goals.add('B')
        self.goals.select(3)
        self.goals.toggle_close()
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open') == {1: {'open': True}, 2: {'open': False}, 3: {'open': False}}
        assert self.goals.top() == set([1])
        self.goals.select(3)
        self.goals.toggle_close()
        # nothing should change
        assert self.goals.all(keys='open') == {1: {'open': True}, 2: {'open': False}, 3: {'open': False}}
        assert self.goals.top() == set([1])

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
        assert self.goals.all(keys='name,select') == {
                1: {'name': 'Root', 'select': 'select'},
        }
        assert self.goals.top() == set([1])

    def test_enumeration_should_not_be_changed_after_delete(self):
        self.goals.add('A')
        self.goals.add('B')
        assert self.goals.all() == {1: {'name': 'Root'}, 2: {'name': 'A'}, 3: {'name': 'B'}}
        self.goals.select(2)
        self.goals.delete()
        assert self.goals.all() == {1: {'name': 'Root'}, 3: {'name': 'B'}}
        assert self.goals.top() == set([3])

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
        assert self.goals.top() == set([3])

    def test_view_edges(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.add('C', 2)
        self.goals.select(3)
        self.goals.hold_select()
        self.goals.select(4)
        self.goals.toggle_link()
        assert self.goals.top() == set([4])
        assert self.goals.all(keys='edge') == {
                1: {'edge': [2, 3]}, 2: {'edge': [4]}, 3: {'edge': [4]}, 4: {'edge': []}}

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
        assert self.goals.top() == set([2, 3])

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
        assert self.goals.top() == set([4])

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
        assert self.goals.all(keys='select') == {1: {'select': 'prev'}, 2: {'select': None},
                3: {'select': None}, 4: {'select': None}, 5: {'select': None}, 6: {'select': None},
                7: {'select': None}, 8: {'select': None}, 9: {'select': None}, 0: {'select': 'select'}}
        assert self.goals.top() == set([2, 3, 4, 5, 6, 7, 8, 9, 0])

    def test_node_enumeration_has_equal_numbers_count_for_all_nodes(self):
        for char in '234567890':
            self.goals.add(char)
        assert self.goals.all() == {1: {'name': 'Root'}, 2: {'name': '2'}, 3: {'name': '3'},
                4: {'name': '4'}, 5: {'name': '5'}, 6: {'name': '6'}, 7: {'name': '7'},
                8: {'name': '8'}, 9: {'name': '9'}, 0: {'name': '0'}}
        self.goals.add('A')
        assert self.goals.all() == {11: {'name': 'Root'}, 12: {'name': '2'}, 13: {'name': '3'},
                14: {'name': '4'}, 15: {'name': '5'}, 16: {'name': '6'}, 17: {'name': '7'},
                18: {'name': '8'}, 19: {'name': '9'}, 10: {'name': '0'}, 21: {'name': 'A'}}
        assert self.goals.top() == set([12, 13, 14, 15, 16, 17, 18, 19, 10, 21])

    def test_selection_should_be_additive(self):
        for char in '234567890A':
            self.goals.add(char)
        assert self.goals.all(keys='select') == {11: {'select': 'select'}, 12: {'select': None},
                13: {'select': None}, 14: {'select': None}, 15: {'select': None}, 16: {'select': None},
                17: {'select': None}, 18: {'select': None}, 19: {'select': None}, 10: {'select': None},
                21: {'select': None}}
        # no change yet
        self.goals.select(2)
        assert self.goals.all(keys='select') == {11: {'select': 'select'}, 12: {'select': None},
                13: {'select': None}, 14: {'select': None}, 15: {'select': None}, 16: {'select': None},
                17: {'select': None}, 18: {'select': None}, 19: {'select': None}, 10: {'select': None},
                21: {'select': None}}
        # now change happens
        self.goals.select(1)
        assert self.goals.all(keys='select') == {11: {'select': 'prev'}, 12: {'select': None},
                13: {'select': None}, 14: {'select': None}, 15: {'select': None}, 16: {'select': None},
                17: {'select': None}, 18: {'select': None}, 19: {'select': None}, 10: {'select': None},
                21: {'select': 'select'}}

    def test_enumeration_will_have_3_numbers_when_there_are_more_than_90_goals(self):
        for i in range(89):
            self.goals.add(str(i))
        sel = self.goals.all(keys='select')
        assert all(k < 100 for k in sel.keys())
        assert sel[11]['select'] == 'select'
        self.goals.add('boo')
        sel = self.goals.all(keys='select')
        assert all(k > 100 for k in sel.keys())
        assert sel[111]['select'] == 'select'
        assert all(not sel[k]['select'] for k in sel.keys() if k != 111)

    def test_select_when_more_than_90_goals(self):
        for i in range(100):
            self.goals.add(str(i))
        self.goals.select(1)
        self.goals.select(4)
        assert self.goals.all(keys='select')[111]['select'] == 'select'
        self.goals.select(5)
        assert self.goals.all(keys='select')[145]['select'] == 'select'

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
        assert self.goals.events[-1] == ('link', 2 ,3)
        self.goals.toggle_link()
        assert self.goals.events[-1] == ('unlink', 2 ,3)


class FakeGoals():
    def __init__(self, result):
        self.result = result

    def all(self, keys=''):
        return self.result


class EnumerationTest(TestCase):
    def test_simple_enumeration_is_not_changed(self):
        goals = FakeGoals({
            1: 'a', 2: 'b', 3: 'c'
        })
        e = Enumeration(goals)
        assert e.all() == {
            1: 'a', 2: 'b', 3: 'c'
        }

    def test_apply_mapping_for_the_10th_element(self):
        goals = FakeGoals({
            1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e', 6: 'f', 7: 'g',
            8: 'h', 9: 'i', 10: 'j'
        })
        e = Enumeration(goals)
        assert e.all() == {
            1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e', 6: 'f', 7: 'g',
            8: 'h', 9: 'i', 0: 'j'
        }
        goals.result[11] = 'k'
        assert e.all() == {
            11: 'a', 12: 'b', 13: 'c', 14: 'd', 15: 'e', 16: 'f',
            17: 'g', 18: 'h', 19: 'i', 10: 'j', 21: 'k'
        }
