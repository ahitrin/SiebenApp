from dataclasses import dataclass
from tempfile import NamedTemporaryFile

from approvaltests.namer import get_default_namer  # type: ignore
from approvaltests import verify, Options  # type: ignore
from approvaltests.reporters import GenericDiffReporterFactory  # type: ignore
from approvaltests.reporters.generic_diff_reporter import GenericDiffReporter  # type: ignore

from siebenapp.layers import all_layers
from siebenapp.manage import print_dot
from siebenapp.system import save
from siebenapp.tests.dsl import build_goaltree, open_, clos_, selected, previous
from siebenapp.tests.test_cli import DummyIO


@dataclass
class FakeArgs:
    db: str


def test_print_dot_empty_file():
    file_name = NamedTemporaryFile().name
    args = FakeArgs(db=file_name)
    log = []
    io = DummyIO([], log)
    print_dot(args, io)
    verify(
        "\n".join(log),
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".dot"),
    )


def test_print_dot_complex_tree():
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
    args = FakeArgs(db=file_name)
    log = []
    io = DummyIO([], log)
    print_dot(args, io)
    verify(
        "\n".join(log),
        GenericDiffReporterFactory().get_first_working(),
        get_default_namer(".dot"),
    )
