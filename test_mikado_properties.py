# coding: utf-8
from mikado import Goals
from hypothesis import given
from hypothesis.strategies import integers


@given(integers())
def test_there_is_always_at_least_one_goal(i):
    g = Goals('Indeletable')
    g.select(i)
    g.delete()
    assert g.all()
