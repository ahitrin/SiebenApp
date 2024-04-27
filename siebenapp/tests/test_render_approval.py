import io
from dataclasses import asdict
from pprint import pprint

import pytest

from siebenapp.render import (
    Renderer,
    GeometryProvider,
    render_lines,
    Point,
    adjust_graph,
)
from siebenapp.render_next import build_with, tube
from siebenapp.tests.dsl import build_goaltree, open_, clos_, selected, previous
from siebenapp.tests.test_cli import verify_file


class FakeGeometry(GeometryProvider):
    def width(self, row, col):
        return Point(44 + 6 * (row % 2), 0)

    def height(self, row, col):
        return Point(0, 40 + 10 * (col % 2))

    def top_left(self, row, col):
        return Point(col * 100, row * 100)

    def top_right(self, row, col):
        return self.top_left(row, col) + self.width(row, col)

    def bottom_left(self, row, col):
        return self.top_left(row, col) + self.height(row, col)

    def bottom_right(self, row, col):
        return self.bottom_left(row, col) + self.width(row, col)


@pytest.fixture
def default_tree():
    return build_goaltree(
        open_(1, "Root", [2, 3, 4, 5, 6], [7, 8]),
        clos_(2, "Closed", blockers=[7]),
        open_(3, "Simply 3", blockers=[5, 8]),
        open_(4, "Also 4", blockers=[5, 6, 7, 8], select=selected),
        open_(5, "Now 5", blockers=[6]),
        clos_(6, "Same 6", blockers=[7]),
        clos_(7, "Lucky 7", [8], select=previous),
        clos_(8, "Finally 8"),
    )


def test_render_example(default_tree) -> None:
    r = Renderer(default_tree)
    result = r.build()
    gp = FakeGeometry()
    adjust_graph(result, gp)
    lines = render_lines(gp, result)
    with io.StringIO() as out:
        print("== Graph\n", file=out)
        pprint(asdict(result), out)
        print("\n== Geometry change after adjust\n", file=out)
        total_delta = Point(0, 0)
        for goal_id in default_tree.goals:
            goal = result.node_opts[goal_id]
            delta = gp.top_left(goal["row"], goal["col"]) - Point(goal["x"], goal["y"])
            total_delta += delta
            print(f"{goal_id}: dx={delta.x}, dy={delta.y}", file=out)
        avg_dx = total_delta.x // len(default_tree.goals)
        avg_dy = total_delta.y // len(default_tree.goals)
        print(f"Avg: dx={avg_dx}, dy={avg_dy}", file=out)
        print("\n== Lines", file=out)
        pprint(lines, out)
        verify_file(out.getvalue())


def test_render_new_example(default_tree) -> None:
    result = default_tree.q()
    result.node_opts = {row.goal_id: {} for row in result.rows}
    rendered_result = build_with(result, tube).rr
    with io.StringIO() as out:
        print("== Graph\n", file=out)
        pprint(asdict(rendered_result), out)
        verify_file(out.getvalue())
