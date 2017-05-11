# coding: utf-8
from siebenapp.goaltree import Goals, Enumeration
from unittest import TestCase


class GoalsTest(TestCase):
    def setUp(self):
        self.goals = Goals('Root')

    def test_there_is_one_goal_at_start(self):
        assert self.goals.all(keys='name,top') == {1: {'name': 'Root', 'top': True}}

    def test_new_goal_moves_to_top(self):
        self.goals.add('A')
        assert self.goals.all(keys='name,top') == {
            1: {'name': 'Root', 'top': False},
            2: {'name': 'A', 'top': True}}

    def test_two_new_goals_move_to_top(self):
        self.goals.add('A')
        self.goals.add('B')
        assert self.goals.all(keys='name,top') == {
            1: {'name': 'Root', 'top': False},
            2: {'name': 'A', 'top': True},
            3: {'name': 'B', 'top': True}}

    def test_two_goals_in_a_chain(self):
        self.goals.add('A')
        self.goals.add('AA', 2)
        assert self.goals.all(keys='name,top') == {
            1: {'name': 'Root', 'top': False},
            2: {'name': 'A', 'top': False},
            3: {'name': 'AA', 'top': True}}

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
        assert self.goals.all(keys='name,edge,top') == {
                1: {'name': 'Root', 'edge': [3], 'top': False},
                2: {'name': 'B', 'edge': [], 'top': True},
                3: {'name': 'A', 'edge': [2], 'top': False},
        }

    def test_insert_goal_between_independent_goals(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.select(2)
        self.goals.hold_select()
        self.goals.select(3)
        self.goals.insert('Wow')
        assert self.goals.all(keys='name,edge,top') == {
                1: {'name': 'Root', 'edge': [2, 3], 'top': False},
                2: {'name': 'A', 'edge': [4], 'top': False},
                3: {'name': 'B', 'edge': [], 'top': True},
                4: {'name': 'Wow', 'edge': [3], 'top': False},
        }

    def test_close_single_goal(self):
        assert self.goals.all(keys='name,open') == {
                1: {'name': 'Root', 'open': True}}
        self.goals.toggle_close()
        assert self.goals.all(keys='name,open,top') == {
                1: {'name': 'Root', 'open': False, 'top': False}}

    def test_reopen_goal(self):
        self.goals.add('A')
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open') == {1: {'open': True}, 2: {'open': False}}
        assert self.goals.all(keys='select') == {1: {'select': 'select'}, 2: {'select': None}}
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open,top') == {
            1: {'open': True, 'top': False},
            2: {'open': True, 'top': True}}

    def test_close_goal_again(self):
        self.goals.add('A')
        self.goals.select(2)
        self.goals.add('Ab')
        self.goals.select(3)
        self.goals.toggle_close()
        assert self.goals.all(keys='open,top') == {
            1: {'open': True, 'top': False},
            2: {'open': True, 'top': True},
            3: {'open': False, 'top': False}}
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open,top') == {
            1: {'open': True, 'top': True},
            2: {'open': False, 'top': False},
            3: {'open': False, 'top': False}}
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open,top') == {
            1: {'open': True, 'top': False},
            2: {'open': True, 'top': True},
            3: {'open': False, 'top': False}}
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open,top') == {
            1: {'open': True, 'top': True},
            2: {'open': False, 'top': False},
            3: {'open': False, 'top': False}}

    def test_closed_leaf_goal_could_not_be_reopened(self):
        self.goals.add('A')
        self.goals.select(2)
        self.goals.add('B')
        self.goals.select(3)
        self.goals.toggle_close()
        self.goals.select(2)
        self.goals.toggle_close()
        assert self.goals.all(keys='open,top') == {
            1: {'open': True, 'top': True},
            2: {'open': False, 'top': False},
            3: {'open': False, 'top': False}}
        self.goals.select(3)
        self.goals.toggle_close()
        # nothing should change
        assert self.goals.all(keys='open,top') == {
            1: {'open': True, 'top': True},
            2: {'open': False, 'top': False},
            3: {'open': False, 'top': False}}

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
        assert self.goals.all(keys='name,select,top') == {
                1: {'name': 'Root', 'select': 'select', 'top': True},
        }

    def test_enumeration_should_not_be_changed_after_delete(self):
        self.goals.add('A')
        self.goals.add('B')
        assert self.goals.all() == {1: {'name': 'Root'}, 2: {'name': 'A'}, 3: {'name': 'B'}}
        self.goals.select(2)
        self.goals.delete()
        assert self.goals.all(keys='name,top') == {
            1: {'name': 'Root', 'top': False},
            3: {'name': 'B', 'top': True}}

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
        assert self.goals.all(keys='top') == {1: {'top': False}, 2: {'top': False}, 3: {'top': True}}

    def test_view_edges(self):
        self.goals.add('A')
        self.goals.add('B')
        self.goals.add('C', 2)
        self.goals.select(3)
        self.goals.hold_select()
        self.goals.select(4)
        self.goals.toggle_link()
        assert self.goals.all(keys='edge,top') == {
            1: {'edge': [2, 3], 'top': False},
            2: {'edge': [4], 'top': False},
            3: {'edge': [4], 'top': False},
            4: {'edge': [], 'top': True}}

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
        assert self.goals.all(keys='top') == {1: {'top': False}, 2: {'top': True}, 3: {'top': True}}

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
        assert self.goals.all(keys='name,edge,top') == {
                1: {'name': 'Root', 'edge': [2], 'top': False},
                2: {'name': 'A', 'edge': [4], 'top': False},
                4: {'name': 'C', 'edge': [], 'top': True}}

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


