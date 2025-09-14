import pytest

from siebenapp.render_next import uniform_locations


@pytest.mark.parametrize(
    "width,num,expected",
    [
        (4, 1, [1]),  # .x..
        (4, 2, [0, 2]),  # x.x.
        (4, 3, [0, 2, 3]),  # x.xx
        (4, 4, [0, 1, 2, 3]),  # xxxx
        (5, 1, [2]),  # ..x..
        (5, 2, [1, 3]),  # .x.x.
        (5, 3, [0, 2, 4]),  # x.x.x
        (5, 4, [0, 2, 3, 4]),  # x.xxx
        (5, 5, [0, 1, 2, 3, 4]),  # xxxxx
    ],
)
def test_uniform_locations(width, num, expected):
    assert expected == uniform_locations(width, num)
