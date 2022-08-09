from tempfile import NamedTemporaryFile

import pytest
from approvaltests.namer import get_default_namer  # type: ignore
from approvaltests import verify, Options  # type: ignore
from approvaltests.reporters import GenericDiffReporterFactory  # type: ignore
from approvaltests.reporters.generic_diff_reporter import GenericDiffReporter  # type: ignore

from siebenapp.layers import all_layers
from siebenapp.manage import main, dot_export
from siebenapp.system import save
from siebenapp.tests.dsl import build_goaltree, open_, clos_, selected, previous
from siebenapp.tests.test_cli import DummyIO


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
        clos_(8, "Finally 8"),
    )
    file_name = NamedTemporaryFile().name
    save(all_layers(g), file_name)
    return file_name


def test_print_dot_complex_tree(complex_goaltree_file):
    io = DummyIO()
    main(["dot", complex_goaltree_file], io)
    verify(
        "\n".join(io.log),
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".dot"),
    )


def test_print_dot_complex_tree_with_closed(complex_goaltree_file):
    io = DummyIO()
    main(["dot", "-n", complex_goaltree_file], io)
    verify(
        "\n".join(io.log),
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".dot"),
    )


def test_print_dot_complex_tree_with_progress(complex_goaltree_file):
    io = DummyIO()
    main(["dot", "-p", complex_goaltree_file], io)
    verify(
        "\n".join(io.log),
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".dot"),
    )


def test_print_dot_complex_tree_only_switchable(complex_goaltree_file):
    io = DummyIO()
    main(["dot", "-t", complex_goaltree_file], io)
    verify(
        "\n".join(io.log),
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
