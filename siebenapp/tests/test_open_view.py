from siebenapp.enumeration import Enumeration
from siebenapp.goaltree import Goals


def test_open_goal_is_shown_by_default():
    g = Goals("Start")
    v = Enumeration(g)
    assert v.q("name") == {1: {"name": "Start"}}
