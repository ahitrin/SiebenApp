import io
from pprint import pprint

from approvaltests import verify  # type: ignore
from approvaltests.reporters import GenericDiffReporterFactory  # type: ignore

from siebenapp.render import (
    Renderer,
    GeometryProvider,
    render_lines,
    Point,
    adjust_graph,
)
from siebenapp.tests.dsl import build_goaltree, open_, clos_, selected, previous


class FakeGeometry(GeometryProvider):
    def top_left(self, row, col):
        return Point(col * 100, row * 100)

    def top_right(self, row, col):
        return Point(col * 100 + 50, row * 100)

    def bottom_left(self, row, col):
        return Point(col * 100, row * 100 + 50)

    def bottom_right(self, row, col):
        return Point(col * 100 + 50, row * 100 + 50)


def test_render_bug_example():
    g = build_goaltree(
        open_(1, "Root", [2, 3, 4, 5, 6], [7, 8]),
        clos_(2, "Closed", blockers=[7]),
        open_(3, "Simply 3", blockers=[5, 8]),
        open_(4, "Also 4", blockers=[5, 6, 7, 8], select=selected),
        open_(5, "Now 5", blockers=[6]),
        clos_(6, "Same 6", blockers=[7]),
        clos_(7, "Lucky 7", [8], select=previous),
        clos_(8, "Finally 8"),
    )
    r = Renderer(g)
    result = r.build()
    adjust_graph(result, FakeGeometry())
    lines = render_lines(FakeGeometry(), result)
    with io.StringIO() as out:
        print("== Graph\n", file=out)
        pprint(result.graph, out)
        print("\n== Edge options\n", file=out)
        pprint(result.edge_opts, out)
        print("\n== Lines", file=out)
        pprint(lines, out)
        verify(
            out.getvalue(), reporter=GenericDiffReporterFactory().get_first_working()
        )
