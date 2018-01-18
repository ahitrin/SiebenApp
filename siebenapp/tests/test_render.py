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
        1: [2, '1_1'],
        2: [1],
    }
    assert min_width(data, 3) == {
        0: [3, 4],
        1: ['1_1', 5, '2_1'],
        2: [6, '1_2', '2_2'],
        3: [2, '1_3'],
        4: [1],
    }
