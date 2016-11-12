# coding: utf-8
from mikado import Goals


def test_there_is_one_goal_at_start():
    goals = Goals('Just a root goal')
    assert goals.all() == {1: 'Just a root goal'}
    assert goals.top() == {1: 'Just a root goal'}


def test_new_goal_moves_to_top():
    goals = Goals('Just do it')
    goals.add('Some later')
    assert goals.all() == {1: 'Just do it', 2: 'Some later'}
    assert goals.top() == {2: 'Some later'}


def test_two_new_goals_move_to_top():
    goals = Goals('Root')
    goals.add('A')
    goals.add('B')
    assert goals.all() == {1: 'Root', 2: 'A', 3: 'B'}
    assert goals.top() == {2: 'A', 3: 'B'}


def test_two_goals_in_a_chain():
    goals = Goals('Root')
    goals.add('A')
    goals.add('AA', 2)
    assert goals.all() == {1: 'Root', 2: 'A', 3: 'AA'}
    assert goals.top() == {3: 'AA'}


def test_rename_goal():
    goals = Goals('Root')
    goals.add('Boom')
    goals.rename(2, 'A')
    assert goals.all() == {1: 'Root', 2: 'A'}


def test_insert_goal_in_the_middle():
    goals = Goals('Root')
    goals.add('B')
    goals.insert(1, 2, 'A')
    assert goals.all() == {1: 'Root', 2: 'B', 3: 'A'}
    assert goals.top() == {2: 'B'}


def test_close_single_goal():
    goals = Goals('Do it')
    assert goals.all(keys='name,open') == {1: {'name': 'Do it',
                                               'open': True}}
    goals.close(1)
    assert goals.all() == {1: 'Do it'}
    assert goals.top() == {}
    assert goals.all(keys='name,open') == {1: {'name': 'Do it',
                                               'open': False}}


def test_reopen_goal():
    goals = Goals('Root')
    goals.add('A')
    goals.close(2)
    assert goals.all(keys='open') == {1: True, 2: False}
    goals.reopen(2)
    assert goals.all(keys='open') == {1: True, 2: True}


def test_delete_single_goal():
    goals = Goals('Root')
    goals.add('A')
    goals.delete(2)
    assert goals.all() == {1: 'Root'}


def test_enumeration_could_be_changed_after_delete():
    goals = Goals('Root')
    goals.add('A')
    goals.add('B')
    assert goals.all() == {1: 'Root', 2: 'A', 3: 'B'}
    goals.delete(2)
    assert goals.all() == {1: 'Root', 2: 'B'}
