from dataclasses import dataclass
from tempfile import NamedTemporaryFile

from approvaltests.namer import get_default_namer  # type: ignore
from approvaltests import verify, Options  # type: ignore
from approvaltests.reporters import GenericDiffReporterFactory  # type: ignore
from approvaltests.reporters.generic_diff_reporter import GenericDiffReporter  # type: ignore

from siebenapp.manage import print_dot
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