def test_simple_enumeration_is_not_changed():
    goals = Goals('a')
    goals.add('b')
    goals.add('c')
    goals.select(2)
    goals.hold_select()
    goals.select(3)
    goals.toggle_link()
    e = Enumeration(goals)
    assert e.all(keys='name,edge') == {
        1: {'name': 'a', 'edge': [2, 3]},
        2: {'name': 'b', 'edge': [3]},
        3: {'name': 'c', 'edge': []},
    }


def test_apply_mapping_for_the_10th_element():
    goals = Goals('a')
    for i, c in enumerate('bcdefghij'):
        goals.add(c)
        goals.select(i + 2)
    e = Enumeration(goals)
    assert e.all(keys='name,edge') == {
        1: {'name': 'a', 'edge': [2]},
        2: {'name': 'b', 'edge': [3]},
        3: {'name': 'c', 'edge': [4]},
        4: {'name': 'd', 'edge': [5]},
        5: {'name': 'e', 'edge': [6]},
        6: {'name': 'f', 'edge': [7]},
        7: {'name': 'g', 'edge': [8]},
        8: {'name': 'h', 'edge': [9]},
        9: {'name': 'i', 'edge': [0]},
        0: {'name': 'j', 'edge': []},
    }
    # simulate goal addition
    goals.select(1)
    goals.add('k')
    assert e.all(keys='name,edge') == {
        11: {'name': 'a', 'edge': [12, 21]},
        12: {'name': 'b', 'edge': [13]},
        13: {'name': 'c', 'edge': [14]},
        14: {'name': 'd', 'edge': [15]},
        15: {'name': 'e', 'edge': [16]},
        16: {'name': 'f', 'edge': [17]},
        17: {'name': 'g', 'edge': [18]},
        18: {'name': 'h', 'edge': [19]},
        19: {'name': 'i', 'edge': [10]},
        10: {'name': 'j', 'edge': []},
        21: {'name': 'k', 'edge': []},
    }


