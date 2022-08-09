# coding: utf-8
import pytest
from approvaltests import verify  # type: ignore
from approvaltests.namer import get_default_namer  # type: ignore
from approvaltests.reporters import GenericDiffReporterFactory  # type: ignore

from siebenapp.domain import Select, EdgeType
from siebenapp.enumeration import Enumeration
from siebenapp.layers import persistent_layers, all_layers
from siebenapp.system import split_long, extract_subtree
from siebenapp.tests.dsl import build_goaltree, open_, clos_, selected, previous
from siebenapp.zoom import ToggleZoom


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


@pytest.fixture()
def extract_source():
    # Legend: goals marked with 'NX' must not be extracted
    return Enumeration(
        all_layers(
            build_goaltree(
                open_(1, "Root NX", [2, 3], select=selected),
                open_(2, "Extract root", [4, 5], blockers=[3]),
                open_(3, "External blocker NX", [7]),
                open_(4, "Subgoal", blockers=[5]),
                open_(
                    5,
                    "Selected subgoal (selection will be lost)",
                    [6],
                    select=previous,
                ),
                clos_(6, "Closed subgoal", blockers=[7]),
                clos_(7, "Another external blocker NX"),
            )
        )
    )


@pytest.fixture()
def extract_target():
    return persistent_layers(
        build_goaltree(
            open_(1, "Extract root", [2, 3], select=selected),
            open_(2, "Subgoal", blockers=[3]),
            open_(3, "Selected subgoal (selection will be lost)", [4]),
            clos_(4, "Closed subgoal"),
        )
    )


def test_extract_wrong_goal_id(extract_source):
    with pytest.raises(AssertionError):
        extract_subtree(extract_source, 10)


def test_extract_successful(extract_source, extract_target):
    result = extract_subtree(extract_source, 2)
    assert extract_target.q(keys="name,edge,open,selection") == result.q(
        keys="name,edge,open,selection"
    )


def test_zoom_after_extract(extract_source, extract_target):
    result = extract_subtree(extract_source, 2)
    result.accept_all(Select(3), ToggleZoom())
    extract_target.accept_all(Select(3), ToggleZoom())
    assert extract_target.q(keys="name,edge,open,selection") == result.q(
        keys="name,edge,open,selection"
    )


def test_extract_misordered():
    source = Enumeration(
        all_layers(
            build_goaltree(
                open_(1, "Global root", [3], select=selected),
                open_(2, "Top"),
                open_(3, "Extraction root", [2]),
            )
        )
    )
    result = extract_subtree(source, 3)
    assert result.q("name,edge") == {
        1: {"name": "Extraction root", "edge": [(2, EdgeType.PARENT)]},
        2: {"name": "Top", "edge": []},
    }
