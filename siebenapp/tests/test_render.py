from siebenapp.render import min_width


def test_min_width_examples():
    data = {
        1: [2, 3, 4],
        2: [3, 5, 6],
        3: [],
        4: [],
        5: [],
        6: [],
    }
    assert min_width(data, 10) == {
        0: [3, 4, 5, 6],
        1: [2],
        2: [1],
    }
    assert min_width(data, 3) == {
        0: [3, 4],
        1: [5],
        2: [6],
        3: [2],
        4: [1],
    }
