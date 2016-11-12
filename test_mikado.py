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
