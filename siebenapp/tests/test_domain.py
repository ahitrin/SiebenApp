from siebenapp.domain import RenderResult


def test_render_result_slice():
    graph = {
        1: {"name": "One", "edge": [], "misc": "nope"},
        2: {"name": "Two", "edge": [], "foo": None},
        "1_1": {"name": "Fake", "edge": [1, 2]},
    }
    r = RenderResult(graph, {})
    assert r.slice("name") == {
        1: {"name": "One"},
        2: {"name": "Two"},
        "1_1": {"name": "Fake"},
    }
    assert r.slice("name,edge") == {
        1: {"name": "One", "edge": []},
        2: {"name": "Two", "edge": []},
        "1_1": {"name": "Fake", "edge": [1, 2]},
    }
