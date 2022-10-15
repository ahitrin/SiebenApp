from tempfile import NamedTemporaryFile

import pytest
from approvaltests import verify, Options  # type: ignore
from approvaltests.namer import get_default_namer  # type: ignore
from approvaltests.reporters import GenericDiffReporterFactory  # type: ignore
from approvaltests.reporters.generic_diff_reporter import GenericDiffReporter  # type: ignore

from siebenapp.domain import Select, child, RenderRow, RenderResult
from siebenapp.enumeration import Enumeration
from siebenapp.layers import all_layers, persistent_layers
from siebenapp.manage import main, dot_export, extract_subtree
from siebenapp.system import save
from siebenapp.tests.dsl import build_goaltree, open_, clos_, selected, previous
from siebenapp.tests.test_cli import DummyIO
from siebenapp.zoom import ToggleZoom


def test_print_dot_empty_file():
    file_name = NamedTemporaryFile().name
    io = DummyIO()
    main(["dot", file_name], io)
    verify(
        "\n".join(io.log),
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".dot"),
    )


@pytest.fixture
def complex_goaltree_file():
    g = build_goaltree(
        open_(1, "Root", [2, 3, 4, 5, 6], [7, 8]),
        clos_(2, "Closed", blockers=[7]),
        open_(3, "Simply 3", blockers=[5, 8]),
        open_(4, "Also 4", blockers=[5, 6, 7, 8], select=selected),
        open_(5, "Now 5", blockers=[6]),
        clos_(6, "Same 6", blockers=[7]),
        clos_(7, "Lucky 7", [8], select=previous),
        clos_(8, "Finally 8", [9]),
        clos_(9, "Nested 9", [10]),
        clos_(10, "More nested 10", [11]),
        clos_(11, "Even more nested 11"),
    )
    file_name = NamedTemporaryFile().name
    save(all_layers(g), file_name)
    return file_name


def test_print_dot_complex_tree(complex_goaltree_file):
    io = DummyIO()
    main(["dot", complex_goaltree_file], io)
    verify(
        io,
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".dot"),
    )


def test_print_dot_complex_tree_with_closed(complex_goaltree_file):
    io = DummyIO()
    main(["dot", "-n", complex_goaltree_file], io)
    verify(
        io,
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".dot"),
    )


def test_print_dot_complex_tree_with_progress(complex_goaltree_file):
    io = DummyIO()
    main(["dot", "-p", complex_goaltree_file], io)
    verify(
        io,
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".dot"),
    )


def test_print_dot_complex_tree_only_switchable(complex_goaltree_file):
    io = DummyIO()
    main(["dot", "-t", complex_goaltree_file], io)
    verify(
        io,
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".dot"),
    )


def test_dot_export():
    goals = build_goaltree(
        open_(1, "Root", [2, 3, 4, 5], blockers=[6]),
        clos_(
            2,
            "This is closed goal with no children or blockers. "
            "It also has a long name that must be compacted",
        ),
        open_(3, 'I have some "special" symbols', [6, 7], select=selected),
        clos_(4, ""),
        open_(5, "Many blockerz", blockers=[2, 4, 6, 7]),
        clos_(6, "!@#$%^&*()\\/,.?"),
        open_(7, ";:[{}]<>", select=previous),
    )
    verify(
        dot_export(goals),
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".dot"),
    )


def test_print_md_empty_file():
    file_name = NamedTemporaryFile().name
    io = DummyIO()
    main(["md", file_name], io)
    verify(
        io,
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".md"),
    )


def test_print_md_complex_tree(complex_goaltree_file):
    io = DummyIO()
    main(["md", complex_goaltree_file], io)
    verify(
        io,
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".md"),
    )


def test_print_md_complex_tree_with_closed(complex_goaltree_file):
    io = DummyIO()
    main(["md", "-n", complex_goaltree_file], io)
    verify(
        io,
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".md"),
    )


def test_print_md_complex_tree_with_progress(complex_goaltree_file):
    io = DummyIO()
    main(["md", "-p", complex_goaltree_file], io)
    verify(
        io,
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".md"),
    )


def test_print_md_complex_tree_only_switchable(complex_goaltree_file):
    io = DummyIO()
    main(["md", "-t", complex_goaltree_file], io)
    verify(
        io,
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".md"),
    )


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
    assert extract_target.q() == result.q()


def test_zoom_after_extract(extract_source, extract_target):
    result = extract_subtree(extract_source, 2)
    result.accept_all(Select(3), ToggleZoom())
    extract_target.accept_all(Select(3), ToggleZoom())
    assert extract_target.q() == result.q()


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
    assert result.q() == RenderResult(
        rows=[
            RenderRow(1, 1, "Extraction root", True, False, "select", [child(2)]),
            RenderRow(2, 2, "Top", True, True, None, []),
        ]
    )
