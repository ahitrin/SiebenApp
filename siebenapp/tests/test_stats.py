import pytest

from siebenapp.stats import complexity
from siebenapp.tests.dsl import build_goaltree, open_


@pytest.mark.parametrize('tree,goals,edges,paths', [
    (build_goaltree(open_(1, 'a', select='select')), 1, 0, 0),
    (build_goaltree(open_(1, 'a', [2], select='select'),
                    open_(2, 'b')), 2, 1, 1),
    (build_goaltree(open_(1, 'a', [2, 3], select='select'),
                    open_(2, 'b'),
                    open_(3, 'c')), 3, 2, 2),
    (build_goaltree(open_(1, 'a', [2], select='select'),
                    open_(2, 'b', [3]),
                    open_(3, 'c')), 3, 2, 2),
    (build_goaltree(open_(1, 'a', [2, 3], select='select'),
                    open_(2, 'b', blockers=[3]),
                    open_(3, 'c')), 3, 3, 3),
    (build_goaltree(open_(1, 'a', [2, 3], select='select'),
                    open_(2, 'b', blockers=[4]),
                    open_(3, 'c', [4]),
                    open_(4, 'd')), 4, 4, 4),
    (build_goaltree(open_(1, 'a', [2, 3], select='select'),
                    open_(2, 'b', blockers=[3]),
                    open_(3, 'c', [4]),
                    open_(4, 'd')), 4, 4, 5),
])
def test_complexity(tree, goals, edges, paths):
    cp = complexity(tree)
    assert cp == {
        'goals': goals,
        'edges': edges,
        'paths': paths
    }
