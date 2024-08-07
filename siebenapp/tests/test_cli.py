from typing import Any

from approvaltests import verify  # type: ignore
from approvaltests.namer import get_default_namer  # type: ignore
from approvaltests.reporters import GenericDiffReporterFactory  # type: ignore

from siebenapp.cli import IO, update_message, loop
from siebenapp.system import load


class DummyIO(IO):
    def __init__(self, commands: list[str] | None = None, log: list[str] | None = None):
        super().__init__()
        self.commands = [] if commands is None else commands
        self.log: list[str] = [] if log is None else log

    def write(self, text: str, *args) -> None:
        self.log.append(" ".join([text, *args]))

    def read(self) -> str:
        if self.commands:
            command = self.commands.pop(0)
            self.log.append(f"> {command}\n")
            return command
        self.log.append("*USER BREAK*")
        raise EOFError("Commands list is empty")

    def __str__(self) -> str:
        return "\n".join(self.log)


def verify_file(content: Any, extension: str | None = None) -> None:
    verify(
        content,
        GenericDiffReporterFactory().get_first_working(),
        namer=get_default_namer(extension) if extension else None,
    )


def test_simple_scenario() -> None:
    commands = [
        "r Approval testing",
        "a Measure coverage",
        "2",
        "a Build simple test",
        "3",
        "c",
    ]
    io = DummyIO(commands)
    db_name = ":memory:"
    goals = load(db_name, update_message)
    loop(io, goals, db_name)
    verify_file(io)


def test_complex_scenario() -> None:
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
    io = DummyIO(commands)
    db_name = ":memory:"
    goals = load(db_name, update_message)
    loop(io, goals, db_name)
    verify_file(io)
