from typing import List

from approvaltests import verify, Options  # type: ignore
from approvaltests.reporters import GenericDiffReporterFactory  # type: ignore
from approvaltests.reporters.generic_diff_reporter import GenericDiffReporter  # type: ignore

from siebenapp.cli import IO, update_message, loop
from siebenapp.system import load


class DummyIO(IO):
    def __init__(self, commands: List[str] = None, log: List[str] = None):
        super().__init__()
        self.commands = [] if commands is None else commands
        self.log = [] if log is None else log

    def write(self, text: str, *args) -> None:
        self.log.append(" ".join([text, *args]))

    def read(self) -> str:
        if self.commands:
            command = self.commands.pop(0)
            self.log.append(f"> {command}\n")
            return command
        self.log.append("*USER BREAK*")
        raise EOFError("Commands list is empty")


def test_simple_scenario():
    log = []
    commands = [
        "r Approval testing",
        "a Measure coverage",
        "2",
        "a Build simple test",
        "3",
        "c",
    ]
    io = DummyIO(commands, log)
    db_name = ":memory:"
    goals = load(db_name, update_message)
    loop(io, goals, db_name)
    verify("\n".join(log), reporter=GenericDiffReporterFactory().get_first_working())


def test_complex_scenario():
    log = []
    commands = [
        "r Cover all current features",
        "a Filter view",
        "a Toggle show open/closed goals",
        "a Toggle show goal progress",
        "a Toggle show switchable goals",
        "a Toggle zoom and unzoom",
        "2",
        "h",
        "6",
        "l",
        "2",
        "z",
        "2",
        "c",
        "z",
        "f Toggle",
        "n",
        "2",
        "c",
        "f",
        "p",
        "t",
        "n",
        "t",
        "4",
        "c",
        "2",
        "c",
        "p",
        "c",
        # exit
        "q",
    ]
    io = DummyIO(commands, log)
    db_name = ":memory:"
    goals = load(db_name, update_message)
    loop(io, goals, db_name)
    verify("\n".join(log), reporter=GenericDiffReporterFactory().get_first_working())
