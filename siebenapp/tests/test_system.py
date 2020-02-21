# coding: utf-8
from pathlib import Path

import pytest

from siebenapp.system import split_long, dot_export
from siebenapp.tests.dsl import build_goaltree, open_, clos_, selected, previous


@pytest.mark.parametrize(
    "source,result",
    [
        ("short", "short"),
        ("10: Example multi-word Sieben label", "10: Example multi-word\nSieben label"),
        (
            "123: Example very-very long multi-word Sieben label",
            "123: Example very-very\nlong multi-word Sieben\nlabel",
        ),
        (
            "43: Manual-placed\nnewlines\nare ignored",
            "43: Manual-placed\nnewlines\nare\nignored",
        ),
    ],
)
def test_split_long_labels(source, result):
    assert split_long(source) == result


def test_dot_export():
    goals = build_goaltree(
        open_(1, "Root", [2, 3, 4, 5], blockers=[6]),
        clos_(
            2,
            "This is closed goal with no children or blockers. It also has a long name that must be compacted",
        ),
        open_(3, 'I have some "special" symbols', [6, 7], select=selected),
        clos_(4, ""),
        open_(5, "Many blockerz", blockers=[2, 4, 6, 7]),
        clos_(6, "!@#$%^&*()\\/,.?"),
        open_(7, ";:[{}]<>", select=previous),
    )
    actual = dot_export(goals).split("\n")
    sample_path = Path(__file__).parent / "data" / "dot_export_sample.dot"
    with sample_path.open() as f:
        expected = [s.rstrip() for s in f.readlines()]
    assert expected == actual
