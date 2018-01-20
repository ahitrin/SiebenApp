from siebenapp.render import render_tree
from siebenapp.tests.dsl import build_goaltree, open_, selected


def get_in(data, column):
    return {k: v[column] for k, v in data.items()}


def test_render_simplest_goal_tree():
    goals = build_goaltree(open_(1, 'Alone', [], selected))
    result = render_tree(goals)
    assert result == {
        1: {
            'row': 0,
            'col': 0,
            'edge': [],
            'name': 'Alone',
            'open': True,
            'select': 'select',
            'switchable': True,
        }
    }


def test_render_4_subgoals_in_a_row():
    goals = build_goaltree(
        open_(1, 'Root', [2, 3, 4, 5], selected),
        open_(2, 'A'),
        open_(3, 'B'),
        open_(4, 'C'),
        open_(5, 'D')
    )
    result = render_tree(goals)
    assert get_in(result, 'row') == {
        2: 0, 3: 0, 4: 0, 5: 0,
        1: 1,
    }


def test_render_add_fake_vertex():
    goals = build_goaltree(
        open_(1, 'Root', [2, 3], selected),
        open_(2, 'A', [3]),
        open_(3, 'B')
    )
    result = render_tree(goals)
    assert get_in(result, 'row') == {
        3: 0,
        2: 1, '1_1': 1,
        1: 2,
    }


def test_render_add_several_fake_vertex():
    goals = build_goaltree(
        open_(1, 'Root', [2, 5], selected),
        open_(2, 'A', [3]),
        open_(3, 'B', [4]),
        open_(4, 'C', [5]),
        open_(5, 'top')
    )
    result = render_tree(goals)
    assert get_in(result, 'row') == {
        5: 0,
        4: 1, '1_1': 1,
        3: 2, '1_2': 2,
        2: 3, '1_3': 3,
        1: 4,
    }


def test_render_5_subgoals_in_several_rows():
    goals = build_goaltree(
        open_(1, 'Root', [2, 3, 4, 5, 6], selected),
        open_(2, 'A'),
        open_(3, 'B'),
        open_(4, 'C'),
        open_(5, 'D'),
        open_(6, 'E')
    )
    result = render_tree(goals)
    assert get_in(result, 'row') == {
        2: 0, 3: 0, 4: 0, 5: 0,
        6: 1, '1_1': 1,
        1: 2,
    }


def test_split_long_edges_using_fake_goals():
    goals = build_goaltree(
        open_(1, 'Root', [2, 5], selected),
        open_(2, 'A', [3]),
        open_(3, 'B', [4]),
        open_(4, 'C', [5]),
        open_(5, 'top')
    )
    result = render_tree(goals)
    assert get_in(result, 'edge') == {
        5: [],
        4: [5], '1_1': [5],
        3: [4], '1_2': ['1_1'],
        2: [3], '1_3': ['1_2'],
        1: [2, '1_3'],
    }