def test_use_mapping_in_selection():
    goals = Goals('a')
    for i, c in enumerate('bcdefghij'):
        goals.add(c)
        goals.select(i + 2)
    e = Enumeration(goals)
    e.select(0)
    assert e.all(keys='name,select') == {
        1: {'name': 'a', 'select': 'prev'},
        2: {'name': 'b', 'select': None},
        3: {'name': 'c', 'select': None},
        4: {'name': 'd', 'select': None},
        5: {'name': 'e', 'select': None},
        6: {'name': 'f', 'select': None},
        7: {'name': 'g', 'select': None},
        8: {'name': 'h', 'select': None},
        9: {'name': 'i', 'select': None},
        0: {'name': 'j', 'select': 'select'},
    }
    e.add('k')
    e.select(1)
    e.select(6)
    assert e.all(keys='name,select') == {
        11: {'name': 'a', 'select': 'prev'},
        12: {'name': 'b', 'select': None},
        13: {'name': 'c', 'select': None},
        14: {'name': 'd', 'select': None},
        15: {'name': 'e', 'select': None},
        16: {'name': 'f', 'select': 'select'},
        17: {'name': 'g', 'select': None},
        18: {'name': 'h', 'select': None},
        19: {'name': 'i', 'select': None},
        10: {'name': 'j', 'select': None},
        21: {'name': 'k', 'select': None},
    }


def test_mapping_for_top():
    goals = Goals('a')
    goals.add('b')
    for i, c in enumerate('cdefghijklmnopqrstuv'):
        goals.add(c)
        goals.delete(i + 3)         # 1: a, 2: b, 3 (i==0): c, 4 (i==1): d, ...
    goals.add('x')
    e = Enumeration(goals)
    assert e.all(keys='name,top,select') == {
        1: {'name': 'a', 'top': False, 'select': 'select'},
        2: {'name': 'b', 'top': True, 'select': None},
        3: {'name': 'x', 'top': True, 'select': None},
    }


def test_toggle_switch_view():
    e = Enumeration(Goals('Root'))
    assert e.view == 'open'
    e.next_view()
    assert e.view == 'top'
    e.next_view()
    assert e.view == 'full'
    e.next_view()
    assert e.view == 'open'


def test_goaltree_selection_may_be_changed_in_top_view():
    goals = Goals('Root')
    goals.add('Top 1')
    goals.add('Top 2')
    e = Enumeration(goals)
    assert e.all(keys='name,top,select') == {
        1: {'name': 'Root', 'top': False, 'select': 'select'},
        2: {'name': 'Top 1', 'top': True, 'select': None},
        3: {'name': 'Top 2', 'top': True, 'select': None},
    }
    e.next_view()
    assert e.events[-2] == ('select', 2)
    assert e.events[-1] == ('hold_select', 2)
    assert e.all(keys='name,top,select') == {
        1: {'name': 'Top 1', 'top': True, 'select': 'select'},
        2: {'name': 'Top 2', 'top': True, 'select': None}
    }


def test_goaltree_previous_selection_may_be_changed_in_top_view():
    goals = Goals('Root')
    goals.add('Top 1')
    goals.add('Top 2')
    goals.hold_select()
    goals.select(2)
    e = Enumeration(goals)
    assert e.all(keys='name,top,select') == {
        1: {'name': 'Root', 'top': False, 'select': 'prev'},
        2: {'name': 'Top 1', 'top': True, 'select': 'select'},
        3: {'name': 'Top 2', 'top': True, 'select': None},
    }
    e.next_view()
    assert e.events[-1] == ('hold_select', 2)
    assert e.all(keys='name,top,select') == {
        1: {'name': 'Top 1', 'top': True, 'select': 'select'},
        2: {'name': 'Top 2', 'top': True, 'select': None}
    }
    e.insert('Illegal goal')
    # New goal must not be inserted because previous selection is reset after the view switching
    e.next_view()
    assert e.all(keys='name,top,select') == {
        1: {'name': 'Root', 'top': False, 'select': None},
        2: {'name': 'Top 1', 'top': True, 'select': 'select'},
        3: {'name': 'Top 2', 'top': True, 'select': None},
    }


def test_simple_top_enumeration_workflow():
    e = Enumeration(Goals('root'))
    e.add('1')
    e.add('2')
    e.select(2)
    e.next_view()
    e.select(2)
    assert e.all() == {
        1: {'name': '1'},
        2: {'name': '2'}
    }
