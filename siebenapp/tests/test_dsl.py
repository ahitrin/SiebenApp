import pytest

from siebenapp.tests.dsl import build_goaltree, open_


def test_two_parents_for_one_goal_is_forbidden():
    with pytest.raises(AssertionError):
        build_goaltree(
            open_(1, 'First parent of 3', [2, 3]),
            open_(2, 'Second parent of 3', [3]),
            open_(3, 'Fellow child')
        )
