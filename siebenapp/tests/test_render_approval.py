import io
import sys
from dataclasses import asdict
from pprint import pprint
from typing import Any

import pytest

from siebenapp.goaltree import Selectable
from siebenapp.render import (
    Renderer,
    GeometryProvider,
    render_lines,
    Point,
)
from siebenapp.render_next import full_render
from siebenapp.tests.dsl import build_goaltree, open_, clos_
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
    return Selectable(
        build_goaltree(
            open_(1, "Root", [2, 3, 4, 5, 6], [7, 8]),
            clos_(2, "Closed", blockers=[7]),
            open_(3, "Simply 3", blockers=[5, 8]),
            open_(4, "Also 4", blockers=[5, 6, 7, 8]),
            open_(5, "Now 5", blockers=[6]),
            clos_(6, "Same 6", blockers=[7]),
            clos_(7, "Lucky 7", [8]),
            clos_(8, "Finally 8"),
            select=(4, 7),
        ),
        [("selection", 4), ("previous_selection", 7)],
    )


def test_render_example(default_tree) -> None:
    r = Renderer(default_tree)
    result = r.build()
    gp = FakeGeometry()
    lines = render_lines(gp, result)
    with io.StringIO() as out:
        print("== Graph\n", file=out)
        pprint(asdict(result), out)
        print("\n== Lines", file=out)
        pprint(lines, out)
        verify_file(out.getvalue())


@pytest.mark.skipif(
    sys.version_info >= (3, 12),
    reason="Minor differences in printing of float values in py312",
)
def test_render_new_example(default_tree) -> None:
    width = 4
    listener: list[tuple[str, Any]] = []
    full_render(default_tree, width, listener)

    with io.StringIO() as out:
        print("= Render process", file=out)
        for msg, content in listener:
            print(f"\n== {msg}\n", file=out)
            pprint(asdict(content), out)
        verify_file(out.getvalue())
