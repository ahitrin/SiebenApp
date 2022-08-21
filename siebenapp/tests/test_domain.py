from siebenapp.domain import RenderResult, RenderRow, EdgeType


def test_render_result_slice():
    graph = {
        1: {"name": "One", "edge": [], "misc": "nope"},
        2: {"name": "Two", "edge": [], "foo": None},
        "1_1": {"name": "Fake", "edge": [1, 2]},
    }
    r = RenderResult(graph)
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


def test_render_result_slice_with_rows():
    rows = [
        RenderRow(
            goal_id=1,
            raw_id=1,
            name="One",
            edges=[],
            is_open=True,
            is_switchable=True,
            select="select",
        ),
        RenderRow(
            goal_id=2,
            raw_id=2,
            name="Two",
            edges=[],
            is_open=True,
            is_switchable=True,
            select=None,
        ),
        RenderRow(
            goal_id="1_1",
            raw_id=-123,
            name="Fake",
            edges=[(1, EdgeType.BLOCKER), (2, EdgeType.BLOCKER)],
            is_open=True,
            is_switchable=False,
            select=None,
        ),
    ]
    r = RenderResult(rows=rows)
    assert r.slice("name") == {
        1: {"name": "One"},
        2: {"name": "Two"},
        "1_1": {"name": "Fake"},
    }
    assert r.slice("name,edge") == {
        1: {"name": "One", "edge": []},
        2: {"name": "Two", "edge": []},
        "1_1": {"name": "Fake", "edge": [(1, EdgeType.BLOCKER), (2, EdgeType.BLOCKER)]},
    }
    assert r.slice("name,edge,open,select,switchable")[2] == {
        "name": "Two",
        "edge": [],
        "open": True,
        "select": None,
        "switchable": True,
    }
