# coding: utf-8
from mikado import Goals


def test_there_is_one_goal_at_start():
    goals = Goals('Just a root goal')
    assert goals.top() == {1: 'Just a root goal'}
    assert goals.all() == {1: 'Just a root goal'}
